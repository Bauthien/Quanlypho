import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse

from .models import Ingredient, InventoryTransaction, MenuItem, Order, OrderItem, OrderItemTopping, Recipe, Table, Topping, User
from .services import apply_order_action


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class StockLimitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ingredient = Ingredient.objects.create(name='Bánh phở thử', unit='kg', current_stock=1)
        cls.menu = MenuItem.objects.create(name='Phở thử', base_price=50000, image_primary='pho.jpg')
        cls.topping = Topping.objects.create(name='Bánh thêm', price=5000)
        cls.recipe = Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=1)
        cls.admin = User.objects.create_user(username='stock-admin', role='ADMIN')
        cls.staff = User.objects.create_user(username='stock-staff', role='STAFF')
        cls.customer = User.objects.create_user(username='stock-customer')
        cls.table = Table.objects.create(table_number='STOCK-1')

    def make_order(self, quantity=2, payment_method='CASH'):
        order = Order.objects.create(
            order_code=f'STOCK-{Order.objects.count()}', customer=self.customer,
            table=self.table, payment_method=payment_method, total_amount=quantity * 50000,
        )
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=quantity, item_price=50000)
        return order

    def assert_pending_without_exports(self, order):
        order.refresh_from_db()
        self.ingredient.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.CART)
        self.assertEqual(self.ingredient.current_stock, 1)
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_cash_action_rejects_shortage_without_changing_payment_or_stock(self):
        order = self.make_order()
        with self.assertRaisesMessage(ValueError, 'Không đủ tồn kho'):
            apply_order_action(order.pk, 'confirm_cash')
        self.assert_pending_without_exports(order)

    def test_direct_paid_save_rolls_back_payment_when_stock_is_short(self):
        order = self.make_order()
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        with self.assertRaisesMessage(ValueError, 'Không đủ tồn kho'):
            order.save()
        self.assert_pending_without_exports(order)

    def test_exact_stock_can_be_sold_to_zero(self):
        order = self.make_order(quantity=1)
        apply_order_action(order.pk, 'confirm_cash')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 0)
        self.assertEqual(InventoryTransaction.objects.get().quantity_changed, -1)

    def test_totals_include_all_order_lines(self):
        order = self.make_order(quantity=1)
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=1, item_price=50000)
        with self.assertRaises(ValueError):
            apply_order_action(order.pk, 'confirm_cash')
        self.assert_pending_without_exports(order)

    def test_totals_include_main_and_topping_using_same_ingredient(self):
        order = self.make_order(quantity=1)
        Recipe.objects.create(topping=self.topping, ingredient=self.ingredient, quantity_required=Decimal('0.20'))
        OrderItemTopping.objects.create(order_item=order.items.get(), topping=self.topping, quantity=1)
        with self.assertRaises(ValueError):
            apply_order_action(order.pk, 'confirm_cash')
        self.assert_pending_without_exports(order)

    def test_shortage_in_one_ingredient_leaves_all_other_ingredients_untouched(self):
        other = Ingredient.objects.create(name='Thịt bò thử', unit='kg', current_stock=5)
        Recipe.objects.create(menu_item=self.menu, ingredient=other, quantity_required=1)
        order = self.make_order()
        with self.assertRaises(ValueError):
            apply_order_action(order.pk, 'confirm_cash')
        other.refresh_from_db()
        self.assertEqual(other.current_stock, 5)
        self.assert_pending_without_exports(order)

    def test_staff_and_admin_show_shortage_instead_of_server_error(self):
        order = self.make_order()
        for user, route, payload in [
            (self.admin, 'admin_order_action', {'action': 'confirm_cash'}),
            (self.staff, 'confirm_cash', {}),
        ]:
            with self.subTest(route=route):
                self.client.force_login(user)
                response = self.client.post(reverse(route, args=[order.pk]), payload, follow=True)
                self.assertContains(response, 'Không đủ tồn kho')
                self.assertContains(response, 'Bánh phở thử')
                self.assert_pending_without_exports(order)

    @override_settings(DEBUG=True)
    def test_simulated_qr_payment_shows_shortage_and_can_retry_after_restock(self):
        order = self.make_order(payment_method='VIETQR')
        self.client.force_login(self.customer)
        url = reverse('simulate_vietqr_payment', args=[order.pk])
        response = self.client.post(url, follow=True)
        self.assertContains(response, 'Không đủ tồn kho')
        self.assert_pending_without_exports(order)
        Ingredient.objects.filter(pk=self.ingredient.pk).update(current_stock=2)
        self.client.post(url)
        order.refresh_from_db()
        self.ingredient.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.ingredient.current_stock, 0)
        self.assertEqual(InventoryTransaction.objects.count(), 1)

    @override_settings(PAYMENT_WEBHOOK_SECRET='stock-test-secret')
    def test_verified_qr_callback_returns_reconciliation_error_for_shortage(self):
        order = self.make_order(payment_method='VIETQR')
        body = json.dumps({'order_code': order.order_code, 'amount': order.total_amount, 'status': 'paid'}).encode()
        signature = hmac.new(b'stock-test-secret', body, hashlib.sha256).hexdigest()
        response = self.client.post(
            reverse('vietqr_webhook'), body, content_type='application/json', HTTP_X_PAYMENT_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.json()['requires_reconciliation'])
        self.assert_pending_without_exports(order)

    def test_unrelated_order_save_does_not_deduct_for_unsaved_payment_status(self):
        order = self.make_order(quantity=1)
        order.payment_status = Order.PaymentStatus.PAID
        order.guest_name = 'Khách thử'
        order.save(update_fields=['guest_name'])
        self.assert_pending_without_exports(order)

    def test_database_rejects_negative_stock_and_minimum_even_with_queryset_update(self):
        for field in ['current_stock', 'minimum_stock']:
            with self.subTest(field=field), self.assertRaises(IntegrityError), transaction.atomic():
                Ingredient.objects.filter(pk=self.ingredient.pk).update(**{field: -1})


class ConcurrentStockLimitTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_different_orders_cannot_oversell_shared_stock(self):
        ingredient = Ingredient.objects.create(name='Bánh phở giới hạn', unit='kg', current_stock=1)
        menu = MenuItem.objects.create(name='Phở giới hạn', base_price=50000, image_primary='pho.jpg')
        Recipe.objects.create(menu_item=menu, ingredient=ingredient, quantity_required=1)
        orders = []
        for index in range(2):
            order = Order.objects.create(order_code=f'STOCK-CONCURRENT-{index}', payment_method='CASH')
            OrderItem.objects.create(order=order, menu_item=menu, quantity=1, item_price=50000)
            orders.append(order.pk)
        barrier = Barrier(2)

        def confirm(order_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                apply_order_action(order_id, 'confirm_cash')
                return 'paid'
            except ValueError:
                return 'shortage'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, orders))
        self.assertCountEqual(results, ['paid', 'shortage'])
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.current_stock, 0)
        self.assertEqual(Order.objects.filter(payment_status='PAID').count(), 1)
        self.assertEqual(InventoryTransaction.objects.count(), 1)


class LegacyNegativeStockMigrationTests(TransactionTestCase):
    def test_migration_preserves_old_balance_but_rejects_new_negative_writes(self):
        before = ('pho_app', '0013_protect_inventory_and_table_history')
        after = ('pho_app', '0014_prevent_negative_inventory')
        executor = MigrationExecutor(connection)
        try:
            executor.migrate([before])
            IngredientBefore = executor.loader.project_state([before]).apps.get_model('pho_app', 'Ingredient')
            ingredient = IngredientBefore.objects.create(name='Tồn âm cũ', unit='kg', current_stock=-100)
        finally:
            MigrationExecutor(connection).migrate([after])
        ingredient = Ingredient.objects.get(pk=ingredient.pk)
        self.assertEqual(ingredient.current_stock, -100)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ingredient.objects.filter(pk=ingredient.pk).update(current_stock=-99)
        admin = User.objects.create_user(username='stock-reconcile-admin', role='ADMIN')
        self.client.force_login(admin)
        response = self.client.post(reverse('admin_ingredient_import', args=[ingredient.pk]), {'quantity': 1}, follow=True)
        self.assertContains(response, 'kiểm kê')
        self.assertFalse(InventoryTransaction.objects.exists())
        response = self.client.post(reverse('admin_ingredient_edit', args=[ingredient.pk]), {
            'name': ingredient.name, 'unit': 'kg', 'current_stock': '0', 'minimum_stock': '0',
        })
        self.assertEqual(response.status_code, 302)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.current_stock, 0)
        self.assertEqual(InventoryTransaction.objects.get().quantity_changed, 100)
