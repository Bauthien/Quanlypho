import json
from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Ingredient, InventoryTransaction, MenuItem, Order, OrderItem,
    PaymentReceipt, Recipe, User,
)


@override_settings(
    DEBUG=True, VIETQR_BANK_ID='', VIETQR_ACCOUNT_NO='', VIETQR_ACCOUNT_NAME='',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class VietQRPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username='qr-customer')
        cls.staff = User.objects.create_user(username='qr-staff', role='STAFF')
        cls.ingredient = Ingredient.objects.create(name='Bánh phở QR', unit='kg', current_stock=10)
        cls.menu = MenuItem.objects.create(name='Phở QR', base_price=50000)
        Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=1)

    def setUp(self):
        self.client.force_login(self.customer)
        self.order = Order.objects.create(
            order_code='QR-PAYMENT-TEST', customer=self.customer,
            payment_method='VIETQR', total_amount=50000, delivery_fee=15000,
        )
        OrderItem.objects.create(order=self.order, menu_item=self.menu, quantity=1, item_price=50000)
        self.detail_url = reverse('order_detail', args=[self.order.pk])
        self.simulate_url = reverse('simulate_vietqr_payment', args=[self.order.pk])

    def test_missing_bank_configuration_shows_demo_qr_and_visible_simulation(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'class="payment-qr"')
        self.assertContains(response, 'QR thử nghiệm')
        self.assertContains(response, 'không dùng để chuyển tiền')
        self.assertContains(response, 'Mô phỏng thanh toán thành công')
        self.assertNotContains(response, '<details class="delivery-history">')
        query = parse_qs(urlparse(response.context['vietqr_image_url']).query)
        payload = json.loads(query['data'][0])
        self.assertEqual(payload, {
            'mode': 'DEMO', 'order_code': self.order.order_code,
            'amount': 65000, 'currency': 'VND',
        })
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PENDING')
        self.assertFalse(PaymentReceipt.objects.filter(order=self.order).exists())

    @override_settings(VIETQR_BANK_ID='970436')
    def test_incomplete_configuration_uses_demo_in_development(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'QR thử nghiệm')
        self.assertContains(response, 'Mô phỏng thanh toán thành công')

    @override_settings(VIETQR_BANK_ID='970436', VIETQR_ACCOUNT_NO='123456789', VIETQR_ACCOUNT_NAME='PHO NHA')
    def test_configured_bank_uses_real_qr_with_saved_amount_and_reference(self):
        response = self.client.get(self.detail_url)
        image_url = response.context['vietqr_image_url']
        self.assertTrue(image_url.startswith('https://img.vietqr.io/image/970436-123456789-compact2.png?'))
        self.assertEqual(parse_qs(urlparse(image_url).query), {
            'amount': ['65000'], 'addInfo': [self.order.order_code], 'accountName': ['PHO NHA'],
        })
        self.assertNotContains(response, 'QR thử nghiệm')
        self.assertContains(response, 'Mô phỏng thanh toán thành công')

    @override_settings(DEBUG=False, VIETQR_BANK_ID='970436', VIETQR_ACCOUNT_NO='123456789')
    def test_production_real_qr_has_no_simulation_controls(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'class="payment-qr"')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')
        self.assertNotContains(response, self.simulate_url)
        self.assertEqual(self.client.post(self.simulate_url).status_code, 404)

    @override_settings(DEBUG=False)
    def test_production_without_bank_shows_configuration_message_only(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Tài khoản nhận VietQR chưa được cấu hình')
        self.assertNotContains(response, 'class="payment-qr"')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')

    def test_read_only_staff_cannot_see_simulation_button(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')

    def test_guest_order_can_display_qr_and_simulate_payment(self):
        self.order.customer = None
        self.order.save(update_fields=['customer'])
        self.client.logout()
        session = self.client.session
        session['guest_orders'] = [self.order.pk]
        session.save()
        self.assertContains(self.client.get(self.detail_url), 'Mô phỏng thanh toán thành công')
        self.client.post(self.simulate_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')

    def test_successful_simulation_moves_order_to_kitchen_and_exports_stock_once(self):
        response = self.client.post(self.simulate_url, follow=True)
        self.assertContains(response, 'Đã mô phỏng thanh toán thành công')
        self.assertContains(response, 'Đã xác nhận thanh toán')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')
        self.assertNotContains(response, 'class="payment-qr"')
        self.client.post(self.simulate_url)
        self.order.refresh_from_db()
        self.ingredient.refresh_from_db()
        self.assertEqual((self.order.payment_status, self.order.order_status), ('PAID', 'PENDING_KITCHEN'))
        self.assertEqual(self.ingredient.current_stock, Decimal('9'))
        self.assertEqual(InventoryTransaction.objects.filter(ingredient=self.ingredient).count(), 1)
        receipt = PaymentReceipt.objects.get(order=self.order)
        self.assertEqual((receipt.provider, receipt.amount, receipt.allocated), ('SIMULATED', 65000, True))

    def test_short_stock_hides_both_demo_qr_and_simulation(self):
        Ingredient.objects.filter(pk=self.ingredient.pk).update(current_stock=0)
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Tạm thời chưa thể thanh toán')
        self.assertNotContains(response, 'class="payment-qr"')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')

    def test_expired_order_hides_both_demo_qr_and_simulation(self):
        Order.objects.filter(pk=self.order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Đơn đã hết thời gian giữ món')
        self.assertNotContains(response, 'class="payment-qr"')
        self.assertNotContains(response, 'Mô phỏng thanh toán thành công')
