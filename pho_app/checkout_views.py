import hashlib
import json
import uuid

from django.contrib import messages
from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .checkout import (calculate_order_checkout, delivery_price, resolve_cart,
                       save_checkout, select_voucher)
from .domain import BusinessError, request_key, serialized
from .models import (Delivery, Order, OrderItem, OrderItemCustomization, OrderItemTopping,
                     QueueTicket, Table, UserAddress)
from .services import active_queue_ticket, customer_point, inventory_deductions, parse_coords, used_bowls
from .stock import expire_orders, reserve_inventory
from .locations import normalize_delivery_phone


def checkout_inputs(request, reserve=False):
    if request.user.is_authenticated and not request.user.is_customer():
        raise BusinessError('Tài khoản nhân viên không đặt món trong chế độ khách hàng.')
    user = request.user if request.user.is_authenticated else None
    try:
        lines = resolve_cart(json.loads(request.POST.get('cart', '[]')))
        points = int(request.POST.get('points', 0) or 0)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise BusinessError(str(exc) or 'Giỏ hàng hoặc số điểm không hợp lệ.')
    kind = request.POST.get('order_type', 'DINE_IN')
    if kind not in ('DINE_IN', 'DELIVERY', 'QUEUE_CART'):
        raise BusinessError('Loại đơn không hợp lệ.')
    address = None
    snapshot = {'recipient_name': request.POST.get('recipient_name', '').strip()[:100] or (user.display_name if user else ''),
        'phone': request.POST.get('recipient_phone', '').strip()[:20] or (user.phone_number if user else ''),
        'address': request.POST.get('delivery_address', '').strip()[:500], 'note': request.POST.get('delivery_note', '')[:500]}
    coords = parse_coords(request.POST.get('customer_lat'), request.POST.get('customer_lng'))
    if request.POST.get('address_id'):
        address = UserAddress.objects.filter(pk=request.POST['address_id'], user=user).first() if user else None
        if not address or str(address.version) != request.POST.get('address_version'):
            raise BusinessError('Địa chỉ đã thay đổi; hãy chọn lại địa chỉ và báo giá.')
        snapshot = {'address_id': address.pk, 'version': address.version, 'recipient_name': address.recipient_name,
            'phone': address.phone, 'address': address.full_address, 'note': address.note,
            'ward': address.ward, 'district': address.district, 'province': address.province}
        if address.latitude is not None or address.longitude is not None:
            coords = parse_coords(address.latitude, address.longitude)
        if 'delivery_note' in request.POST:
            snapshot['note'] = request.POST.get('delivery_note', '')[:500]
    fee, distance = 0, None
    if kind == 'DELIVERY':
        if not snapshot['address'] or not snapshot['recipient_name'] or not snapshot['phone']:
            raise BusinessError('Điền tên người nhận, điện thoại và địa chỉ giao hàng.')
        snapshot['phone'] = normalize_delivery_phone(snapshot['phone'])
        fee, distance = delivery_price(coords)
        snapshot['latitude'], snapshot['longitude'] = coords
        snapshot['shop_latitude'], snapshot['shop_longitude'] = settings.RESTAURANT_LAT, settings.RESTAURANT_LNG
    wallet_id = request.POST.get('wallet_id') or None
    code = request.POST.get('voucher_code', '')
    if wallet_id and code.strip():
        raise BusinessError('Mỗi đơn chỉ dùng một voucher. Chọn mã trong ví hoặc nhập mã khuyến mãi.')
    wallet, policy = select_voucher(user, wallet_id, code, reserve)
    quote = calculate_order_checkout(lines, user, fee, distance, policy, points)
    # Bind quote to current user, address and exact server-calculated prices.
    identity = {'user': user.pk if user else None, 'quote': quote, 'delivery': snapshot if kind == 'DELIVERY' else {},
        'type': kind, 'cart': json.loads(request.POST.get('cart', '[]')), 'wallet': wallet_id, 'code': code.strip().upper()}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()
    return lines, kind, snapshot, coords, distance, wallet, quote, digest


@require_POST
@serialized
def quote_checkout(request):
    try:
        lines, _, _, _, _, _, quote, digest = checkout_inputs(request)
        from .services import ensure_inventory_available
        ensure_inventory_available(inventory_deductions([(l['product'], l['qty'], [(t, l['qty']) for t in l['toppings']]) for l in lines]))
        quote = {**quote, 'token': signing.dumps({'digest': digest}, salt='checkout')}
        return JsonResponse({'ok': True, **quote})
    except (BusinessError, ValueError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@require_POST
def place_order(request):
    # Persist the anonymous session outside the order savepoint. If validation
    # rolls back the order, SessionMiddleware must still be able to save it.
    if not request.user.is_authenticated and not request.session.session_key:
        request.session.create()
    try:
        order = create_order(request)
    except (BusinessError, ValueError, signing.BadSignature) as exc:
        messages.error(request, str(exc))
        return redirect('menu')
    if order.customer_id is None:
        request.session['guest_orders'] = list(dict.fromkeys(request.session.get('guest_orders', []) + [order.pk]))[-100:]
    request.session['latest_order_id'] = order.pk
    messages.success(request, f'Đã tạo đơn {order.order_code}. Giữ món và ưu đãi trong 15 phút.')
    return redirect(f"{reverse('order_detail', args=[order.pk])}?placed=1")


@serialized
def create_order(request):
    expire_orders()
    principal = str(request.user.pk) if request.user.is_authenticated else request.session.session_key
    if not principal:
        request.session.create()
        principal = request.session.session_key
    key = request.POST.get('request_key') or uuid.uuid4().hex
    req = request_key(f'checkout:{principal}', key, {k: v for k, v in request.POST.items()
        if k not in ('csrfmiddlewaretoken', 'account_generation', 'quote_token')})
    if req.result:
        return Order.objects.get(pk=req.result['order'])
    lines, kind, snapshot, coords, distance, wallet, quote, digest = checkout_inputs(request, reserve=True)
    token = request.POST.get('quote_token')
    if token and signing.loads(token, salt='checkout', max_age=900).get('digest') != digest:
        raise BusinessError('Giá, điểm, quyền lợi hoặc địa chỉ vừa thay đổi. Hãy xem lại báo giá.')
    ticket = active_queue_ticket(request)
    table_id = request.POST.get('table_id') or None
    if kind == 'QUEUE_CART':
        if not ticket or ticket.status != 'CALLED' or not ticket.table_id:
            raise BusinessError('Giỏ xếp hàng chỉ thanh toán sau khi được gọi số.')
        kind, table_id = 'DINE_IN', ticket.table_id
    elif ticket and ticket.status == 'CALLED' and kind == 'DINE_IN':
        table_id = ticket.table_id
    table = None
    if kind == 'DINE_IN' and table_id:
        table = Table.objects.select_for_update().filter(pk=table_id, status__in=['AVAILABLE', 'OCCUPIED']).first()
        if not table:
            raise BusinessError('Bàn không còn khả dụng.')
        other_ticket = QueueTicket.objects.filter(table=table, status='CALLED')
        if ticket:
            other_ticket = other_ticket.exclude(pk=ticket.pk)
        if other_ticket.exists() or used_bowls(table) + sum(l['qty'] for l in lines if l['product'].category == 'PHO') > table.capacity:
            raise BusinessError('Bàn không còn đủ chỗ hoặc đang giữ cho khách khác.')
    payment = 'VIETQR' if kind == 'DELIVERY' else request.POST.get('payment_method', 'VIETQR')
    if payment not in ('CASH', 'VIETQR'):
        raise BusinessError('Phương thức thanh toán không hợp lệ.')
    user = request.user if request.user.is_authenticated else None
    order = Order.objects.create(order_code=f'PHO-{uuid.uuid4().hex[:12].upper()}', customer=user,
        guest_name=request.POST.get('guest_name', 'Khách tại quán')[:100] if not user else '', table=table,
        queue_ticket=ticket if ticket and ticket.status == 'CALLED' and kind == 'DINE_IN' else None,
        order_type=kind, payment_method=payment, total_amount=quote['subtotal'], delivery_fee=quote['delivery_fee'],
        delivery_address=snapshot['address'] if kind == 'DELIVERY' else '', delivery_snapshot=snapshot if kind == 'DELIVERY' else {},
        distance_raw_km=distance, delivery_distance_km=round(distance, 2) if distance is not None else None,
        customer_location=customer_point(*coords) if kind == 'DELIVERY' and coords else None,
        shipping_code=f'VD-{uuid.uuid4().hex[:8].upper()}' if kind == 'DELIVERY' else '')
    saved = []
    for line in lines:
        item = OrderItem.objects.create(order=order, menu_item=line['product'], quantity=line['qty'], item_price=line['price'], note=line['note'])
        OrderItemTopping.objects.bulk_create([OrderItemTopping(order_item=item, topping=t, quantity=line['qty']) for t in line['toppings']])
        OrderItemCustomization.objects.bulk_create([OrderItemCustomization(order_item=item, customization=c) for c in line['choices']])
        saved.append(item)
    save_checkout(order, quote, saved, wallet)
    deductions = inventory_deductions([(l['product'], l['qty'], [(t, l['qty']) for t in l['toppings']]) for l in lines])
    reserve_inventory(order, deductions)
    if kind == 'DELIVERY':
        Delivery.objects.create(order=order)
    if not quote['payable']:
        order.payment_status, order.order_status = 'PAID', 'PENDING_KITCHEN'
        order.save(update_fields=['payment_status', 'order_status'])
    if table:
        table.status = 'OCCUPIED'
        table.save(update_fields=['status'])
    if order.queue_ticket_id:
        ticket.status = 'SEATED'
        ticket.save(update_fields=['status'])
        request.session.pop('queue_ticket_id', None)
    req.result = {'order': order.pk}
    req.save(update_fields=['result'])
    return order
