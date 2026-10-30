import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .accounts import delete_address, find_vault, remember_login, save_address, switch_account, valid_slots
from .aftersales import (begin_refund, confirm_refund, create_replacement, decide_request,
    ensure_allocations, may_access_order, open_request)
from .commerce_forms import AddressForm, ProfileForm, RewardForm, TierForm, VoucherForm
from .delivery import delivery_action
from .domain import BusinessError, serialized, audit
from .loyalty import (account_for, daily_checkin, evaluate_and_upgrade_tier, exchange_reward,
    expire_points, issue_period_benefits, point_balance, process_events, reward_review)
from .models import (DailyCheckin, DomainEvent, Ingredient, InventoryIncident, Order, PaymentReceipt,
    Review,
    RefundAttempt, RefundPlan, RewardCatalog, ServiceRequest, TierConfig, User, UserAddress,
    UserVoucher, Voucher)
from .permissions import admin_required, staff_required
from .stock import expire_orders, record_waste, reserved_totals, return_unused


def account_context(request):
    context = {'account_generation': getattr(getattr(request, 'account_vault', None), 'generation', ''),
            'browser_slots': valid_slots(getattr(request, 'account_vault', None)), 'checkout_request_key': uuid.uuid4().hex}
    if request.user.is_authenticated and request.user.is_customer():
        context.update({'checkout_addresses': request.user.addresses.all(),
            'checkout_vouchers': request.user.vouchers.filter(state='AVAILABLE', starts_at__lte=timezone.now(), expires_at__gt=timezone.now()).select_related('voucher')})
    return context


def browser_context(request):
    response = JsonResponse({'generation': getattr(getattr(request, 'account_vault', None), 'generation', ''),
                         'user_id': request.user.pk if request.user.is_authenticated else None})
    response['Cache-Control'] = 'no-store'
    return response


@login_required
@require_GET
def address_preview(request):
    try:
        address_id = int(request.GET.get('address_id', ''))
    except (ValueError, TypeError):
        raise Http404
    address = get_object_or_404(UserAddress, pk=address_id, user=request.user)
    from .checkout import delivery_price
    try:
        if address.latitude is None or address.longitude is None:
            raise BusinessError('Địa chỉ chưa có vị trí nhận món. Hãy cập nhật vị trí trước khi tính phí giao.')
        fee, distance = delivery_price((float(address.latitude), float(address.longitude)))
        tier = account_for(request.user).tier if request.user.is_customer() else None
        nearby = bool(tier and tier.nearby_shipping and distance <= 5)
        response = JsonResponse({'ok': True, 'fee': fee, 'distance': str(distance), 'nearby_discount': fee if nearby else 0})
    except BusinessError as exc:
        response = JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    response['Cache-Control'] = 'no-store'
    return response


@login_required
@serialized
def account_home(request):
    process_events()
    user = User.objects.get(pk=request.user.pk)
    profile = ProfileForm(instance=user, initial={'version': user.profile_version})
    password_form = PasswordChangeForm(user)
    for field in password_form.fields.values():
        field.widget.attrs['class'] = 'form-input'
        field.widget.attrs.pop('autofocus', None)
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'profile':
                profile = ProfileForm(request.POST, request.FILES, instance=user)
                if profile.is_valid():
                    if profile.cleaned_data['version'] != user.profile_version:
                        raise BusinessError('Hồ sơ đã thay đổi trên tab khác. Hãy tải lại.')
                    user = profile.save(commit=False)
                    user.profile_version += 1
                    user.save()
                    messages.success(request, 'Đã lưu hồ sơ.')
                    return redirect('account')
            elif request.POST.get('action') == 'password':
                password_form = PasswordChangeForm(user, request.POST)
                if password_form.is_valid():
                    user = password_form.save()
                    remember_login(request, user)
                    messages.success(request, 'Đã đổi mật khẩu và thu hồi các phiên cũ của tài khoản này.')
                    return redirect('account')
        except BusinessError as exc:
            messages.error(request, str(exc))
    for field in password_form.fields.values():
        field.widget.attrs['class'] = 'form-input'
    context = {'profile_form': profile, 'password_form': password_form, 'addresses': user.addresses.all(),
        'address_form': AddressForm(), 'request_key': uuid.uuid4().hex}
    if user.is_customer():
        account = evaluate_and_upgrade_tier(user.pk)
        expire_points(account)
        tiers = list(TierConfig.objects.all())
        next_tier = next((t for t in tiers if t.rank > (account.tier.rank if account.tier else 0)), None)
        context.update({'wallet': account, 'balance': point_balance(account), 'tiers': tiers,
            'reserved_points': sum(account.lots.values_list('reserved', flat=True)),
            'next_tier': next_tier, 'spend_remaining': max(0, next_tier.minimum_spend - account.total_qualifying_spend) if next_tier else 0,
            'reviews_remaining': max(0, next_tier.good_reviews - account.good_review_count) if next_tier else 0,
            'progress': min(100, account.total_qualifying_spend * 100 // next_tier.minimum_spend) if next_tier else 100,
            'vouchers': user.vouchers.filter(state='AVAILABLE', expires_at__gt=timezone.now()).select_related('voucher'),
            'rewards': RewardCatalog.objects.filter(active=True).select_related('voucher'),
            'point_history': account.transactions.all()[:40], 'checkin': DailyCheckin.objects.filter(user=user, date=timezone.localdate()).first(),
            'vip_hotline': settings.VIP_HOTLINE if account.tier and account.tier.rank >= 3 else '',
            'orders': Order.objects.filter(customer=user).order_by('-created_at')[:30]})
        last_checkin = DailyCheckin.objects.filter(user=user).order_by('-date').first()
        streak = last_checkin.streak if last_checkin and (timezone.localdate() - last_checkin.date).days <= 1 else 0
        completed_days = ((streak - 1) % 7 + 1) if streak else 0
        context['checkin_days'] = [{'number': day, 'complete': day <= completed_days} for day in range(1, 8)]
        context['rewards'] = list(context['rewards'])
        for reward in context['rewards']:
            reward.points_short = max(0, reward.points_cost - context['balance'])
        now = timezone.now()
        context['reviews_progress'] = min(100, account.good_review_count * 100 // next_tier.good_reviews) if next_tier and next_tier.good_reviews else 100
        context['expiring_points'] = sum(account.lots.filter(expires_at__gt=now, expires_at__lte=now + timedelta(days=30)).values_list('available', flat=True))
        vouchers = list(user.vouchers.select_related('voucher', 'order').order_by('expires_at', 'pk'))
        for voucher in vouchers:
            voucher.ui_state = ('expired' if voucher.expires_at <= now else 'held' if voucher.state == 'RESERVED' else 'used' if voucher.state in ('CONSUMED', 'RESTORED') else 'available')
            voucher.ui_label = {'expired': 'Hết hạn', 'held': 'Đang giữ cho đơn', 'used': 'Đã sử dụng', 'available': 'Khả dụng'}[voucher.ui_state]
            voucher.ui_category = 'shipping' if voucher.policy.get('kind') == 'SHIPPING' else 'food'
            voucher.ui_source = 'exchange' if voucher.source == 'EXCHANGE' else 'tier' if voucher.source == 'TIER' else 'other'
            voucher.not_started = voucher.starts_at > now
        context['all_vouchers'] = vouchers
        context['voucher_count'] = sum(v.ui_state == 'available' and not v.not_started for v in vouchers)
        context['account_cases'] = ServiceRequest.objects.filter(order__customer=user).select_related('order', 'replacement').prefetch_related('refund_plans__attempts', 'allocations').order_by('-created_at')[:10]
        context['my_reviews'] = list(Review.objects.filter(customer=user).select_related('menu_item', 'order').order_by('-created_at'))
    return render(request, 'pho_app/customer/account.html', context)


@login_required
def address_edit(request, address_id=None):
    address = get_object_or_404(UserAddress, pk=address_id, user=request.user) if address_id else None
    form = AddressForm(request.POST or None, instance=address, initial={'version': address.version if address else 0})
    if request.method == 'POST' and form.is_valid():
        try:
            save_address(request.user, form.cleaned_data, address_id, form.cleaned_data.get('version'))
        except (BusinessError, ValidationError) as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, 'Đã lưu địa chỉ nhận món.')
            return redirect('account')
    return render(request, 'pho_app/customer/address_form.html', {'form': form, 'address': address})


@login_required
@require_POST
def address_action(request, address_id):
    try:
        if request.POST.get('action') == 'delete':
            delete_address(request.user, address_id, request.POST.get('version'))
        else:
            save_address(request.user, {'is_default': True}, address_id, request.POST.get('version'))
        messages.success(request, 'Đã cập nhật sổ địa chỉ.')
    except (BusinessError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('account')


@require_POST
def account_switch(request):
    try:
        user = switch_account(request, request.POST.get('slot_id'))
        return redirect(user.home_url_name())
    except (BusinessError, ValueError) as exc:
        messages.error(request, str(exc))
        return redirect('login')


@login_required
@require_POST
def loyalty_action(request):
    if not request.user.is_customer():
        raise Http404
    try:
        if request.POST.get('action') == 'checkin':
            result = daily_checkin(request.user)
            messages.success(request, f'Đã điểm danh hôm nay: {result.points} điểm. Chuỗi {result.streak} ngày.')
        elif request.POST.get('action') == 'exchange':
            voucher = exchange_reward(request.user, request.POST.get('reward_id'), request.POST.get('request_key'))
            messages.success(request, f'Đã đổi {voucher.voucher.name} vào ví voucher.')
    except (BusinessError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('account')


def order_support(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if not may_access_order(request, order):
        raise Http404
    if request.method == 'POST':
        try:
            allocation_ids = [int(v) for v in request.POST.getlist('allocations')]
            case = open_request(order.pk, request.POST.get('kind'), request.POST.get('reason', ''),
                request.POST.get('remedy', 'REFUND'), allocation_ids, request.POST.get('request_key'), request.user,
                request.POST.get('evidence', ''))
            process_events()
            messages.success(request, f'Đã tiếp nhận yêu cầu #{case.pk}. Xem tiến độ bên dưới.')
            return redirect('order_support', order_id=order.pk)
        except (BusinessError, ValueError) as exc:
            messages.error(request, str(exc))
    ensure_allocations(order)
    allocations = list(order.allocations.select_related('item'))
    cases = list(order.service_requests.prefetch_related('refund_plans__attempts', 'allocations'))
    for case in cases:
        case.ui_cash = sum(unit.cash for unit in case.allocations.all())
        case.ui_points = sum(unit.points for unit in case.allocations.all())
        case.ui_refund_confirmed = sum(plan.amount for plan in case.refund_plans.all() if plan.state == 'SUCCEEDED')
    return render(request, 'pho_app/customer/order_support.html', {'order': order,
        'allocations': allocations,
        'support_available': order.purpose == 'REGULAR' and any(not unit.case_id and not unit.refunded for unit in allocations),
        'support_can_cancel': order.order_status not in ('COMPLETED', 'CANCELLED') and all(not unit.case_id and not unit.refunded for unit in allocations),
        'support_kind': request.POST.get('kind', 'CANCEL' if order.order_status in ('CART', 'PENDING_KITCHEN') else 'ISSUE'),
        'cases': cases, 'request_key': uuid.uuid4().hex})


@staff_required
def service_queue(request):
    """Màn hình tiếp nhận & xử lý yêu cầu khiếu nại, đổi món và hoàn tiền của khách hàng."""
    process_events()
    cases = list(ServiceRequest.objects.select_related('order', 'replacement').prefetch_related('allocations', 'refund_plans__receipt', 'refund_plans__attempts').order_by('-pk')[:100])
    receipts = list(PaymentReceipt.objects.filter(requires_reconciliation=True).select_related('order').order_by('-pk')[:50])
    open_cases = sum(1 for c in cases if c.state == 'OPEN')
    processing_cases = sum(1 for c in cases if c.state in ('APPROVED', 'REFUNDING', 'REPLACING'))
    closed_cases = sum(1 for c in cases if c.state == 'CLOSED')

    return render(request, 'pho_app/operations/service_queue.html', {
        'cases': cases,
        'open_cases': open_cases,
        'processing_cases': processing_cases,
        'closed_cases': closed_cases,
        'receipts': receipts,
        'failed_events': DomainEvent.objects.filter(processed_at__isnull=True).exclude(error=''),
        'request_key': uuid.uuid4().hex,
    })


@staff_required
def delivery_queue(request):
    """Màn hình điều phối giao hàng: theo dõi đơn ship, bàn giao shipper và cập nhật trạng thái."""
    process_events()
    delivery_orders = list(Order.objects.filter(
        order_type='DELIVERY',
        payment_status='PAID',
        order_status__in=['READY', 'DELIVERING', 'DELIVERY_EXCEPTION', 'COMPLETED']
    ).select_related('delivery').prefetch_related('delivery__attempts').order_by('-created_at')[:100])

    ready_count = sum(1 for o in delivery_orders if o.order_status == 'READY')
    delivering_count = sum(1 for o in delivery_orders if o.order_status == 'DELIVERING')
    exception_count = sum(1 for o in delivery_orders if o.order_status == 'DELIVERY_EXCEPTION')
    completed_count = sum(1 for o in delivery_orders if o.order_status == 'COMPLETED')

    return render(request, 'pho_app/operations/delivery_queue.html', {
        'delivery_orders': delivery_orders,
        'ready_count': ready_count,
        'delivering_count': delivering_count,
        'exception_count': exception_count,
        'completed_count': completed_count,
        'failed_events': DomainEvent.objects.filter(processed_at__isnull=True).exclude(error=''),
        'request_key': uuid.uuid4().hex,
    })


@staff_required
@require_POST
def service_action(request, case_id):
    case = get_object_or_404(ServiceRequest, pk=case_id)
    try:
        action = request.POST.get('action')
        if action in ('approve', 'reject', 'replacement') and not request.user.is_admin_role():
            raise BusinessError('Chỉ quản lý được xét duyệt hoặc tạo giao bù.')
        if action in ('approve', 'reject'):
            decide_request(case.pk, action == 'approve', request.user, request.POST.get('note', ''))
        elif action == 'replacement':
            create_replacement(case.pk, request.user)
        elif action == 'begin_refund':
            plan = get_object_or_404(RefundPlan, pk=request.POST.get('plan_id'), case=case)
            if plan.receipt.provider != 'CASH' and not request.user.is_admin_role():
                raise BusinessError('Chỉ quản lý được thực hiện hoàn chuyển khoản.')
            begin_refund(plan.pk, request.user, request.POST.get('reference', ''))
        elif action == 'confirm_refund':
            attempt = get_object_or_404(RefundAttempt, pk=request.POST.get('attempt_id'), plan__case=case)
            if attempt.plan.receipt.provider != 'CASH' and not request.user.is_admin_role():
                raise BusinessError('Chỉ quản lý được đối soát ngân hàng.')
            confirm_refund(attempt.pk, request.POST.get('state'), request.user, request.POST.get('note', ''))
        process_events()
        messages.success(request, 'Đã cập nhật yêu cầu hỗ trợ.')
    except (BusinessError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('service_queue')


@staff_required
@require_POST
def delivery_update(request, order_id):
    try:
        delivery_action(order_id, request.POST.get('action'), request.user, request.POST.get('evidence', ''),
                        request.POST.get('courier', ''), request.POST.get('version'))
        process_events()
        messages.success(request, 'Đã cập nhật giao nhận.')
    except (BusinessError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('delivery_queue')


@admin_required
@require_POST
@serialized
def reconcile_receipt(request):
    from .payments import receive_payment
    try:
        action = request.POST.get('action')
        if action == 'record':
            if not request.POST.get('note', '').strip():
                raise BusinessError('Cần bằng chứng xác nhận chứng từ đã kiểm tra.')
            order = get_object_or_404(Order, order_code=request.POST.get('order_code'))
            receipt, _ = receive_payment(order.pk, request.POST.get('amount'), 'BANK', request.POST.get('reference'), timezone.now())
            if order.payment_status == 'PAID' and order.benefits_state == 'LEGACY' and not order.receipts.filter(allocated=True).exists() and receipt.amount == order.amount_due:
                receipt.allocated, receipt.requires_reconciliation = True, False
                receipt.save()
            audit(request.user, 'RECEIPT_VERIFIED', receipt, evidence=request.POST.get('note', ''))
        elif action == 'refund_extra':
            receipt = get_object_or_404(PaymentReceipt, pk=request.POST.get('receipt_id'), allocated=False)
            from .aftersales import receipt_budget
            amount = receipt_budget(receipt)
            if amount <= 0:
                raise BusinessError('Khoản thu đã có nghĩa vụ hoàn.')
            plan = RefundPlan.objects.create(receipt=receipt, amount=amount, key=f'extra:{receipt.pk}')
            begin_refund(plan.pk, request.user, request.POST.get('reference', ''))
        elif action == 'confirm_extra':
            attempt = get_object_or_404(RefundAttempt, pk=request.POST.get('attempt_id'), plan__case__isnull=True)
            confirm_refund(attempt.pk, request.POST.get('state'), request.user, request.POST.get('note', ''))
            if attempt.plan.state == 'SUCCEEDED':
                PaymentReceipt.objects.filter(pk=attempt.plan.receipt_id).update(requires_reconciliation=False)
        elif action == 'retry_extra':
            plan = get_object_or_404(RefundPlan, pk=request.POST.get('plan_id'), case__isnull=True)
            begin_refund(plan.pk, request.user, request.POST.get('reference', ''))
        messages.success(request, 'Đã ghi nhận đối soát.')
    except (BusinessError, ValueError, TypeError) as exc:
        messages.error(request, str(exc))
    return redirect('service_queue')


@admin_required
def promotions(request):
    edit = Voucher.objects.filter(pk=request.GET.get('edit')).first() if request.GET.get('edit') else None
    form = VoucherForm(request.POST if request.method == 'POST' and request.POST.get('action') not in ('reward', 'tier') else None, instance=edit, auto_id='voucher_%s')
    reward_edit = RewardCatalog.objects.filter(pk=request.GET.get('reward_edit')).first() if request.GET.get('reward_edit') else None
    reward_form = RewardForm(instance=reward_edit, auto_id='reward_%s')
    tier_edit = TierConfig.objects.filter(pk=request.GET.get('tier')).first() if request.GET.get('tier') else None
    tier_form = TierForm(instance=tier_edit, auto_id='tier_%s') if tier_edit else None
    if request.method == 'POST':
        if request.POST.get('action') == 'tier' and tier_edit:
            tier_form = TierForm(request.POST, instance=tier_edit, auto_id='tier_%s')
            if tier_form.is_valid():
                tier_form.save()
                audit(request.user, 'TIER_CONFIG_UPDATED', tier_edit)
                messages.success(request, 'Đã lưu cấu hình hạng. Quyền lợi đã phát và đơn cũ giữ bản chụp.')
                return redirect('promotions')
        elif request.POST.get('action') == 'reward':
            reward_form = RewardForm(request.POST, instance=RewardCatalog.objects.filter(pk=request.POST.get('reward_id')).first() if request.POST.get('reward_id') else None, auto_id='reward_%s')
            if reward_form.is_valid():
                reward_form.save()
                messages.success(request, 'Đã lưu quà đổi điểm.')
                return redirect('promotions')
        elif form.is_valid():
            form.save()
            messages.success(request, 'Đã lưu khuyến mãi. Voucher đã phát giữ chính sách khi phát.')
            return redirect('promotions')
    vouchers = list(Voucher.objects.exclude(code__startswith='TIER_').exclude(code__startswith='MONTHLY_SHIP_').exclude(code__startswith='POINTS_').order_by('-pk'))
    now = timezone.now()
    for voucher in vouchers:
        voucher.ui_state, voucher.ui_label = ('off', 'Đã tắt') if not voucher.active else ('expired', 'Hết hạn') if voucher.ends_at <= now else ('scheduled', 'Sắp diễn ra') if voucher.starts_at > now else ('active', 'Đang chạy')
    return render(request, 'pho_app/operations/promotions.html', {'form': form, 'reward_form': reward_form,
        'vouchers': vouchers, 'active_count': sum(v.ui_state == 'active' for v in vouchers),
        'rewards': RewardCatalog.objects.select_related('voucher').all(), 'tiers': TierConfig.objects.all(),
        'edit': edit, 'reward_edit': reward_edit, 'tier_edit': tier_edit, 'tier_form': tier_form})


@admin_required
@require_POST
def stock_operation(request):
    try:
        action = request.POST.get('action')
        if action == 'return':
            return_unused(int(request.POST['order_id']), int(request.POST['ingredient_id']), request.POST['quantity'],
                          request.user, request.POST.get('evidence', ''), request.POST.get('request_key'))
        elif action == 'waste':
            record_waste(int(request.POST['order_id']) if request.POST.get('order_id') else None,
                int(request.POST['ingredient_id']), request.POST['quantity'], request.user, request.POST.get('evidence', ''), request.POST.get('request_key'))
        elif action == 'resolve':
            incident = get_object_or_404(InventoryIncident, pk=request.POST.get('incident_id'), resolved=False)
            if not request.POST.get('evidence', '').strip():
                raise BusinessError('Cần ghi kết quả xử lý các đơn cam kết trước khi mở kho.')
            ingredient = incident.ingredient
            if ingredient.current_stock < reserved_totals().get(ingredient.pk, 0):
                raise BusinessError('Tồn thực tế vẫn thấp hơn lượng giữ; xử lý hoặc hủy các đơn liên quan trước.')
            incident.resolved = True
            incident.detail += '\nKết quả: ' + request.POST['evidence']
            incident.save()
            audit(request.user, 'INVENTORY_RESOLVED', incident)
        messages.success(request, 'Đã ghi nhận nghiệp vụ kho.')
    except ObjectDoesNotExist:
        messages.error(request, 'Đơn hoặc nguyên liệu không có phiếu xuất phù hợp. Hãy tải lại và chọn từ danh sách.')
    except (BusinessError, ValueError, KeyError, TypeError, ValidationError) as exc:
        messages.error(request, str(exc))
    return redirect('admin_inventory')


@admin_required
@require_POST
def maintenance(request):
    count = expire_orders(1000)
    process_events(1000)
    messages.success(request, f'Đã đóng {count} đơn quá hạn và xử lý lại sự kiện chờ.')
    return redirect('service_queue')
