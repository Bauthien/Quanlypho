import json
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    CustomizationOption, Ingredient, InventoryTransaction, MenuItem, Order,
    OrderItem, QueueTicket, Recipe, Table, Topping, User,
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CheckoutStockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username='checkout-stock-customer')
        cls.ingredient = Ingredient.objects.create(name='Bánh phở tươi', unit='kg', current_stock=Decimal('0.10'))
        cls.menu = MenuItem.objects.create(name='Phở cần 200 gram', base_price=50000, image_primary='pho.jpg')
        Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=Decimal('0.20'))
        cls.other = MenuItem.objects.create(name='Phở cần 100 gram', base_price=45000, image_primary='pho.jpg')
        Recipe.objects.create(menu_item=cls.other, ingredient=cls.ingredient, quantity_required=Decimal('0.10'))
        cls.topping = Topping.objects.create(name='Bánh thêm', price=5000)
        Recipe.objects.create(topping=cls.topping, ingredient=cls.ingredient, quantity_required=Decimal('0.05'))
        cls.table = Table.objects.create(table_number='CHECKOUT-STOCK', capacity=10)
        cls.choices = list({option.category: option.pk for option in CustomizationOption.objects.all()}.values())

    def setUp(self):
        self.client.force_login(self.customer)

    def line(self, menu=None, qty=1, toppings=None):
        return {'id': (menu or self.menu).pk, 'qty': qty, 'toppings': toppings or [], 'customizations': self.choices}

    def checkout(self, lines=None, **changes):
        data = {
            'cart': json.dumps(lines or [self.line()]), 'order_type': 'DINE_IN',
            'payment_method': 'VIETQR', 'table_id': self.table.pk,
        }
        data.update(changes)
        return self.client.post(reverse('place_order'), data, follow=True)

    def assert_no_order_or_stock_changes(self):
        self.assertFalse(Order.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists())
        self.ingredient.refresh_from_db()
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.AVAILABLE)
        self.assertNotIn('latest_order_id', self.client.session)

    def test_point_one_kg_rejects_cash_and_qr_before_creating_order(self):
        for method in ['CASH', 'VIETQR']:
            with self.subTest(method=method):
                response = self.checkout(payment_method=method)
                self.assertContains(response, 'Không đủ tồn kho')
                self.assertContains(response, 'Bánh phở tươi')
                self.assert_no_order_or_stock_changes()
                self.assertEqual(self.ingredient.current_stock, Decimal('0.10'))

    def test_guest_cannot_bypass_stock_check(self):
        self.client.logout()
        self.assertContains(self.checkout(), 'Không đủ tồn kho')
        self.assert_no_order_or_stock_changes()

    def test_delivery_cannot_bypass_stock_check(self):
        self.assertContains(self.checkout(order_type='DELIVERY', table_id='', delivery_address='Địa chỉ thử'), 'Không đủ tồn kho')
        self.assert_no_order_or_stock_changes()

    def test_queue_checkout_keeps_ticket_called_when_stock_is_short(self):
        ticket = QueueTicket.objects.create(customer=self.customer, table=self.table, ticket_number='STOCK-Q', status='CALLED')
        self.assertContains(self.checkout(order_type='QUEUE_CART'), 'Không đủ tồn kho')
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, QueueTicket.Status.CALLED)
        self.assert_no_order_or_stock_changes()

    def test_total_requirements_include_different_dishes_using_same_ingredient(self):
        Ingredient.objects.filter(pk=self.ingredient.pk).update(current_stock=Decimal('0.20'))
        self.assertContains(self.checkout([self.line(), self.line(self.other)]), 'Không đủ tồn kho')
        self.assert_no_order_or_stock_changes()
        self.assertEqual(self.ingredient.current_stock, Decimal('0.20'))

    def test_total_requirements_include_toppings(self):
        self.assertContains(self.checkout([self.line(self.other, toppings=[self.topping.pk])]), 'Không đủ tồn kho')
        self.assert_no_order_or_stock_changes()

    def test_exact_stock_is_enough_and_only_deducted_after_payment(self):
        response = self.checkout([self.line(self.other)])
        order = Order.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.payment_status, 'PENDING')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, Decimal('0.10'))
        self.assertFalse(InventoryTransaction.objects.exists())
        order.payment_status = 'PAID'
        order.order_status = 'PENDING_KITCHEN'
        order.save()
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 0)

    def test_pho_without_recipe_cannot_be_ordered(self):
        Recipe.objects.filter(menu_item=self.menu).delete()
        self.assertContains(self.checkout(), 'chưa thể phục vụ')
        self.assert_no_order_or_stock_changes()

    def test_missing_recipe_cannot_bypass_payment_for_old_pending_order(self):
        Recipe.objects.filter(menu_item=self.menu).delete()
        order = self.pending_order()
        order.payment_status = 'PAID'
        with self.assertRaisesMessage(ValueError, 'chưa thể phục vụ'):
            order.save()
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'PENDING')

    def pending_order(self):
        order = Order.objects.create(order_code='CHECKOUT-OLD', customer=self.customer, total_amount=50000)
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=1, item_price=50000)
        return order

    @override_settings(VIETQR_BANK_ID='TEST', VIETQR_ACCOUNT_NO='123456')
    def test_old_pending_order_hides_qr_and_simulation_when_stock_drops(self):
        order = self.pending_order()
        response = self.client.get(reverse('order_detail', args=[order.pk]))
        self.assertContains(response, 'Tạm thời chưa thể thanh toán')
        self.assertNotContains(response, 'class="payment-qr"')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')
        self.assertEqual(response.context['vietqr_image_url'], '')
        Ingredient.objects.filter(pk=self.ingredient.pk).update(current_stock=Decimal('0.20'))
        response = self.client.get(reverse('order_detail', args=[order.pk]))
        self.assertContains(response, 'class="payment-qr"')

    def test_pending_cash_order_does_not_invite_payment_when_stock_is_short(self):
        order = self.pending_order()
        order.payment_method = 'CASH'
        order.save(update_fields=['payment_method'])
        response = self.client.get(reverse('order_detail', args=[order.pk]))
        self.assertContains(response, 'Tạm thời chưa thể thanh toán')
        self.assertNotContains(response, 'Mời bạn thanh toán')

    def test_menu_exposes_actual_sellable_quantities_and_blocks_missing_recipe(self):
        missing = MenuItem.objects.create(name='Phở chưa có công thức', base_price=50000, image_primary='pho.jpg')
        items = {item['id']: item for item in self.client.get(reverse('menu')).context['menu_payload']}
        self.assertFalse(items[self.menu.pk]['is_available'])
        self.assertEqual(items[self.menu.pk]['max_quantity'], 0)
        self.assertTrue(items[self.other.pk]['is_available'])
        self.assertEqual(items[self.other.pk]['max_quantity'], 1)
        self.assertFalse(items[missing.pk]['is_available'])
