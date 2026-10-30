from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from pho_app.models import Ingredient, InventoryIncident, Order, StockMovement, User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class StockOperationsHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='admin_stock', role=User.Role.ADMIN)
        cls.customer = User.objects.create_user(username='cust_stock')
        cls.ingredient = Ingredient.objects.create(name='Thịt bò tái', unit='kg', current_stock=Decimal('10.00'), minimum_stock=Decimal('2.00'))
        cls.order = Order.objects.create(customer=cls.customer, order_code='PHO-TEST-01', total_amount=100000)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_stock_incidents_tab_renders_history(self):
        # Create test movements
        StockMovement.objects.create(
            order=self.order,
            ingredient=self.ingredient,
            key='return:test-key-1',
            kind='RETURN_UNUSED',
            quantity=Decimal('1.50'),
            evidence='Khách đổi món, bếp trả lại thịt bò',
            actor=self.admin,
        )
        StockMovement.objects.create(
            order=None,
            ingredient=self.ingredient,
            key='waste:test-key-2',
            kind='WASTE_WAREHOUSE',
            quantity=Decimal('0.50'),
            evidence='Hao hụt rã đông cuối ngày',
            actor=self.admin,
        )
        # Create resolved incident
        InventoryIncident.objects.create(
            ingredient=self.ingredient,
            detail='Chênh lệch kiểm kê 2kg.\nKết quả: Đã nhập bù hàng',
            resolved=True,
        )

        response = self.client.get(reverse('admin_inventory'))
        self.assertEqual(response.status_code, 200)

        # Context assertions
        self.assertIn('stock_operations_history', response.context)
        self.assertEqual(len(response.context['stock_operations_history']), 2)
        self.assertIn('resolved_stock_incidents', response.context)
        self.assertEqual(len(response.context['resolved_stock_incidents']), 1)

        # Content assertions
        self.assertContains(response, 'Lịch sử hoàn kho &amp; ghi nhận hao hụt')
        self.assertContains(response, 'Hoàn kho (chưa dùng)')
        self.assertContains(response, 'Hao hụt tại kho')
        self.assertContains(response, 'Khách đổi món, bếp trả lại thịt bò')
        self.assertContains(response, 'Hao hụt rã đông cuối ngày')
        self.assertContains(response, 'PHO-TEST-01')
        self.assertContains(response, 'kg')
        self.assertContains(response, 'Lịch sử sự cố chênh lệch đã mở kho')
