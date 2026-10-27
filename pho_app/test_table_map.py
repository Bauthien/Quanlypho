from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import MenuItem, Order, OrderItem, QueueTicket, Table, User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class UnifiedTableMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='table-admin', role='ADMIN')
        cls.staff = User.objects.create_user(username='table-staff', role='STAFF')
        cls.customer = User.objects.create_user(username='table-customer')
        cls.kitchen = User.objects.create_user(username='table-kitchen', role='KITCHEN')
        cls.table = Table.objects.create(table_number='MERGED-1', capacity=4)

    def test_admin_and_staff_have_one_table_navigation_and_one_screen(self):
        for user in (self.admin, self.staff):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse('table_map'))
                self.assertTemplateUsed(response, 'pho_app/table_map.html')
                self.assertContains(response, f'href="{reverse("table_map")}"', count=1)
                self.assertContains(response, '<span>Sơ đồ bàn &amp; QR</span>', html=True)
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertNotContains(response, '<span>Sơ đồ bàn</span>')
                self.assertContains(response, 'Bàn MERGED-1')
                self.assertContains(response, 'Lọc trạng thái bàn')

    def test_legacy_table_pages_redirect_to_the_unified_screen(self):
        self.client.force_login(self.admin)
        for name in ('admin_table_list', 'staff_table_map'):
            self.assertRedirects(self.client.get(reverse(name)), reverse('table_map'))
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.get(reverse('staff_table_map')), reverse('table_map'))

    def test_customers_kitchen_and_guests_cannot_open_table_map(self):
        self.assertRedirects(self.client.get(reverse('table_map')), reverse('login'))
        for user in (self.customer, self.kitchen):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('table_map')).status_code, 302)

    def test_qr_uses_current_menu_link_even_without_a_saved_image(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('table_map'))
        table = next(table for table in response.context['tables'] if table.pk == self.table.pk)
        qr_data = parse_qs(urlparse(table.qr_image_url).query)['data'][0]
        self.assertEqual(qr_data, f'http://testserver{reverse("menu")}?table={self.table.pk}')
        self.assertContains(response, f'Mã QR Bàn {self.table.table_number}')
        self.table.refresh_from_db()
        self.assertFalse(self.table.qr_code_url)

    def test_only_admin_sees_and_can_use_table_editing_actions(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('table_map'))
        for name, args in (('admin_table_create', []), ('admin_table_edit', [self.table.pk]), ('admin_table_delete', [self.table.pk])):
            url = reverse(name, args=args)
            self.assertNotContains(response, url)
            self.assertEqual(self.client.post(url, {'table_number': 'UNAUTHORIZED', 'capacity': 2}).status_code, 302)
        self.table.refresh_from_db()
        self.assertEqual(self.table.table_number, 'MERGED-1')
        self.client.force_login(self.admin)
        response = self.client.get(reverse('table_map'))
        self.assertContains(response, reverse('admin_table_create'))
        self.assertContains(response, reverse('admin_table_edit', args=[self.table.pk]))
        self.assertContains(response, reverse('admin_table_delete', args=[self.table.pk]))

    def test_admin_table_changes_return_to_unified_screen(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.post(reverse('admin_table_create'), {'table_number': 'MERGED-NEW', 'capacity': 2}), reverse('table_map'))
        table = Table.objects.get(table_number='MERGED-NEW')
        self.assertRedirects(self.client.post(reverse('admin_table_edit', args=[table.pk]), {'table_number': 'MERGED-EDITED', 'capacity': 3}), reverse('table_map'))
        self.assertRedirects(self.client.post(reverse('admin_table_delete', args=[table.pk])), reverse('table_map'))
        self.assertFalse(Table.objects.filter(pk=table.pk).exists())

    def test_cleaning_action_stays_on_map_and_rejects_external_redirects(self):
        self.client.force_login(self.staff)
        Table.objects.filter(pk=self.table.pk).update(status='CLEANING')
        self.assertRedirects(self.client.post(reverse('free_table', args=[self.table.pk]), {'next': reverse('table_map')}), reverse('table_map'))
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'AVAILABLE')
        Table.objects.filter(pk=self.table.pk).update(status='CLEANING')
        self.assertRedirects(self.client.post(reverse('free_table', args=[self.table.pk]), {'next': 'https://example.com'}), reverse('staff_home'))

    def test_reserved_table_cannot_be_cleared_from_unified_screen(self):
        self.client.force_login(self.staff)
        Table.objects.filter(pk=self.table.pk).update(status='OCCUPIED')
        QueueTicket.objects.create(ticket_number='MERGED-Q', table=self.table, status='CALLED')
        response = self.client.post(reverse('free_table', args=[self.table.pk]), {'next': reverse('table_map')}, follow=True)
        self.assertContains(response, 'Chưa thể dọn bàn vì khách đã được gọi')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'OCCUPIED')

    def test_clear_completed_order_stays_on_unified_screen(self):
        self.client.force_login(self.staff)
        menu = MenuItem.objects.create(name='Phở bàn hợp nhất', base_price=50000)
        order = Order.objects.create(order_code='MERGED-ORDER', table=self.table, payment_status='PAID', order_status='COMPLETED')
        OrderItem.objects.create(order=order, menu_item=menu, quantity=2, item_price=50000)
        response = self.client.post(reverse('free_order_table', args=[order.pk]), {'next': reverse('table_map')})
        self.assertRedirects(response, reverse('table_map'))
        order.refresh_from_db()
        self.assertTrue(order.is_cleared)
