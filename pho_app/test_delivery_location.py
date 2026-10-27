import json
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomizationOption, Ingredient, MenuItem, Order, Recipe, User, UserAddress
from .services import parse_coords
from .locations import delivery_destination
from .commerce_forms import AddressForm


@override_settings(RESTAURANT_LAT=10.7769, RESTAURANT_LNG=106.7009, DELIVERY_MAX_KM=20,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DeliveryLocationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='location-customer', full_name='Khách giao', phone_number='0901234567')
        cls.other = User.objects.create_user(username='location-other')
        cls.menu = MenuItem.objects.create(name='Phở GPS', base_price=50000)
        cls.ingredient = Ingredient.objects.create(name='Bánh GPS', unit='g', current_stock=10000)
        Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=100)
        cls.choices = [CustomizationOption.objects.get_or_create(category=c, name=f'GPS {c}')[0].pk for c in ('BROTH', 'VEGGIE', 'NOODLE')]

    def setUp(self):
        self.client.force_login(self.user)

    def body(self, **extra):
        return {'cart': json.dumps([{'id': self.menu.pk, 'qty': 1, 'customizations': self.choices}]),
            'order_type': 'DELIVERY', 'recipient_name': 'Người nhận', 'recipient_phone': '0901234567',
            'delivery_address': '12 Nguyễn Huệ, Thành phố Hồ Chí Minh', 'customer_lat': '10.7769', 'customer_lng': '106.7009', **extra}

    def address(self, **extra):
        return UserAddress.objects.create(user=self.user, recipient_name='Khách lưu', phone='0901234567',
            street='12 Nguyễn Huệ', ward='Phường Bến Nghé', province='Hồ Chí Minh', **extra)

    def test_missing_or_invalid_coordinates_are_not_quoted_as_a_valid_fallback(self):
        for data in ({}, {'lat': 'NaN', 'lng': '106'}, {'lat': '10.7'}, {'lat': '91', 'lng': '106'}):
            with self.subTest(data=data):
                response = self.client.get(reverse('delivery_fee_quote'), data)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()['ok'])
                self.assertNotIn('fee', response.json())

    def test_decimal_comma_coordinates_are_normalized_and_finite(self):
        self.assertEqual(parse_coords('10,7769', '106,7009'), (10.7769, 106.7009))
        for lat, lng in (('Infinity', 106), ('NaN', 106), ('', 106), (10, -181), (True, 106)):
            self.assertIsNone(parse_coords(lat, lng))

    def test_fee_preview_quote_and_order_use_the_same_distance_and_fee(self):
        preview = self.client.get(reverse('delivery_fee_quote'), {'lat': '10.78', 'lng': '106.71'}).json()
        body = self.body(customer_lat='10.78', customer_lng='106.71')
        quote = self.client.post(reverse('checkout_quote'), body).json()
        self.assertTrue(quote['ok'])
        self.assertEqual(quote['delivery_fee'], preview['fee'])
        response = self.client.post(reverse('place_order'), {**body, 'quote_token': quote['token']})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(customer=self.user)
        self.assertEqual(order.delivery_fee, preview['fee'])
        self.assertEqual(order.customer_location.x, 106.71)
        self.assertEqual(order.customer_location.y, 10.78)
        self.assertEqual(order.delivery_snapshot['shop_latitude'], 10.7769)

    def test_saved_address_without_coordinates_accepts_a_position_for_this_order_only(self):
        address = self.address()
        body = self.body(address_id=address.pk, address_version=address.version)
        response = self.client.post(reverse('checkout_quote'), body)
        self.assertTrue(response.json()['ok'])
        self.client.post(reverse('place_order'), {**body, 'quote_token': response.json()['token']})
        order = Order.objects.get(customer=self.user)
        self.assertEqual(order.delivery_snapshot['latitude'], 10.7769)
        self.assertEqual(order.delivery_snapshot['address'], address.full_address)
        address.refresh_from_db()
        self.assertIsNone(address.latitude)

    def test_saved_coordinates_cannot_be_overridden_to_hide_an_out_of_range_address(self):
        address = self.address(latitude=21.0278, longitude=105.8342)
        response = self.client.post(reverse('checkout_quote'), self.body(address_id=address.pk, address_version=address.version))
        self.assertEqual(response.status_code, 400)
        self.assertIn('ngoài phạm vi', response.json()['error'])

    def test_invalid_phone_and_stale_or_foreign_address_are_rejected(self):
        self.assertEqual(self.client.post(reverse('checkout_quote'), self.body(recipient_phone='abc')).status_code, 400)
        address = self.address(latitude=10.7769, longitude=106.7009)
        self.assertEqual(self.client.post(reverse('checkout_quote'), self.body(address_id=address.pk, address_version=0)).status_code, 400)
        address.user = self.other
        address.save()
        self.assertEqual(self.client.post(reverse('checkout_quote'), self.body(address_id=address.pk, address_version=address.version)).status_code, 400)

    def test_coordinate_change_invalidates_the_previously_signed_quote(self):
        body = self.body()
        quote = self.client.post(reverse('checkout_quote'), body).json()
        self.client.post(reverse('place_order'), {**body, 'customer_lat': '10.78', 'quote_token': quote['token']})
        self.assertFalse(Order.objects.filter(customer=self.user).exists())

    def test_checkout_and_address_form_offer_manual_coordinates_and_map_picker(self):
        response = self.client.get(reverse('menu'))
        self.assertContains(response, 'data-location-picker')
        self.assertContains(response, 'Chọn trên bản đồ')
        self.assertContains(response, 'data-location-lat')
        response = self.client.get(reverse('address_create'))
        self.assertContains(response, 'data-location-picker')
        self.assertContains(response, 'data-location-lng')

    def test_navigation_uses_the_saved_destination_and_origin_after_settings_change(self):
        self.client.post(reverse('place_order'), self.body(delivery_note='Tầng 2, cổng sau'))
        order = Order.objects.get(customer=self.user)
        with override_settings(RESTAURANT_LAT=21, RESTAURANT_LNG=105):
            destination = delivery_destination(order)
        query = parse_qs(urlparse(destination['directions_url']).query)
        self.assertEqual(query['origin'], ['10.7769,106.7009'])
        self.assertEqual(query['destination'], ['10.7769,106.7009'])
        response = self.client.get(reverse('order_detail', args=[order.pk]))
        self.assertContains(response, 'Chỉ đường giao hàng')
        self.assertContains(response, 'tel:0901234567')
        self.assertContains(response, 'Tầng 2, cổng sau')

    def test_saved_address_keeps_its_order_location_when_address_book_changes(self):
        address = self.address(latitude=10.7769, longitude=106.7009)
        self.client.post(reverse('place_order'), self.body(address_id=address.pk, address_version=address.version))
        UserAddress.objects.filter(pk=address.pk).update(latitude=21, longitude=105, street='Nơi mới')
        order = Order.objects.get(customer=self.user)
        self.assertEqual(parse_qs(urlparse(delivery_destination(order)['map_url']).query)['query'], ['10.7769,106.7009'])
        self.assertIn('12 Nguyễn Huệ', order.delivery_address)

    def test_address_form_rejects_invalid_coordinates_and_normalizes_phone(self):
        data = {'recipient_name': 'Khách', 'phone': '090 123 4567', 'street': '12 Nguyễn Huệ', 'ward': 'Bến Nghé', 'province': 'Hồ Chí Minh', 'label': 'HOME', 'latitude': '10.7', 'longitude': '106.7'}
        form = AddressForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '0901234567')
        for extra in ({'latitude': '91'}, {'longitude': ''}, {'phone': 'không có số'}):
            self.assertFalse(AddressForm({**data, **extra}).is_valid())

    def test_invalid_or_out_of_range_delivery_does_not_create_an_order(self):
        for extra in ({'customer_lat': '', 'customer_lng': ''}, {'customer_lat': 'NaN'}, {'customer_lat': '21.0278', 'customer_lng': '105.8342'}):
            self.client.post(reverse('place_order'), self.body(**extra))
            self.assertFalse(Order.objects.filter(customer=self.user).exists())

    def test_print_labels_use_recipient_contact_instead_of_account_name(self):
        self.client.post(reverse('place_order'), self.body(recipient_name='Người nhận riêng', delivery_note='Gọi khi đến'))
        order = Order.objects.get(customer=self.user)
        Order.objects.filter(pk=order.pk).update(payment_status='PAID', order_status='READY')
        admin = User.objects.create_user(username='location-admin', role='ADMIN')
        self.client.force_login(admin)
        response = self.client.get(reverse('delivery_labels', args=[order.pk]))
        self.assertContains(response, 'Người nhận riêng', count=2)
        self.assertContains(response, '0901234567', count=2)
        self.assertContains(response, 'Gọi khi đến', count=2)
