from django.test import TestCase
import hashlib
import hmac
import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import CustomizationOption, Ingredient, MenuItem, Order, OrderItem, QueueTicket, Recipe, Table, Topping, User


class AuthAndRoleTests(TestCase):
    def test_register_defaults_to_customer(self):
        response = self.client.post(reverse('register'), {
            'username': 'khach1',
            'full_name': 'Nguyen Van A',
            'phone_number': '0900000000',
            'password1': 'Matkhau@123',
            'password2': 'Matkhau@123',
            'role': User.Role.ADMIN,
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='khach1')
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertFalse(user.is_superuser)

    def test_django_admin_is_disabled(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 404)

    def test_only_admin_can_change_roles(self):
        customer = User.objects.create_user(username='c1', password='pass12345', role=User.Role.CUSTOMER)
        staff = User.objects.create_user(username='s1', password='pass12345', role=User.Role.STAFF)
        admin = User.objects.create_user(username='a1', password='pass12345', role=User.Role.ADMIN)

        self.client.login(username='s1', password='pass12345')
        response = self.client.post(reverse('admin_update_role', args=[customer.id]), {
            'role': User.Role.KITCHEN,
            'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.role, User.Role.CUSTOMER)

        self.client.login(username='a1', password='pass12345')
        response = self.client.post(reverse('admin_update_role', args=[customer.id]), {
            'role': User.Role.KITCHEN,
            'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.role, User.Role.KITCHEN)
        self.assertTrue(admin.is_admin_role())
        self.assertTrue(staff.is_staff_role())

    def test_customer_cannot_open_staff_or_admin(self):
        User.objects.create_user(username='c2', password='pass12345', role=User.Role.CUSTOMER)
        self.client.login(username='c2', password='pass12345')
        self.assertEqual(self.client.get(reverse('staff_home')).status_code, 302)
        self.assertEqual(self.client.get(reverse('admin_home')).status_code, 302)
        self.assertEqual(self.client.get(reverse('kitchen_home')).status_code, 302)

    def test_staff_and_kitchen_cannot_cross_into_other_role_actions(self):
        staff = User.objects.create_user(username='role-staff', password='pass12345', role=User.Role.STAFF)
        kitchen = User.objects.create_user(username='role-kitchen', password='pass12345', role=User.Role.KITCHEN)
        item = MenuItem.objects.create(name='Role test pho', base_price=50000)
        order = Order.objects.create(order_code='ROLE-TEST', payment_method=Order.PaymentMethod.CASH)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('kitchen_home')).status_code, 302)
        self.client.post(reverse('kitchen_start', args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.order_status, Order.OrderStatus.CART)

        self.client.force_login(kitchen)
        self.assertEqual(self.client.get(reverse('staff_home')).status_code, 302)
        self.client.post(reverse('confirm_cash', args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.CART)

    def test_state_changing_customer_endpoints_require_csrf(self):
        customer = User.objects.create_user(username='csrf-customer', password='pass12345')
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(customer)
        order_payload = json.dumps([{'id': 1, 'qty': 1, 'toppings': [], 'customizations': []}])

        queue_response = secure_client.post(reverse('take_queue'), {'people_count': '1'})
        order_response = secure_client.post(reverse('place_order'), {'cart': order_payload})

        self.assertEqual(queue_response.status_code, 403)
        self.assertEqual(order_response.status_code, 403)
        self.assertFalse(QueueTicket.objects.exists())
        self.assertFalse(Order.objects.exists())

    def test_logout_requires_csrf_protected_post(self):
        customer = User.objects.create_user(username='logout-customer', password='pass12345')
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(customer)

        self.assertEqual(secure_client.get(reverse('logout')).status_code, 405)
        self.assertEqual(secure_client.post(reverse('logout')).status_code, 403)
        secure_client.get(reverse('menu'))
        token = secure_client.cookies['csrftoken'].value
        self.assertEqual(secure_client.post(reverse('logout'), HTTP_X_CSRFTOKEN=token).status_code, 302)
        self.assertNotIn('_auth_user_id', secure_client.session)

    def test_payment_simulation_is_owner_only_and_development_only(self):
        owner = User.objects.create_user(username='sim-owner', password='pass12345')
        other = User.objects.create_user(username='sim-other', password='pass12345')
        staff = User.objects.create_user(username='sim-staff', password='pass12345', role=User.Role.STAFF)
        order = Order.objects.create(
            order_code='SIM-ROLE-TEST', customer=owner,
            payment_method=Order.PaymentMethod.VIETQR,
        )
        url = reverse('simulate_vietqr_payment', args=[order.pk])
        with override_settings(DEBUG=True):
            self.client.force_login(other)
            self.assertEqual(self.client.post(url).status_code, 302)
            self.client.force_login(staff)
            self.assertEqual(self.client.post(url).status_code, 302)
            order.refresh_from_db()
            self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

            self.client.force_login(owner)
            self.assertEqual(self.client.post(url).status_code, 302)
            order.refresh_from_db()
            self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)

        order.payment_status = Order.PaymentStatus.PENDING
        order.order_status = Order.OrderStatus.CART
        order.save(update_fields=['payment_status', 'order_status'])
        self.client.force_login(owner)
        with override_settings(DEBUG=False):
            self.assertEqual(self.client.post(url).status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_menu_is_public_but_checkout_requires_customer_login(self):
        self.assertEqual(self.client.get(reverse('menu')).status_code, 200)
        self.assertEqual(self.client.post(reverse('take_queue')).status_code, 302)

    def test_customer_can_use_home_and_take_queue_from_menu(self):
        drink = MenuItem.objects.create(
            name='Nước suối', category=MenuItem.Category.DRINK, base_price=8000,
            image_primary='menu_items/water.jpg',
        )
        pho = MenuItem.objects.create(
            name='Phở Tái', category=MenuItem.Category.PHO, base_price=50000,
            image_primary='menu_items/pho.jpg',
        )
        customer = User.objects.create_user(username='queue-customer', password='pass12345')
        self.client.login(username='queue-customer', password='pass12345')

        home_response = self.client.get(reverse('home'))
        self.assertEqual(home_response.status_code, 200)
        self.assertTemplateUsed(home_response, 'pho_app/customer/home.html')
        self.assertEqual(list(home_response.context['featured_items']), [pho])
        self.assertNotIn(drink, home_response.context['featured_items'])

        menu_response = self.client.get(reverse('menu'))
        self.assertContains(menu_response, 'href="/thuc-don/?door=1#queue-banner"')
        self.assertContains(menu_response, 'Lấy số xếp hàng')

        response = self.client.post(reverse('take_queue'), {'people_count': '3'})
        self.assertEqual(response.status_code, 302)
        ticket = QueueTicket.objects.get(customer=customer)
        self.assertEqual(ticket.status, QueueTicket.Status.WAITING)
        self.assertEqual(ticket.people_count, 3)
        self.assertTrue(self.client.get(reverse('queue_status')).json()['active'])

        menu_response = self.client.get(reverse('menu'))
        self.assertContains(menu_response, ticket.ticket_number)
        self.assertContains(menu_response, 'Bạn đã có số xếp hàng, không cần lấy thêm.')
        self.assertNotContains(menu_response, 'Lấy số xếp hàng')

    def test_vietqr_order_waits_for_verified_webhook(self):
        customer = User.objects.create_user(username='qr-customer', password='pass12345')
        table = Table.objects.create(table_number=5)
        item = MenuItem.objects.create(name='Phở Tái', base_price=50000, image_primary='menu_items/pho.jpg')
        ingredient = Ingredient.objects.create(name='Bánh phở kiểm thử QR', unit='kg', current_stock=10)
        Recipe.objects.create(menu_item=item, ingredient=ingredient, quantity_required='0.20')
        topping = Topping.objects.create(name='Trứng chần', price=5000, inventory_mode='UNTRACKED')
        options_by_category = {}
        for option in CustomizationOption.objects.all().order_by('category', 'id'):
            options_by_category.setdefault(option.category, option)
        options = list(options_by_category.values())
        self.assertEqual(len(options), 3)
        self.client.login(username='qr-customer', password='pass12345')
        response = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{
                'id': item.pk,
                'qty': 2,
                'toppings': [topping.pk],
                'customizations': [option.pk for option in options],
                'note': 'Không cay',
            }]),
            'order_type': Order.OrderType.DINE_IN,
            'table_id': table.pk,
            'payment_method': Order.PaymentMethod.VIETQR,
        })
        order = Order.objects.get(customer=customer)
        self.assertRedirects(response, f"{reverse('order_detail', args=[order.pk])}?placed=1")
        self.assertEqual(order.total_amount, 110000)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.CART)
        self.assertEqual(order.items.get().toppings.count(), 1)
        table.refresh_from_db()
        self.assertEqual(table.status, Table.Status.OCCUPIED)

        body = json.dumps({'order_code': order.order_code, 'amount': 110000, 'status': 'success', 'transaction_id': 'BANK-QR-TEST'}).encode()
        signature = hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()
        with override_settings(PAYMENT_WEBHOOK_SECRET='test-secret'):
            response = self.client.post(
                reverse('vietqr_webhook'), data=body, content_type='application/json',
                HTTP_X_PAYMENT_SIGNATURE=signature,
            )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.order_status, Order.OrderStatus.PENDING_KITCHEN)

    def test_invalid_payment_signature_does_not_send_order_to_kitchen(self):
        order = Order.objects.create(order_code='PHO-TEST-INVALID')
        body = json.dumps({'order_code': order.order_code, 'amount': 1, 'status': 'success'}).encode()
        with override_settings(PAYMENT_WEBHOOK_SECRET='test-secret'):
            response = self.client.post(
                reverse('vietqr_webhook'), data=body, content_type='application/json',
                HTTP_X_PAYMENT_SIGNATURE='not-valid',
            )
        self.assertEqual(response.status_code, 401)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.CART)

    def test_failed_payment_callback_cannot_reopen_cancelled_order(self):
        order = Order.objects.create(
            order_code='PHO-FAILED-THEN-PAID',
            payment_method=Order.PaymentMethod.VIETQR,
            total_amount=10000,
        )
        with override_settings(PAYMENT_WEBHOOK_SECRET='test-secret'):
            # A failure notification alone cannot prove that no money can arrive.
            # Explicit cancellation is terminal; late money is retained for reconciliation.
            Order.objects.filter(pk=order.pk).update(payment_status='FAILED', order_status='CANCELLED')
            for status, expected_status in [('failed', 200), ('success', 202)]:
                body = json.dumps({
                    'order_code': order.order_code,
                    'amount': 10000,
                    'status': status,
                    'transaction_id': 'BANK-LATE-TEST',
                }).encode()
                signature = hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()
                response = self.client.post(
                    reverse('vietqr_webhook'), data=body, content_type='application/json',
                    HTTP_X_PAYMENT_SIGNATURE=signature,
                )
                self.assertEqual(response.status_code, expected_status)

        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(order.order_status, Order.OrderStatus.CANCELLED)

    def test_order_detail_rejects_other_customers_even_with_placed_flag(self):
        owner = User.objects.create_user(username='order-owner', password='pass12345')
        stranger = User.objects.create_user(username='order-stranger', password='pass12345')
        order = Order.objects.create(order_code='PRIVATE-ORDER', customer=owner)
        self.client.login(username='order-stranger', password='pass12345')

        response = self.client.get(reverse('order_detail', args=[order.pk]), {'placed': '1'})

        self.assertRedirects(response, reverse('menu'))

    def test_malformed_cart_arrays_are_rejected_without_server_error(self):
        customer = User.objects.create_user(username='bad-cart-customer', password='pass12345')
        item = MenuItem.objects.create(name='Phở Invalid', base_price=45000)
        self.client.login(username='bad-cart-customer', password='pass12345')

        response = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{'id': item.pk, 'qty': 1, 'toppings': None, 'customizations': []}]),
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(customer=customer).exists())
        self.assertContains(response, 'Không tìm thấy món hợp lệ')

    def test_invalid_cash_confirmation_does_not_occupy_selected_table(self):
        staff = User.objects.create_user(username='cashier-invalid', password='pass12345', role=User.Role.STAFF)
        customer = User.objects.create_user(username='qr-not-cash', password='pass12345')
        table = Table.objects.create(table_number=71)
        order = Order.objects.create(
            order_code='QR-NOT-CASH', customer=customer,
            payment_method=Order.PaymentMethod.VIETQR,
        )
        self.client.login(username=staff.username, password='pass12345')

        response = self.client.post(reverse('confirm_cash', args=[order.pk]), {'table_id': table.pk})

        self.assertRedirects(response, reverse('staff_home'))
        order.refresh_from_db()
        table.refresh_from_db()
        self.assertIsNone(order.table_id)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(table.status, Table.Status.AVAILABLE)

    def test_queue_call_does_not_assign_a_table_too_small_for_group(self):
        staff = User.objects.create_user(username='group-cashier', password='pass12345', role=User.Role.STAFF)
        ticket = QueueTicket.objects.create(ticket_number='P-GROUP', people_count=4)
        table = Table.objects.create(table_number=72, capacity=2)
        self.client.login(username=staff.username, password='pass12345')

        response = self.client.post(reverse('call_next_queue'), {'table_id': table.pk})

        self.assertRedirects(response, reverse('staff_home'))
        ticket.refresh_from_db()
        table.refresh_from_db()
        self.assertEqual(ticket.status, QueueTicket.Status.WAITING)
        self.assertIsNone(ticket.table_id)
        self.assertEqual(table.status, Table.Status.AVAILABLE)

    def test_staff_calls_oldest_ticket_to_an_available_table(self):
        staff = User.objects.create_user(username='counter', password='pass12345', role=User.Role.STAFF)
        first = QueueTicket.objects.create(ticket_number='P-001')
        second = QueueTicket.objects.create(ticket_number='P-002')
        table = Table.objects.create(table_number=3)
        self.client.login(username='counter', password='pass12345')
        response = self.client.post(reverse('call_next_queue'), {'table_id': table.pk})
        self.assertRedirects(response, reverse('staff_home'))
        first.refresh_from_db()
        second.refresh_from_db()
        table.refresh_from_db()
        self.assertEqual(first.status, QueueTicket.Status.CALLED)
        self.assertEqual(first.table, table)
        self.assertEqual(second.status, QueueTicket.Status.WAITING)
        self.assertEqual(table.status, Table.Status.OCCUPIED)

    def test_staff_table_map_is_role_protected_and_shows_current_usage(self):
        staff = User.objects.create_user(username='map-staff', password='pass12345', role=User.Role.STAFF)
        table = Table.objects.create(table_number='MAP-1', capacity=4, status=Table.Status.OCCUPIED)
        item = MenuItem.objects.create(name='Map Pho', base_price=50000, category=MenuItem.Category.PHO)
        order = Order.objects.create(
            order_code='MAP-ORDER', table=table, payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.COMPLETED,
        )
        OrderItem.objects.create(order=order, menu_item=item, quantity=2, item_price=50000)
        customer = User.objects.create_user(username='map-customer', password='pass12345')

        self.client.force_login(customer)
        self.assertEqual(self.client.get(reverse('table_map')).status_code, 302)
        self.client.force_login(staff)
        response = self.client.get(reverse('table_map'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bàn MAP-1')
        self.assertContains(response, '2 / 4 tô đang dùng')
        self.assertContains(response, 'Khách ăn xong · trả 2 tô')

    def test_cashier_dashboard_lists_cash_orders_with_capacity_choices(self):
        staff = User.objects.create_user(username='cash-capacity-staff', password='pass12345', role=User.Role.STAFF)
        item = MenuItem.objects.create(name='Capacity Pho', base_price=50000, category=MenuItem.Category.PHO)
        order = Order.objects.create(
            order_code='CASH-CAPACITY', payment_method=Order.PaymentMethod.CASH,
            order_type=Order.OrderType.DINE_IN,
        )
        OrderItem.objects.create(order=order, menu_item=item, quantity=2, item_price=50000)
        small = Table.objects.create(table_number='CAP-SMALL', capacity=1)
        fit = Table.objects.create(table_number='CAP-FIT', capacity=2)
        self.client.force_login(staff)

        response = self.client.get(reverse('staff_home'))

        cash_row = next(row for row in response.context['cash_orders'] if row.pk == order.pk)
        self.assertEqual(cash_row.pho_count, 2)
        self.assertIn(fit, cash_row.suitable_tables)
        self.assertNotIn(small, cash_row.suitable_tables)
        self.assertContains(response, 'Xác nhận & chuyển bếp')

    def test_called_queue_ticket_keeps_table_reserved_in_table_map(self):
        staff = User.objects.create_user(username='map-queue-staff', password='pass12345', role=User.Role.STAFF)
        table = Table.objects.create(table_number='MAP-QUEUE', capacity=4, status=Table.Status.OCCUPIED)
        ticket = QueueTicket.objects.create(
            ticket_number='P-MAP-1', status=QueueTicket.Status.CALLED,
            table=table, people_count=2,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('table_map'))
        self.assertContains(response, ticket.ticket_number)
        self.assertContains(response, 'Hoàn tất hoặc hủy các đơn còn mở trước khi dọn bàn.')

        self.client.post(reverse('free_table', args=[table.pk]))
        ticket.refresh_from_db()
        table.refresh_from_db()
        self.assertEqual(ticket.status, QueueTicket.Status.CALLED)
        self.assertEqual(table.status, Table.Status.OCCUPIED)

    def test_guest_can_take_queue_and_keep_ticket_in_session(self):
        response = self.client.post(reverse('take_queue'), {'guest_name': 'Lan'})
        self.assertEqual(response.status_code, 302)
        ticket = QueueTicket.objects.get()
        self.assertEqual(ticket.guest_name, 'Lan')
        self.assertEqual(ticket.people_count, 1)
        self.assertEqual(ticket.status, QueueTicket.Status.WAITING)
        status = self.client.get(reverse('queue_status')).json()
        self.assertTrue(status['active'])
        self.assertEqual(status['ticket'], ticket.ticket_number)

    def test_queue_cart_cannot_checkout_before_called(self):
        customer = User.objects.create_user(username='wait-c', password='pass12345')
        QueueTicket.objects.create(customer=customer, ticket_number='P-009')
        item = MenuItem.objects.create(name='Phở Nam', base_price=45000, image_primary='menu_items/pho.jpg')
        options = {}
        for option in CustomizationOption.objects.all().order_by('category', 'id'):
            options.setdefault(option.category, option)
        self.client.login(username='wait-c', password='pass12345')
        response = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{
                'id': item.pk, 'qty': 1, 'toppings': [],
                'customizations': [opt.pk for opt in options.values()],
                'note': '',
            }]),
            'order_type': Order.OrderType.QUEUE_CART,
            'payment_method': Order.PaymentMethod.VIETQR,
        })
        self.assertEqual(Order.objects.count(), 0)
        self.assertRedirects(response, reverse('menu'))

    def test_delivery_fee_uses_distance_and_requires_vietqr(self):
        customer = User.objects.create_user(username='ship-c', password='pass12345')
        item = MenuItem.objects.create(name='Phở Gà', base_price=40000, image_primary='menu_items/pho.jpg')
        ingredient = Ingredient.objects.create(name='Bánh phở kiểm thử giao hàng', unit='kg', current_stock=10)
        Recipe.objects.create(menu_item=item, ingredient=ingredient, quantity_required='0.20')
        options = {}
        for option in CustomizationOption.objects.all().order_by('category', 'id'):
            options.setdefault(option.category, option)
        self.client.login(username='ship-c', password='pass12345')
        quote = self.client.get(reverse('delivery_fee_quote'), {'lat': '10.7769', 'lng': '106.7009'}).json()
        self.assertTrue(quote['ok'])
        self.assertGreaterEqual(quote['fee'], 15000)
        response = self.client.post(reverse('place_order'), {
            'cart': json.dumps([{
                'id': item.pk, 'qty': 1, 'toppings': [],
                'customizations': [opt.pk for opt in options.values()],
                'note': '',
            }]),
            'order_type': Order.OrderType.DELIVERY,
            'payment_method': Order.PaymentMethod.CASH,
            'delivery_address': '12 Nguyễn Huệ, Q1',
            'recipient_name': 'Khách giao hàng',
            'recipient_phone': '0901234567',
            'customer_lat': '10.7769',
            'customer_lng': '106.7009',
        })
        order = Order.objects.get(customer=customer)
        self.assertRedirects(response, f"{reverse('order_detail', args=[order.pk])}?placed=1")
        self.assertEqual(order.order_type, Order.OrderType.DELIVERY)
        self.assertEqual(order.payment_method, Order.PaymentMethod.VIETQR)
        self.assertGreater(order.delivery_fee, 0)
        self.assertTrue(order.shipping_code)
