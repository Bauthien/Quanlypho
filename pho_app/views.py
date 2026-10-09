import json
import hashlib
import hmac
import uuid
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import MenuItemForm, RegisterForm, StyledAuthForm, ToppingForm, UserRoleForm
from .models import (
    CustomizationOption,
    MenuItem,
    Order,
    OrderItem,
    OrderItemCustomization,
    OrderItemTopping,
    QueueTicket,
    Table,
    Topping,
    User,
)
from .permissions import admin_required, kitchen_required, staff_required


def _generate_order_code():
    return f"PHO-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def _vietqr_image_url(order):
    bank = getattr(settings, 'VIETQR_BANK_ID', '')
    account = getattr(settings, 'VIETQR_ACCOUNT_NO', '')
    account_name = getattr(settings, 'VIETQR_ACCOUNT_NAME', '')
    if not bank or not account:
        return ''
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
    return redirect('menu')


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
    if request.user.is_authenticated and request.user.role in (User.Role.STAFF, User.Role.KITCHEN, User.Role.ADMIN):
        return redirect(request.user.home_url_name())
    items = MenuItem.objects.filter(is_active=True)
    menu_payload = [
        {
            'id': item.id,
            'name': item.name,
            'price': int(item.base_price),
            'desc': 'Chọn món và thanh toán VietQR hoặc tiền mặt.',
            'image': item.image_primary.url if item.image_primary else '',
        }
        for item in items
    ]
    options = list(CustomizationOption.objects.all().order_by('category', 'id').values('id', 'category', 'name'))
    toppings = list(Topping.objects.all().order_by('name').values('id', 'name', 'price'))
    active_ticket = QueueTicket.objects.filter(
        customer=request.user,
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).select_related('table').first() if request.user.is_authenticated else None
    selected_table = request.GET.get('table', '')
    tables = Table.objects.filter(status=Table.Status.AVAILABLE)
    if selected_table.isdigit():
        tables = (tables | Table.objects.filter(pk=selected_table, status=Table.Status.OCCUPIED)).distinct()
    return render(request, 'pho_app/customer/menu.html', {
        'menu_items': items,
        'menu_payload': menu_payload,
        'customization_options': options,
        'toppings': toppings,
        'tables': tables.order_by('table_number'),
        'active_ticket': active_ticket,
        'selected_table': selected_table,
        'delivery_flat_fee': getattr(settings, 'DELIVERY_FLAT_FEE', 30000),
    })


@login_required
@require_POST
def place_order(request):
    if not request.user.is_customer():
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
        selected_toppings = list(Topping.objects.filter(pk__in=topping_ids))
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
    delivery_fee = Decimal(str(getattr(settings, 'DELIVERY_FLAT_FEE', 30000))) if order_type == Order.OrderType.DELIVERY else Decimal('0')
    if order_type == Order.OrderType.DELIVERY and not address:
        messages.error(request, 'Vui lòng nhập địa chỉ giao hàng.')
        return redirect('menu')

    table = None
    ticket = None
    if order_type == Order.OrderType.DINE_IN:
        if not table_id:
            messages.error(request, 'Vui lòng chọn bàn trống hoặc quét mã QR tại bàn.')
            return redirect('menu')

    with transaction.atomic():
        if order_type == Order.OrderType.QUEUE_CART:
            ticket = QueueTicket.objects.select_for_update().filter(
                customer=request.user,
                status=QueueTicket.Status.CALLED,
            ).order_by('-created_at').first()
            if not ticket or not ticket.table_id:
                messages.error(request, 'Bạn chỉ có thể thanh toán giỏ xếp hàng sau khi được gọi số.')
                return redirect('menu')
            table = Table.objects.select_for_update().filter(pk=ticket.table_id, status=Table.Status.OCCUPIED).first()
            if not table:
                messages.error(request, 'Bàn gắn với số của bạn không còn khả dụng. Vui lòng liên hệ thu ngân.')
                return redirect('menu')
        elif order_type == Order.OrderType.DINE_IN:
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
        order = Order.objects.create(
            order_code=_generate_order_code(),
            customer=request.user,
            order_type=order_type,
            table=table,
            queue_ticket=ticket,
            payment_method=payment_method,
            payment_status=Order.PaymentStatus.PENDING,
            order_status=Order.OrderStatus.CART,
            total_amount=total,
            delivery_fee=delivery_fee,
            delivery_address=address or None,
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
        if ticket:
            ticket.status = QueueTicket.Status.SEATED
            ticket.save(update_fields=['status'])

    messages.info(request, f'Đơn {order.order_code} đã tạo. Trạng thái: chờ thanh toán.')
    return redirect('order_detail', order_id=order.pk)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'), pk=order_id, customer=request.user)
    return render(request, 'pho_app/customer/order_detail.html', {
        'order': order,
        'vietqr_image_url': _vietqr_image_url(order) if order.payment_method == Order.PaymentMethod.VIETQR else '',
        'grand_total': order.total_amount + order.delivery_fee,
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


@login_required
@require_POST
def take_queue_number(request):
    if not request.user.is_customer():
        messages.error(request, 'Chỉ khách hàng mới lấy số xếp hàng.')
        return redirect(request.user.home_url_name())

    existing = QueueTicket.objects.filter(
        customer=request.user,
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).first()
    if existing:
        messages.info(request, f'Bạn đang có số {existing.ticket_number}.')
        return redirect('menu')

    ticket = QueueTicket.objects.create(
        customer=request.user,
        ticket_number=f'TMP-{uuid.uuid4().hex}',
    )
    ticket.ticket_number = f'P-{ticket.pk:03d}'
    ticket.save(update_fields=['ticket_number'])
    messages.success(request, f'Đã lấy số {ticket.ticket_number}. Vui lòng chờ gọi.')
    return redirect('menu')


@login_required
def queue_status(request):
    if not request.user.is_customer():
        return JsonResponse({'active': False})
    ticket = QueueTicket.objects.filter(
        customer=request.user,
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).select_related('table').first()
    if not ticket:
        return JsonResponse({'active': False})
    return JsonResponse({
        'active': True,
        'ticket': ticket.ticket_number,
        'status': ticket.status,
        'table': ticket.table.table_number if ticket.table_id else None,
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
        'tables': Table.objects.all().order_by('table_number'),
        'available_tables': Table.objects.filter(status=Table.Status.AVAILABLE).order_by('table_number'),
    })


@staff_required
@require_POST
def confirm_cash_payment(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id, payment_method=Order.PaymentMethod.CASH)
        if order.payment_status != Order.PaymentStatus.PENDING or order.order_status != Order.OrderStatus.CART:
            messages.info(request, 'Đơn này đã được xử lý trước đó.')
            return redirect('staff_home')
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
    messages.success(request, f'Đã nhận tiền đơn {order.order_code}. Đơn đã chuyển xuống bếp.')
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
    order = get_object_or_404(Order, pk=order_id, order_type=Order.OrderType.DELIVERY, order_status=Order.OrderStatus.READY)
    order.order_status = Order.OrderStatus.DELIVERING
    order.save(update_fields=['order_status', 'updated_at'])
    messages.success(request, f'Đã bàn giao đơn {order.order_code} cho đơn vị giao hàng.')
    return redirect('staff_home')


@staff_required
@require_POST
def complete_delivery(request, order_id):
    order = get_object_or_404(Order, pk=order_id, order_type=Order.OrderType.DELIVERY, order_status=Order.OrderStatus.DELIVERING)
    order.order_status = Order.OrderStatus.COMPLETED
    order.save(update_fields=['order_status', 'updated_at'])
    messages.success(request, f'Đã hoàn tất giao đơn {order.order_code}.')
    return redirect('staff_home')


@staff_required
@require_POST
def complete_dine_in(request, order_id):
    order = get_object_or_404(Order, pk=order_id, order_type=Order.OrderType.DINE_IN, order_status=Order.OrderStatus.READY)
    order.order_status = Order.OrderStatus.COMPLETED
    order.save(update_fields=['order_status', 'updated_at'])
    if order.table_id:
        Table.objects.filter(pk=order.table_id).update(status=Table.Status.CLEANING)
    messages.success(request, f'Đã phục vụ xong đơn {order.order_code}. Bàn chuyển sang trạng thái cần dọn.')
    return redirect('staff_home')


@staff_required
@require_POST
def free_table(request, table_id):
    table = get_object_or_404(Table, pk=table_id, status=Table.Status.CLEANING)
    table.status = Table.Status.AVAILABLE
    table.save(update_fields=['status'])
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
    order = get_object_or_404(Order, pk=order_id, payment_status=Order.PaymentStatus.PAID, order_status=Order.OrderStatus.PENDING_KITCHEN)
    order.order_status = Order.OrderStatus.COOKING
    order.save(update_fields=['order_status', 'updated_at'])
    messages.success(request, f'Bếp đã nhận đơn {order.order_code}.')
    return redirect('kitchen_home')


@kitchen_required
@require_POST
def kitchen_complete(request, order_id):
    order = get_object_or_404(
        Order, pk=order_id, payment_status=Order.PaymentStatus.PAID,
        order_status__in=[Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING],
    )
    order.order_status = Order.OrderStatus.READY
    order.save(update_fields=['order_status', 'updated_at'])
    if order.order_type == Order.OrderType.DELIVERY:
        messages.success(request, f'Đơn giao {order.order_code} đã xong. Cần in 2 tem riêng (hộp khô + nước dùng).')
        return redirect('delivery_labels', order_id=order.pk)
    else:
        table_label = f'Bàn {order.table.table_number}' if order.table else 'Mang ra'
        messages.success(request, f'{table_label} - Đơn {order.order_code} đã xong.')
    return redirect('kitchen_home')


@kitchen_required
def delivery_labels(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'),
        pk=order_id,
        order_type=Order.OrderType.DELIVERY,
        order_status=Order.OrderStatus.READY,
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
        'menu_items': MenuItem.objects.count(),
        'orders': Order.objects.count(),
        'revenue': paid.aggregate(total=Sum('total_amount'))['total'] or 0,
        'dine_in': paid.filter(order_type=Order.OrderType.DINE_IN).count(),
        'delivery': paid.filter(order_type=Order.OrderType.DELIVERY).count(),
        'waiting': QueueTicket.objects.filter(status=QueueTicket.Status.WAITING).count(),
    }
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:8]
    return render(request, 'pho_app/admin/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
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
    return render(request, 'pho_app/admin/menu_list.html', {
        'items': MenuItem.objects.all().order_by('name'),
        'toppings': Topping.objects.all().order_by('name'),
    })


@admin_required
def admin_menu_create(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã thêm món mới.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/menu_form.html', {'form': form, 'title': 'Thêm món'})


@admin_required
def admin_menu_edit(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã cập nhật món.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/menu_form.html', {'form': form, 'title': 'Sửa món', 'item': item})


@admin_required
@require_POST
def admin_menu_delete(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    item.is_active = False
    item.save(update_fields=['is_active'])
    messages.success(request, 'Đã ẩn món khỏi thực đơn; lịch sử đơn hàng được giữ nguyên.')
    return redirect('admin_menu')


@admin_required
def admin_topping_create(request):
    form = ToppingForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã thêm topping.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/topping_form.html', {'form': form, 'title': 'Thêm topping'})


@admin_required
def admin_topping_edit(request, topping_id):
    topping = get_object_or_404(Topping, pk=topping_id)
    form = ToppingForm(request.POST or None, request.FILES or None, instance=topping)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã cập nhật topping.')
        return redirect('admin_menu')
    return render(request, 'pho_app/admin/topping_form.html', {'form': form, 'title': 'Sửa topping'})


@admin_required
@require_POST
def admin_topping_delete(request, topping_id):
    topping = get_object_or_404(Topping, pk=topping_id)
    if topping.orderitemtopping_set.exists():
        messages.error(request, 'Không thể xóa topping đã có trong đơn hàng; lịch sử bán hàng cần được giữ nguyên.')
        return redirect('admin_menu')
    topping.delete()
    messages.success(request, 'Đã xóa topping.')
    return redirect('admin_menu')
