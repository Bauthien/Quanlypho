"""Order management uses the real workflow against an isolated test database."""
import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from threading import Barrier

from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from .models import (
    CustomizationOption, Ingredient, InventoryTransaction, MenuItem, Order,
    OrderItem, OrderItemCustomization, OrderItemTopping, Recipe, Table, Topping, User,
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class OrderManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='orders-admin', role=User.Role.ADMIN)
        cls.customer = User.objects.create_user(username='anbinh', full_name='An Bình')
        cls.staff = User.objects.create_user(username='orders-staff', role=User.Role.STAFF)
        cls.kitchen = User.objects.create_user(username='orders-kitchen', role=User.Role.KITCHEN)
        cls.table = Table.objects.create(table_number='A12', status=Table.Status.OCCUPIED)
        cls.menu = MenuItem.objects.create(name='Phở tái', base_price=50000, image_primary='pho.jpg')
        cls.topping = Topping.objects.create(name='Trứng chần', price=5000)
        cls.ingredient = Ingredient.objects.create(name='Nguyên liệu thử', unit='kg', current_stock=100)
        Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=Decimal('.2'))
        Recipe.objects.create(topping=cls.topping, ingredient=cls.ingredient, quantity_required=Decimal('.05'))
        cls.order = Order.objects.create(
            order_code='PHO-TEST', customer=cls.customer, table=cls.table,
            payment_method=Order.PaymentMethod.CASH, total_amount=110000,
        )
        cls.item = OrderItem.objects.create(order=cls.order, menu_item=cls.menu, quantity=2, item_price=55000, note='Ít cay')
        OrderItemTopping.objects.create(order_item=cls.item, topping=cls.topping, quantity=2)
        option = CustomizationOption.objects.first()
        OrderItemCustomization.objects.create(order_item=cls.item, customization=option)

    def setUp(self):
        self.client.force_login(self.admin)

    def action(self, action, order=None, **kwargs):
        return self.client.post(reverse('admin_order_action', args=[(order or self.order).pk]), {'action': action}, **kwargs)

    def make_order(self, code='OTHER', **kwargs):
        return Order.objects.create(order_code=code, total_amount=70000, **kwargs)

    def mark_paid(self, status=Order.OrderStatus.PENDING_KITCHEN, order=None):
        order = order or self.order
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = status
        order.save()
        return order

    def test_only_admin_can_view_list_and_detail(self):
        paths = [reverse('admin_orders'), reverse('admin_order_detail', args=[self.order.pk])]
        for user in [self.customer, self.staff, self.kitchen]:
            self.client.force_login(user)
            for path in paths:
                with self.subTest(role=user.role, path=path):
                    self.assertRedirects(self.client.get(path), reverse(user.home_url_name()), fetch_redirect_response=False)
        self.client.logout()
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 302)
        self.client.force_login(self.admin)
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_actions_require_admin_post_and_csrf(self):
        url = reverse('admin_order_action', args=[self.order.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(self.admin)
        self.assertEqual(secure_client.post(url, {'action': 'confirm_cash'}).status_code, 403)
        for user in [self.customer, self.staff, self.kitchen]:
            self.client.force_login(user)
            self.action('confirm_cash')
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_sidebar_and_dashboard_link_to_new_pages(self):
        response = self.client.get(reverse('admin_orders'))
        self.assertContains(response, f'href="{reverse("admin_orders")}" aria-current="page"')
        self.assertContains(self.client.get(reverse('admin_home')), reverse('admin_order_detail', args=[self.order.pk]))

    def test_search_by_code_customer_username_table_and_shipping_code(self):
        self.order.shipping_code = 'VD-TIMKIEM'
        self.order.save(update_fields=['shipping_code'])
        self.make_order()
        for query in ['PHO-TEST', 'An Bình', 'anbinh', 'A12', 'VD-TIMKIEM']:
            with self.subTest(query=query):
                response = self.client.get(reverse('admin_orders'), {'q': query})
                self.assertEqual([row.pk for row in response.context['page_obj']], [self.order.pk])

    def test_guest_name_search_and_customer_name_priority(self):
        guest = self.make_order(guest_name='Khách vãng lai')
        response = self.client.get(reverse('admin_orders'), {'q': 'vãng lai'})
        self.assertEqual([row.pk for row in response.context['page_obj']], [guest.pk])
        self.order.guest_name = 'Tên dự phòng'
        self.order.save(update_fields=['guest_name'])
        response = self.client.get(reverse('admin_order_detail', args=[self.order.pk]))
        self.assertContains(response, 'An Bình')
        self.assertNotContains(response, 'Tên dự phòng')

    def test_combined_filters_and_paid_total_include_delivery_fee(self):
        order = self.make_order(
            order_type=Order.OrderType.DELIVERY, payment_method=Order.PaymentMethod.VIETQR,
            payment_status=Order.PaymentStatus.PAID, order_status=Order.OrderStatus.DELIVERING, delivery_fee=23000,
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse('admin_orders'), {
            'order_type': 'DELIVERY', 'order_status': 'DELIVERING', 'payment_status': 'PAID',
            'payment_method': 'VIETQR', 'date_from': today, 'date_to': today,
        })
        self.assertEqual([row.pk for row in response.context['page_obj']], [order.pk])
        stats = response.context['stats']
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['delivering'], 1)
        self.assertEqual(stats['paid_total'], Decimal('93000'))
        self.assertContains(response, '93.000 ₫')

    def test_stats_cover_full_filtered_result_not_current_page(self):
        for index in range(25):
            self.make_order(code=f'GROUP-{index:02}', payment_status=Order.PaymentStatus.PAID,
                            order_status=Order.OrderStatus.COOKING, delivery_fee=10000)
        response = self.client.get(reverse('admin_orders'), {'q': 'GROUP', 'page': 2, 'sort': 'oldest'})
        self.assertEqual(len(response.context['page_obj']), 5)
        self.assertEqual(response.context['stats']['total'], 25)
        self.assertEqual(response.context['stats']['preparing'], 25)
        self.assertEqual(response.context['stats']['paid_total'], 2000000)
        self.assertContains(response, 'q=GROUP')
        self.assertContains(response, 'sort=oldest')
        self.assertNotContains(response, 'page=2&amp;page=')

    def test_all_stat_buckets_and_unpaid_amount_exclusion(self):
        for status in ['PENDING_KITCHEN', 'COOKING', 'READY', 'DELIVERING', 'COMPLETED', 'CANCELLED']:
            self.make_order(code=status, order_status=status,
                            payment_status='FAILED' if status == 'CANCELLED' else 'PAID')
        stats = self.client.get(reverse('admin_orders')).context['stats']
        self.assertEqual({key: stats[key] for key in ['total', 'waiting', 'preparing', 'ready', 'delivering', 'completed', 'cancelled']},
                         dict(total=7, waiting=1, preparing=2, ready=1, delivering=1, completed=1, cancelled=1))
        self.assertEqual(stats['paid_total'], 350000)

    def test_dates_use_local_timezone_including_end_date(self):
        local = timezone.make_aware(datetime(2026, 10, 5, 23, 59, 59))
        Order.objects.filter(pk=self.order.pk).update(created_at=local)
        self.make_order()
        response = self.client.get(reverse('admin_orders'), {'date_from': '2026-10-05', 'date_to': '2026-10-05'})
        self.assertEqual([row.pk for row in response.context['page_obj']], [self.order.pk])

    def test_invalid_filters_show_errors_without_server_error(self):
        for query in [{'date_from': 'abc'}, {'date_from': '2026-10-10', 'date_to': '2026-10-01'},
                      {'sort': 'total_amount; DROP TABLE'}, {'order_status': 'UNKNOWN'}, {'q': 'x' * 201}]:
            with self.subTest(query=query):
                response = self.client.get(reverse('admin_orders'), query)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['filter_form'].errors)
                self.assertEqual(response.context['stats']['total'], 0)
        for page in ['abc', '-1', '999999']:
            self.assertEqual(self.client.get(reverse('admin_orders'), {'page': page}).status_code, 200)

    def test_empty_and_sorting(self):
        newer = self.make_order(delivery_fee=100000)
        response = self.client.get(reverse('admin_orders'))
        self.assertEqual(response.context['page_obj'][0], newer)
        response = self.client.get(reverse('admin_orders'), {'sort': 'oldest'})
        self.assertEqual(response.context['page_obj'][0], self.order)
        response = self.client.get(reverse('admin_orders'), {'sort': 'total_desc'})
        self.assertEqual(response.context['page_obj'][0], newer)
        response = self.client.get(reverse('admin_orders'), {'sort': 'total_asc'})
        self.assertEqual(response.context['page_obj'][0], self.order)
        response = self.client.get(reverse('admin_orders'), {'q': 'không tồn tại'})
        self.assertContains(response, 'Không tìm thấy đơn hàng')
        self.assertEqual(response.context['stats']['paid_total'], 0)

    def test_detail_keeps_saved_prices_without_adding_toppings_twice(self):
        MenuItem.objects.filter(pk=self.menu.pk).update(base_price=999999)
        Topping.objects.filter(pk=self.topping.pk).update(price=888888)
        self.order.delivery_fee = 23000
        self.order.save(update_fields=['delivery_fee'])
        response = self.client.get(reverse('admin_order_detail', args=[self.order.pk]))
        self.assertEqual(response.context['grand_total'], 133000)
        self.assertEqual(response.context['order_items'][0].line_total, 110000)
        for text in ['55.000 ₫', '110.000 ₫', '133.000 ₫', 'Trứng chần', 'Ít cay']:
            self.assertContains(response, text)
        self.assertNotContains(response, '999.999')
        self.assertNotContains(response, '888.888')

    def test_detail_queries_do_not_grow_with_item_count(self):
        url = reverse('admin_order_detail', args=[self.order.pk])
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as one:
            self.client.get(url)
        for _ in range(10):
            item = OrderItem.objects.create(order=self.order, menu_item=self.menu, quantity=1, item_price=55000)
            OrderItemTopping.objects.create(order_item=item, topping=self.topping, quantity=1)
        with CaptureQueriesContext(connection) as many:
            self.client.get(url)
        self.assertEqual(len(one), len(many))

    def test_cash_dine_in_lifecycle_preserves_separate_table_cleaning(self):
        for action, status in [('confirm_cash', 'PENDING_KITCHEN'), ('start_cooking', 'COOKING'),
                               ('finish_cooking', 'READY'), ('complete_dine_in', 'COMPLETED')]:
            self.assertEqual(self.action(action).status_code, 302)
            self.order.refresh_from_db()
            self.assertEqual(self.order.order_status, status)
        self.assertFalse(self.order.is_cleared)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.OCCUPIED)
        self.client.post(reverse('free_table', args=[self.table.pk]))
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_cleared)

    def test_delivery_lifecycle_and_existing_direct_kitchen_finish_exception(self):
        self.order.order_type = Order.OrderType.DELIVERY
        self.mark_paid()
        for action, status in [('finish_cooking', 'READY'), ('handover_delivery', 'DELIVERING'), ('complete_delivery', 'COMPLETED')]:
            self.action(action)
            self.order.refresh_from_db()
            self.assertEqual(self.order.order_status, status)
        self.assertTrue(self.order.shipping_code)

    def test_invalid_transitions_do_not_change_data(self):
        for action in ['start_cooking', 'finish_cooking', 'handover_delivery', 'complete_delivery', 'complete_dine_in', 'UNKNOWN']:
            self.action(action)
            self.order.refresh_from_db()
            self.assertEqual(self.order.order_status, Order.OrderStatus.CART)
            self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(InventoryTransaction.objects.exists())
        self.mark_paid(Order.OrderStatus.READY)
        self.action('handover_delivery')  # A dine-in order cannot be handed to a courier.
        self.action('cancel_cash')
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.READY)

    def test_unpaid_ready_order_cannot_be_served_or_delivered(self):
        for order_type, actions in [('DINE_IN', ['complete_dine_in']), ('DELIVERY', ['handover_delivery', 'complete_delivery'])]:
            Order.objects.filter(pk=self.order.pk).update(order_type=order_type, order_status='READY')
            for action in actions:
                self.action(action)
                self.order.refresh_from_db()
                self.assertEqual(self.order.order_status, Order.OrderStatus.READY)

    def test_vietqr_and_queue_cart_cannot_be_manually_confirmed(self):
        Order.objects.filter(pk=self.order.pk).update(payment_method='VIETQR')
        self.action('confirm_cash')
        self.action('cancel_cash')
        Order.objects.filter(pk=self.order.pk).update(payment_method='CASH', order_type='QUEUE_CART')
        self.action('confirm_cash')
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_kitchen_can_only_open_orders_in_kitchen_workflow(self):
        kitchen = User.objects.create_user(username='scoped-kitchen', role=User.Role.KITCHEN)
        self.client.force_login(kitchen)

        self.assertRedirects(
            self.client.get(reverse('order_detail', args=[self.order.pk])),
            reverse('menu'),
            fetch_redirect_response=False,
        )
        Order.objects.filter(pk=self.order.pk).update(
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.PENDING_KITCHEN,
        )
        self.assertEqual(self.client.get(reverse('order_detail', args=[self.order.pk])).status_code, 200)
        Order.objects.filter(pk=self.order.pk).update(order_status=Order.OrderStatus.COMPLETED)
        self.assertRedirects(
            self.client.get(reverse('order_detail', args=[self.order.pk])),
            reverse('menu'),
            fetch_redirect_response=False,
        )

    def test_staff_cannot_clear_table_with_unfinished_order(self):
        order = self.make_order(code='UNFINISHED-TABLE', table=self.table, order_status=Order.OrderStatus.COOKING)
        self.client.force_login(self.staff)

        response = self.client.post(reverse('free_table', args=[self.table.pk]))

        self.assertRedirects(response, reverse('staff_home'))
        order.refresh_from_db()
        self.table.refresh_from_db()
        self.assertFalse(order.is_cleared)
        self.assertEqual(self.table.status, Table.Status.OCCUPIED)

    def test_staff_cannot_clear_individual_order_before_completion(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('free_order_table', args=[self.order.pk]))

        self.assertEqual(response.status_code, 404)
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_cleared)

    def test_table_assignment_rejects_wrong_order_type_and_insufficient_capacity(self):
        self.client.force_login(self.staff)
        delivery_order = self.make_order(code='DELIVERY-NO-TABLE', order_type=Order.OrderType.DELIVERY)
        response = self.client.post(reverse('assign_order_table', args=[delivery_order.pk]), {'table_id': self.table.pk})
        self.assertRedirects(response, reverse('staff_home'))
        delivery_order.refresh_from_db()
        self.assertIsNone(delivery_order.table_id)

        three_bowls_order = self.make_order(code='THREE-BOWLS', order_type=Order.OrderType.DINE_IN)
        OrderItem.objects.create(order=three_bowls_order, menu_item=self.menu, quantity=5, item_price=50000)
        small_table = Table.objects.create(table_number='SMALL', capacity=4, status=Table.Status.AVAILABLE)
        response = self.client.post(reverse('assign_order_table', args=[three_bowls_order.pk]), {'table_id': small_table.pk})
        self.assertRedirects(response, reverse('staff_home'))
        three_bowls_order.refresh_from_db()
        small_table.refresh_from_db()
        self.assertIsNone(three_bowls_order.table_id)
        self.assertEqual(small_table.status, Table.Status.AVAILABLE)

    def test_table_assignment_releases_paid_dine_in_order_to_kitchen(self):
        order = self.make_order(
            code='WAITING-FOR-SEAT', order_type=Order.OrderType.DINE_IN,
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.PENDING_KITCHEN,
        )
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=2, item_price=50000)
        available_table = Table.objects.create(table_number='AVAILABLE-2', capacity=4)
        self.client.force_login(self.staff)

        cashier_page = self.client.get(reverse('staff_home'))
        queued_order = next(row for row in cashier_page.context['paid_unassigned_orders'] if row.pk == order.pk)
        self.assertEqual(queued_order.pho_count, 2)
        self.assertIn(available_table, queued_order.suitable_tables)
        response = self.client.post(reverse('assign_order_table', args=[order.pk]), {'table_id': available_table.pk})

        self.assertRedirects(response, reverse('staff_home'))
        order.refresh_from_db()
        available_table.refresh_from_db()
        self.assertEqual(order.table_id, available_table.pk)
        self.assertEqual(available_table.status, Table.Status.OCCUPIED)
        self.client.force_login(self.kitchen)
        kitchen_page = self.client.get(reverse('kitchen_home'))
        self.assertIn(order, kitchen_page.context['orders'])

    def test_cashier_must_choose_table_with_capacity_before_cash_confirmation(self):
        order = self.make_order(
            code='CASH-NEEDS-TABLE', order_type=Order.OrderType.DINE_IN,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            order_status=Order.OrderStatus.CART,
        )
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=2, item_price=50000)
        too_small = Table.objects.create(table_number='CAP-1', capacity=1)
        suitable = Table.objects.create(table_number='CAP-2', capacity=2)
        self.client.force_login(self.staff)

        missing = self.client.post(reverse('confirm_cash', args=[order.pk]))
        self.assertRedirects(missing, reverse('staff_home'))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

        rejected = self.client.post(reverse('confirm_cash', args=[order.pk]), {'table_id': too_small.pk})
        self.assertRedirects(rejected, reverse('staff_home'))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertIsNone(order.table_id)

        accepted = self.client.post(reverse('confirm_cash', args=[order.pk]), {'table_id': suitable.pk})
        self.assertRedirects(accepted, reverse('staff_home'))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.order_status, Order.OrderStatus.PENDING_KITCHEN)
        self.assertEqual(order.table_id, suitable.pk)

    def test_two_of_four_bowls_can_be_cleared_from_cashier_table_map(self):
        table = Table.objects.create(table_number='TABLE-8-TEST', capacity=4, status=Table.Status.OCCUPIED)
        order = self.make_order(
            code='TWO-OF-FOUR', table=table,
            order_type=Order.OrderType.DINE_IN,
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.COMPLETED,
        )
        OrderItem.objects.create(order=order, menu_item=self.menu, quantity=2, item_price=50000)
        self.client.force_login(self.staff)

        response = self.client.get(reverse('staff_table_map'))
        self.assertContains(response, '2 / 4 tô đang dùng')
        cleared = self.client.post(reverse('free_table', args=[table.pk]))

        self.assertRedirects(cleared, reverse('staff_home'))
        order.refresh_from_db()
        table.refresh_from_db()
        self.assertTrue(order.is_cleared)
        self.assertEqual(table.status, Table.Status.AVAILABLE)

    def test_repeated_cash_confirmation_across_screens_deducts_inventory_once(self):
        self.action('confirm_cash')
        self.action('confirm_cash')
        self.client.post(reverse('confirm_cash', args=[self.order.pk]))
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, Decimal('99.50'))
        self.assertEqual(InventoryTransaction.objects.count(), 2)
        self.action('start_cooking')
        self.action('start_cooking')
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.COOKING)
        self.assertEqual(InventoryTransaction.objects.count(), 2)

    @override_settings(PAYMENT_WEBHOOK_SECRET='orders-test-secret')
    def test_vietqr_verified_callback_is_still_required_and_idempotent(self):
        Order.objects.filter(pk=self.order.pk).update(payment_method='VIETQR', delivery_fee=23000)
        body = json.dumps({'order_code': self.order.order_code, 'amount': 133000, 'status': 'paid'}).encode()
        self.assertEqual(self.client.post(reverse('vietqr_webhook'), body, content_type='application/json').status_code, 401)
        signature = hmac.new(b'orders-test-secret', body, hashlib.sha256).hexdigest()
        for _ in range(2):
            response = self.client.post(reverse('vietqr_webhook'), body, content_type='application/json', HTTP_X_PAYMENT_SIGNATURE=signature)
            self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.PENDING_KITCHEN)
        self.assertEqual(InventoryTransaction.objects.count(), 2)

    def test_cancel_only_pending_cash_and_releases_empty_table(self):
        self.action('cancel_cash')
        self.action('cancel_cash')
        self.order.refresh_from_db()
        self.table.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.table.status, Table.Status.AVAILABLE)
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_cancel_does_not_release_table_with_other_active_order(self):
        self.make_order(table=self.table, order_status=Order.OrderStatus.COOKING)
        self.action('cancel_cash')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.OCCUPIED)

    def test_cancel_does_not_release_completed_but_uncleared_table(self):
        self.make_order(table=self.table, order_status=Order.OrderStatus.COMPLETED)
        self.action('cancel_cash')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.OCCUPIED)

    def test_cancel_ignores_orders_that_have_been_cleared(self):
        self.make_order(table=self.table, order_status=Order.OrderStatus.COMPLETED, is_cleared=True)
        self.action('cancel_cash')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.AVAILABLE)

    def test_existing_staff_and_kitchen_permissions_and_actions(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('confirm_cash', args=[self.order.pk]))
        self.client.post(reverse('kitchen_start', args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.PENDING_KITCHEN)
        self.client.force_login(self.kitchen)
        self.client.post(reverse('kitchen_start', args=[self.order.pk]))
        self.client.post(reverse('kitchen_complete', args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.READY)
        self.client.post(reverse('complete_dine_in', args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.READY)

    def test_delivery_labels_only_for_paid_delivery_ready_or_delivering(self):
        self.order.order_type = Order.OrderType.DELIVERY
        self.order.save(update_fields=['order_type'])
        url = reverse('delivery_labels', args=[self.order.pk])
        self.assertNotContains(self.client.get(reverse('admin_order_detail', args=[self.order.pk])), url)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.mark_paid(Order.OrderStatus.READY)
        self.assertContains(self.client.get(reverse('admin_order_detail', args=[self.order.pk])), url)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_nonexistent_order_returns_404(self):
        self.assertEqual(self.client.get(reverse('admin_order_detail', args=[999999])).status_code, 404)
        self.assertEqual(self.client.post(reverse('admin_order_action', args=[999999]), {'action': 'confirm_cash'}).status_code, 404)


class ConcurrentOrderPaymentTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_checkout_locks_table_inside_atomic_transaction(self):
        customer = User.objects.create_user(username='checkout-lock-customer', password='password123')
        table = Table.objects.create(table_number='LOCK-1', capacity=4, status=Table.Status.AVAILABLE)
        menu_item = MenuItem.objects.create(
            name='Phở kiểm tra transaction',
            base_price=50000,
            category=MenuItem.Category.PHO,
            image_primary='pho.jpg',
        )
        ingredient = Ingredient.objects.create(name='Bánh phở kiểm thử khóa bàn', unit='kg', current_stock=10)
        Recipe.objects.create(menu_item=menu_item, ingredient=ingredient, quantity_required='0.20')
        options = {}
        for option in CustomizationOption.objects.all():
            options.setdefault(option.category, option.pk)
        self.assertEqual(set(options), set(CustomizationOption.Category.values))

        client = Client()
        client.force_login(customer)
        response = client.post(reverse('place_order'), {
            'cart': json.dumps([{
                'id': menu_item.pk,
                'qty': 1,
                'toppings': [],
                'customizations': list(options.values()),
            }]),
            'order_type': Order.OrderType.DINE_IN,
            'payment_method': Order.PaymentMethod.VIETQR,
            'table_id': table.pk,
        })

        order = Order.objects.get(customer=customer)
        self.assertRedirects(response, f'{reverse("order_detail", args=[order.pk])}?placed=1')
        self.assertEqual(order.table_id, table.pk)

    @skipUnlessDBFeature('has_select_for_update')
    def test_two_cash_confirmations_deduct_inventory_once(self):
        from .services import InvalidOrderTransition, apply_order_action
        ingredient = Ingredient.objects.create(name='Bò thử', unit='kg', current_stock=10)
        menu = MenuItem.objects.create(name='Phở thử', base_price=50000, image_primary='pho.jpg')
        Recipe.objects.create(menu_item=menu, ingredient=ingredient, quantity_required=1)
        order = Order.objects.create(order_code='CONCURRENT', payment_method='CASH', total_amount=50000)
        OrderItem.objects.create(order=order, menu_item=menu, quantity=1, item_price=50000)
        barrier = Barrier(2)

        def confirm():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                apply_order_action(order.pk, 'confirm_cash')
                return 'changed'
            except InvalidOrderTransition:
                return 'already_processed'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: confirm(), range(2)))
        self.assertCountEqual(results, ['changed', 'already_processed'])
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.current_stock, 9)
        self.assertEqual(InventoryTransaction.objects.count(), 1)


class CustomerOrderingAndTableWorkflowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='khach1', password='password123', role=User.Role.CUSTOMER)
        self.staff = User.objects.create_user(username='thungan1', password='password123', role=User.Role.STAFF)
        self.table = Table.objects.create(table_number='9', capacity=4, status=Table.Status.AVAILABLE)
        self.menu_item = MenuItem.objects.create(name='Phở Tái Lăn', base_price=60000, category=MenuItem.Category.PHO, image_primary='pho.jpg')
        ingredient = Ingredient.objects.create(name='Bánh phở kiểm thử xếp bàn', unit='kg', current_stock=10)
        Recipe.objects.create(menu_item=self.menu_item, ingredient=ingredient, quantity_required='0.20')
        options = {}
        for option in CustomizationOption.objects.all():
            options.setdefault(option.category, option.pk)
        self.options = list(options.values())

    def test_place_order_without_table_cash_and_vietqr(self):
        self.client.force_login(self.customer)
        # 1. Place order with CASH and without table
        res_cash = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{'id': self.menu_item.pk, 'qty': 1, 'toppings': [], 'customizations': self.options}]),
            'order_type': Order.OrderType.DINE_IN,
            'payment_method': Order.PaymentMethod.CASH,
            'table_id': '',
        })
        cash_order = Order.objects.filter(customer=self.customer, payment_method=Order.PaymentMethod.CASH).first()
        self.assertIsNotNone(cash_order)
        self.assertIsNone(cash_order.table)
        self.assertRedirects(res_cash, f"{reverse('order_detail', args=[cash_order.pk])}?placed=1")

        # 2. Place order with VIETQR and without table
        res_qr = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{'id': self.menu_item.pk, 'qty': 2, 'toppings': [], 'customizations': self.options}]),
            'order_type': Order.OrderType.DINE_IN,
            'payment_method': Order.PaymentMethod.VIETQR,
            'table_id': '',
        })
        qr_order = Order.objects.filter(customer=self.customer, payment_method=Order.PaymentMethod.VIETQR).first()
        self.assertIsNotNone(qr_order)
        self.assertIsNone(qr_order.table)
        self.assertRedirects(res_qr, f"{reverse('order_detail', args=[qr_order.pk])}?placed=1")

        # 3. Cashier directs cash customer to table upon payment confirmation
        self.client.force_login(self.staff)
        res_confirm = self.client.post(reverse('confirm_cash', args=[cash_order.pk]), {
            'table_id': self.table.pk,
        })
        self.assertRedirects(res_confirm, reverse('staff_home'))
        cash_order.refresh_from_db()
        self.assertEqual(cash_order.table_id, self.table.pk)
        self.assertEqual(cash_order.payment_status, Order.PaymentStatus.PAID)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.Status.OCCUPIED)

        # 4. Cashier assigns table to QR order
        qr_order.payment_status = Order.PaymentStatus.PAID
        qr_order.order_status = Order.OrderStatus.PENDING_KITCHEN
        qr_order.save(update_fields=['payment_status', 'order_status'])
        qr_table = Table.objects.create(table_number='10', capacity=4, status=Table.Status.AVAILABLE)
        res_assign = self.client.post(reverse('assign_order_table', args=[qr_order.pk]), {
            'table_id': qr_table.pk,
        })
        self.assertRedirects(res_assign, reverse('staff_home'))
        qr_order.refresh_from_db()
        self.assertEqual(qr_order.table_id, qr_table.pk)

    def test_public_reviews_page_does_not_redirect_to_login(self):
        response = self.client.get(reverse('reviews_list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_view_menu(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)

    def test_customer_registration_and_login_by_username_or_phone(self):
        # 1. Register new customer with simple password
        res_reg = self.client.post(reverse('register'), {
            'username': 'khachmoi_test',
            'full_name': 'Khách Mới',
            'phone_number': '0988776655',
            'password1': '123456',
            'password2': '123456',
        })
        self.assertRedirects(res_reg, reverse('menu'))
        new_user = User.objects.filter(username='khachmoi_test').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, User.Role.CUSTOMER)

        # 2. Logout via POST
        res_logout = self.client.post(reverse('logout'))
        self.assertRedirects(res_logout, reverse('login'))

        # 3. Login using mixed-case username
        res_login_username = self.client.post(reverse('login'), {
            'username': 'KhachMoi_Test',
            'password': '123456',
        })
        self.assertRedirects(res_login_username, reverse('menu'))

        # 4. Logout and login using phone number
        self.client.post(reverse('logout'))
        res_login_phone = self.client.post(reverse('login'), {
            'username': '0988776655',
            'password': '123456',
        })
        self.assertRedirects(res_login_phone, reverse('menu'))


