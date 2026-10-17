import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import MenuItemForm
from .models import CustomizationOption, MenuItem, Order, OrderItem, OrderItemTopping, Topping, User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MenuManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='menu-admin', role=User.Role.ADMIN)
        cls.customer = User.objects.create_user(username='menu-customer')
        cls.staff = User.objects.create_user(username='menu-staff', role=User.Role.STAFF)
        cls.kitchen = User.objects.create_user(username='menu-kitchen', role=User.Role.KITCHEN)
        cls.pho = MenuItem.objects.create(name='Phở bò', base_price=55000, image_primary='pho.jpg')
        cls.drink = MenuItem.objects.create(name='Món uống đặt tên riêng', base_price=20000, category='DRINK', image_primary='drink.jpg')
        cls.topping = Topping.objects.create(name='Trứng chần', price=5000)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_categories_and_toppings_share_the_catalog(self):
        response = self.client.get(reverse('admin_menu'))
        self.assertContains(response, 'data-filter-category="pho"')
        self.assertContains(response, 'data-filter-category="drink"')
        self.assertContains(response, 'data-filter-category="topping"')
        self.assertContains(response, 'data-filter-group="topping"')
        self.assertNotContains(response, 'Đang ẩn')
        self.assertNotContains(response, 'menu-min-price')

    def test_menu_category_is_an_explicit_form_choice(self):
        form = MenuItemForm()
        self.assertIn('category', form.fields)
        self.assertNotIn('is_active', form.fields)
        self.assertEqual(dict(form.fields['category'].choices)['DRINK'], 'Đồ uống')

    def test_inactive_items_are_not_listed_in_admin_or_customer_menu(self):
        self.pho.is_active = False
        self.pho.save(update_fields=['is_active'])
        self.topping.is_active = False
        self.topping.save(update_fields=['is_active'])
        self.assertNotContains(self.client.get(reverse('admin_menu')), 'data-filter-item="Phở bò"')
        self.client.logout()
        response = self.client.get(reverse('menu'))
        self.assertNotIn(self.pho.pk, [item['id'] for item in response.context['menu_payload']])
        self.assertNotIn(self.topping.pk, [item['id'] for item in response.context['toppings']])

    def test_customer_menu_uses_saved_category_instead_of_guessing_name(self):
        self.client.logout()
        items = self.client.get(reverse('menu')).context['menu_payload']
        drink = next(item for item in items if item['id'] == self.drink.pk)
        self.assertEqual(drink['category'], 'drink')

    def test_delete_removes_menu_item_from_catalog_and_is_repeatable(self):
        url = reverse('admin_menu_delete', args=[self.pho.pk])
        for _ in range(2):
            self.assertRedirects(self.client.post(url), reverse('admin_menu'))
        self.pho.refresh_from_db()
        self.assertFalse(self.pho.is_active)
        self.assertNotContains(self.client.get(reverse('admin_menu')), 'data-filter-item="Phở bò"')

    def test_delete_removes_topping_and_is_repeatable(self):
        url = reverse('admin_topping_delete', args=[self.topping.pk])
        for _ in range(2):
            self.assertRedirects(self.client.post(url), reverse('admin_menu'))
        self.topping.refresh_from_db()
        self.assertFalse(self.topping.is_active)
        self.assertNotContains(self.client.get(reverse('admin_menu')), 'data-filter-item="Trứng chần"')

    def test_delete_preserves_paid_order_items_toppings_and_prices(self):
        order = Order.objects.create(order_code='MENU-HISTORY', total_amount=120000)
        item = OrderItem.objects.create(order=order, menu_item=self.pho, quantity=2, item_price=60000)
        extra = OrderItemTopping.objects.create(order_item=item, topping=self.topping, quantity=2)
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.COMPLETED
        order.save()
        self.client.post(reverse('admin_menu_delete', args=[self.pho.pk]))
        self.client.post(reverse('admin_topping_delete', args=[self.topping.pk]))
        item.refresh_from_db()
        extra.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(item.item_price, 60000)
        self.assertEqual(extra.quantity, 2)
        self.assertEqual(order.total_amount, 120000)
        response = self.client.get(reverse('admin_order_detail', args=[order.pk]))
        self.assertContains(response, 'Phở bò')
        self.assertContains(response, 'Trứng chần')
        self.assertContains(response, '120.000 ₫')

    def test_deleted_catalog_entries_cannot_be_edited_back_into_menu(self):
        for name, delete, edit, item in [
            ('Phở bò', 'admin_menu_delete', 'admin_menu_edit', self.pho),
            ('Trứng chần', 'admin_topping_delete', 'admin_topping_edit', self.topping),
        ]:
            self.client.post(reverse(delete, args=[item.pk]))
            self.assertEqual(self.client.get(reverse(edit, args=[item.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse(edit, args=[item.pk]), {'name': name, 'base_price': 1, 'price': 1}).status_code, 404)

    def test_deletion_requires_admin_post_and_csrf(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.admin)
        for route, item in [('admin_menu_delete', self.pho), ('admin_topping_delete', self.topping)]:
            url = reverse(route, args=[item.pk])
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(secure.post(url).status_code, 403)
            for user in [self.customer, self.staff, self.kitchen]:
                self.client.force_login(user)
                self.assertEqual(self.client.post(url).status_code, 302)
            item.refresh_from_db()
            self.assertTrue(item.is_active)
            self.client.force_login(self.admin)

    def test_deleted_topping_in_stale_cart_is_rejected(self):
        self.client.post(reverse('admin_topping_delete', args=[self.topping.pk]))
        self.client.force_login(self.customer)
        options = {}
        for option in CustomizationOption.objects.all():
            options.setdefault(option.category, option.pk)
        response = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{'id': self.pho.pk, 'qty': 1, 'toppings': [self.topping.pk], 'customizations': list(options.values())}]),
        }, follow=True)
        self.assertFalse(Order.objects.filter(customer=self.customer).exists())
        self.assertContains(response, 'Tùy chọn món không hợp lệ')
