import hashlib
import hmac
import json
import re
import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Avg, Count, F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    IngredientForm, IngredientImportForm, MenuItemForm, OrderFilterForm, RecipeForm,
    RegisterForm, StyledAuthForm, TableForm, ToppingForm, UserRoleForm,
)
from .models import (
    CustomizationOption,
    Ingredient,
    InventoryTransaction,
    MenuItem,
    Order,
    OrderItem,
    OrderItemCustomization,
    OrderItemTopping,
    QueueTicket,
    Recipe,
    Review,
    Table,
    Topping,
    User,
)
from .permissions import admin_required, kitchen_or_staff_required, kitchen_required, staff_required
from .domain import serialized, BusinessError
from .services import (
    InsufficientStock,
    InvalidOrderTransition,
    ORDER_ACTION_LABELS,
    active_queue_ticket,
    apply_order_action,
    available_order_actions,
    catalog_stock_limits,
    compute_delivery_fee,
    customer_point,
    ensure_inventory_available,
    inventory_deductions,
    order_inventory_deductions,
    parse_coords,
    tables_are_full,
    tables_with_capacity,
    used_bowls,
)


def _perform_order_action(request, order_id, action):
    try:
        if action == 'confirm_cash':
            order = Order.objects.get(pk=order_id)
            if action not in available_order_actions(order):
                raise InvalidOrderTransition('Đơn không còn chờ xác nhận tiền mặt.')
            from .payments import receive_payment
            from .domain import audit
            receipt, _ = receive_payment(order.pk, order.amount_due, 'CASH', f'cash-order:{order.pk}')
            audit(request.user, 'CASH_RECEIVED', receipt)
            if not receipt.allocated:
                messages.error(request, f'Đã lưu phiếu thu, cần đối soát: {receipt.note}')
                return None
            order.refresh_from_db()
        else:
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
        grand_total=Coalesce('payable_amount', F('total_amount') + F('delivery_fee')),
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
        'grand_total': order.amount_due,
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
    bank = getattr(settings, 'VIETQR_BANK_ID', '')
    account = getattr(settings, 'VIETQR_ACCOUNT_NO', '')
    account_name = getattr(settings, 'VIETQR_ACCOUNT_NAME', '')
    if not bank or not account or order.amount_due <= 0:
        return ''
    query = urlencode({
        'amount': int(order.amount_due),
        'addInfo': order.order_code,
        'accountName': account_name,
    })
    return f'https://img.vietqr.io/image/{bank}-{account}-compact2.png?{query}'



def django_admin_disabled(request):
    raise Http404('Trang quản trị Django đã được tắt. Vui lòng dùng trang Quản lý của hệ thống.')


def home(request):
    if request.user.is_authenticated and not request.user.is_customer():
        return redirect(request.user.home_url_name())
    return render(request, 'pho_app/customer/home.html', {
        'featured_items': MenuItem.objects.filter(
            is_active=True,
            category=MenuItem.Category.PHO,
        ).order_by('id')[:3],
    })


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated and request.method == 'GET' and not request.GET.get('switch'):
        return redirect(request.user.home_url_name())
    form = StyledAuthForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from .accounts import remember_login
        remember_login(request, form.get_user())
        messages.success(request, f'Xin chào {request.user.display_name}!')
        return redirect(request.user.home_url_name())
    return render(request, 'pho_app/auth/login.html', {'form': form})


@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated and request.method == 'GET' and not request.GET.get('switch'):
        return redirect(request.user.home_url_name())
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        from .accounts import remember_login
        remember_login(request, user)
        messages.success(request, 'Đăng ký thành công. Tài khoản của bạn là khách hàng.')
        return redirect('menu')
    return render(request, 'pho_app/auth/register.html', {'form': form})


@require_POST
def logout_view(request):
    from .accounts import logout_current
    logout_current(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')


@ensure_csrf_cookie
def menu_view(request):
    from .stock import expire_orders
    expire_orders()
    if request.user.is_authenticated and request.user.is_customer():
        from .loyalty import evaluateAndUpgradeTier
        evaluateAndUpgradeTier(request.user.pk)
    selected_table = request.GET.get('table', '')
    is_door = request.GET.get('door') == '1'
    items = list(MenuItem.objects.filter(is_active=True))
    stock_limits = catalog_stock_limits(items)
    menu_payload = [
        {
            'id': item.id,
            'name': item.name,
            'category': item.category.lower(),
            'price': int(item.base_price),
            'desc': 'Chọn món và thanh toán VietQR hoặc tiền mặt.',
            'image': item.image_primary.url if item.image_primary else '',
            'is_available': stock_limits[item.pk] > 0,
            'max_quantity': stock_limits[item.pk],
        }
        for item in items
    ]
    options = list(CustomizationOption.objects.all().order_by('category', 'id').values('id', 'category', 'name'))
    toppings = [{
        'id': topping.pk, 'name': topping.name, 'price': topping.price, 'category': topping.category.lower(),
        'applies_to_all': topping.applies_to_all,
        'allowed_menu_items': [item.pk for item in topping.allowed_menu_items.all()],
    } for topping in Topping.objects.filter(is_active=True).prefetch_related('allowed_menu_items').order_by('name')]
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



def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'), pk=order_id)
    can_view = False
    if request.user.is_authenticated and (request.user.is_staff_role() or request.user.is_admin_role()):
        can_view = True
    elif order.customer and request.user.is_authenticated and order.customer == request.user:
        can_view = True
    elif order.customer_id is None and order.pk in request.session.get('guest_orders', []):
        can_view = True
    elif request.user.is_authenticated and request.user.is_kitchen():
        can_view = (
            order.payment_status == Order.PaymentStatus.PAID
            and order.order_status in {
                Order.OrderStatus.PENDING_KITCHEN,
                Order.OrderStatus.COOKING,
                Order.OrderStatus.READY,
            }
        )
    if not can_view:
        return redirect('menu')

    inventory_error = ''
    if order.payment_status == Order.PaymentStatus.PENDING and order.order_status != Order.OrderStatus.CANCELLED:
        try:
            if order.expires_at and order.expires_at <= timezone.now():
                raise InvalidOrderTransition('Đơn đã hết thời gian giữ món và ưu đãi. Vui lòng đặt lại đơn.')
            if order.benefits_state == 'LEGACY':
                ensure_inventory_available(order_inventory_deductions(order))
        except InvalidOrderTransition as exc:
            inventory_error = str(exc)

    awaiting_qr_payment = (
        order.payment_method == Order.PaymentMethod.VIETQR
        and order.payment_status == Order.PaymentStatus.PENDING
        and order.order_status == Order.OrderStatus.CART
        and not inventory_error
    )
    vietqr_image_url = _vietqr_image_url(order) if awaiting_qr_payment else ''
    payment_qr_is_demo = bool(
        settings.DEBUG and awaiting_qr_payment and not vietqr_image_url and order.amount_due > 0
    )
    if payment_qr_is_demo:
        # A demo QR contains order information only, never a bank transfer payload.
        query = urlencode({
            'size': '260x260',
            'data': json.dumps({
                'mode': 'DEMO', 'order_code': order.order_code,
                'amount': int(order.amount_due), 'currency': 'VND',
            }, separators=(',', ':')),
        })
        vietqr_image_url = f'https://api.qrserver.com/v1/create-qr-code/?{query}'
    can_simulate_payment = settings.DEBUG and awaiting_qr_payment and (
        (request.user.is_authenticated and order.customer_id == request.user.pk)
        or (order.customer_id is None and order.pk in request.session.get('guest_orders', []))
    )

    return render(request, 'pho_app/customer/order_detail.html', {
        'order': order,
        'vietqr_image_url': vietqr_image_url,
        'payment_qr_is_demo': payment_qr_is_demo,
        'can_simulate_payment': can_simulate_payment,
        'inventory_error': inventory_error,
        'grand_total': order.amount_due,
        'clear_cart': request.GET.get('placed') == '1' and can_view,
    })


@csrf_exempt
@require_POST
def vietqr_webhook(request):
    secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', '')
    if not secret:
        return HttpResponse('Payment webhook is not configured.', status=503)
    signature = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(request.headers.get('X-Payment-Signature', ''), signature):
        return HttpResponse('Invalid signature.', status=401)
    try:
        payload = json.loads(request.body)
        if str(payload.get('status', '')).lower() not in {'success', 'paid'}:
            # A payment failure notification is not proof that no transfer can arrive.
            return JsonResponse({'ok': True, 'settled': False})
        external_id = str(payload.get('transaction_id', '')).strip()
        if not external_id:
            return JsonResponse({'ok': False, 'requires_reconciliation': True,
                'error': 'Cần transaction_id từ ngân hàng; không dùng mã đơn thay mã giao dịch.'}, status=400)
        order = Order.objects.filter(order_code=payload['order_code'], payment_method='VIETQR').first()
        if not order:
            return HttpResponse('Order not found.', status=404)
        from .payments import receive_payment
        receipt, duplicate = receive_payment(order.pk, payload['amount'], 'BANK', external_id)
        return JsonResponse({'ok': receipt.allocated, 'duplicate': duplicate,
            'requires_reconciliation': receipt.requires_reconciliation, 'detail': receipt.note},
            status=202 if receipt.requires_reconciliation else 200)
    except (BusinessError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@require_POST
def take_queue_number(request):
    if request.user.is_authenticated and not request.user.is_customer():
        messages.error(request, 'Tài khoản nhân viên không thể lấy số xếp hàng khách hàng.')
        return redirect(request.user.home_url_name())

    existing = active_queue_ticket(request)
    if existing:
        messages.info(request, f'Bạn đang có số {existing.ticket_number}.')
        return redirect(request.POST.get('next') or 'menu')

    customer_user = request.user if (request.user.is_authenticated and request.user.is_customer()) else None
    guest_name = request.POST.get('guest_name', '').strip()[:100]
    if not customer_user and not guest_name:
        guest_name = request.user.display_name if request.user.is_authenticated else 'Khách'
    try:
        people_count = max(1, min(20, int(request.POST.get('people_count', 1))))
    except (TypeError, ValueError):
        people_count = 1

    ticket = QueueTicket.objects.create(
        customer=customer_user,
        guest_name='' if customer_user else guest_name,
        ticket_number=f'TMP-{uuid.uuid4().hex[:12]}',
        people_count=people_count,
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


@require_GET
def delivery_fee_quote(request):
    coords = parse_coords(request.GET.get('lat'), request.GET.get('lng'))
    if not coords:
        return JsonResponse({'ok': False, 'error': 'Chọn vị trí nhận món bằng GPS, bản đồ hoặc nhập đủ tọa độ hợp lệ.', 'fallback': False}, status=400)
    fee, distance, ok = compute_delivery_fee(coords[0], coords[1])
    if not ok:
        return JsonResponse({
            'ok': False,
            'distance_km': float(distance) if distance is not None else None,
            'max_km': getattr(settings, 'DELIVERY_MAX_KM', 10),
            'message': 'Ngoài phạm vi giao hàng.',
            'error': 'Địa chỉ nằm ngoài phạm vi giao hàng. Vui lòng chọn địa chỉ khác.',
        }, status=400)
    return JsonResponse({
        'ok': True,
        'fee': int(fee),
        'distance_km': float(distance) if distance is not None else None,
        'fallback': False,
        'max_km': settings.DELIVERY_MAX_KM,
        'latitude': coords[0], 'longitude': coords[1],
    })


@staff_required
def staff_home(request):
    cash_orders = list(Order.objects.filter(
        payment_method=Order.PaymentMethod.CASH,
        payment_status=Order.PaymentStatus.PENDING,
    ).exclude(order_status=Order.OrderStatus.CANCELLED).select_related('customer', 'table').prefetch_related('items__menu_item'))
    paid_unassigned_orders = list(Order.objects.filter(
        order_type=Order.OrderType.DINE_IN,
        payment_status=Order.PaymentStatus.PAID,
        order_status__in=[Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.READY],
        table__isnull=True,
    ).select_related('customer').prefetch_related('items__menu_item'))

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

    tables = natural_sort_table(Table.objects.all())
    active_dining_orders = Order.objects.filter(
        order_type=Order.OrderType.DINE_IN,
        is_cleared=False,
        table__isnull=False,
    ).exclude(order_status=Order.OrderStatus.CANCELLED).select_related('customer', 'table').prefetch_related('items__menu_item')

    active_orders_by_table = {}
    for o in active_dining_orders:
        o.pho_count = sum(i.quantity for i in o.items.all() if i.menu_item.category == MenuItem.Category.PHO)
        active_orders_by_table.setdefault(o.table_id, []).append(o)

    for t in tables:
        t.active_orders = active_orders_by_table.get(t.id, [])
        t.current_pho_bowls = sum(o.pho_count for o in t.active_orders)
        t.remaining_capacity = max(0, t.capacity - t.current_pho_bowls)
    occupied_tables = [t for t in tables if t.active_orders]

    called_table_ids = set(QueueTicket.objects.filter(
        status=QueueTicket.Status.CALLED,
        table__isnull=False,
    ).values_list('table_id', flat=True))
    assignable_tables = [
        table for table in tables
        if table.pk not in called_table_ids
        and (
            table.status == Table.Status.AVAILABLE
            or (table.status == Table.Status.OCCUPIED and table.active_orders)
        )
    ]
    for order in [*cash_orders, *paid_unassigned_orders]:
        order.pho_count = sum(
            item.quantity for item in order.items.all()
            if item.menu_item.category == MenuItem.Category.PHO
        )
        order.suitable_tables = [
            table for table in assignable_tables
            if table.remaining_capacity >= order.pho_count
        ]

    return render(request, 'pho_app/staff/dashboard.html', {
        'cash_orders': cash_orders,
        'paid_unassigned_orders': paid_unassigned_orders,
        'waiting_tickets': waiting_tickets,
        'delivery_ready': delivery_ready,
        'delivery_in_transit': delivery_in_transit,
        'serving_ready': serving_ready,
        'tables': tables,
        'occupied_tables': occupied_tables,
        'available_tables': [table for table in tables if table.status == Table.Status.AVAILABLE],
    })


@staff_required
def staff_table_map(request):
    return redirect('table_map')


@staff_required
def table_map(request):
    tables = natural_sort_table(Table.objects.all())
    active_orders = Order.objects.filter(
        order_type=Order.OrderType.DINE_IN,
        is_cleared=False,
    ).exclude(order_status=Order.OrderStatus.CANCELLED).select_related(
        'customer', 'table',
    ).prefetch_related('items__menu_item')
    orders_by_table = {}
    for order in active_orders:
        order.pho_count = sum(
            item.quantity for item in order.items.all()
            if item.menu_item.category == MenuItem.Category.PHO
        )
        if order.table_id:
            orders_by_table.setdefault(order.table_id, []).append(order)

    called_tickets = {
        ticket.table_id: ticket
        for ticket in QueueTicket.objects.filter(status=QueueTicket.Status.CALLED).select_related('customer')
    }
    for table in tables:
        table.active_orders = orders_by_table.get(table.pk, [])
        table.current_pho_bowls = sum(order.pho_count for order in table.active_orders)
        table.remaining_capacity = max(0, table.capacity - table.current_pho_bowls)
        table.called_ticket = called_tickets.get(table.pk)
        table.qr_image_url = _generate_table_qr(request, table)
        table.can_clear = not table.called_ticket and all(
            order.order_status in (Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED)
            for order in table.active_orders
        )

    return render(request, 'pho_app/table_map.html', {
        'tables': tables,
        'available_count': sum(table.status == Table.Status.AVAILABLE for table in tables),
        'occupied_count': sum(table.status == Table.Status.OCCUPIED for table in tables),
        'cleaning_count': sum(table.status == Table.Status.CLEANING for table in tables),
    })


@staff_required
@require_POST
@transaction.atomic
def confirm_cash_payment(request, order_id):
    table_id = request.POST.get('table_id')
    try:
        posted_table_id = int(table_id) if table_id else None
    except (TypeError, ValueError):
        messages.error(request, 'Mã bàn không hợp lệ; chưa xác nhận thanh toán.')
        return redirect('staff_home')

    snapshot = get_object_or_404(Order.objects.only('table_id'), pk=order_id)
    table_id_to_lock = posted_table_id or snapshot.table_id
    table = None
    if table_id_to_lock:
        table = Table.objects.select_for_update().filter(pk=table_id_to_lock).first()

    order = get_object_or_404(Order.objects.select_for_update().prefetch_related('items__menu_item'), pk=order_id)
    if (
        order.payment_method != Order.PaymentMethod.CASH
        or order.payment_status != Order.PaymentStatus.PENDING
        or order.order_status != Order.OrderStatus.CART
    ):
        messages.error(request, 'Đơn không còn ở trạng thái chờ xác nhận tiền mặt.')
        return redirect('staff_home')
    if order.order_type != Order.OrderType.DINE_IN:
        messages.error(request, 'Đơn này không thuộc luồng phục vụ tại bàn.')
        return redirect('staff_home')
    if order.table_id and posted_table_id and order.table_id != posted_table_id:
        messages.error(request, 'Đơn đã được xếp vào bàn khác; chưa xác nhận thanh toán.')
        return redirect('staff_home')
    if not order.table_id and not posted_table_id:
        messages.error(request, 'Hãy chọn bàn còn đủ sức chứa trước khi xác nhận thanh toán và chuyển bếp.')
        return redirect('staff_home')
    if not table or table.status not in (Table.Status.AVAILABLE, Table.Status.OCCUPIED):
        messages.error(request, 'Bàn không còn khả dụng; chưa xác nhận thanh toán.')
        return redirect('staff_home')
    if not order.table_id and table.status == Table.Status.OCCUPIED and (
        not Order.objects.filter(table=table, is_cleared=False).exclude(
            order_status=Order.OrderStatus.CANCELLED,
        ).exists()
        or QueueTicket.objects.filter(table=table, status=QueueTicket.Status.CALLED).exists()
    ):
        messages.error(request, 'Bàn này đã được dành cho khách khác; vui lòng chọn bàn đang trống.')
        return redirect('staff_home')
    if QueueTicket.objects.select_for_update().filter(
        table=table,
        status=QueueTicket.Status.CALLED,
    ).exists():
        messages.error(request, 'Bàn này đang được giữ cho khách đã gọi từ hàng đợi.')
        return redirect('staff_home')

    pho_count = sum(
        item.quantity for item in order.items.all()
        if item.menu_item.category == MenuItem.Category.PHO
    )
    already_assigned = order.table_id == table.pk
    occupied_bowls = used_bowls(table)
    available_bowls = table.capacity - occupied_bowls + (pho_count if already_assigned else 0)
    if available_bowls < pho_count:
        messages.error(request, f'Bàn {table.table_number} không đủ chỗ cho {pho_count} tô phở; còn {max(0, available_bowls)} chỗ.')
        return redirect('staff_home')

    paid_order = _perform_order_action(request, order_id, 'confirm_cash')
    if not paid_order:
        return redirect('staff_home')
    if not paid_order.table_id:
        paid_order.table = table
        paid_order.save(update_fields=['table', 'updated_at'])
    if table.status == Table.Status.AVAILABLE:
        table.status = Table.Status.OCCUPIED
        table.save(update_fields=['status'])
    return redirect('staff_home')


@staff_required
@require_POST
@transaction.atomic
def assign_order_table(request, order_id):
    table_id = request.POST.get('table_id')
    try:
        table_pk = int(table_id)
    except (TypeError, ValueError):
        messages.error(request, 'Bàn không hợp lệ.')
        return redirect('staff_home')

    table = Table.objects.select_for_update().filter(
        pk=table_pk,
        status__in=[Table.Status.AVAILABLE, Table.Status.OCCUPIED],
    ).first()
    if not table:
        messages.error(request, 'Bàn không tồn tại hoặc hiện không nhận khách.')
        return redirect('staff_home')
    order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
    if (
        order.order_type != Order.OrderType.DINE_IN
        or order.payment_status != Order.PaymentStatus.PAID
        or order.order_status not in (Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.READY)
        or order.table_id
    ):
        messages.error(request, 'Chỉ có thể xếp bàn cho đơn tại quán đã thanh toán, chưa được xếp bàn và đang chờ bếp hoặc phục vụ.')
        return redirect('staff_home')
    if QueueTicket.objects.select_for_update().filter(
        table=table,
        status=QueueTicket.Status.CALLED,
    ).exists():
        messages.error(request, 'Bàn này đang được giữ cho khách đã gọi từ hàng đợi.')
        return redirect('staff_home')
    if table.status == Table.Status.OCCUPIED and not Order.objects.filter(
        table=table,
        is_cleared=False,
    ).exclude(order_status=Order.OrderStatus.CANCELLED).exists():
        messages.error(request, 'Bàn này đang được giữ cho khách khác; vui lòng chọn bàn trống.')
        return redirect('staff_home')

    used_capacity = used_bowls(table)
    order_pho_qty = sum(
        item.quantity for item in order.items.select_related('menu_item').all()
        if item.menu_item.category == MenuItem.Category.PHO
    )
    if used_capacity + order_pho_qty > table.capacity:
        messages.error(request, f'Bàn {table.table_number} không còn đủ chỗ cho đơn này.')
        return redirect('staff_home')

    order.table = table
    order.save(update_fields=['table', 'updated_at'])
    if table.status == Table.Status.AVAILABLE:
        table.status = Table.Status.OCCUPIED
        table.save(update_fields=['status'])
    messages.success(request, f'Đã điều hướng đơn {order.order_code} vào Bàn {table.table_number}.')
    return redirect('staff_home')


@staff_required
@require_POST
def call_next_queue(request):
    with transaction.atomic():
        ticket = QueueTicket.objects.select_for_update().filter(
            status=QueueTicket.Status.WAITING,
        ).order_by('created_at', 'pk').first()
        if not ticket:
            messages.info(request, 'Không còn khách đang xếp hàng.')
            return redirect('staff_home')
        table = Table.objects.select_for_update().filter(
            pk=request.POST.get('table_id'), status=Table.Status.AVAILABLE,
        ).first()
        if not table:
            messages.error(request, 'Chọn một bàn đang trống trước khi gọi khách.')
            return redirect('staff_home')
        if table.capacity < ticket.people_count:
            messages.error(request, f'Số {ticket.ticket_number} cần bàn ít nhất {ticket.people_count} chỗ; Bàn {table.table_number} chỉ có {table.capacity}.')
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
    destination = 'table_map' if request.POST.get('next') == reverse('table_map') else 'staff_home'
    table = get_object_or_404(Table.objects.select_for_update(), pk=table_id, status__in=[Table.Status.CLEANING, Table.Status.OCCUPIED])
    unfinished_orders = Order.objects.select_for_update().filter(
        table=table,
        is_cleared=False,
    ).exclude(order_status__in=[Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED])
    if unfinished_orders.exists():
        messages.error(request, 'Chưa thể dọn bàn vì vẫn còn đơn chưa hoàn tất.')
        return redirect(destination)
    if QueueTicket.objects.select_for_update().filter(
        table=table,
        status=QueueTicket.Status.CALLED,
    ).exists():
        messages.error(request, 'Chưa thể dọn bàn vì khách đã được gọi từ hàng đợi nhưng chưa vào bàn.')
        return redirect(destination)
    table.status = Table.Status.AVAILABLE
    table.save(update_fields=['status'])
    Order.objects.filter(table=table, is_cleared=False).update(is_cleared=True)
    messages.success(request, f'Bàn {table.table_number} đã dọn xong toàn bộ và sẵn sàng đón khách.')
    return redirect(destination)


@staff_required
@require_POST
@transaction.atomic
def free_order_table(request, order_id):
    order = get_object_or_404(
        Order.objects.select_for_update(),
        pk=order_id,
        is_cleared=False,
        order_type=Order.OrderType.DINE_IN,
        order_status=Order.OrderStatus.COMPLETED,
        payment_status=Order.PaymentStatus.PAID,
    )
    table = order.table
    order.is_cleared = True
    order.save(update_fields=['is_cleared', 'updated_at'])

    pho_qty = sum(item.quantity for item in order.items.all() if item.menu_item.category == MenuItem.Category.PHO)

    if table:
        has_other_active = Order.objects.filter(
            table=table,
            is_cleared=False,
        ).exclude(order_status=Order.OrderStatus.CANCELLED).exists()

        if not has_other_active:
            table.status = Table.Status.AVAILABLE
            table.save(update_fields=['status'])
            messages.success(request, f'Khách đơn {order.order_code} đã ăn xong. Bàn {table.table_number} hiện đã trống hoàn toàn.')
        else:
            remaining = max(0, table.capacity - used_bowls(table))
            messages.success(request, f'Khách đơn {order.order_code} đã ăn xong (giải phóng {pho_qty} tô). Bàn {table.table_number} hiện còn trống {remaining}/{table.capacity} chỗ (tô).')
    else:
        messages.success(request, f'Đã giải phóng đơn {order.order_code}.')

    return redirect('table_map' if request.POST.get('next') == reverse('table_map') else 'staff_home')


@kitchen_required
def kitchen_home(request):
    orders = Order.objects.filter(
        payment_status=Order.PaymentStatus.PAID,
        order_status__in=[Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING],
    ).filter(
        Q(order_type=Order.OrderType.DELIVERY) | Q(table__isnull=False),
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
    paid = Order.objects.filter(payment_status=Order.PaymentStatus.PAID).annotate(
        effective_total=Coalesce('payable_amount', F('total_amount') + F('delivery_fee')))
    stats = {
        'users': User.objects.count(),
        'customers': User.objects.filter(role=User.Role.CUSTOMER).count(),
        'staff': User.objects.filter(role=User.Role.STAFF).count(),
        'kitchen': User.objects.filter(role=User.Role.KITCHEN).count(),
        'admins': User.objects.filter(role=User.Role.ADMIN).count(),
        'menu_items': MenuItem.objects.filter(is_active=True).count(),
        'orders': Order.objects.count(),
        'revenue': paid.aggregate(total=Sum('effective_total'))['total'] or 0,
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
        .annotate(total=Sum('effective_total'))
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
    if not settings.DEBUG:
        raise Http404('Payment simulation is available only in development.')
    order = get_object_or_404(Order.objects.select_for_update(), pk=order_id, payment_method=Order.PaymentMethod.VIETQR)
    can_pay = False
    if order.customer and request.user.is_authenticated and order.customer == request.user:
        can_pay = True
    elif order.customer_id is None and order.pk in request.session.get('guest_orders', []):
        can_pay = True

    if not can_pay:
        return redirect('menu')

    if order.payment_status == Order.PaymentStatus.PENDING:
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        try:
            order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
        except InvalidOrderTransition as exc:
            messages.error(request, str(exc))
            return redirect('order_detail', order_id=order.pk)
        from .models import PaymentReceipt
        PaymentReceipt.objects.get_or_create(provider='SIMULATED', external_id=f'dev-order:{order.pk}', defaults={
            'order': order, 'amount': int(order.amount_due), 'allocated': True,
            'received_at': timezone.now(), 'note': 'Mô phỏng ở môi trường phát triển, không phải giao dịch ngân hàng.'})
        messages.success(request, 'Đã mô phỏng thanh toán thành công! Đơn đã chuyển xuống bếp.')
    return redirect('order_detail', order_id=order.pk)

@staff_required
@require_POST
def cancel_cash_order(request, order_id):
    _perform_order_action(request, order_id, 'cancel_cash')
    return redirect('staff_home')

def _generate_table_qr(request, table):
    menu_url = request.build_absolute_uri(f"{reverse('menu')}?table={table.pk}")
    return 'https://api.qrserver.com/v1/create-qr-code/?' + urlencode({'size': '500x500', 'data': menu_url})

@admin_required
def admin_table_list(request):
    return redirect('table_map')

@admin_required
def admin_table_create(request):
    form = TableForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        table = form.save(commit=False)
        with transaction.atomic():
            table.save()
            table.qr_code_url = _generate_table_qr(request, table)
            table.save(update_fields=['qr_code_url'])
        messages.success(request, 'Đã thêm bàn mới thành công.')
        return redirect('table_map')
    return render(request, 'pho_app/admin/table_form.html', {'form': form})

@admin_required
def admin_table_edit(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    form = TableForm(request.POST if request.method == 'POST' else None, instance=table)
    if request.method == 'POST' and form.is_valid():
        table.qr_code_url = _generate_table_qr(request, table)
        form.save()
        messages.success(request, 'Đã cập nhật bàn thành công.')
        return redirect('table_map')
    return render(request, 'pho_app/admin/table_form.html', {'table': table, 'form': form})

@admin_required
@require_POST
def admin_table_delete(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    try:
        table.delete()
    except ProtectedError:
        messages.error(request, 'Không thể xóa bàn đã có đơn hàng hoặc vé xếp hàng. Lịch sử bàn được giữ nguyên.')
    else:
        messages.success(request, 'Đã xóa bàn.')
    return redirect('table_map')


# ==========================================
# REVIEWS - ĐÁNH GIÁ KHÁCH HÀNG
# ==========================================
def reviews_list(request):
    reviews = Review.objects.all().select_related('customer', 'menu_item', 'order').order_by('-created_at')
    
    # Phân trang - 10 đánh giá mỗi trang
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'pho_app/customer/reviews.html', {
        'page_obj': page_obj,
        'paginator': paginator,
    })


def review_form(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Vui lòng đăng nhập để viết đánh giá.')
        return redirect('login')
    
    if not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới được đánh giá.')
        return redirect(request.user.home_url_name())
    
    # Lấy menu items và recent orders cho dropdown
    menu_items = MenuItem.objects.all().order_by('name')
    recent_orders = Order.objects.filter(customer=request.user, order_status='COMPLETED', purpose='REGULAR').order_by('-created_at')[:20]
    
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
    avg_rating = round(Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0, 1)
    
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'pho_app/admin/reviews.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'avg_rating': avg_rating,
        'avg_rating_percent': avg_rating * 20,
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
    
    if order and (order.order_status != 'COMPLETED' or order.purpose != 'REGULAR' or (menu_item and not order.items.filter(menu_item=menu_item).exists())):
        messages.error(request, 'Chỉ đánh giá món thuộc đơn mua hàng đã hoàn tất.')
        return redirect('reviews_list')
    review = Review.objects.filter(customer=request.user, menu_item=menu_item, order=order).order_by('-pk').first()
    if review:
        review.rating, review.comment, review.revision = int(rating), comment, review.revision + 1
        review.save(update_fields=['rating', 'comment', 'revision'])
    else:
        review = Review.objects.create(customer=request.user, menu_item=menu_item, order=order, rating=int(rating), comment=comment)
    from .loyalty import reward_review
    reward_review(review)
    
    messages.success(request, 'Cảm ơn bạn đã đánh giá!')
    return redirect('reviews_list')


def custom_404_view(request, exception=None):
    """Trang thông báo lỗi 404 tùy chỉnh thân thiện, đồng bộ nhận diện thương hiệu Phở Nhà."""
    return render(request, '404.html', status=404)


# ==========================================
# MODULE QUẢN LÝ TỒN KHO & ĐỊNH LƯỢNG (BOM)
# ==========================================
@admin_required
def admin_inventory(request):
    """Trang quản lý kho nguyên liệu, công thức định lượng và lịch sử biến động kho."""
    ingredients = list(Ingredient.objects.all().order_by('name'))
    from .stock import reserved_totals, available_balances
    from .models import InventoryIncident, InventoryRequirement, StockReservation
    held, available = reserved_totals(), available_balances()
    for ingredient in ingredients:
        ingredient.held_stock = held.get(ingredient.pk, 0)
        ingredient.available_stock = available.get(ingredient.pk, 0)
    recipes = Recipe.objects.select_related('menu_item', 'topping', 'ingredient').all().order_by('menu_item__name', 'topping__name')
    recent_transactions = list(InventoryTransaction.objects.select_related('ingredient', 'created_by').order_by('-created_at'))

    total_ingredients = len(ingredients)
    shared_ingredient_count = sum(ingredient.usage == Ingredient.Usage.SHARED for ingredient in ingredients)
    food_ingredient_count = sum(ingredient.usage == Ingredient.Usage.PHO for ingredient in ingredients) + shared_ingredient_count
    drink_ingredient_count = sum(ingredient.usage == Ingredient.Usage.DRINK for ingredient in ingredients) + shared_ingredient_count
    low_stock_count = Ingredient.objects.filter(current_stock__lte=F('minimum_stock')).count()
    total_recipes = recipes.count()

    menu_items = list(MenuItem.objects.filter(is_active=True).order_by('name'))
    toppings = list(Topping.objects.filter(is_active=True).prefetch_related('allowed_menu_items').order_by('name'))
    from .recipes import recipe_editor_data
    editor_data = recipe_editor_data(ingredients, menu_items, toppings, recipes)
    editor_data['user_id'] = request.user.pk

    stock_orders = list(Order.objects.filter(stock_reservation__state='CONSUMED').order_by('-created_at')[:100])
    stock_order_options = {str(order.pk): [] for order in stock_orders}
    for line in InventoryRequirement.objects.filter(reservation__order__in=stock_orders).select_related('reservation'):
        stock_order_options[str(line.reservation.order_id)].append(line.ingredient_id)

    ing_map = {i.pk: i for i in ingredients}

    def format_qty_and_servings(r):
        ing = ing_map.get(r.ingredient_id, r.ingredient)
        unit = (ing.unit or '').strip().lower()
        qty = r.quantity_required
        avail = getattr(ing, 'available_stock', ing.current_stock)
        
        if unit == 'kg' and qty < 1:
            formatted_qty = f'{int(qty * 1000)} g'
            raw_qty_note = f'{qty:g} kg'
        elif unit == 'lit' and qty < 1:
            formatted_qty = f'{int(qty * 1000)} ml'
            raw_qty_note = f'{qty:g} lít'
        else:
            formatted_qty = f'{qty:g} {ing.unit}'
            raw_qty_note = ''

        servings = int(avail / qty) if qty > 0 and avail > 0 else 0
        is_low = avail <= ing.minimum_stock
        usage_names = {'PHO': 'Món chính', 'DRINK': 'Nước uống', 'SHARED': 'Dùng chung'}
        usage_display = usage_names.get(ing.usage, ing.usage)

        return {
            'id': r.pk,
            'ingredient_id': ing.pk,
            'name': ing.name,
            'unit': ing.unit,
            'usage_display': usage_display,
            'quantity_required': qty,
            'formatted_qty': formatted_qty,
            'raw_qty_note': raw_qty_note,
            'available_stock': avail,
            'is_low_stock': is_low,
            'servings': servings,
        }

    recipe_list = list(recipes)
    product_recipes = []
    for item in menu_items:
        item_recipes = [r for r in recipe_list if r.menu_item_id == item.pk]
        target = 'DRINK' if item.category == MenuItem.Category.DRINK else 'MENU'
        display_recipes = [format_qty_and_servings(r) for r in item_recipes]
        servings_list = [d['servings'] for d in display_recipes if d['quantity_required'] > 0]
        max_servings = min(servings_list) if servings_list else None
        search_kw = ' '.join(d['name'] for d in display_recipes)
        product_recipes.append({
            'id': item.pk,
            'name': item.name,
            'kind': 'menu',
            'target': target,
            'category': item.category,
            'category_display': 'Nước uống' if item.category == MenuItem.Category.DRINK else 'Món chính',
            'inventory_mode': item.inventory_mode,
            'inventory_mode_display': 'Đóng chai / lon' if item.inventory_mode == 'DIRECT' else 'Pha chế (BOM)' if item.category == MenuItem.Category.DRINK else 'Định lượng (BOM)',
            'recipes': item_recipes,
            'display_recipes': display_recipes,
            'ingredient_count': len(item_recipes),
            'has_recipe': len(item_recipes) > 0 or item.inventory_mode == 'DIRECT',
            'max_servings': max_servings,
            'search_keywords': search_kw,
            'tone_class': 'tone-red' if target == 'MENU' else 'tone-blue',
        })
    for item in toppings:
        item_recipes = [r for r in recipe_list if r.topping_id == item.pk]
        display_recipes = [format_qty_and_servings(r) for r in item_recipes]
        servings_list = [d['servings'] for d in display_recipes if d['quantity_required'] > 0]
        max_servings = min(servings_list) if servings_list else None
        search_kw = ' '.join(d['name'] for d in display_recipes)
        product_recipes.append({
            'id': item.pk,
            'name': item.name,
            'kind': 'topping',
            'target': 'TOPPING',
            'category': item.category or 'PHO',
            'category_display': 'Topping',
            'inventory_mode': 'BOM',
            'inventory_mode_display': 'Topping (BOM)',
            'recipes': item_recipes,
            'display_recipes': display_recipes,
            'ingredient_count': len(item_recipes),
            'has_recipe': len(item_recipes) > 0,
            'max_servings': max_servings,
            'search_keywords': search_kw,
            'tone_class': 'tone-green',
        })

    recipe_filter_counts = {
        'all': len(product_recipes),
        'menu': sum(1 for p in product_recipes if p['target'] == 'MENU'),
        'drink': sum(1 for p in product_recipes if p['target'] == 'DRINK'),
        'topping': sum(1 for p in product_recipes if p['target'] == 'TOPPING'),
        'missing': sum(1 for p in product_recipes if not p['has_recipe']),
    }

    return render(request, 'pho_app/admin/inventory_list.html', {
        'ingredients': ingredients,
        'recipes': recipes,
        'product_recipes': product_recipes,
        'recipe_filter_counts': recipe_filter_counts,
        'recent_transactions': recent_transactions,
        'total_ingredients': total_ingredients,
        'food_ingredient_count': food_ingredient_count,
        'drink_ingredient_count': drink_ingredient_count,
        'shared_ingredient_count': shared_ingredient_count,
        'low_stock_count': low_stock_count,
        'total_recipes': total_recipes,
        'recipe_editor_data': editor_data,
        'menu_items': menu_items,
        'toppings': toppings,
        'stock_incidents': InventoryIncident.objects.filter(resolved=False).select_related('ingredient'),
        'stock_request_key': uuid.uuid4().hex,
        'stock_orders': stock_orders, 'stock_order_options': stock_order_options,
        'stock_holds': StockReservation.objects.filter(state='ACTIVE', expires_at__gt=timezone.now()).select_related('order').prefetch_related('lines__ingredient')[:8],
    })


@admin_required
def admin_ingredient_create(request):
    """Thêm nguyên liệu mới vào kho."""
    usage = request.GET.get('usage', Ingredient.Usage.PHO)
    if usage not in Ingredient.Usage.values:
        usage = Ingredient.Usage.PHO
    form = IngredientForm(request.POST if request.method == 'POST' else None, initial={'usage': usage})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            ingredient = form.save()
            if ingredient.current_stock > 0:
                InventoryTransaction.objects.create(
                    ingredient=ingredient,
                    transaction_type=InventoryTransaction.TransactionType.IMPORT,
                    quantity_changed=ingredient.current_stock,
                    created_by=request.user,
                )
        messages.success(request, f'Đã thêm nguyên liệu "{ingredient.name}" vào kho thành công.')
        return redirect('admin_inventory')

    return render(request, 'pho_app/admin/ingredient_form.html', {'form': form})


@admin_required
@transaction.atomic
def admin_ingredient_edit(request, ingredient_id):
    """Chỉnh sửa thông tin nguyên liệu và điều chỉnh kho."""
    ingredient = get_object_or_404(Ingredient.objects.select_for_update(), pk=ingredient_id)
    previous_stock = ingredient.current_stock
    previous_unit = ingredient.unit
    form = IngredientForm(request.POST if request.method == 'POST' else None, instance=ingredient)
    if request.method == 'POST' and form.is_valid():
        diff = form.cleaned_data['current_stock'] - previous_stock
        # A legacy negative balance can make the adjustment larger than the ledger field.
        if abs(diff) > Decimal('99999999.99'):
            form.add_error('current_stock', 'Mức điều chỉnh vượt giới hạn. Vui lòng điều chỉnh thành nhiều lần.')
            return render(request, 'pho_app/admin/ingredient_form.html', {'ingredient': ingredient, 'form': form})
        from .stock import reserved_totals
        held = reserved_totals().get(ingredient.pk, 0)
        if form.cleaned_data['unit'] != previous_unit and (ingredient.recipe_set.exists() or ingredient.inventorytransaction_set.exists()):
            form.add_error('unit', 'Nguyên liệu đã có lịch sử: cần quy đổi có kiểm toán, không chỉ đổi nhãn đơn vị.')
            return render(request, 'pho_app/admin/ingredient_form.html', {'ingredient': ingredient, 'form': form})
        ingredient = form.save()
        if ingredient.current_stock < held:
            from .models import InventoryIncident
            InventoryIncident.objects.create(ingredient=ingredient, detail=f'Kiểm kê {ingredient.current_stock}, đang giữ {held}; đã khóa nhận đơn/xuất kho cho nguyên liệu này.')
            messages.warning(request, 'Tồn thực tế thấp hơn lượng cam kết. Đã khóa nguyên liệu để xử lý chênh lệch.')
        if diff != 0:
            InventoryTransaction.objects.create(
                ingredient=ingredient,
                transaction_type=InventoryTransaction.TransactionType.ADJUST,
                quantity_changed=diff,
                created_by=request.user,
            )
        messages.success(request, f'Đã cập nhật thông tin nguyên liệu "{ingredient.name}".')
        return redirect('admin_inventory')

    return render(request, 'pho_app/admin/ingredient_form.html', {'ingredient': ingredient, 'form': form})


@admin_required
@require_POST
def admin_ingredient_delete(request, ingredient_id):
    """Xóa nguyên liệu khỏi kho."""
    ingredient = get_object_or_404(Ingredient, pk=ingredient_id)
    name = ingredient.name
    try:
        ingredient.delete()
    except ProtectedError:
        messages.error(request, f'Không thể xóa nguyên liệu "{name}" đang có định lượng hoặc lịch sử kho. Dữ liệu được giữ nguyên.')
    else:
        messages.success(request, f'Đã xóa nguyên liệu "{name}" khỏi kho.')
    return redirect('admin_inventory')


@admin_required
@require_POST
def admin_ingredient_import(request, ingredient_id):
    """Nhập thêm số lượng hàng vào kho nhanh chóng."""
    form = IngredientImportForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Số lượng nhập phải từ 0,01, tối đa 2 chữ số thập phân và trong giới hạn tồn kho.')
        return redirect('admin_inventory')

    qty = form.cleaned_data['quantity']
    with transaction.atomic():
        ingredient = get_object_or_404(Ingredient.objects.select_for_update(), pk=ingredient_id)
        from .stock import convert_stock_units
        from .domain import audit
        entered_qty = qty
        entered_unit = form.cleaned_data.get('input_unit') or ingredient.unit
        try:
            qty = convert_stock_units(qty, entered_unit, ingredient.unit)
        except BusinessError as exc:
            messages.error(request, str(exc))
            return redirect('admin_inventory')
        if ingredient.current_stock + qty < 0:
            messages.error(request, f'Tồn kho cũ đang âm {abs(ingredient.current_stock):g} {ingredient.unit}. Hãy kiểm kê và cập nhật tồn thực tế trước khi nhập thêm.')
            return redirect('admin_inventory')
        if ingredient.current_stock + qty > Decimal('99999999.99'):
            messages.error(request, 'Tổng tồn kho sau khi nhập vượt giới hạn cho phép.')
            return redirect('admin_inventory')
        ingredient.current_stock += qty
        ingredient.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            ingredient=ingredient,
            transaction_type=InventoryTransaction.TransactionType.IMPORT,
            quantity_changed=qty,
            created_by=request.user,
        )
        audit(request.user, 'STOCK_IMPORT', ingredient, input_quantity=str(entered_qty), input_unit=entered_unit,
              stock_quantity=str(qty), stock_unit=ingredient.unit)
    messages.success(request, f'Đã nhập thêm +{qty:g} {ingredient.unit} cho nguyên liệu "{ingredient.name}".')
    return redirect('admin_inventory')


@admin_required
@require_POST
def admin_recipe_create(request):
    """Thiết lập định lượng (BOM) tiêu hao cho món chính hoặc topping."""
    if 'rows' in request.POST:
        from .recipes import RecipeBatchForm, recipe_revision
        form = RecipeBatchForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=422)
        target = type(form.target).objects.select_for_update().get(pk=form.target.pk)
        if form.cleaned_data['revision'] != recipe_revision(target):
            return JsonResponse({'ok': False, 'errors': {'revision': [{'message': 'Định lượng đã được cập nhật ở trang khác. Tải lại trang trước khi lưu để tránh ghi đè.', 'code': 'conflict'}]}}, status=409)
        is_topping = isinstance(target, Topping)
        target.recipes.all().delete()
        Recipe.objects.bulk_create([
            Recipe(ingredient=ingredient, quantity_required=quantity, **({'topping': target} if is_topping else {'menu_item': target}))
            for ingredient, quantity in form.cleaned_data['cleaned_rows']
        ])
        if is_topping:
            target.applies_to_all = form.cleaned_data['applies_to_all']
            target.save(update_fields=['applies_to_all'])
            target.allowed_menu_items.set([] if target.applies_to_all else form.cleaned_data['allowed_menu_items'])
        else:
            target.inventory_mode = (form.cleaned_data.get('inventory_mode') or 'BOM') if target.category == 'DRINK' else 'BOM'
            target.save(update_fields=['inventory_mode'])
        from .domain import audit
        audit(request.user, 'RECIPE_UPDATED', target, ingredient_count=len(form.cleaned_data['cleaned_rows']))
        messages.success(request, f'Đã lưu {len(form.cleaned_data["cleaned_rows"])} nguyên liệu cho {target.name}.')
        return JsonResponse({'ok': True, 'redirect': reverse('admin_inventory') + '?view=recipes'})
    form = RecipeForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Chọn đúng một món chính hoặc topping còn kinh doanh, nguyên liệu hợp lệ và định lượng dương (tối đa 2 chữ số thập phân).')
        return redirect('admin_inventory')

    ingredient = form.cleaned_data['ingredient_id']
    menu_item = form.cleaned_data['menu_item_id']
    topping = form.cleaned_data['topping_id']
    qty = form.cleaned_data['quantity_required']
    Recipe.objects.create(
        menu_item=menu_item,
        topping=topping,
        ingredient=ingredient,
        quantity_required=qty,
    )
    target_name = menu_item.name if menu_item else topping.name
    messages.success(request, f'Đã lưu định lượng: 1x {target_name} tiêu hao {qty:g} {ingredient.unit} {ingredient.name}.')
    return redirect('admin_inventory')


@admin_required
@require_GET
def admin_recipe_auto_suggest(request):
    """
    Đề xuất định lượng tự động bằng mô hình Domain-specific Semantic NLP and Heuristic Engine.
    """
    from .nlp_bom import suggest_recipe_bom
    target_kind = request.GET.get('target', 'MENU')
    product_id = request.GET.get('id')
    scope = request.GET.get('scope', 'PHO')

    product_name = ''
    category = 'PHO'
    if target_kind == 'TOPPING':
        topping = get_object_or_404(Topping, pk=product_id)
        product_name = topping.name
        category = topping.category or scope
    else:
        menu_item = get_object_or_404(MenuItem, pk=product_id)
        product_name = menu_item.name
        category = menu_item.category

    ingredients = list(
        Ingredient.objects.filter(usage__in=[category, Ingredient.Usage.SHARED])
        .values('id', 'name', 'unit', 'usage')
    )

    result = suggest_recipe_bom(
        product_name=product_name,
        category=category,
        target_kind=target_kind,
        available_ingredients=ingredients
    )
    return JsonResponse(result)


@admin_required
@require_POST
def admin_recipe_clear_product(request, kind, product_id):
    """Xóa toàn bộ công thức định lượng của một sản phẩm."""
    if kind == 'topping':
        item = get_object_or_404(Topping, pk=product_id)
        count = item.recipes.count()
        item.recipes.all().delete()
    else:
        item = get_object_or_404(MenuItem, pk=product_id)
        count = item.recipes.count()
        item.recipes.all().delete()
    messages.success(request, f'Đã xóa định lượng ({count} nguyên liệu) của {item.name}.')
    return redirect(reverse('admin_inventory') + '?view=recipes')


@admin_required
@require_POST
def admin_recipe_delete(request, recipe_id):
    """Xóa công thức định lượng."""
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe.delete()
    messages.success(request, 'Đã xóa công thức định lượng thành công.')
    return redirect('admin_inventory')


# All legacy stock/role/order mutation paths share the transaction gate.
for _name in ('confirm_cash_payment', 'assign_order_table', 'free_table', 'free_order_table',
              'admin_ingredient_create', 'admin_ingredient_edit', 'admin_ingredient_import',
              'admin_recipe_create', 'admin_recipe_delete', 'admin_recipe_clear_product', 'admin_update_role', 'submit_review', 'simulate_vietqr_payment'):
    globals()[_name] = serialized(globals()[_name])
