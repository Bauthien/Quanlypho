"""Financial invariants and real HTTP flows for the TH4 additions."""
import hashlib
import hmac
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .accounts import delete_address, save_address
from .aftersales import (begin_refund, confirm_refund, decide_request, open_request,
                        create_replacement, apply_refund_benefits)
from .checkout import calculate_order_checkout, split_integer, delivery_price
from .delivery import delivery_action
from .domain import BusinessError
from .loyalty import (account_for, award_points, daily_checkin, debit_points, exchange_reward,
    expire_points, issue_period_benefits, months_after, point_balance, process_events,
    reconcile_order_loyalty, revoke_points, reward_review)
from .models import *
from .payments import receive_payment
from .services import apply_order_action
from .stock import expire_orders, return_unused


def configure_tiers():
    for rank, code, spend, rate, ship, near in [(0, 'MEMBER', 0, 0, 0, False),
        (1, 'BRONZE', 500000, 2, 0, False), (2, 'SILVER', 2000000, 5, 2, False),
        (3, 'GOLD', 5000000, 7, 3, True), (4, 'DIAMOND', 12000000, 10, 10, True)]:
        TierConfig.objects.get_or_create(code=code, defaults={'name': code, 'rank': rank, 'minimum_spend': spend,
            'good_reviews': 2 if rank else 0, 'discount_percent': rate, 'monthly_shipping': ship, 'nearby_shipping': near})


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    DELIVERY_BASE_FEE=15000, DELIVERY_FEE_PER_KM=8000, DELIVERY_MAX_KM=20,
    RESTAURANT_LAT=10.7769, RESTAURANT_LNG=106.7009)
class CommerceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        configure_tiers()
        cls.user = User.objects.create_user(username='commerce', password='StrongPass@123', phone_number='0901234567', full_name='Khách thử')
        cls.admin = User.objects.create_user(username='operator', password='StrongPass@123', role='ADMIN')
        cls.ingredient = Ingredient.objects.create(name='Bánh phở', unit='g', current_stock=10000)
        cls.pho = MenuItem.objects.create(name='Phở thử', base_price=50000)
        Recipe.objects.create(menu_item=cls.pho, ingredient=cls.ingredient, quantity_required=200)
        cls.choices = [CustomizationOption.objects.get_or_create(category=c, name=f'Chuẩn {c}')[0].pk for c in ('BROTH', 'VEGGIE', 'NOODLE')]

    def setUp(self):
        self.client.force_login(self.user)

    def body(self, **extra):
        result = {'cart': json.dumps([{'id': self.pho.pk, 'qty': 2, 'customizations': self.choices}]),
                  'order_type': 'DINE_IN', 'payment_method': 'VIETQR', 'request_key': uuid.uuid4().hex}
        result.update(extra)
        return result

    def order(self, **extra):
        response = self.client.post(reverse('place_order'), self.body(**extra))
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.url, reverse('menu'))
        return Order.objects.latest('pk')

    def paid(self, **extra):
        order = self.order(**extra)
        receipt, _ = receive_payment(order.pk, order.amount_due, 'BANK', uuid.uuid4().hex)
        self.assertTrue(receipt.allocated)
        order.refresh_from_db()
        return order

    def complete(self, order):
        apply_order_action(order.pk, 'start_cooking')
        apply_order_action(order.pk, 'finish_cooking')
        apply_order_action(order.pk, 'complete_dine_in')
        process_events()
        order.refresh_from_db()

    def finish_refund(self, case):
        for plan in case.refund_plans.all():
            attempt = begin_refund(plan.pk, self.admin, f'BANK-REFUND-{plan.pk}')
            confirm_refund(attempt.pk, 'SUCCEEDED', self.admin, 'Sao kê xác nhận tiền đã ra')
        process_events()
        case.refresh_from_db()

    def test_quote_order_bank_amount_and_repeat_request_agree(self):
        body = self.body()
        quote = self.client.post(reverse('checkout_quote'), body).json()
        body['quote_token'] = quote['token']
        first = self.client.post(reverse('place_order'), body)
        second = self.client.post(reverse('place_order'), body)
        self.assertEqual(first.url, second.url)
        order = Order.objects.get()
        self.assertEqual(order.amount_due, quote['payable'])
        self.assertEqual(sum(order.allocations.values_list('cash', flat=True)), order.amount_due)

    def test_hold_reduces_available_but_does_not_export_until_paid_once(self):
        from .stock import available_balances
        order = self.order()
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 10000)
        self.assertEqual(available_balances()[self.ingredient.pk], 9600)
        receipt, _ = receive_payment(order.pk, order.amount_due, 'BANK', 'tx1')
        receive_payment(order.pk, order.amount_due, 'BANK', 'tx1')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 9600)
        self.assertEqual(StockMovement.objects.filter(kind='EXPORT').count(), 1)
        self.assertEqual(available_balances()[self.ingredient.pk], 9600)

    def test_changed_recipe_after_hold_does_not_change_export(self):
        order = self.order()
        Recipe.objects.update(quantity_required=500)
        receive_payment(order.pk, order.amount_due, 'BANK', 'snapshot')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 9600)

    def test_expired_order_releases_stock_points_and_voucher(self):
        wallet = account_for(self.user)
        award_points(wallet, 'seed', 100, 'Seed')
        voucher = Voucher.objects.create(code='TEN', name='Giảm 10k', kind='FIXED', value=10000,
            starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=1), public=True)
        order = self.order(points=50, voucher_code='TEN')
        Order.objects.filter(pk=order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        expire_orders()
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'CANCELLED')
        self.assertEqual(point_balance(wallet), 100)
        self.assertEqual(order.stock_reservation.state, 'EXPIRED')
        receipt, _ = receive_payment(order.pk, order.amount_due, 'BANK', 'late')
        self.assertFalse(receipt.allocated)
        self.assertTrue(receipt.requires_reconciliation)

    def test_second_real_transfer_is_not_mistaken_for_callback_retry(self):
        order = self.paid()
        receipt, duplicate = receive_payment(order.pk, order.amount_due, 'BANK', 'second-real-transfer')
        self.assertFalse(duplicate)
        self.assertFalse(receipt.allocated)
        self.assertTrue(receipt.requires_reconciliation)
        self.assertEqual(order.receipts.count(), 2)

    def test_integer_allocation_example_and_maximum_point_capacity(self):
        a = account_for(self.user)
        a.tier = TierConfig.objects.get(code='SILVER'); a.save()
        award_points(a, 'seed', 1000, 'Seed')
        other = MenuItem.objects.create(name='B', base_price=100000)
        first = MenuItem.objects.create(name='A', base_price=200000)
        lines = [{'product': first, 'qty': 1, 'price': 200000}, {'product': other, 'qty': 1, 'price': 100000}]
        policy = {'kind': 'FIXED', 'value': 50000, 'cap': 0, 'minimum': 0, 'eligible_menu_ids': []}
        quote = calculate_order_checkout(lines, self.user, fee=25000, distance=6, policy=policy, requested_points=100)
        self.assertEqual(quote['payable'], 250000)
        self.assertEqual([u['cash'] for u in quote['allocations']], [150667, 75333, 24000])
        self.assertEqual([u['points'] for u in quote['allocations']], [60, 30, 10])
        self.assertEqual(split_integer(3, [100, 1, 1], [1, 1, 1]), [1, 1, 1])

    def test_free_dish_coupon_covers_only_one_base_unit(self):
        topping = Topping.objects.create(name='Trứng', price=10000, inventory_mode='UNTRACKED')
        policy = {'kind': 'FREE_ITEM', 'value': 0, 'cap': 100000, 'minimum': 0, 'eligible_menu_ids': []}
        quote = calculate_order_checkout([{'product': self.pho, 'qty': 2, 'price': 60000}], self.user, policy=policy)
        self.assertEqual(quote['voucher_discount'], 50000)
        self.assertEqual(quote['payable'], 70000)

    def test_gold_nearby_shipping_and_far_monthly_are_separate(self):
        account = account_for(self.user)
        account.tier = TierConfig.objects.get(code='GOLD'); account.save()
        lines = [{'product': self.pho, 'qty': 1, 'price': 50000}]
        near = calculate_order_checkout(lines, self.user, fee=55000, distance=Decimal('5.000000'))
        far = calculate_order_checkout(lines, self.user, fee=63000, distance=Decimal('5.004'))
        self.assertEqual(near['auto_shipping_discount'], 55000)
        self.assertEqual(far['auto_shipping_discount'], 0)
        with patch('pho_app.services.haversine_km', return_value=5.004):
            fee, distance = delivery_price((10.7, 106.7))
        self.assertEqual(fee, 63000)
        self.assertGreater(distance, 5)

    def test_monthly_top_up_counts_used_rights(self):
        account = account_for(self.user)
        for code, expected in [('SILVER', 2), ('GOLD', 3), ('DIAMOND', 10), ('SILVER', 10)]:
            account.tier = TierConfig.objects.get(code=code); account.save()
            issue_period_benefits(account)
            self.assertEqual(UserVoucher.objects.filter(user=self.user, source='MONTHLY').count(), expected)
            UserVoucher.objects.filter(user=self.user, source='MONTHLY').update(state='CONSUMED')

    def test_exchange_is_idempotent_and_does_not_debit_at_checkout(self):
        account = account_for(self.user)
        award_points(account, 'seed', 500, 'Seed')
        voucher = Voucher.objects.create(code='REWARD', name='Reward', kind='FIXED', value=10000,
            starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=100))
        reward = RewardCatalog.objects.create(name='Reward', points_cost=100, voucher=voucher)
        first = exchange_reward(self.user, reward.pk, 'same')
        second = exchange_reward(self.user, reward.pk, 'same')
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(point_balance(account), 400)
        self.paid(wallet_id=first.pk)
        self.assertEqual(point_balance(account), 400)

    def test_fifo_expiry_and_debt_recovery(self):
        account = account_for(self.user)
        award_points(account, 'invalid', 10, 'Seed')
        debit_points(account, 10, key='spent')
        award_points(account, 'valid', 5, 'Seed')
        revoke_points(account, 'invalid', 7, 'reverse')
        account.refresh_from_db()
        self.assertEqual(account.debt, 2)
        self.assertEqual(point_balance(account), 0)
        award_points(account, 'new', 3, 'Seed')
        account.refresh_from_db()
        self.assertEqual(account.debt, 0)
        self.assertEqual(point_balance(account), 1)
        for lot in account.lots.all():
            self.assertEqual(lot.original, lot.available + lot.reserved + lot.spent + lot.expired + lot.revoked)

    def test_checkin_duplicate_and_seventh_day(self):
        day = timezone.localdate()
        for i in range(7):
            with patch('pho_app.loyalty.timezone.localdate', return_value=day + timedelta(days=i)):
                first = daily_checkin(self.user)
                self.assertEqual(daily_checkin(self.user).pk, first.pk)
        self.assertEqual(sum(DailyCheckin.objects.values_list('points', flat=True)), 8)

    def test_cancel_before_cooking_stops_kitchen_and_cash_refund_is_separate(self):
        order = self.paid()
        case = open_request(order.pk, 'CANCEL', 'Không còn nhu cầu', 'REFUND', [], 'cancel', self.user)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'CANCELLED')
        with self.assertRaises(BusinessError):
            apply_order_action(order.pk, 'start_cooking')
        self.assertFalse(case.benefits_applied)
        self.finish_refund(case)
        self.assertEqual(case.state, 'CLOSED')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 9600)

    def test_unknown_refund_keeps_budget_and_rejects_second_attempt(self):
        order = self.paid()
        case = open_request(order.pk, 'CANCEL', 'Hủy', 'REFUND', [], 'cancel', self.user)
        plan = case.refund_plans.get()
        attempt = begin_refund(plan.pk, self.admin, 'REF-1')
        confirm_refund(attempt.pk, 'UNKNOWN', self.admin, 'Chờ sao kê')
        with self.assertRaises(BusinessError):
            begin_refund(plan.pk, self.admin, 'REF-2')
        confirm_refund(attempt.pk, 'FAILED_FINAL', self.admin, 'Ngân hàng xác nhận không chi')
        retry = begin_refund(plan.pk, self.admin, 'REF-2')
        confirm_refund(retry.pk, 'SUCCEEDED', self.admin, 'Đã chi')
        confirm_refund(retry.pk, 'SUCCEEDED', self.admin, 'Đã chi')
        process_events()
        self.assertEqual(plan.attempts.filter(state='SUCCEEDED').count(), 1)

    def test_partial_refund_and_completion_adjust_purchase_points(self):
        account = account_for(self.user)
        award_points(account, 'seed', 100, 'Seed')
        order = self.paid(points=100)
        self.complete(order)
        contribution = order.loyalty_contribution
        self.assertEqual(contribution.current_spend, 90000)
        self.assertEqual(contribution.points_target, 9)
        allocation = order.allocations.first()
        case = open_request(order.pk, 'ISSUE', 'Giao thiếu một phần', 'REFUND', [allocation.pk], 'partial', self.user)
        decide_request(case.pk, True, self.admin, 'Xác minh giao thiếu')
        self.finish_refund(case)
        contribution.refresh_from_db()
        self.assertEqual(contribution.current_spend, 45000)
        self.assertEqual(contribution.points_target, 4)
        self.assertEqual(sum(order.point_holds.values_list('restored', flat=True)), 50)

    def test_replacement_has_separate_stock_no_money_no_loyalty(self):
        order = self.paid()
        self.complete(order)
        case = open_request(order.pk, 'ISSUE', 'Làm lại món lỗi', 'REPLACE', [order.allocations.first().pk], 'replace', self.user)
        decide_request(case.pk, True, self.admin, 'Đồng ý làm lại')
        replacement = create_replacement(case.pk, self.admin)
        self.assertEqual(replacement.purpose, 'SERVICE_REPLACEMENT')
        self.assertEqual(replacement.amount_due, 0)
        self.assertEqual(create_replacement(case.pk, self.admin).pk, replacement.pk)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 9400)
        self.complete(replacement)
        self.assertFalse(LoyaltyOrderContribution.objects.filter(order=replacement).exists())

    def test_delivery_failure_retry_and_proof_of_completion(self):
        order = self.paid(order_type='DELIVERY', recipient_name='A', recipient_phone='0901234567', delivery_address='Địa chỉ thử', customer_lat='10.7769', customer_lng='106.7009')
        apply_order_action(order.pk, 'finish_cooking')
        delivery_action(order.pk, 'handover', self.admin, 'Bàn giao A', 'A')
        delivery_action(order.pk, 'failed', self.admin, 'Không liên hệ được')
        self.assertFalse(LoyaltyOrderContribution.objects.filter(order=order).exists())
        delivery_action(order.pk, 'retry', self.admin, 'Khách hẹn lại', 'B')
        delivery_action(order.pk, 'delivered', self.admin, 'Người nhận xác nhận')
        process_events()
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'COMPLETED')
        self.assertEqual(order.delivery.attempts.count(), 2)
        self.assertEqual(order.loyalty_contribution.current_spend, 100000)
        with self.assertRaises(BusinessError):
            delivery_action(order.pk, 'failed', self.admin, 'Callback cũ')

    def test_address_default_ownership_version_and_order_snapshot(self):
        data = {'recipient_name': 'A', 'phone': '0901234567', 'street': '1 Đường A', 'ward': 'Phường A', 'province': 'Thành phố A', 'label': 'HOME'}
        first = save_address(self.user, data)
        second = save_address(self.user, data)
        self.assertTrue(first.is_default)
        with self.assertRaises(BusinessError):
            delete_address(self.user, first.pk, first.version)
        save_address(self.user, {'is_default': True}, second.pk, second.version)
        delete_address(self.user, first.pk, first.version)
        with self.assertRaises(BusinessError):
            save_address(self.admin, data, second.pk, second.version)

    def test_review_reward_is_rating_neutral_and_once_per_order(self):
        order = self.paid(); self.complete(order)
        review = Review.objects.create(customer=self.user, order=order, rating=1, comment='Không hài lòng về món thử này')
        reward_review(review); reward_review(review)
        account = account_for(self.user)
        self.assertEqual(PointLot.objects.get(source=f'review:{order.pk}').original, 5)
        self.assertEqual(account.good_review_count, 0)
        review.rating = 4; review.save(); reward_review(review)
        account.refresh_from_db()
        self.assertEqual(account.good_review_count, 1)

    def test_customer_and_operator_pages_render(self):
        self.assertContains(self.client.get(reverse('account')), 'Thành viên')
        self.assertEqual(self.client.get(reverse('address_create')).status_code, 200)
        order = self.paid()
        self.assertContains(self.client.get(reverse('order_support', args=[order.pk])), 'Gửi yêu cầu')
        self.client.force_login(self.admin)
        for name in ('service_queue', 'promotions', 'admin_inventory'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_switch_preserves_other_slots_and_rejects_old_tab_generation(self):
        client = Client()
        client.post(reverse('login'), {'username': self.user.username, 'password': 'StrongPass@123'})
        generation = client.get(reverse('browser_context')).json()['generation']
        client.post(reverse('login'), {'username': self.admin.username, 'password': 'StrongPass@123', 'account_generation': generation})
        self.assertEqual(SavedAccountSession.objects.filter(revoked=False).count(), 2)
        stale = client.post(reverse('loyalty_action'), {'action': 'checkin', 'account_generation': generation})
        self.assertEqual(stale.status_code, 409)
        generation = client.get(reverse('browser_context')).json()['generation']
        slot = SavedAccountSession.objects.get(user=self.user)
        response = client.post(reverse('account_switch'), {'slot_id': slot.pk, 'account_generation': generation})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.session['_auth_user_id'], str(self.user.pk))
        self.assertNotIn('guest_orders', client.session)

    @override_settings(PAYMENT_WEBHOOK_SECRET='test-secret')
    def test_signed_webhook_requires_actual_transaction_id(self):
        order = self.order()
        payload = {'order_code': order.order_code, 'amount': int(order.amount_due), 'status': 'paid'}
        def post(data):
            raw = json.dumps(data).encode()
            return self.client.post(reverse('vietqr_webhook'), raw, content_type='application/json',
                HTTP_X_PAYMENT_SIGNATURE=hmac.new(b'test-secret', raw, hashlib.sha256).hexdigest())
        self.assertEqual(post(payload).status_code, 400)
        self.assertEqual(post({**payload, 'transaction_id': 'bank-123'}).status_code, 200)

    def test_return_unused_is_bounded_and_idempotent(self):
        order = self.paid()
        case = open_request(order.pk, 'CANCEL', 'Hủy', 'REFUND', [], 'cancel', self.user)
        return_unused(order.pk, self.ingredient.pk, '200', self.admin, 'Bếp xác nhận chưa dùng', 'same')
        return_unused(order.pk, self.ingredient.pk, '200', self.admin, 'Bếp xác nhận chưa dùng', 'same')
        with self.assertRaises(BusinessError):
            return_unused(order.pk, self.ingredient.pk, '300', self.admin, 'Vượt xuất', 'other')
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 9800)

    def test_zero_payable_uses_internal_settlement_without_fake_receipt(self):
        Voucher.objects.create(code='FREE', name='Miễn tiền món', kind='FIXED', value=100000,
            starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=1), public=True)
        order = self.order(voucher_code='FREE')
        self.assertEqual(order.amount_due, 0)
        self.assertEqual(order.payment_status, 'PAID')
        self.assertFalse(order.receipts.exists())
        self.assertEqual(order.stock_reservation.state, 'CONSUMED')
        self.complete(order)
        self.assertEqual(order.loyalty_contribution.points_target, 0)

    def test_profile_rejects_stale_version_role_injection_and_bad_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = {'action': 'profile', 'version': self.user.profile_version, 'full_name': 'Tên mới',
                'phone_number': '0901234567', 'email': 'a@example.com', 'gender': 'OTHER', 'role': 'ADMIN'}
        self.assertEqual(self.client.post(reverse('account'), data).status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'CUSTOMER')
        stale = self.client.post(reverse('account'), {**data, 'full_name': 'Tên cũ'})
        self.assertContains(stale, 'Hồ sơ đã thay đổi')
        bad = SimpleUploadedFile('avatar.png', b'not an image', content_type='image/png')
        response = self.client.post(reverse('account'), {**data, 'version': self.user.profile_version, 'avatar': bad})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_referral_award_once_then_reverse_full_refund(self):
        inviter = User.objects.create_user(username='inviter')
        self.user.referred_by = inviter; self.user.save(update_fields=['referred_by'])
        order = self.paid(); self.complete(order)
        reconcile_order_loyalty(order.pk)
        self.assertEqual(PointLot.objects.filter(source__startswith='referral:').count(), 2)
        case = open_request(order.pk, 'ISSUE', 'Món lỗi hoàn toàn', 'REFUND', [], 'all', self.user)
        decide_request(case.pk, True, self.admin, 'Lỗi đã xác minh')
        self.finish_refund(case)
        referral = ReferralReward.objects.get(newcomer=self.user)
        self.assertTrue(referral.reversed)
        self.assertEqual(point_balance(account_for(inviter)), 0)
        next_order = self.paid(); self.complete(next_order)
        self.assertEqual(PointLot.objects.filter(source__startswith='referral:').count(), 2)

    def test_highest_only_pack_and_no_second_gift_after_downgrade(self):
        from .loyalty import evaluate_and_upgrade_tier
        account = account_for(self.user)
        order = self.paid(); self.complete(order)
        c = order.loyalty_contribution
        c.original_spend = c.current_spend = 2300000; c.save()
        other = self.paid(); self.complete(other)
        Review.objects.create(customer=self.user, order=order, rating=4, comment='Bình luận dài hơn hai mươi ký tự')
        Review.objects.create(customer=self.user, order=other, rating=5, comment='Phở rất ngon và giao hàng đúng giờ')
        account = evaluate_and_upgrade_tier(self.user.pk)
        self.assertEqual(account.tier.code, 'SILVER')
        self.assertEqual(UserVoucher.objects.filter(user=self.user, source='TIER').count(), 3)
        self.assertFalse(BenefitGrant.objects.filter(user=self.user, key='tier:BRONZE').exists())
        Review.objects.filter(customer=self.user).update(is_published=False)
        self.assertEqual(evaluate_and_upgrade_tier(self.user.pk).tier.code, 'MEMBER')
        Review.objects.filter(customer=self.user).update(is_published=True)
        evaluate_and_upgrade_tier(self.user.pk)
        self.assertEqual(UserVoucher.objects.filter(user=self.user, source='TIER').count(), 3)

    def test_address_order_snapshot_and_stale_address_quote(self):
        data = {'recipient_name': 'Người nhận', 'phone': '0901234567', 'street': '1 Đường A', 'ward': 'Phường A',
            'province': 'Thành phố A', 'label': 'HOME', 'latitude': Decimal('10.7769000'), 'longitude': Decimal('106.7009000')}
        address = save_address(self.user, data)
        body = self.body(order_type='DELIVERY', address_id=str(address.pk), address_version=str(address.version))
        quote = self.client.post(reverse('checkout_quote'), body).json()
        save_address(self.user, {**data, 'street': '2 Đường B'}, address.pk, address.version)
        response = self.client.post(reverse('place_order'), {**body, 'quote_token': quote['token']}, follow=True)
        self.assertContains(response, 'Địa chỉ đã thay đổi')
        self.assertFalse(Order.objects.exists())

    def test_held_invalid_points_revoke_on_release_without_debt(self):
        account = account_for(self.user)
        award_points(account, 'invalid-hold', 100, 'Seed')
        order = self.order(points=100)
        revoke_points(account, 'invalid-hold', 100, 'reverse-hold')
        self.assertEqual(account.lots.get(source='invalid-hold').pending_revocation, 100)
        open_request(order.pk, 'CANCEL', 'Hủy trước trả tiền', 'REFUND', [], 'cancel', self.user)
        account.refresh_from_db()
        lot = account.lots.get(source='invalid-hold')
        self.assertEqual(lot.revoked, 100)
        self.assertEqual(account.debt, 0)
        self.assertEqual(point_balance(account), 0)

    def test_expired_saved_slot_can_reauthenticate_with_password(self):
        client = Client()
        client.post(reverse('login'), {'username': self.user.username, 'password': 'StrongPass@123'})
        generation = client.get(reverse('browser_context')).json()['generation']
        SavedAccountSession.objects.filter(user=self.user).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(client.get(reverse('account')).status_code, 409)
        response = client.post(reverse('login'), {'username': self.user.username, 'password': 'StrongPass@123', 'account_generation': generation})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get(reverse('account')).status_code, 200)

    def test_cash_receipt_survives_stock_reconciliation_failure(self):
        order = self.order(payment_method='CASH')
        Ingredient.objects.filter(pk=self.ingredient.pk).update(current_stock=0)
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_order_action', args=[order.pk]), {'action': 'confirm_cash'})
        self.assertEqual(response.status_code, 302)
        receipt = PaymentReceipt.objects.get(order=order, provider='CASH')
        self.assertTrue(receipt.requires_reconciliation)
        self.assertFalse(receipt.allocated)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'PENDING')

    def test_stock_unit_conversion_is_audited_and_does_not_mix_dimensions(self):
        from .stock import convert_stock_units
        self.assertEqual(convert_stock_units('1.25', 'kg', 'g'), Decimal('1250.00'))
        self.assertEqual(convert_stock_units('500', 'ml', 'lít'), Decimal('.50'))
        with self.assertRaises(BusinessError):
            convert_stock_units('1', 'ml', 'g')
        with self.assertRaises(BusinessError):
            convert_stock_units('.01', 'g', 'kg')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_ingredient_import', args=[self.ingredient.pk]), {'quantity': '1.25', 'input_unit': 'kg'})
        self.assertEqual(response.status_code, 302)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.current_stock, 11250)
        self.assertTrue(AuditEvent.objects.filter(action='STOCK_IMPORT', object_id=str(self.ingredient.pk)).exists())

    def test_referral_uses_first_completion_even_when_events_arrive_out_of_order(self):
        inviter = User.objects.create_user(username='inviter-late')
        self.user.referred_by = inviter; self.user.save(update_fields=['referred_by'])
        first, second = self.paid(), self.paid()
        now = timezone.now()
        Order.objects.filter(pk=first.pk).update(order_status='COMPLETED', completed_at=now - timedelta(minutes=1))
        Order.objects.filter(pk=second.pk).update(order_status='COMPLETED', completed_at=now)
        reconcile_order_loyalty(second.pk)
        self.assertFalse(ReferralReward.objects.filter(newcomer=self.user).exists())
        # The first order was fully refunded before its completion event ran.
        first.allocations.update(refunded=True)
        reconcile_order_loyalty(first.pk)
        referral = ReferralReward.objects.get(newcomer=self.user)
        self.assertEqual(referral.order_id, first.pk)
        self.assertTrue(referral.reversed)
        self.assertEqual(account_for(inviter).debt, 0)
        self.assertEqual(account_for(self.user).debt, 0)
        self.assertFalse(PointLot.objects.filter(source__startswith='referral:').exists())

    def test_released_campaign_wallet_cannot_bypass_last_redemption_quota(self):
        Voucher.objects.create(code='LAST', name='Mã cuối', kind='FIXED', value=10000, quota=1,
            starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=1), public=True)
        first = self.order(voucher_code='LAST')
        wallet = self.user.vouchers.get(source='CAMPAIGN')
        open_request(first.pk, 'CANCEL', 'Đổi ý', 'REFUND', [], 'cancel-last', self.user)
        other = User.objects.create_user(username='other-campaign')
        self.client.force_login(other)
        second = self.order(voucher_code='LAST')
        self.client.force_login(self.user)
        response = self.client.post(reverse('place_order'), self.body(wallet_id=wallet.pk), follow=True)
        self.assertContains(response, 'hết lượt sử dụng')
        self.assertEqual(Order.objects.count(), 2)

    def test_point_expiry_uses_vietnam_calendar_for_leap_day(self):
        from datetime import datetime, timezone as dt_timezone
        # 20:00 UTC Feb 28 is 03:00 Feb 29 in Vietnam.
        earned = datetime(2024, 2, 28, 20, tzinfo=dt_timezone.utc)
        expiry = timezone.localtime(months_after(earned))
        self.assertEqual((expiry.year, expiry.month, expiry.day, expiry.hour), (2025, 2, 28, 3))

    def test_promotion_editors_have_unique_field_ids(self):
        from html.parser import HTMLParser

        class FieldIds(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
                self.labels = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get('id'):
                    self.ids.append(attrs['id'])
                if tag == 'label' and attrs.get('for'):
                    self.labels.append(attrs['for'])

        self.client.force_login(self.admin)
        response = self.client.get(reverse('promotions'), {'tier': TierConfig.objects.first().pk})
        self.assertEqual(response.status_code, 200)
        parser = FieldIds()
        parser.feed(response.content.decode())
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.labels).issubset(set(parser.ids)))

    def test_stock_picker_rejects_ingredient_without_order_export_gracefully(self):
        order = self.paid()
        open_request(order.pk, 'CANCEL', 'Chưa chế biến', 'REFUND', [], 'picker-cancel', self.user)
        unrelated = Ingredient.objects.create(name='Không thuộc đơn', unit='g', current_stock=500)
        self.client.force_login(self.admin)
        response = self.client.post(reverse('stock_operation'), {
            'action': 'return', 'order_id': order.pk, 'ingredient_id': unrelated.pk,
            'quantity': '1', 'evidence': 'Đã xác nhận với bếp', 'request_key': 'invalid-picker'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'không có phiếu xuất phù hợp')
        unrelated.refresh_from_db()
        self.assertEqual(unrelated.current_stock, 500)
        self.assertFalse(StockMovement.objects.filter(key='return:invalid-picker').exists())


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections
from django.test import TransactionTestCase, skipUnlessDBFeature


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CommerceConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_checkouts_cannot_hold_last_shared_stock(self):
        configure_tiers()
        ingredient = Ingredient.objects.create(name='Giới hạn', unit='g', current_stock=200)
        product = MenuItem.objects.create(name='Một tô cuối', base_price=50000)
        Recipe.objects.create(menu_item=product, ingredient=ingredient, quantity_required=200)
        choices = [CustomizationOption.objects.get_or_create(category=c, name=f'Chuẩn {c}')[0].pk for c in ('BROTH', 'VEGGIE', 'NOODLE')]
        users = [User.objects.create_user(username=f'concurrent-{i}') for i in range(2)]
        clients = []
        for user in users:
            client = Client(); client.force_login(user); clients.append(client)
        barrier = Barrier(2)
        def checkout(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                response = clients[index].post(reverse('place_order'), {'cart': json.dumps([{'id': product.pk, 'qty': 1, 'customizations': choices}]), 'request_key': uuid.uuid4().hex})
                return response.url
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            urls = list(pool.map(checkout, range(2)))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(StockReservation.objects.filter(state='ACTIVE').count(), 1)
        self.assertEqual(sum(url == reverse('menu') for url in urls), 1)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.current_stock, 200)
