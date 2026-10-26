"""Authoritative quote and immutable integer allocation, shared by every payer."""
import math
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING

from django.conf import settings
from django.utils import timezone

from .domain import BusinessError, serialized
from .loyalty import (account_for, debit_points, point_balance, settle_point_holds,
                      voucher_policy, grant_voucher)
from .models import (CustomizationOption, LoyaltyAccount, TierConfig, MenuItem, OrderAllocation, Topping, UserVoucher, Voucher)


def split_integer(total, weights, caps=None):
    """Capped largest remainder allocation; exact sums, stable index tie break."""
    if total < 0 or any(w < 0 for w in weights):
        raise BusinessError('Phân bổ tiền không hợp lệ.')
    caps = list(caps if caps is not None else [total] * len(weights))
    if sum(caps) < total:
        raise BusinessError('Không đủ khả năng phân bổ khoản giảm.')
    result = [0] * len(weights)
    left = total
    while left:
        active = [i for i in range(len(weights)) if result[i] < caps[i]]
        denom = sum(weights[i] for i in active)
        if not active or not denom:
            raise BusinessError('Không phân bổ được khoản giảm.')
        raw = {i: Decimal(left) * weights[i] / denom for i in active}
        assigned = 0
        for i in active:
            amount = min(caps[i] - result[i], int(raw[i]))
            result[i] += amount
            assigned += amount
        left -= assigned
        if left:
            for i in sorted(active, key=lambda i: (-(raw[i] - int(raw[i])), i)):
                if left and result[i] < caps[i]:
                    result[i] += 1
                    left -= 1
    return result


def resolve_cart(payload):
    if not isinstance(payload, list) or not 1 <= len(payload) <= 50:
        raise BusinessError('Giỏ hàng phải có từ 1 đến 50 dòng món.')
    lines = []
    for row in payload:
        if not isinstance(row, dict) or not isinstance(row.get('toppings', []), list) or not isinstance(row.get('customizations', []), list):
            raise BusinessError('Không tìm thấy món hợp lệ. Dữ liệu giỏ hàng không hợp lệ.')
        try:
            pk, qty = int(row['id']), int(row.get('qty', 1))
            tids, cids = [int(i) for i in row.get('toppings', [])], [int(i) for i in row.get('customizations', [])]
        except (KeyError, TypeError, ValueError):
            raise BusinessError('Số lượng hoặc mã món không hợp lệ.')
        product = MenuItem.objects.filter(pk=pk, is_active=True).first()
        if not product or not 1 <= qty <= 99 or len(tids) != len(set(tids)) or len(cids) != len(set(cids)):
            raise BusinessError('Món hoặc số lượng đã thay đổi; hãy tải lại thực đơn.')
        toppings = list(Topping.objects.filter(pk__in=tids, is_active=True).order_by('pk'))
        choices = list(CustomizationOption.objects.filter(pk__in=cids).order_by('pk'))
        if product.category == 'PHO':
            if len(toppings) != len(tids) or len(choices) != len(cids) or len(choices) != 3 or {c.category for c in choices} != {'BROTH', 'VEGGIE', 'NOODLE'}:
                raise BusinessError('Tùy chọn món không hợp lệ. Chọn đủ một nước dùng, rau/giá và bánh phở; topping phải còn phục vụ.')
        elif tids or cids:
            raise BusinessError('Đồ uống không có tùy chọn phở hoặc topping.')
        price = int(product.base_price + sum((t.price for t in toppings), Decimal(0)))
        lines.append({'product': product, 'qty': qty, 'toppings': toppings, 'choices': choices,
                      'note': str(row.get('note', ''))[:500], 'price': price})
    return lines


def delivery_price(coords):
    from .services import haversine_km
    if not coords:
        raise BusinessError('Cần tọa độ địa chỉ nhận để xác minh phạm vi giao hàng trước khi đặt đơn.')
    raw = Decimal(str(haversine_km(float(getattr(settings, 'RESTAURANT_LAT', 10.7769)),
        float(getattr(settings, 'RESTAURANT_LNG', 106.7009)), *coords)))
    if raw > Decimal(str(settings.DELIVERY_MAX_KM)):
        raise BusinessError('Địa chỉ nằm ngoài phạm vi giao hàng.')
    distance = raw.quantize(Decimal('.000001'), rounding=ROUND_CEILING)
    fee = int(getattr(settings, 'DELIVERY_BASE_FEE', 15000)) + int(getattr(settings, 'DELIVERY_FEE_PER_KM', 8000)) * max(1, math.ceil(raw))
    return fee, distance


def select_voucher(user, wallet_id=None, code='', reserve=False):
    now = timezone.now()
    if not wallet_id and not code:
        return None, None
    if not user or not user.is_customer():
        raise BusinessError('Đăng nhập tài khoản khách hàng để dùng voucher.')
    if wallet_id:
        wallet = UserVoucher.objects.select_related('voucher').filter(pk=wallet_id, user=user).first()
        if not wallet or wallet.state != 'AVAILABLE' or not wallet.starts_at <= now < wallet.expires_at:
            raise BusinessError('Voucher không thuộc tài khoản, hết hạn hoặc đang được giữ cho đơn khác.')
        if wallet.source == 'CAMPAIGN':
            check_campaign_capacity(wallet.voucher, user)
        return wallet, wallet.policy
    voucher = Voucher.objects.filter(code__iexact=code.strip(), public=True, active=True).first()
    if not voucher or not voucher.starts_at <= now < voucher.ends_at:
        raise BusinessError('Mã khuyến mãi không hợp lệ hoặc hết hạn.')
    check_campaign_capacity(voucher, user)
    if reserve:
        import uuid
        wallet = grant_voucher(user, voucher, 'CAMPAIGN', f'campaign:{uuid.uuid4().hex}', voucher.ends_at)
        return wallet, wallet.policy
    return None, voucher_policy(voucher)


def check_campaign_capacity(voucher, user):
    # Compensation gifts and point exchanges have their own issuance budgets.
    # A released campaign wallet still competes for campaign redemption capacity.
    used = UserVoucher.objects.filter(voucher=voucher, source='CAMPAIGN', state__in=['RESERVED', 'CONSUMED'])
    if voucher.quota and used.count() >= voucher.quota:
        raise BusinessError('Mã đã hết lượt sử dụng.')
    if used.filter(user=user).count() >= voucher.per_user_limit:
        raise BusinessError('Bạn đã dùng hết lượt của mã này.')


def calculate_order_checkout(lines, user=None, fee=0, distance=None, policy=None, requested_points=0):
    account = LoyaltyAccount.objects.filter(user=user).select_related('tier').first() if user else None
    tier = account.tier if account else None
    gross_units, indices = [], []
    for index, line in enumerate(lines):
        for unit in range(line['qty']):
            gross_units.append(line['price'])
            indices.append((index, unit + 1))
    gross = sum(gross_units)
    tier_discount = gross * (tier.discount_percent if tier else 0) // 100
    tier_parts = split_integer(tier_discount, gross_units, gross_units)
    net = [g - d for g, d in zip(gross_units, tier_parts)]
    coupon_parts = [0] * len(net)
    voucher_discount = shipping_discount = 0
    auto_shipping = fee if tier and tier.nearby_shipping and distance is not None and distance <= 5 else 0
    if policy:
        eligible_ids = policy.get('eligible_menu_ids', [])
        eligible = [i for i, (idx, _) in enumerate(indices) if not eligible_ids or lines[idx]['product'].pk in eligible_ids]
        subtotal = sum(net[i] for i in eligible)
        if subtotal < policy['minimum']:
            raise BusinessError(f"Voucher yêu cầu tiền món sau giảm hạng từ {policy['minimum']:,}đ.")
        kind = policy['kind']
        if kind == 'SHIPPING':
            if not fee or distance is None or (policy.get('shipping_scope') == 'FAR' and distance <= 5):
                raise BusinessError('Voucher giao hàng không phù hợp loại đơn hoặc khoảng cách.')
            remaining_fee = fee - auto_shipping
            shipping_discount = min(remaining_fee, policy['cap']) if policy['cap'] else remaining_fee
            if not shipping_discount:
                raise BusinessError('Đơn đã được miễn phí giao theo hạng; hãy chọn voucher giảm món.')
        elif kind == 'FREE_ITEM':
            eligible = [i for i in eligible if lines[indices[i][0]]['product'].category == 'PHO'
                        and lines[indices[i][0]]['product'].base_price < 100000]
            if not eligible:
                raise BusinessError('Voucher tặng một món phở có giá gốc dưới 100.000đ, không gồm topping.')
            i = max(eligible, key=lambda i: lines[indices[i][0]]['product'].base_price)
            base = int(lines[indices[i][0]]['product'].base_price)
            amount = base * net[i] // gross_units[i] if gross_units[i] else 0
            coupon_parts[i] = min(net[i], amount)
        else:
            discount = subtotal * policy['value'] // 100 if kind == 'PERCENT' else policy['value']
            if kind == 'PERCENT' and policy['cap']:
                discount = min(discount, policy['cap'])
            discount = min(discount, subtotal)
            if not discount:
                raise BusinessError('Voucher không có món phù hợp trong giỏ.')
            weights = [net[i] if i in eligible else 0 for i in range(len(net))]
            coupon_parts = split_integer(discount, weights, weights)
        voucher_discount = sum(coupon_parts)
    net = [n - c for n, c in zip(net, coupon_parts)]
    ship_net = fee - auto_shipping - shipping_discount
    all_net = net + ([ship_net] if fee else [])
    remaining = sum(all_net)
    available = point_balance(account) if account and not account.debt else 0
    max_points = min(remaining // 200, available, sum(n // 100 for n in all_net))
    if requested_points < 0 or requested_points > max_points:
        raise BusinessError(f'Đơn này dùng tối đa {max_points} điểm khả dụng.')
    point_parts = split_integer(requested_points, all_net, [n // 100 for n in all_net]) if requested_points else [0] * len(all_net)
    parts = [{'line': idx, 'unit': unit, 'net': net[i], 'points': point_parts[i], 'cash': net[i] - 100 * point_parts[i]}
             for i, (idx, unit) in enumerate(indices)]
    if fee:
        parts.append({'line': None, 'unit': 0, 'net': ship_net, 'points': point_parts[-1], 'cash': ship_net - 100 * point_parts[-1]})
    return {'subtotal': gross, 'tier': tier.code if tier else 'MEMBER', 'tier_discount': tier_discount,
        'voucher_discount': voucher_discount, 'delivery_fee': fee, 'auto_shipping_discount': auto_shipping,
        'voucher_shipping_discount': shipping_discount, 'points': requested_points, 'point_discount': requested_points * 100,
        'max_points': max_points, 'payable': remaining - requested_points * 100, 'allocations': parts, 'policy_version': 1}


def save_checkout(order, quote, saved_items, wallet):
    order.checkout_snapshot = quote
    order.payable_amount = quote['payable']
    order.benefits_state = 'RESERVED'
    order.expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'CHECKOUT_HOLD_MINUTES', 15))
    order.save(update_fields=['checkout_snapshot', 'payable_amount', 'benefits_state', 'expires_at'])
    for part in quote['allocations']:
        item = saved_items[part['line']] if part['line'] is not None else None
        OrderAllocation.objects.create(order=order, item=item, unit=part['unit'],
            label=item.menu_item.name if item else 'Phí giao hàng', net_before_points=part['net'], points=part['points'], cash=part['cash'])
    if wallet:
        wallet.state, wallet.order = 'RESERVED', order
        wallet.save(update_fields=['state', 'order'])
    if quote['points']:
        debit_points(account_for(order.customer), quote['points'], order=order, key=f'checkout:{order.pk}')


def consume_benefits(order):
    if order.benefits_state != 'RESERVED':
        return
    if not order.expires_at or timezone.now() >= order.expires_at:
        raise BusinessError('Thời gian giữ ưu đãi đã hết; khoản tiền cần đối soát.')
    UserVoucher.objects.filter(order=order, state='RESERVED').update(state='CONSUMED')
    settle_point_holds(order, True)
    order.benefits_state = 'CONSUMED'
    type(order).objects.filter(pk=order.pk).update(benefits_state='CONSUMED')


def release_benefits(order, expired=False):
    from .stock import release_inventory
    release_inventory(order, expired)
    UserVoucher.objects.filter(order=order, state='RESERVED').update(state='AVAILABLE', order=None)
    settle_point_holds(order, False)
    if order.benefits_state == 'RESERVED':
        order.benefits_state = 'RELEASED'
        type(order).objects.filter(pk=order.pk).update(benefits_state='RELEASED')


calculateOrderCheckout = calculate_order_checkout
