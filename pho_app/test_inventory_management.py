from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Ingredient, InventoryTransaction, MenuItem, Order, OrderItem,
    OrderItemTopping, QueueTicket, Recipe, Review, Table, Topping, User,
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InventoryManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='inventory-admin', role=User.Role.ADMIN)
        cls.customer = User.objects.create_user(username='inventory-customer')
        cls.menu = MenuItem.objects.create(name='Phở tái', base_price=50000, image_primary='pho.jpg')
        cls.topping = Topping.objects.create(name='Trứng chần', price=5000)
        cls.ingredient = Ingredient.objects.create(
            name='Nguyên liệu thử', unit='gram', current_stock=100, minimum_stock=10,
        )
        cls.table = Table.objects.create(table_number='INV-1', capacity=4)

    def setUp(self):
        self.client.force_login(self.admin)

    def recipe_payload(self, **changes):
        data = {
            'menu_item_id': self.menu.pk, 'ingredient_id': self.ingredient.pk,
            'quantity_required': '2.50',
        }
        data.update(changes)
        return data

    def test_recipe_rejects_both_targets(self):
        response = self.client.post(reverse('admin_recipe_create'), self.recipe_payload(topping_id=self.topping.pk))
        self.assertRedirects(response, reverse('admin_inventory'))
        self.assertFalse(Recipe.objects.exists())

    def test_recipe_rejects_missing_invalid_or_inactive_target(self):
        self.menu.is_active = False
        self.menu.save(update_fields=['is_active'])
        self.topping.is_active = False
        self.topping.save(update_fields=['is_active'])
        for changes in [
            {'menu_item_id': ''}, {'menu_item_id': 'invalid'}, {'menu_item_id': 999999},
            {}, {'menu_item_id': '', 'topping_id': self.topping.pk},
        ]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('admin_recipe_create'), self.recipe_payload(**changes))
                self.assertEqual(response.status_code, 302)
                self.assertFalse(Recipe.objects.exists())

    def test_recipe_rejects_invalid_amounts(self):
        for amount in ['0', '-1', 'NaN', 'Infinity', '0.001', '100000000', 'invalid']:
            with self.subTest(amount=amount):
                response = self.client.post(reverse('admin_recipe_create'), self.recipe_payload(quantity_required=amount))
                self.assertEqual(response.status_code, 302)
                self.assertFalse(Recipe.objects.exists())

    def test_recipe_accepts_exactly_one_target(self):
        for changes in [{}, {'menu_item_id': '', 'topping_id': self.topping.pk}]:
            with self.subTest(changes=changes):
                self.assertRedirects(
                    self.client.post(reverse('admin_recipe_create'), self.recipe_payload(**changes)),
                    reverse('admin_inventory'),
                )
        self.assertEqual(Recipe.objects.filter(menu_item=self.menu, topping=None).count(), 1)
        self.assertEqual(Recipe.objects.filter(topping=self.topping, menu_item=None).count(), 1)

    def test_model_validation_rejects_ambiguous_recipe(self):
        for targets in [{}, {'menu_item': self.menu, 'topping': self.topping}]:
            with self.subTest(targets=targets), self.assertRaises(ValidationError):
                Recipe(ingredient=self.ingredient, quantity_required=1, **targets).full_clean()

    def test_database_rejects_ambiguous_recipe(self):
        for targets in [{}, {'menu_item': self.menu, 'topping': self.topping}]:
            with self.subTest(targets=targets), self.assertRaises(IntegrityError), transaction.atomic():
                Recipe.objects.create(ingredient=self.ingredient, quantity_required=1, **targets)

    def test_paid_order_deducts_main_and_topping_recipes_once(self):
        Recipe.objects.create(menu_item=self.menu, ingredient=self.ingredient, quantity_required=2)
        Recipe.objects.create(topping=self.topping, ingredient=self.ingredient, quantity_required=3)
        order = Order.objects.create(order_code='INV-PAID', customer=self.customer)
        item = OrderItem.objects.create(order=order, menu_item=self.menu, quantity=2, item_price=50000)
        OrderItemTopping.objects.create(order_item=item, topping=self.topping, quantity=2)
        order.payment_status = Order.PaymentStatus.PAID
        order.save()
        order.save()
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, Decimal('90'))
        # One aggregated export per order/ingredient, even when both BOMs use it.
        self.assertEqual(InventoryTransaction.objects.count(), 1)

    def test_ingredient_with_recipe_cannot_be_deleted(self):
        recipe = Recipe.objects.create(menu_item=self.menu, ingredient=self.ingredient, quantity_required=1)
        self.assertRedirects(
            self.client.post(reverse('admin_ingredient_delete', args=[self.ingredient.pk])),
            reverse('admin_inventory'),
        )
        self.assertTrue(Ingredient.objects.filter(pk=self.ingredient.pk).exists())
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())

    def test_ingredient_with_transactions_cannot_be_deleted(self):
        entry = InventoryTransaction.objects.create(
            ingredient=self.ingredient, transaction_type='IMPORT', quantity_changed=100,
        )
        response = self.client.post(reverse('admin_ingredient_delete', args=[self.ingredient.pk]), follow=True)
        self.assertContains(response, 'Không thể xóa')
        entry.refresh_from_db()
        self.assertEqual(entry.ingredient_id, self.ingredient.pk)
        with self.assertRaises(ProtectedError):
            self.ingredient.delete()

    def test_unused_ingredient_can_be_deleted(self):
        self.client.post(reverse('admin_ingredient_delete', args=[self.ingredient.pk]))
        self.assertFalse(Ingredient.objects.filter(pk=self.ingredient.pk).exists())

    def test_ingredient_create_and_edit_reject_invalid_numbers(self):
        for field in ['current_stock', 'minimum_stock']:
            for amount in ['-1', 'NaN', 'Infinity', '0.001', '100000000', 'invalid']:
                for route, args in [('admin_ingredient_create', []), ('admin_ingredient_edit', [self.ingredient.pk])]:
                    with self.subTest(field=field, amount=amount, route=route):
                        data = {'name': 'Nguyên liệu mới', 'unit': 'gram', 'current_stock': '100', 'minimum_stock': '10'}
                        data[field] = amount
                        response = self.client.post(reverse(route, args=args), data)
                        self.assertEqual(response.status_code, 200)
                        self.assertFalse(Ingredient.objects.filter(name='Nguyên liệu mới').exists())
                        self.ingredient.refresh_from_db()
                        self.assertEqual(self.ingredient.current_stock, 100)
                        self.assertEqual(self.ingredient.minimum_stock, 10)
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_ingredient_form_keeps_values_after_invalid_post(self):
        response = self.client.post(reverse('admin_ingredient_create'), {
            'name': 'Tên đã nhập', 'unit': 'kg', 'current_stock': '-1', 'minimum_stock': '5',
        })
        self.assertContains(response, 'value="Tên đã nhập"')
        self.assertTrue(response.context['form'].errors)

    def test_ingredient_create_edit_and_import_record_exact_changes(self):
        self.client.post(reverse('admin_ingredient_create'), {
            'name': 'Bánh phở thử', 'unit': 'kg', 'current_stock': '20.25', 'minimum_stock': '0',
        })
        ingredient = Ingredient.objects.get(name='Bánh phở thử')
        self.client.post(reverse('admin_ingredient_edit', args=[ingredient.pk]), {
            'name': ingredient.name, 'unit': 'kg', 'current_stock': '10.10', 'minimum_stock': '0',
        })
        self.client.post(reverse('admin_ingredient_import', args=[ingredient.pk]), {'quantity': '0.01'})
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.current_stock, Decimal('10.11'))
        self.assertEqual(
            list(InventoryTransaction.objects.filter(ingredient=ingredient).order_by('pk').values_list('quantity_changed', flat=True)),
            [Decimal('20.25'), Decimal('-10.15'), Decimal('0.01')],
        )

    def test_import_rejects_invalid_amounts_without_stock_changes(self):
        for amount in ['0', '-1', 'NaN', 'Infinity', '0.001', '100000000']:
            with self.subTest(amount=amount):
                response = self.client.post(reverse('admin_ingredient_import', args=[self.ingredient.pk]), {'quantity': amount})
                self.assertEqual(response.status_code, 302)
                self.ingredient.refresh_from_db()
                self.assertEqual(self.ingredient.current_stock, 100)
                self.assertFalse(InventoryTransaction.objects.exists())

    def test_table_create_edit_reject_invalid_capacity(self):
        for capacity in ['0', '-1', '', 'invalid', '1.5', '2147483648']:
            for route, args in [('admin_table_create', []), ('admin_table_edit', [self.table.pk])]:
                with self.subTest(capacity=capacity, route=route):
                    response = self.client.post(reverse(route, args=args), {'table_number': 'INV-NEW', 'capacity': capacity})
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(Table.objects.filter(table_number='INV-NEW').exists())
                    self.table.refresh_from_db()
                    self.assertEqual(self.table.capacity, 4)

    def test_table_form_validates_names_and_accepts_valid_capacity(self):
        duplicate = self.client.post(reverse('admin_table_create'), {'table_number': 'inv-1', 'capacity': '2'})
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Table.objects.count(), 1)
        response = self.client.post(reverse('admin_table_create'), {'table_number': 'INV-NEW', 'capacity': '1'})
        self.assertRedirects(response, reverse('table_map'))
        self.assertEqual(Table.objects.get(table_number='INV-NEW').capacity, 1)

    def test_table_with_orders_cannot_be_deleted(self):
        order = Order.objects.create(order_code='INV-TABLE', table=self.table)
        response = self.client.post(reverse('admin_table_delete', args=[self.table.pk]), follow=True)
        self.assertContains(response, 'Không thể xóa')
        order.refresh_from_db()
        self.assertEqual(order.table_id, self.table.pk)
        with self.assertRaises(ProtectedError):
            self.table.delete()

    def test_table_with_queue_history_cannot_be_deleted(self):
        ticket = QueueTicket.objects.create(ticket_number='INV-Q', table=self.table, status='SEATED')
        self.client.post(reverse('admin_table_delete', args=[self.table.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.table_id, self.table.pk)

    def test_unused_table_can_be_deleted(self):
        self.client.post(reverse('admin_table_delete', args=[self.table.pk]))
        self.assertFalse(Table.objects.filter(pk=self.table.pk).exists())

    def test_reviews_show_order_status_and_fractional_average(self):
        order = Order.objects.create(order_code='INV-REVIEW', order_status='COOKING')
        for rating in [4, 5]:
            Review.objects.create(customer=self.customer, order=order, rating=rating)
        response = self.client.get(reverse('review_list_all'))
        self.assertContains(response, 'Bếp đang làm', count=2)
        self.assertEqual(response.context['avg_rating'], 4.5)
        self.assertContains(response, 'width: 90%')
        self.assertContains(response, 'role="img"')

    def test_inventory_tabs_have_accessible_relationships(self):
        response = self.client.get(reverse('admin_inventory'))
        for tab, panel, selected in [
            ('tabBtnIngredients', 'tabIngredientsSection', 'true'),
            ('tabBtnRecipes', 'tabRecipesSection', 'false'),
            ('tabBtnHistory', 'tabHistorySection', 'false'),
        ]:
            self.assertContains(response, f'role="tab" aria-selected="{selected}"')
            self.assertContains(response, f'aria-controls="{panel}"')
            self.assertContains(response, f'role="tabpanel" aria-labelledby="{tab}"')

    def test_inventory_recipe_selector_starts_with_hidden_target_disabled(self):
        response = self.client.get(reverse('admin_inventory'))
        self.assertContains(response, 'id="toppingSelect" name="topping_id" class="form-input" disabled')

    def test_stock_mutations_require_admin_post(self):
        routes = [
            ('admin_ingredient_delete', [self.ingredient.pk]),
            ('admin_ingredient_import', [self.ingredient.pk]),
            ('admin_recipe_create', []), ('admin_table_delete', [self.table.pk]),
        ]
        for route, args in routes:
            self.assertEqual(self.client.get(reverse(route, args=args)).status_code, 405)
        self.client.force_login(self.customer)
        for route, args in routes:
            self.assertEqual(self.client.post(reverse(route, args=args)).status_code, 302)
        self.assertTrue(Ingredient.objects.filter(pk=self.ingredient.pk).exists())
        self.assertTrue(Table.objects.filter(pk=self.table.pk).exists())
