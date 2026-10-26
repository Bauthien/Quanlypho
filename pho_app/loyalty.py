import calendar
import secrets
import unicodedata
from datetime import timedelta

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .domain import BusinessError, serialized, request_key
from .models import (BenefitGrant, DailyCheckin, DomainEvent, LoyaltyAccount,
    LoyaltyOrderContribution, Order, PointHold, PointLot, PointTransaction,
    ReferralReward, RewardCatalog, Review, TierConfig, User, UserVoucher, Voucher)


def months_after(value, count=12):
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    month = value.month - 1 + count
    year, month = value.year + month // 12, month % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))


def account_for(user):
    account, _ = LoyaltyAccount.objects.get_or_create(user=user, defaults={'tier': TierConfig.objects.order_by('rank').first()})
    if not user.referral_code:
        user.referral_code = secrets.token_hex(6).upper()
        user.save(update_fields=['referral_code'])
    return account


def points_transaction(account, key, kind, amount, description):
    return PointTransaction.objects.get_or_create(key=key, defaults={
        'account': account, 'kind': kind, 'amount': amount, 'description': description})


def expire_points(account, now=None):
    now = now or timezone.now()
    for lot in account.lots.filter(expires_at__lte=now, available__gt=0).order_by('earned_at', 'pk'):
        amount = lot.available
        lot.available = 0
        lot.expired += amount
        lot.save(update_fields=['available', 'expired'])
        points_transaction(account, f'expire:{lot.pk}:{lot.expired}', 'EXPIRE', -amount, 'Điểm hết hạn')


def point_balance(account):
    return account.lots.filter(expires_at__gt=timezone.now()).aggregate(total=Sum('available'))['total'] or 0


def recover_debt(account):
    for lot in account.lots.filter(available__gt=0, expires_at__gt=timezone.now()).order_by('earned_at', 'pk'):
        amount = min(account.debt, lot.available)
        if not amount:
            break
        lot.available -= amount
        lot.revoked += amount
        lot.save(update_fields=['available', 'revoked'])
        account.debt -= amount
        points_transaction(account, f'debt:{lot.pk}:{lot.revoked}', 'DEBT_RECOVERY', -amount, 'Bù điểm đã sử dụng trước khi hoàn đơn')
    account.save(update_fields=['debt'])


def award_points(account, source, amount, description, earned_at=None, expires_at=None):
    if amount <= 0 or PointLot.objects.filter(source=source).exists():
        return
    earned_at = earned_at or timezone.now()
    expiry = expires_at or months_after(earned_at)
    already_expired = expiry <= timezone.now()
    lot = PointLot.objects.create(account=account, source=source, earned_at=earned_at,
        expires_at=expiry, original=amount, available=0 if already_expired else amount,
        expired=amount if already_expired else 0)
    points_transaction(account, source, 'EARN', amount, description)
    if already_expired:
        points_transaction(account, f'expire:{lot.pk}:{amount}', 'EXPIRE', -amount, 'Điểm nguồn đã hết hạn')
    recover_debt(account)


def revoke_points(account, source_prefix, amount, key):
    if amount <= 0 or PointTransaction.objects.filter(key=key).exists():
        return
    expire_points(account)
    remaining = amount
    for lot in account.lots.filter(source__startswith=source_prefix).order_by('earned_at', 'pk'):
        take = min(remaining, lot.available)
        lot.available -= take
        lot.revoked += take
        remaining -= take
        expired = min(remaining, lot.expired)
        lot.expired -= expired
        lot.revoked += expired
        remaining -= expired
        pending = min(remaining, lot.reserved - lot.pending_revocation)
        lot.pending_revocation += pending
        remaining -= pending
        spent = min(remaining, lot.spent)
        lot.spent -= spent
        lot.revoked += spent
        account.debt += spent
        remaining -= spent
        lot.save()
        if remaining == 0:
            break
    account.debt += remaining
    account.save(update_fields=['debt'])
    points_transaction(account, key, 'REVOKE', -amount, 'Điều chỉnh điểm sau hoàn tiền hoặc kiểm duyệt')
    recover_debt(account)


def debit_points(account, amount, *, order=None, key=''):
    expire_points(account)
    recover_debt(account)
    if account.debt or point_balance(account) < amount:
        raise BusinessError('Không đủ điểm khả dụng hoặc còn điểm cần bù.')
    left = amount
    for lot in account.lots.filter(available__gt=0, expires_at__gt=timezone.now()).order_by('earned_at', 'pk'):
        use = min(left, lot.available)
        lot.available -= use
        if order:
            lot.reserved += use
            PointHold.objects.create(order=order, lot=lot, amount=use)
        else:
            lot.spent += use
        lot.save()
        left -= use
        if not left:
            break
    if amount:
        points_transaction(account, key, 'HOLD' if order else 'EXCHANGE', -amount,
                           'Giữ điểm thanh toán' if order else 'Đổi điểm lấy voucher')


def settle_point_holds(order, consume):
    for hold in order.point_holds.filter(state='RESERVED').select_related('lot__account'):
        lot = hold.lot
        account = lot.account
        pending = min(lot.pending_revocation, hold.amount)
        lot.reserved -= hold.amount
        lot.pending_revocation -= pending
        if consume:
            lot.spent += hold.amount - pending
            lot.revoked += pending
            account.debt += pending
        else:
            lot.revoked += pending
            rest = hold.amount - pending
            if lot.expires_at <= timezone.now():
                lot.expired += rest
            else:
                lot.available += rest
        lot.save()
        account.save(update_fields=['debt'])
        hold.state = 'CONSUMED' if consume else 'RELEASED'
        hold.save(update_fields=['state'])
        if not consume:
            points_transaction(account, f'release:{hold.pk}', 'RELEASE', hold.amount - pending, 'Giải phóng điểm giữ theo đơn')
        recover_debt(account)


def restore_order_points(order, target):
    left = target - (order.point_holds.aggregate(total=Sum('restored'))['total'] or 0)
    for hold in order.point_holds.filter(state='CONSUMED').select_related('lot__account').order_by('pk'):
        amount = min(left, hold.amount - hold.restored)
        if amount <= 0:
            continue
        lot, account = hold.lot, hold.lot.account
        # Revoked held points become debt, so refunding them first settles debt.
        recoverable = min(amount, lot.spent)
        lot.spent -= recoverable
        lot.revoked += recoverable
        lot.save()
        award_points(account, f'restore:{hold.pk}:{hold.restored + amount}', amount, 'Hoàn điểm thanh toán',
            earned_at=timezone.now(), expires_at=lot.expires_at if lot.expires_at > timezone.now() else timezone.now() + timedelta(days=7))
        hold.restored += amount
        hold.save(update_fields=['restored'])
        left -= amount
        if left <= 0:
            break


def voucher_policy(voucher):
    return {key: getattr(voucher, key) for key in ('kind', 'value', 'cap', 'minimum', 'eligible_menu_ids', 'shipping_scope', 'name')}


def grant_voucher(user, voucher, source, key, expires_at, starts_at=None, policy=None):
    return UserVoucher.objects.get_or_create(grant_key=key, defaults={
        'user': user, 'voucher': voucher, 'source': source, 'policy': policy or voucher_policy(voucher),
        'starts_at': starts_at or timezone.now(), 'expires_at': expires_at})[0]


def internal_voucher(code, name, kind, value=0, cap=0, scope='ANY'):
    now = timezone.now()
    return Voucher.objects.get_or_create(code=code, defaults={'name': name, 'kind': kind, 'value': value,
        'cap': cap, 'shipping_scope': scope, 'starts_at': now, 'ends_at': months_after(now, 120)})[0]


def issue_tier_pack(account, tier):
    grant, created = BenefitGrant.objects.get_or_create(user=account.user, key=f'tier:{tier.code}')
    if not created:
        return
    specs = {
        'BRONZE': [('PERCENT', 20, 100000)],
        'SILVER': [('PERCENT', 20, 100000)] * 3,
        'GOLD': [('FREE_ITEM', 0, 100000)] + [('PERCENT', 25, 150000)] * 2,
        'DIAMOND': [('FREE_ITEM', 0, 100000)] * 3 + [('PERCENT', 30, 200000)] + [('PERCENT', 25, 150000)] * 3,
    }
    for index, (kind, value, cap) in enumerate(specs.get(tier.code, [])):
        voucher = internal_voucher(f'TIER_{tier.code}_{kind}_{value}', f'Quà hạng {tier.name}', kind, value, cap)
        grant_voucher(account.user, voucher, 'TIER', f'tier:{account.user_id}:{tier.code}:{index}',
                      timezone.now() + timedelta(days=getattr(settings, 'TIER_VOUCHER_DAYS', 90)))
        grant.count += 1
    grant.save(update_fields=['count'])


def evaluate_and_upgrade_tier(user_id):
    user = User.objects.get(pk=user_id)
    account = account_for(user)
    contribution = LoyaltyOrderContribution.objects.filter(account=account).aggregate(total=Sum('current_spend'))['total'] or 0
    # An order contributes at most one good review, including edits and moderation.
    good_orders = set()
    for review in Review.objects.filter(customer=user, is_published=True, order__loyalty_contribution__original_spend__gt=0,
                                        order__order_status='COMPLETED', rating__gte=4).exclude(order__purpose='SERVICE_REPLACEMENT'):
        if len(' '.join(unicodedata.normalize('NFC', review.comment).split())) >= 20:
            good_orders.add(review.order_id)
    tier = TierConfig.objects.filter(minimum_spend__lte=contribution, good_reviews__lte=len(good_orders)).order_by('-rank').first()
    account.total_qualifying_spend, account.good_review_count, account.tier = contribution, len(good_orders), tier
    if tier and tier.rank > account.highest_rank:
        issue_tier_pack(account, tier)
        account.highest_rank = tier.rank
    account.save()
    issue_period_benefits(account)
    return account


def issue_period_benefits(account, now=None):
    now = now or timezone.now()
    local = timezone.localtime(now)
    tier, user = account.tier, account.user
    if not tier:
        return
    period = local.strftime('%Y-%m')
    monthly, _ = BenefitGrant.objects.get_or_create(user=user, key=f'month:{period}')
    target = tier.monthly_shipping
    end = months_after(local.replace(day=1, hour=0, minute=0, second=0, microsecond=0), 1)
    scope = 'FAR' if tier.code in ('GOLD', 'DIAMOND') else 'ANY'
    voucher = internal_voucher(f'MONTHLY_SHIP_{scope}', 'Miễn phí giao hàng hằng tháng', 'SHIPPING', scope=scope)
    while monthly.count < target:
        grant_voucher(user, voucher, 'MONTHLY', f'month:{user.pk}:{period}:{monthly.count}', end, starts_at=now)
        monthly.count += 1
    monthly.save(update_fields=['count'])
    birth = user.date_of_birth
    if birth and tier.rank >= 2:
        day = min(birth.day, calendar.monthrange(local.year, birth.month)[1])
        if (local.month, local.day) == (birth.month, day):
            code = getattr(settings, 'BIRTHDAY_SPECIAL_VOUCHER' if tier.rank >= 3 else 'BIRTHDAY_STANDARD_VOUCHER', '')
            birthday_voucher = Voucher.objects.filter(code=code, active=True).first() if code else None
            if birthday_voucher:
                grant, created = BenefitGrant.objects.get_or_create(user=user, key=f'birthday:{local.year}')
                if created:
                    grant_voucher(user, birthday_voucher, 'BIRTHDAY', f'birthday:{user.pk}:{local.year}', now + timedelta(days=30))
                    grant.count = 1
                    grant.save(update_fields=['count'])


@serialized
def daily_checkin(user):
    account = account_for(user)
    today = timezone.localdate()
    existing = DailyCheckin.objects.filter(user=user, date=today).first()
    if existing:
        return existing
    previous = DailyCheckin.objects.filter(user=user, date=today - timedelta(days=1)).first()
    streak = previous.streak + 1 if previous else 1
    amount = getattr(settings, 'CHECKIN_BASE_POINTS', 1) * (2 if streak % 7 == 0 else 1)
    result = DailyCheckin.objects.create(user=user, date=today, streak=streak, points=amount)
    award_points(account, f'checkin:{user.pk}:{today}', amount, f'Điểm danh ngày {today:%d/%m}')
    return result


@serialized
def exchange_reward(user, reward_id, key):
    req = request_key(f'exchange:{user.pk}', key, {'reward': reward_id})
    if req.result:
        return UserVoucher.objects.get(pk=req.result['voucher'])
    reward = RewardCatalog.objects.select_related('voucher').filter(pk=reward_id, active=True).first()
    if not reward or reward.points_cost <= 0 or not reward.voucher.active:
        raise BusinessError('Quà đổi điểm không còn khả dụng.')
    if reward.quota and UserVoucher.objects.filter(grant_key__startswith=f'exchange:{reward.pk}:').count() >= reward.quota:
        raise BusinessError('Quà đổi điểm đã hết lượt.')
    account = account_for(user)
    debit_points(account, reward.points_cost, key=f'exchange:{req.pk}')
    voucher = grant_voucher(user, reward.voucher, 'EXCHANGE', f'exchange:{reward.pk}:{req.pk}',
                            timezone.now() + timedelta(days=reward.validity_days))
    req.result = {'voucher': voucher.pk}
    req.save(update_fields=['result'])
    return voucher


@serialized
def reconcile_order_loyalty(order_id):
    order = Order.objects.get(pk=order_id)
    if not order.customer_id or order.purpose != 'REGULAR' or order.order_status != 'COMPLETED':
        return
    account = account_for(order.customer)
    allocations = order.allocations.filter(item__isnull=False)
    original = allocations.aggregate(total=Sum('cash'))['total'] or 0
    current = allocations.filter(refunded=False).aggregate(total=Sum('cash'))['total'] or 0
    c, _ = LoyaltyOrderContribution.objects.get_or_create(order=order, defaults={
        'account': account, 'original_spend': original})
    target = current // 10000
    c.revision += 1
    if target > c.points_target:
        award_points(account, f'purchase:{order.pk}:{c.revision}', target - c.points_target,
                      f'Tích điểm đơn {order.order_code}', earned_at=order.completed_at or order.updated_at)
    elif target < c.points_target:
        revoke_points(account, f'purchase:{order.pk}:', c.points_target - target, f'purchase-revoke:{order.pk}:{c.revision}')
    c.current_spend, c.points_target = current, target
    c.save()
    evaluate_and_upgrade_tier(order.customer_id)
    if original > 0:
        # Event processing can be retried out of order. Choose the first actual
        # eligible completion, rather than the first event that happens to run.
        earliest = Order.objects.filter(customer_id=order.customer_id, purpose='REGULAR',
            order_status='COMPLETED', allocations__item__isnull=False, allocations__cash__gt=0
        ).order_by('completed_at', 'pk').values_list('pk', flat=True).first()
        if earliest != order.pk and not ReferralReward.objects.filter(newcomer=order.customer).exists():
            return
        referral, _ = ReferralReward.objects.get_or_create(newcomer=order.customer, defaults={
            'inviter_id': order.customer.referred_by_id or order.customer_id, 'order': order})
        # A sentinel self-record for users without an inviter prevents later retroactive awards.
        if referral.inviter_id != referral.newcomer_id and referral.order_id == order.pk:
            amount = getattr(settings, 'REFERRAL_POINTS', 50)
            for beneficiary in (referral.inviter, referral.newcomer):
                wallet = account_for(beneficiary)
                source = f'referral:{referral.pk}:{beneficiary.pk}'
                if current > 0 and not referral.reversed:
                    award_points(wallet, source, amount, 'Thưởng giới thiệu đơn đầu tiên', earned_at=order.completed_at or order.updated_at)
                elif current == 0 and not referral.reversed:
                    if PointLot.objects.filter(account=wallet, source=source).exists():
                        revoke_points(wallet, source, amount, f'reverse:{source}')
            if current == 0:
                referral.reversed = True
                referral.save(update_fields=['reversed'])


@serialized
def reward_review(review):
    order = review.order
    if not order or order.customer_id != review.customer_id or order.order_status != 'COMPLETED' or order.purpose != 'REGULAR':
        return
    reconcile_order_loyalty(order.pk)
    contribution = LoyaltyOrderContribution.objects.filter(order=order).first()
    if contribution and contribution.original_spend > 0:
        award_points(account_for(review.customer), f'review:{order.pk}', getattr(settings, 'REVIEW_POINTS', 5), 'Thưởng đánh giá đơn đã mua')
    evaluate_and_upgrade_tier(review.customer_id)


def enqueue(key, kind, **payload):
    from django.db import transaction
    event, created = DomainEvent.objects.get_or_create(key=key, defaults={'kind': kind, 'payload': payload})
    if created:
        transaction.on_commit(lambda: process_events(100), robust=True)
    return event


def process_events(limit=100):
    """Each event has its own transaction; cash confirmation is already durable."""
    for event_id in DomainEvent.objects.filter(processed_at__isnull=True).order_by('pk').values_list('pk', flat=True)[:limit]:
        try:
            process_event(event_id)
        except Exception as exc:
            DomainEvent.objects.filter(pk=event_id).update(error=str(exc)[:1000])


@serialized
def process_event(event_id):
    event = DomainEvent.objects.get(pk=event_id)
    if event.processed_at:
        return
    if event.kind == 'ORDER_COMPLETED':
        reconcile_order_loyalty(event.payload['order_id'])
    elif event.kind == 'REFUND_BENEFITS':
        from .aftersales import apply_refund_benefits
        apply_refund_benefits(event.payload['case_id'])
    event.processed_at, event.error = timezone.now(), ''
    event.save(update_fields=['processed_at', 'error'])


# Names preserved from the functional requirements.
evaluateAndUpgradeTier = serialized(evaluate_and_upgrade_tier)
