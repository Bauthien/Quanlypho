from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountFlowTests(TestCase):
	def test_registration_always_creates_customer(self):
		response = self.client.post(reverse('pho_app:register'), {
			'username': 'new-customer',
			'full_name': 'Nguyen Van A',
			'phone_number': '0900000000',
			'password1': 'Strong-pass-2026!',
			'password2': 'Strong-pass-2026!',
			'role': User.Role.ADMIN,
		})

		self.assertRedirects(response, reverse('pho_app:role_home'))
		user = User.objects.get(username='new-customer')
		self.assertEqual(user.role, User.Role.CUSTOMER)
		self.assertTrue(user.check_password('Strong-pass-2026!'))

	def test_each_non_admin_role_sees_role_welcome(self):
		user = User.objects.create_user(
			username='cashier', password='Strong-pass-2026!', role=User.Role.STAFF
		)
		self.client.force_login(user)

		response = self.client.get(reverse('pho_app:role_home'))

		self.assertContains(response, 'Thu ngân')

	def test_admin_role_can_open_dashboard_and_change_roles(self):
		admin = User.objects.create_user(
			username='manager', password='Strong-pass-2026!', role=User.Role.ADMIN
		)
		customer = User.objects.create_user(
			username='customer', password='Strong-pass-2026!'
		)
		self.client.force_login(admin)

		dashboard = self.client.get(reverse('pho_app:admin_dashboard'))
		self.assertContains(dashboard, 'Dashboard quản trị')

		response = self.client.post(
			reverse('pho_app:update_user_role', args=[customer.pk]),
			{'role': User.Role.KITCHEN},
		)
		self.assertRedirects(response, reverse('pho_app:admin_dashboard'))
		customer.refresh_from_db()
		self.assertEqual(customer.role, User.Role.KITCHEN)

	def test_customer_cannot_open_admin_dashboard(self):
		customer = User.objects.create_user(
			username='customer', password='Strong-pass-2026!'
		)
		self.client.force_login(customer)

		response = self.client.get(reverse('pho_app:admin_dashboard'))

		self.assertRedirects(response, reverse('pho_app:role_home'))
