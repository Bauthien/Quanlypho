import hashlib
import hmac
import json
import re
import uuid
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Prefetch, Q, Sum
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import MenuItemForm, OrderFilterForm, RegisterForm, StyledAuthForm, ToppingForm, UserRoleForm
from .models import (
    CustomizationOption,
    MenuItem,
    Order,
    OrderItem,
    OrderItemCustomization,
    OrderItemTopping,
    QueueTicket,
    Review,
    Table,
    Topping,
    User,
)
from .permissions import admin_required, kitchen_or_staff_required, kitchen_required, staff_required
from .services import (
    InvalidOrderTransition,
    ORDER_ACTION_LABELS,
    active_queue_ticket,
    apply_order_action,
    available_order_actions,
    compute_delivery_fee,
    customer_point,
    parse_coords,
    tables_are_full,
    tables_with_capacity,
    used_bowls,
)


def _perform_order_action(request, order_id, action):
    try:
        order = apply_order_action(order_id, action)
    except Order.DoesNotExist as exc:
        raise Http404('Không tìm thấy đơn hàng.') from exc
    except InvalidOrderTransition as exc:
        messages.error(request, str(exc))
        return None
    messages.success(request, f'{order.order_code}: {ORDER_ACTION_LABELS[action]}.')
    return order


@admin_required
def admin_orders(request):
    filter_form = OrderFilterForm(request.GET)
    orders = Order.objects.select_related('customer', 'table').annotate(
        grand_total=F('total_amount') + F('delivery_fee'),
    )
    sort = 'newest'
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data['q']:
            query = data['q']
            orders = orders.filter(
                Q(order_code__icontains=query) | Q(customer__full_name__icontains=query)
                | Q(customer__username__icontains=query) | Q(guest_name__icontains=query)
                | Q(table__table_number__icontains=query) | Q(shipping_code__icontains=query)
            )
        for field in ('order_type', 'order_status', 'payment_status', 'payment_method'):
            if data[field]:
                orders = orders.filter(**{field: data[field]})
        if data['date_from']:
            orders = orders.filter(created_at__date__gte=data['date_from'])
        if data['date_to']:
            orders = orders.filter(created_at__date__lte=data['date_to'])
        sort = data['sort'] or 'newest'
    else:
        orders = orders.none()
    stats = orders.aggregate(
        total=Count('pk'),
        waiting=Count('pk', filter=Q(payment_status=Order.PaymentStatus.PENDING)),
        preparing=Count('pk', filter=Q(order_status__in=[Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING])),
        ready=Count('pk', filter=Q(order_status=Order.OrderStatus.READY)),
        delivering=Count('pk', filter=Q(order_status=Order.OrderStatus.DELIVERING)),
        completed=Count('pk', filter=Q(order_status=Order.OrderStatus.COMPLETED)),
        cancelled=Count('pk', filter=Q(order_status=Order.OrderStatus.CANCELLED)),
        paid_total=Sum('grand_total', filter=Q(payment_status=Order.PaymentStatus.PAID), default=Decimal('0')),
    )
    ordering = {
        'newest': ('-created_at', '-pk'), 'oldest': ('created_at', 'pk'),
        'total_desc': ('-grand_total', '-pk'), 'total_asc': ('grand_total', 'pk'),
    }[sort]
    page_obj = Paginator(orders.order_by(*ordering), 20).get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)
    return render(request, 'pho_app/admin/orders.html', {
        'filter_form': filter_form, 'page_obj': page_obj, 'stats': stats,
        'query_string': query_params.urlencode(),
        'page_links': page_obj.paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1),
        'stat_cards': [
            ('Tổng đơn', stats['total'], 'orders', 'neutral'),
            ('Chờ thanh toán', stats['waiting'], 'wallet', 'warning'),
            ('Đang chế biến', stats['preparing'], 'chef', 'brand'),
            ('Sẵn sàng phục vụ', stats['ready'], 'bowl', 'success'),
            ('Đang giao', stats['delivering'], 'truck', 'brand'),
            ('Hoàn tất', stats['completed'], 'check', 'success'),
            ('Đã hủy', stats['cancelled'], 'close', 'neutral'),
        ],
    })


@admin_required
def admin_order_detail(request, order_id):
    items = OrderItem.objects.select_related('menu_item').prefetch_related(
        Prefetch('toppings', queryset=OrderItemTopping.objects.select_related('topping').order_by('pk')),
        Prefetch('customizations', queryset=OrderItemCustomization.objects.select_related('customization').order_by('pk')),
    ).order_by('pk')
    order = get_object_or_404(Order.objects.select_related('customer', 'table', 'queue_ticket').prefetch_related(
        Prefetch('items', queryset=items),
    ), pk=order_id)
    order_items = list(order.items.all())
    for item in order_items:
        # item_price already includes the selected toppings for one bowl.
        item.line_total = item.item_price * item.quantity
    actions = [{'name': action, 'label': ORDER_ACTION_LABELS[action]} for action in available_order_actions(order)]
    return render(request, 'pho_app/admin/order_detail.html', {
        'order': order, 'order_items': order_items, 'order_actions': actions,
        'grand_total': order.total_amount + order.delivery_fee,
        'can_print_labels': order.payment_status == Order.PaymentStatus.PAID
            and order.order_type == Order.OrderType.DELIVERY
            and order.order_status in (Order.OrderStatus.READY, Order.OrderStatus.DELIVERING),
    })


@admin_required
@require_POST
def admin_order_action(request, order_id):
    _perform_order_action(request, order_id, request.POST.get('action', ''))
    return redirect('admin_order_detail', order_id=order_id)


def natural_sort_table(tables_qs):
    tables = list(tables_qs)
    tables.sort(key=lambda t: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(t.table_number))])
    return tables


def _generate_order_code():
    return f"PHO-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def _vietqr_image_url(order):
    bank = getattr(settings, 'VIETQR_BANK_ID', '') or '970415'
    account = getattr(settings, 'VIETQR_ACCOUNT_NO', '') or '113366668888'
    account_name = getattr(settings, 'VIETQR_ACCOUNT_NAME', '') or 'TEST PHO GIA TRUYEN'
    query = urlencode({
        'amount': int(order.total_amount + order.delivery_fee),
        'addInfo': order.order_code,
        'accountName': account_name,
    })
    return f'https://img.vietqr.io/image/{bank}-{account}-compact2.png?{query}'



def django_admin_disabled(request):
    raise Http404('Trang quản trị Django đã được tắt. Vui lòng dùng trang Quản lý của hệ thống.')


def home(request):
    if request.user.is_authenticated:
        return redirect(request.user.home_url_name())
    return render(request, 'pho_app/customer/home.html', {
        'featured_items': MenuItem.objects.filter(is_active=True)[:3],
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.home_url_name())
    form = StyledAuthForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Xin chào {request.user.display_name}!')
        return redirect(request.user.home_url_name())
    return render(request, 'pho_app/auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.home_url_name())
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Đăng ký thành công. Tài khoản của bạn là khách hàng.')
        return redirect('menu')
    return render(request, 'pho_app/auth/register.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất.')
    return redirect('login')


def menu_view(request):
    selected_table = request.GET.get('table', '')
    is_door = request.GET.get('door') == '1'
    if request.user.is_authenticated and request.user.role in (User.Role.STAFF, User.Role.KITCHEN, User.Role.ADMIN):
        if not selected_table:
            return redirect(request.user.home_url_name())
    items = MenuItem.objects.filter(is_active=True)
    menu_payload = [
        {
            'id': item.id,
            'name': item.name,
            'category': item.category.lower(),
            'price': int(item.base_price),
            'desc': 'Chọn món và thanh toán VietQR hoặc tiền mặt.',
            'image': item.image_primary.url if item.image_primary else '',
        }
        for item in items
    ]
    options = list(CustomizationOption.objects.all().order_by('category', 'id').values('id', 'category', 'name'))
    toppings = list(Topping.objects.filter(is_active=True).order_by('name').values('id', 'name', 'price'))
    latest_order = Order.objects.filter(customer=request.user).order_by('-created_at').first() if request.user.is_authenticated else Order.objects.filter(pk=request.session.get('latest_order_id')).first()
    ticket = active_queue_ticket(request)
    tables_qs = tables_with_capacity()
    full_house = tables_are_full()

    if selected_table.isdigit():
        tables = tables_qs.filter(Q(remaining_cap__gt=0) | Q(pk=selected_table))
    elif ticket and ticket.status == QueueTicket.Status.CALLED and ticket.table_id:
        tables = tables_qs.filter(Q(remaining_cap__gt=0) | Q(pk=ticket.table_id))
    else:
        tables = tables_qs.filter(remaining_cap__gt=0)

    table_obj = None
    remaining_capacity = 999
    scanned_table_full = False

    if selected_table.isdigit():
        table_obj = tables_qs.filter(pk=selected_table).first()
        if table_obj:
            remaining_capacity = getattr(table_obj, 'remaining_cap', 0)
            scanned_table_full = remaining_capacity <= 0
            if scanned_table_full:
                messages.warning(request, f'Bàn {table_obj.table_number} hiện đã hết chỗ. Bạn có thể xem menu và lấy số xếp hàng.')

    tables = natural_sort_table(tables)
    door_qr = request.build_absolute_uri('/thuc-don/?door=1')
    return render(request, 'pho_app/customer/menu.html', {
        'menu_items': items,
        'menu_payload': menu_payload,
        'customization_options': options,
        'toppings': toppings,
        'tables': tables,
        'latest_order': latest_order,
        'active_ticket': ticket,
        'selected_table': selected_table,
        'remaining_capacity': remaining_capacity,
        'table_obj': table_obj,
        'tables_full': full_house,
        'is_door': is_door,
        'scanned_table_full': scanned_table_full,
        'delivery_flat_fee': getattr(settings, 'DELIVERY_FLAT_FEE', 30000),
        'delivery_max_km': getattr(settings, 'DELIVERY_MAX_KM', 10),
        'door_qr_url': door_qr,
    })


@require_POST
def place_order(request):
    if request.user.is_authenticated and not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới được đặt món.')
        return redirect(request.user.home_url_name())

    try:
        payload = json.loads(request.POST.get('cart', '[]'))
    except json.JSONDecodeError:
        messages.error(request, 'Giỏ hàng không hợp lệ.')
        return redirect('menu')

    if not isinstance(payload, list) or not payload or len(payload) > 50:
        messages.error(request, 'Giỏ hàng đang trống.')
        return redirect('menu')

    payment_method = request.POST.get('payment_method', Order.PaymentMethod.VIETQR)
    order_type = request.POST.get('order_type', Order.OrderType.DINE_IN)
    table_id = request.POST.get('table_id') or None

    if payment_method not in dict(Order.PaymentMethod.choices):
        payment_method = Order.PaymentMethod.VIETQR
    if order_type not in dict(Order.OrderType.choices):
        order_type = Order.OrderType.DINE_IN

    if order_type == Order.OrderType.DELIVERY:
        payment_method = Order.PaymentMethod.VIETQR

    total = Decimal('0')
    resolved_items = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        try:
            menu_id = int(row.get('id'))
            quantity = int(row.get('qty', 1))
            topping_ids = [int(value) for value in row.get('toppings', [])]
            customization_ids = [int(value) for value in row.get('customizations', [])]
        except (TypeError, ValueError):
            continue
        menu_item = MenuItem.objects.filter(pk=menu_id, is_active=True).first()
        if not menu_item:
            continue
        if not 1 <= quantity <= 99:
            continue
        if len(topping_ids) != len(set(topping_ids)) or len(customization_ids) != len(set(customization_ids)):
            continue
        selected_options = list(CustomizationOption.objects.filter(pk__in=customization_ids))
        if len({option.category for option in selected_options}) != len(selected_options):
            messages.error(request, f'Chỉ chọn một tùy chọn cho mỗi nhóm của món {menu_item.name}.')
            return redirect('menu')
        required_categories = {choice[0] for choice in CustomizationOption.Category.choices}
        if {option.category for option in selected_options} != required_categories:
            messages.error(request, f'Vui lòng chọn đủ nước dùng, rau/gia và bánh phở cho món {menu_item.name}.')
            return redirect('menu')
        selected_toppings = list(Topping.objects.filter(pk__in=topping_ids, is_active=True))
        if len(selected_toppings) != len(topping_ids) or len(selected_options) != len(customization_ids):
            messages.error(request, 'Tùy chọn món không hợp lệ. Vui lòng tải lại thực đơn.')
            return redirect('menu')
        note = str(row.get('note', '')).strip()[:500]
        item_total = menu_item.base_price + sum((topping.price for topping in selected_toppings), Decimal('0'))
        resolved_items.append((menu_item, quantity, selected_toppings, selected_options, note, item_total))
        total += item_total * quantity

    if not resolved_items:
        messages.error(request, 'Không tìm thấy món hợp lệ.')
        return redirect('menu')

    address = request.POST.get('delivery_address', '').strip()
    delivery_fee = Decimal('0')
    delivery_distance = None
    location = None
    ticket = active_queue_ticket(request)

    if order_type == Order.OrderType.QUEUE_CART:
        if not ticket or ticket.status != QueueTicket.Status.CALLED or not ticket.table_id:
            messages.error(request, 'Giỏ xếp hàng chỉ thanh toán sau khi được gọi số. Bạn vẫn có thể chọn món trước.')
            return redirect('menu')
        order_type = Order.OrderType.DINE_IN
        table_id = str(ticket.table_id)
    elif ticket and ticket.status == QueueTicket.Status.CALLED and ticket.table_id and order_type == Order.OrderType.DINE_IN:
        table_id = str(ticket.table_id)

    if order_type == Order.OrderType.DELIVERY:
        payment_method = Order.PaymentMethod.VIETQR
        coords = parse_coords(request.POST.get('customer_lat'), request.POST.get('customer_lng'))
        lat = coords[0] if coords else None
        lng = coords[1] if coords else None

        # Nếu không có địa chỉ VÀ không có GPS thì mới báo lỗi
        if not address and not coords:
            messages.error(request, 'Vui lòng nhập địa chỉ giao hàng hoặc dùng vị trí hiện tại.')
            return redirect('menu')

        delivery_fee, delivery_distance, in_range = compute_delivery_fee(lat, lng)
        if not in_range:
            messages.error(request, f'Địa chỉ nằm ngoài phạm vi giao hàng ({getattr(settings, "DELIVERY_MAX_KM", 10)} km).')
            return redirect('menu')
        if coords:
            location = customer_point(lat, lng)

    table = None
    if order_type == Order.OrderType.DINE_IN:
        if not table_id:
            messages.error(request, 'Vui lòng chọn bàn trống hoặc quét mã QR tại bàn.')
            return redirect('menu')

    with transaction.atomic():
        seated_ticket = None
        if ticket and ticket.status == QueueTicket.Status.CALLED:
            seated_ticket = QueueTicket.objects.select_for_update().filter(pk=ticket.pk, status=QueueTicket.Status.CALLED).first()
            if seated_ticket and seated_ticket.table_id:
                table = Table.objects.select_for_update().filter(pk=seated_ticket.table_id).first()
                ticket = seated_ticket
        if table is None and order_type == Order.OrderType.DINE_IN:
            try:
                table_pk = int(table_id)
            except (TypeError, ValueError):
                messages.error(request, 'Bàn không hợp lệ.')
                return redirect('menu')
            table = Table.objects.select_for_update().filter(
                pk=table_pk,
                status__in=[Table.Status.AVAILABLE, Table.Status.OCCUPIED],
            ).first()
            if not table:
                messages.error(request, 'Bàn này không còn trống. Vui lòng chọn bàn khác hoặc lấy số xếp hàng.')
                return redirect('menu')

        if table and order_type == Order.OrderType.DINE_IN:
            used_capacity = used_bowls(table)
            cart_qty = sum(item[1] for item in resolved_items)
            if used_capacity + cart_qty > table.capacity:
                messages.error(request, f'Bàn {table.table_number} chỉ còn tối đa {max(0, table.capacity - used_capacity)} chỗ (tô). Không thể đặt tại bàn đang hết.')
                return redirect('menu')

        order = Order.objects.create(
            order_code=_generate_order_code(),
            customer=request.user if request.user.is_authenticated else None,
            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',
            order_type=order_type,
            table=table,
            queue_ticket=ticket if ticket and ticket.status == QueueTicket.Status.CALLED else None,
            payment_method=payment_method,
            payment_status=Order.PaymentStatus.PENDING,
            order_status=Order.OrderStatus.CART,
            total_amount=total,
            delivery_fee=delivery_fee,
            delivery_address=address or None,
            delivery_distance_km=delivery_distance,
            customer_location=location,
            shipping_code=f'VD-{uuid.uuid4().hex[:6].upper()}' if order_type == Order.OrderType.DELIVERY else '',
        )
        for menu_item, quantity, selected_toppings, selected_options, note, item_price in resolved_items:
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                item_price=item_price,
                note=note,
            )
            OrderItemTopping.objects.bulk_create([
                OrderItemTopping(order_item=order_item, topping=topping, quantity=quantity)
                for topping in selected_toppings
            ])
            OrderItemCustomization.objects.bulk_create([
                OrderItemCustomization(order_item=order_item, customization=option)
                for option in selected_options
            ])
        if table and table.status == Table.Status.AVAILABLE:
            Table.objects.filter(pk=table.pk, status=Table.Status.AVAILABLE).update(status=Table.Status.OCCUPIED)
        if ticket and ticket.status == QueueTicket.Status.CALLED:
            ticket.status = QueueTicket.Status.SEATED
            ticket.save(update_fields=['status'])
            request.session.pop('queue_ticket_id', None)

    messages.info(request, f'Đơn {order.order_code} đã tạo. Trạng thái: chờ thanh toán.')
    if not request.user.is_authenticated:
        guest_orders = request.session.get('guest_orders', [])
        guest_orders.append(order.pk)
        request.session['guest_orders'] = guest_orders
        request.session['latest_order_id'] = order.pk
    return redirect(f"{reverse('order_detail', args=[order.pk])}?placed=1")


def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'), pk=order_id)
    if order.customer:
        if not request.user.is_authenticated or order.customer != request.user:
            return redirect('menu')
    else:
        if order.pk not in request.session.get('guest_orders', []):
            return redirect('menu')

    return render(request, 'pho_app/customer/order_detail.html', {
        'order': order,
        'vietqr_image_url': _vietqr_image_url(order) if order.payment_method == Order.PaymentMethod.VIETQR else '',
        'grand_total': order.total_amount + order.delivery_fee,
        'clear_cart': request.GET.get('placed') == '1',
    })


@csrf_exempt
@require_POST
def vietqr_webhook(request):
    secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', '')
    if not secret:
        return HttpResponse('Payment webhook is not configured.', status=503)
    supplied_signature = request.headers.get('X-Payment-Signature', '')
    expected_signature = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        return HttpResponse('Invalid signature.', status=401)
    try:
        payload = json.loads(request.body)
        order_code = str(payload['order_code'])
        paid_amount = Decimal(str(payload['amount']))
        success = str(payload.get('status', '')).lower() in {'success', 'paid'}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return HttpResponse('Invalid payment payload.', status=400)
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(order_code=order_code).first()
        if not order or order.payment_method != Order.PaymentMethod.VIETQR:
            return HttpResponse('Order not found.', status=404)
        expected_amount = order.total_amount + order.delivery_fee
        if paid_amount != expected_amount:
            return HttpResponse('Payment amount mismatch.', status=400)
        if order.payment_status == Order.PaymentStatus.PAID:
            return JsonResponse({'ok': True, 'duplicate': True})
        if not success:
            order.payment_status = Order.PaymentStatus.FAILED
            order.order_status = Order.OrderStatus.CANCELLED
        else:
            order.payment_status = Order.PaymentStatus.PAID
            order.order_status = Order.OrderStatus.PENDING_KITCHEN
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
    return JsonResponse({'ok': True})


@require_POST
def take_queue_number(request):
    if request.user.is_authenticated and not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới lấy số xếp hàng.')
        return redirect(request.user.home_url_name())

    existing = active_queue_ticket(request)
    if existing:
        messages.info(request, f'Bạn đang có số {existing.ticket_number}.')
        return redirect(request.POST.get('next') or 'menu')

    guest_name = request.POST.get('guest_name', '').strip()[:100]
    ticket = QueueTicket.objects.create(
        customer=request.user if request.user.is_authenticated else None,
        guest_name='' if request.user.is_authenticated else guest_name,
        ticket_number=f'TMP-{uuid.uuid4().hex[:12]}',
    )
    ticket.ticket_number = f'P-{ticket.pk:03d}'
    ticket.save(update_fields=['ticket_number'])
    request.session['queue_ticket_id'] = ticket.pk
    messages.success(request, f'Đã lấy số {ticket.ticket_number}. Bạn có thể xem menu và chọn món trước, chưa cần thanh toán.')
    return redirect('menu')


def queue_status(request):
    ticket = active_queue_ticket(request)
    if not ticket:
        return JsonResponse({'active': False, 'tables_full': tables_are_full()})
    return JsonResponse({
        'active': True,
        'ticket': ticket.ticket_number,
        'status': ticket.status,
        'table': ticket.table.table_number if ticket.table_id else None,
        'tables_full': tables_are_full(),
    })


def delivery_fee_quote(request):
    coords = parse_coords(request.GET.get('lat'), request.GET.get('lng'))
    if not coords:
        fee, distance, ok = compute_delivery_fee()
        return JsonResponse({'ok': True, 'fee': int(fee), 'distance_km': None, 'fallback': True})
    fee, distance, ok = compute_delivery_fee(coords[0], coords[1])
    if not ok:
        return JsonResponse({
            'ok': False,
            'distance_km': float(distance) if distance is not None else None,
            'max_km': getattr(settings, 'DELIVERY_MAX_KM', 10),
            'message': 'Ngoài phạm vi giao hàng.',
        })
    return JsonResponse({
        'ok': True,
        'fee': int(fee),
        'distance_km': float(distance) if distance is not None else None,
        'fallback': False,
    })


@staff_required
def staff_home(request):
    cash_orders = Order.objects.filter(
        payment_method=Order.PaymentMethod.CASH,
        payment_status=Order.PaymentStatus.PENDING,
    ).exclude(order_status=Order.OrderStatus.CANCELLED).select_related('customer', 'table').prefetch_related('items__menu_item')

    waiting_tickets = QueueTicket.objects.filter(status=QueueTicket.Status.WAITING).select_related('customer')
    delivery_ready = Order.objects.filter(
        order_type=Order.OrderType.DELIVERY,
        order_status=Order.OrderStatus.READY,
    ).select_related('customer')
    delivery_in_transit = Order.objects.filter(
        order_type=Order.OrderType.DELIVERY,
        order_status=Order.OrderStatus.DELIVERING,
    ).select_related('customer')
    serving_ready = Order.objects.filter(
        order_type=Order.OrderType.DINE_IN,
        order_status=Order.OrderStatus.READY,
    ).select_related('customer', 'table')

    return render(request, 'pho_app/staff/dashboard.html', {
        'cash_orders': cash_orders,
        'waiting_tickets': waiting_tickets,
        'delivery_ready': delivery_ready,
        'delivery_in_transit': delivery_in_transit,
        'serving_ready': serving_ready,
        'tables': natural_sort_table(Table.objects.all()),
        'available_tables': natural_sort_table(Table.objects.filter(status=Table.Status.AVAILABLE)),
    })


@staff_required
@require_POST
def confirm_cash_payment(request, order_id):
    _perform_order_action(request, order_id, 'confirm_cash')
    return redirect('staff_home')


@staff_required
@require_POST
def call_next_queue(request):
    with transaction.atomic():
        table = Table.objects.select_for_update().filter(
            pk=request.POST.get('table_id'), status=Table.Status.AVAILABLE,
        ).first()
        if not table:
            messages.error(request, 'Chọn một bàn đang trống trước khi gọi khách.')
            return redirect('staff_home')
        ticket = QueueTicket.objects.select_for_update().filter(
            status=QueueTicket.Status.WAITING,
        ).order_by('created_at', 'pk').first()
        if not ticket:
            messages.info(request, 'Không còn khách đang xếp hàng.')
            return redirect('staff_home')
        ticket.status = QueueTicket.Status.CALLED
        ticket.table = table
        ticket.save(update_fields=['status', 'table'])
        table.status = Table.Status.OCCUPIED
        table.save(update_fields=['status'])
    messages.success(request, f'Đã gọi số {ticket.ticket_number}.')
    return redirect('staff_home')


@staff_required
@require_POST
def handover_delivery(request, order_id):
    _perform_order_action(request, order_id, 'handover_delivery')
    return redirect('staff_home')


@staff_required
@require_POST
def complete_delivery(request, order_id):
    _perform_order_action(request, order_id, 'complete_delivery')
    return redirect('staff_home')


@staff_required
@require_POST
def complete_dine_in(request, order_id):
    _perform_order_action(request, order_id, 'complete_dine_in')
    return redirect('staff_home')


@staff_required
@require_POST
@transaction.atomic
def free_table(request, table_id):
    table = get_object_or_404(Table.objects.select_for_update(), pk=table_id, status__in=[Table.Status.CLEANING, Table.Status.OCCUPIED])
    table.status = Table.Status.AVAILABLE
    table.save(update_fields=['status'])
    Order.objects.filter(table=table, is_cleared=False).update(is_cleared=True)
    messages.success(request, f'Bàn {table.table_number} đã dọn xong và sẵn sàng đón khách.')
    return redirect('staff_home')


@kitchen_required
def kitchen_home(request):
    orders = Order.objects.filter(
        payment_status=Order.PaymentStatus.PAID,
        order_status__in=[Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING],
    ).select_related('customer', 'table').prefetch_related(
        'items__menu_item', 'items__customizations__customization', 'items__toppings__topping',
    )
    return render(request, 'pho_app/kitchen/dashboard.html', {'orders': orders})


@kitchen_required
@require_POST
def kitchen_start(request, order_id):
    _perform_order_action(request, order_id, 'start_cooking')
    return redirect('kitchen_home')


@kitchen_required
@require_POST
def kitchen_complete(request, order_id):
    order = _perform_order_action(request, order_id, 'finish_cooking')
    if order and order.order_type == Order.OrderType.DELIVERY:
        messages.success(request, f'Đơn giao {order.order_code} đã xong. In 2 tem (hộp khô + nước lèo). Mã vận đơn {order.shipping_code}.')
        return redirect('delivery_labels', order_id=order.pk)
    return redirect('kitchen_home')


@kitchen_or_staff_required
def delivery_labels(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'),
        pk=order_id,
        order_type=Order.OrderType.DELIVERY,
        payment_status=Order.PaymentStatus.PAID,
        order_status__in=[Order.OrderStatus.READY, Order.OrderStatus.DELIVERING],
    )
    return render(request, 'pho_app/kitchen/delivery_labels.html', {'order': order})


@admin_required
def admin_home(request):
    paid = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)
    stats = {
        'users': User.objects.count(),
        'customers': User.objects.filter(role=User.Role.CUSTOMER).count(),
        'staff': User.objects.filter(role=User.Role.STAFF).count(),
        'kitchen': User.objects.filter(role=User.Role.KITCHEN).count(),
        'admins': User.objects.filter(role=User.Role.ADMIN).count(),
        'menu_items': MenuItem.objects.filter(is_active=True).count(),
        'orders': Order.objects.count(),
        'revenue': paid.aggregate(total=Sum('total_amount'))['total'] or 0,
        'dine_in': paid.filter(order_type=Order.OrderType.DINE_IN).count(),
        'delivery': paid.filter(order_type=Order.OrderType.DELIVERY).count(),
        'waiting': QueueTicket.objects.filter(status=QueueTicket.Status.WAITING).count(),
    }
    recent_orders = Order.objects.select_related('customer', 'table').order_by('-created_at')[:8]
    today = timezone.localdate()
    first_day = today - timedelta(days=6)
    daily_revenue = {
        row['day']: row['total']
        for row in paid.filter(created_at__date__gte=first_day)
        .annotate(day=TruncDate('created_at')).values('day')
        .annotate(total=Sum('total_amount'))
    }
    revenue_chart = [
        {'label': (first_day + timedelta(days=index)).strftime('%d/%m'),
         'total': int(daily_revenue.get(first_day + timedelta(days=index), 0))}
        for index in range(7)
    ]
    paid_count = stats['dine_in'] + stats['delivery']
    return render(request, 'pho_app/admin/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
        'revenue_chart': revenue_chart,
        'weekly_revenue': sum(day['total'] for day in revenue_chart),
        'dine_in_percent': round(stats['dine_in'] * 100 / paid_count) if paid_count else 0,
        'waiting_tickets': QueueTicket.objects.filter(status=QueueTicket.Status.WAITING).select_related('customer')[:5],
        'door_qr_url': request.build_absolute_uri('/thuc-don/?door=1'),
    })


@admin_required
def admin_users(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('-date_joined')
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(full_name__icontains=q) | Q(phone_number__icontains=q)
        )
    return render(request, 'pho_app/admin/users.html', {
        'users': users,
        'q': q,
        'role_choices': User.Role.choices,
    })


@admin_required
@require_POST
def admin_update_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    form = UserRoleForm(request.POST, instance=target)
    if not form.is_valid():
        messages.error(request, 'Không cập nhật được vai trò.')
        return redirect('admin_users')

    new_role = form.cleaned_data['role']
    if target == request.user and (new_role != User.Role.ADMIN or not form.cleaned_data['is_active']):
        messages.error(request, 'Bạn không thể tự gỡ quyền quản lý hoặc khóa tài khoản của chính mình.')
        return redirect('admin_users')

    admin_count = User.objects.filter(role=User.Role.ADMIN).count()
    if target.role == User.Role.ADMIN and new_role != User.Role.ADMIN and admin_count <= 1:
        messages.error(request, 'Phải còn ít nhất một tài khoản quản lý.')
        return redirect('admin_users')

    form.save()
    messages.success(request, f'Đã cập nhật vai trò của {target.username} thành {target.get_role_display()}.')
    return redirect('admin_users')


@admin_required
def admin_menu_list(request):
    items = list(MenuItem.objects.filter(is_active=True).order_by('-category', 'name'))
    toppings = list(Topping.objects.filter(is_active=True).order_by('name'))
    return render(request, 'pho_app/admin/menu_list.html', {
        'items': items, 'toppings': toppings, 'catalog_count': len(items) + len(toppings),
    })


def _redirect_to_catalog(request):
    category = request.POST.get('category', 'all')
    if category in {'pho', 'drink', 'topping'}:
        return redirect(f'{reverse("admin_menu")}?{urlencode({"category": category})}')
    return redirect('admin_menu')


@admin_required
def admin_menu_create(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã thêm món mới.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/menu_form.html', {'form': form, 'title': 'Thêm món'})


@admin_required
@transaction.atomic
def admin_menu_edit(request, item_id):
    item = get_object_or_404(MenuItem.objects.select_for_update(), pk=item_id, is_active=True)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã cập nhật món.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/menu_form.html', {'form': form, 'title': 'Sửa món', 'item': item})


@admin_required
@require_POST
@transaction.atomic
def admin_menu_delete(request, item_id):
    item = get_object_or_404(MenuItem.objects.select_for_update(), pk=item_id)
    item.is_active = False
    item.save(update_fields=['is_active'])
    messages.success(request, f'Đã xóa {item.name} khỏi thực đơn. Lịch sử đơn hàng được giữ nguyên.')
    return _redirect_to_catalog(request)


@admin_required
def admin_topping_create(request):
    form = ToppingForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã thêm topping.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/topping_form.html', {'form': form, 'title': 'Thêm topping'})


@admin_required
@transaction.atomic
def admin_topping_edit(request, topping_id):
    topping = get_object_or_404(Topping.objects.select_for_update(), pk=topping_id, is_active=True)
    form = ToppingForm(request.POST or None, request.FILES or None, instance=topping)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã cập nhật topping.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/topping_form.html', {'form': form, 'title': 'Sửa topping'})


@admin_required
@require_POST
@transaction.atomic
def admin_topping_delete(request, topping_id):
    topping = get_object_or_404(Topping.objects.select_for_update(), pk=topping_id)
    topping.is_active = False
    topping.save(update_fields=['is_active'])
    messages.success(request, f'Đã xóa {topping.name} khỏi thực đơn. Lịch sử đơn hàng được giữ nguyên.')
    return _redirect_to_catalog(request)

@require_POST
@transaction.atomic
def simulate_vietqr_payment(request, order_id):
    order = get_object_or_404(Order.objects.select_for_update(), pk=order_id, payment_method=Order.PaymentMethod.VIETQR)
    if order.customer:
        if not request.user.is_authenticated or order.customer != request.user:
            return redirect('menu')
    else:
        if order.pk not in request.session.get('guest_orders', []):
            return redirect('menu')
    if order.payment_status == Order.PaymentStatus.PENDING:
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
        messages.success(request, 'Đã mô phỏng thanh toán thành công! Đơn đã chuyển xuống bếp.')
    return redirect('order_detail', order_id=order.pk)

@staff_required
@require_POST
def cancel_cash_order(request, order_id):
    _perform_order_action(request, order_id, 'cancel_cash')
    return redirect('staff_home')

def _generate_table_qr(request, table):
    # Dùng API qrserver.com để tạo mã QR
    from urllib.parse import urlencode
    domain = request.build_absolute_uri('/')[:-1] # Bỏ dấu / ở cuối
    menu_url = f"{domain}/thuc-don/?table={table.id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={menu_url}"
    return qr_url

@admin_required
def admin_table_list(request):

    tables = natural_sort_table(Table.objects.all())
    return render(request, 'pho_app/admin/table_list.html', {'tables': tables})

@admin_required
def admin_table_create(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number', '').strip()
        capacity = int(request.POST.get('capacity', 4))
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exists():
                messages.error(request, f'Lỗi: Tên bàn "{table_number}" đã tồn tại! Vui lòng chọn tên khác.')
            else:
                table = Table.objects.create(table_number=table_number, capacity=capacity, status=Table.Status.AVAILABLE)
                table.qr_code_url = _generate_table_qr(request, table)
                table.save(update_fields=['qr_code_url'])
                messages.success(request, 'Đã thêm bàn mới thành công.')
                return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html')

@admin_required
def admin_table_edit(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    if request.method == 'POST':
        table_number = request.POST.get('table_number', '').strip()
        capacity = int(request.POST.get('capacity', 4))
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exclude(pk=table.pk).exists():
                messages.error(request, f'Lỗi: Tên bàn "{table_number}" đã tồn tại ở bàn khác!')
            else:
                table.table_number = table_number
                table.capacity = capacity
                table.qr_code_url = _generate_table_qr(request, table)
                table.save()
                messages.success(request, 'Đã cập nhật bàn thành công.')
                return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html', {'table': table})

@admin_required
@require_POST
def admin_table_delete(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    table.delete()
    messages.success(request, 'Đã xóa bàn.')
    return redirect('admin_table_list')


# ==========================================
# REVIEWS - ĐÁNH GIÁ KHÁCH HÀNG
# ==========================================
@login_required
def reviews_list(request):
    if not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới xem danh sách đánh giá.')
        return redirect(request.user.home_url_name())
    
    reviews = Review.objects.filter(customer=request.user).select_related('menu_item', 'order').order_by('-created_at')
    
    # Phân trang - 10 đánh giá mỗi trang
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'pho_app/customer/reviews.html', {
        'page_obj': page_obj,
        'paginator': paginator,
    })


@login_required
def review_form(request):
    if not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới được đánh giá.')
        return redirect(request.user.home_url_name())
    
    # Lấy menu items và recent orders cho dropdown
    menu_items = MenuItem.objects.all().order_by('name')
    recent_orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:10]
    
    return render(request, 'pho_app/customer/review_form.html', {
        'menu_items': menu_items,
        'recent_orders': recent_orders,
    })


@login_required
def review_list_all(request):
    # Hiển thị tất cả đánh giá cho admin
    if not request.user.is_admin_role():
        messages.error(request, 'Chỉ quản lý mới xem tất cả đánh giá.')
        return redirect(request.user.home_url_name())
    
    reviews = Review.objects.select_related('customer', 'menu_item', 'order').order_by('-created_at')
    
    # Tính trung bình đánh giá
    avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'pho_app/admin/reviews.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'avg_rating': round(avg_rating, 1),
    })


@login_required
@require_POST
def submit_review(request):
    if not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới được đánh giá.')
        return redirect(request.user.home_url_name())
    
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()[:500]
    menu_item_id = request.POST.get('menu_item_id')
    order_id = request.POST.get('order_id')
    
    if not rating or not rating.isdigit() or not 1 <= int(rating) <= 5:
        messages.error(request, 'Vui lòng chọn đánh giá từ 1 đến 5 sao.')
        return redirect('reviews_list')
    
    try:
        menu_item = MenuItem.objects.get(pk=menu_item_id) if menu_item_id else None
        order = Order.objects.get(pk=order_id, customer=request.user) if order_id else None
    except (MenuItem.DoesNotExist, Order.DoesNotExist):
        messages.error(request, 'Món ăn hoặc đơn hàng không hợp lệ.')
        return redirect('reviews_list')
    
    Review.objects.create(
        customer=request.user,
        menu_item=menu_item,
        order=order,
        rating=int(rating),
        comment=comment,
    )
    
    messages.success(request, 'Cảm ơn bạn đã đánh giá!')
    return redirect('reviews_list')
