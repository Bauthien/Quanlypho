from django.test import TestCase
import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomizationOption, MenuItem, Order, OrderItem, QueueTicket, Table, Topping, User


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

    def test_menu_is_public_but_checkout_requires_customer_login(self):
        self.assertEqual(self.client.get(reverse('menu')).status_code, 200)
        self.assertEqual(self.client.post(reverse('take_queue')).status_code, 302)

    def test_vietqr_order_waits_for_verified_webhook(self):
        customer = User.objects.create_user(username='qr-customer', password='pass12345')
        table = Table.objects.create(table_number=5)
        item = MenuItem.objects.create(name='Phở Tái', base_price=50000, image_primary='menu_items/pho.jpg')
        topping = Topping.objects.create(name='Trứng chần', price=5000)
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
        self.assertRedirects(response, reverse('order_detail', args=[order.pk]))
        self.assertEqual(order.total_amount, 110000)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.CART)
        self.assertEqual(order.items.get().toppings.count(), 1)
        table.refresh_from_db()
        self.assertEqual(table.status, Table.Status.OCCUPIED)

        body = json.dumps({'order_code': order.order_code, 'amount': 110000, 'status': 'success'}).encode()
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
