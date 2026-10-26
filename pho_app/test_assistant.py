import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Ingredient, MenuItem, Order, Recipe, TierConfig, User, UserAddress, UserVoucher, Voucher


class AssistantInterfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='assistant-customer', full_name='Khách kiểm tra')
        cls.other = User.objects.create_user(username='assistant-other')
        cls.admin = User.objects.create_user(username='assistant-admin', role='ADMIN')
        cls.ingredient = Ingredient.objects.create(name='Bánh phở', unit='g', current_stock=400)
        cls.pho = MenuItem.objects.create(name='Phở tái', base_price=55000)
        cls.second = MenuItem.objects.create(name='Phở nạm', base_price=65000)
        for product in (cls.pho, cls.second):
            Recipe.objects.create(menu_item=product, ingredient=cls.ingredient, quantity_required=200)

    def ask(self, **changes):
        data = {'message': 'Gợi ý phở cho 2 người', 'people': 2, 'budget': 150000}
        data.update(changes)
        return self.client.post(reverse('assistant_reply'), json.dumps(data), content_type='application/json')

    def test_current_prices_and_budget_without_order_mutation(self):
        response = self.ask()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['mode'], 'catalog')
        self.assertFalse(data['history_used'])
        self.assertEqual(sum(p['quantity'] for p in data['products']), 2)
        self.assertEqual(data['subtotal'], sum(p['price'] * p['quantity'] for p in data['products']))
        self.assertLessEqual(data['subtotal'], 150000)
        self.assertFalse(Order.objects.exists())

    def test_shared_ingredient_stock_is_not_recommended_twice(self):
        response = self.ask(message='Gợi ý phở', people=4, budget=500000)
        self.assertLessEqual(sum(p['quantity'] for p in response.json()['products']), 2)
        self.ingredient.current_stock = 0
        self.ingredient.save()
        self.assertEqual(self.ask().json()['products'], [])

    def test_budget_can_choose_repeated_affordable_dish(self):
        self.ingredient.current_stock = 600
        self.ingredient.save()
        data = self.ask(message='Gợi ý món', people=3, budget=170000).json()
        self.assertEqual(sum(p['quantity'] for p in data['products']), 3)
        self.assertLessEqual(data['subtotal'], 170000)

    def test_invalid_input_and_role(self):
        self.assertEqual(self.ask(people=9).status_code, 400)
        self.assertEqual(self.ask(budget=-1).status_code, 400)
        self.assertEqual(self.ask(message='x' * 1001).status_code, 400)
        self.assertEqual(self.client.post(reverse('assistant_reply'), '[]', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get(reverse('assistant_reply')).status_code, 405)
        self.client.force_login(self.admin)
        self.assertEqual(self.ask().status_code, 403)

    def test_vietnamese_budget_and_people_in_message(self):
        data = self.ask(message='Gợi ý món cho 1 người với 60.000đ').json()
        self.assertLessEqual(data['subtotal'], 60000)
        self.assertEqual(sum(p['quantity'] for p in data['products']), 1)
        self.assertEqual(self.ask(message='Gợi ý cho 12 người').status_code, 400)
        self.assertEqual(self.ask(message='Gợi ý phở -100k').status_code, 400)

    def test_support_does_not_disclose_orders_or_claim_refund(self):
        data = self.ask(message='Tra mã đơn PHO-123 và hoàn tiền').json()
        self.assertEqual(data['products'], [])
        self.assertEqual(data['links'][0]['url'], reverse('login'))
        self.assertIn('không tự tạo yêu cầu', data['text'])
        self.assertFalse(data['history_used'])

    def test_address_preview_checks_ownership_and_coordinates(self):
        self.client.force_login(self.user)
        address = UserAddress.objects.create(user=self.other, recipient_name='Người khác', phone='0901234567', street='Một địa chỉ', ward='Phường', province='Thành phố')
        self.assertEqual(self.client.get(reverse('address_preview'), {'address_id': address.pk}).status_code, 404)
        self.assertEqual(self.client.get(reverse('address_preview'), {'address_id': 'invalid'}).status_code, 404)
        address.user = self.user
        address.save()
        response = self.client.get(reverse('address_preview'), {'address_id': address.pk})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_wallet_tabs_use_current_owner_and_historical_states(self):
        self.client.force_login(self.user)
        now = timezone.now()
        voucher = Voucher.objects.create(code='WALLET-UI', name='Ưu đãi của tôi', kind='FIXED', value=10000, starts_at=now, ends_at=now + timedelta(days=30))
        policy = {'name': voucher.name, 'kind': 'FIXED', 'value': 10000}
        UserVoucher.objects.create(user=self.user, voucher=voucher, policy=policy, grant_key='wallet-ui-owned', starts_at=now, expires_at=now + timedelta(days=30), state='AVAILABLE')
        UserVoucher.objects.create(user=self.other, voucher=voucher, policy={'name': 'Riêng tư người khác'}, grant_key='wallet-ui-other', starts_at=now, expires_at=now + timedelta(days=30))
        response = self.client.get(reverse('account'))
        self.assertContains(response, 'Ưu đãi của tôi')
        self.assertNotContains(response, 'Riêng tư người khác')
        self.assertContains(response, 'data-list-filter="expired"')
