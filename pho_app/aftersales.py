import uuid
from datetime import timedelta

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .domain import BusinessError, serialized, request_key, audit
from .loyalty import enqueue, reconcile_order_loyalty, restore_order_points, grant_voucher
from .models import (Order, OrderAllocation, PaymentReceipt, RefundAttempt, RefundPlan,
    ServiceRequest, Table, UserVoucher)


def may_access_order(request, order):
    return (request.user.is_authenticated and (request.user.pk == order.customer_id or
            request.user.role in ('STAFF', 'ADMIN'))) or (order.customer_id is None and order.pk in request.session.get('guest_orders', []))


def receipt_budget(receipt):
    held = receipt.refund_plans.exclude(state='VOID').aggregate(total=Sum('amount'))['total'] or 0
    return receipt.amount - held


def ensure_allocations(order):
    if order.allocations.exists():
        return
    # Explicitly label legacy prices; old discounts did not exist in the schema.
    for item in order.items.select_related('menu_item'):
        for unit in range(1, item.quantity + 1):
            OrderAllocation.objects.create(order=order, item=item, unit=unit, label=item.menu_item.name,
                net_before_points=int(item.item_price), cash=int(item.item_price))
    if order.delivery_fee:
        OrderAllocation.objects.create(order=order, label='Phí giao hàng', net_before_points=int(order.delivery_fee), cash=int(order.delivery_fee))


@serialized
def open_request(order_id, kind, reason, remedy, allocation_ids, key, actor=None, evidence=''):
    order = Order.objects.get(pk=order_id)
    req = request_key(f'service:{order_id}', key, {'kind': kind, 'reason': reason, 'remedy': remedy, 'units': sorted(allocation_ids), 'evidence': evidence})
    if req.result:
        return ServiceRequest.objects.get(pk=req.result['case'])
    if kind not in ('CANCEL', 'ISSUE') or remedy not in ('REFUND', 'REPLACE') or not reason.strip():
        raise BusinessError('Cần loại yêu cầu, lý do và phương án xử lý hợp lệ.')
    if order.purpose != 'REGULAR':
        raise BusinessError('Liên hệ hỗ trợ trên yêu cầu gốc của đơn giao bù.')
    if kind == 'CANCEL' and order.order_status in ('COMPLETED', 'CANCELLED'):
        raise BusinessError('Đơn đã kết thúc; hãy gửi yêu cầu món lỗi nếu cần hỗ trợ.')
    window = getattr(settings, 'ISSUE_REPORT_HOURS', 2)
    if kind == 'ISSUE' and order.completed_at and timezone.now() > order.completed_at + timedelta(hours=window):
        if not actor or actor.role != 'ADMIN':
            raise BusinessError(f'Đã qua {window} giờ tiếp nhận tự động. Liên hệ cửa hàng để được xem xét ngoại lệ.')
    ensure_allocations(order)
    selected = list(order.allocations.filter(pk__in=allocation_ids)) if allocation_ids else list(order.allocations.all())
    if kind == 'CANCEL':
        selected = list(order.allocations.all())
        remedy = 'REFUND'
    if not selected or (allocation_ids and kind != 'CANCEL' and len(selected) != len(set(allocation_ids))):
        raise BusinessError('Phần món yêu cầu không thuộc đơn.')
    if remedy == 'REPLACE' and any(a.item_id is None for a in selected):
        raise BusinessError('Chọn các phần món cần giao bù, không chọn phí giao hàng.')
    if any(a.case_id or a.refunded for a in selected):
        raise BusinessError('Phần món đã được giữ cho yêu cầu khác hoặc đã xử lý.')
    case = ServiceRequest.objects.create(order=order, request_key=f'service:{req.pk}', kind=kind,
        reason=reason[:2000], remedy=remedy, evidence=evidence[:2000])
    OrderAllocation.objects.filter(pk__in=[a.pk for a in selected]).update(case=case)
    req.result = {'case': case.pk}
    req.save(update_fields=['result'])
    if kind == 'CANCEL' and order.order_status in ('CART', 'PENDING_KITCHEN'):
        decide_request(case.pk, True, actor, 'Tự động duyệt trước chế biến')
    audit(actor, 'SERVICE_OPEN', case)
    return case


@serialized
def decide_request(case_id, approve, actor, note):
    from .checkout import release_benefits
    case = ServiceRequest.objects.select_related('order').get(pk=case_id)
    if case.state != 'OPEN':
        return case
    order = case.order
    auto = case.kind == 'CANCEL' and order.order_status in ('CART', 'PENDING_KITCHEN')
    if not auto and (not actor or actor.role != 'ADMIN'):
        raise BusinessError('Cần quản lý xét duyệt yêu cầu sau chế biến.')
    case.state = 'APPROVED' if approve else 'REJECTED'
    case.decision_note, case.decided_by = note[:2000], actor if getattr(actor, 'is_authenticated', False) else None
    if not approve:
        case.allocations.update(case=None)
    elif case.kind == 'CANCEL':
        previous = order.order_status
        if previous in ('DELIVERING', 'DELIVERY_EXCEPTION') and (not actor or actor.role != 'ADMIN'):
            raise BusinessError('Đơn đang giao cần quản lý điều phối.')
        order.order_status = 'CANCELLED'
        order.version += 1
        if order.payment_status != 'PAID':
            order.payment_status = 'FAILED'
            release_benefits(order)
        order.save(update_fields=['order_status', 'payment_status', 'version', 'updated_at'])
        if order.table_id and not Order.objects.filter(table_id=order.table_id, is_cleared=False).exclude(order_status='CANCELLED').exists():
            Table.objects.filter(pk=order.table_id).update(status='AVAILABLE')
    if approve and case.remedy == 'REFUND':
        amount = case.allocations.aggregate(total=Sum('cash'))['total'] or 0
        left = amount
        receipts = list(order.receipts.filter(allocated=True).order_by('pk'))
        # Legacy payment flags are not proof of an actual receipt. Reconciliation UI
        # must record a verified bank transaction or signed cash receipt first.
        if order.payment_status == 'PAID' and left and sum(receipt_budget(r) for r in receipts) < left:
            raise BusinessError('Chưa có đủ phiếu thu đã đối soát. Ghi nhận chứng từ thật trước khi duyệt hoàn.')
        for receipt in receipts:
            part = min(left, receipt_budget(receipt))
            if part:
                RefundPlan.objects.create(case=case, receipt=receipt, amount=part, key=f'case:{case.pk}:receipt:{receipt.pk}')
                left -= part
        if order.payment_status != 'PAID' or amount == 0:
            case.state = 'REFUND_CONFIRMED'
            enqueue(f'refund:{case.pk}', 'REFUND_BENEFITS', case_id=case.pk)
    case.save()
    audit(actor, 'SERVICE_DECISION', case, approve=approve, note=note)
    return case


@serialized
def begin_refund(plan_id, actor, reference):
    plan = RefundPlan.objects.get(pk=plan_id)
    if plan.state == 'SUCCEEDED':
        return plan.attempts.order_by('-pk').first()
    if not reference.strip():
        raise BusinessError('Cần mã lệnh hoàn hoặc phiếu chi để đối soát.')
    if plan.attempts.filter(state__in=['SUBMITTED', 'UNKNOWN']).exists():
        raise BusinessError('Lệnh hoàn đang chờ đối soát. Không được gửi một lệnh chi khác.')
    attempt = RefundAttempt.objects.create(plan=plan, actor=actor, reference=reference[:120])
    plan.state = 'SUBMITTED'
    plan.save(update_fields=['state'])
    audit(actor, 'REFUND_SUBMITTED', attempt)
    return attempt


@serialized
def confirm_refund(attempt_id, state, actor, note):
    attempt = RefundAttempt.objects.select_related('plan__case').get(pk=attempt_id)
    if state not in ('SUCCEEDED', 'FAILED_FINAL', 'UNKNOWN') or not note.strip():
        raise BusinessError('Cần kết quả và bằng chứng đối soát hoàn tiền.')
    if attempt.state in ('SUCCEEDED', 'FAILED_FINAL'):
        if attempt.state != state:
            raise BusinessError('Kết quả cuối đã được ghi nhận.')
        return attempt
    attempt.state, attempt.note = state, note[:2000]
    attempt.finished_at = timezone.now() if state != 'UNKNOWN' else None
    attempt.save()
    plan = attempt.plan
    plan.state = 'RESERVED' if state == 'FAILED_FINAL' else state
    plan.save(update_fields=['state'])
    case = plan.case
    if state == 'SUCCEEDED' and case and not case.refund_plans.exclude(state='SUCCEEDED').exists():
        case.state = 'REFUND_CONFIRMED'
        case.save(update_fields=['state'])
        enqueue(f'refund:{case.pk}', 'REFUND_BENEFITS', case_id=case.pk)
    audit(actor, 'REFUND_RECONCILED', attempt, state=state, note=note)
    return attempt


@serialized
def apply_refund_benefits(case_id):
    case = ServiceRequest.objects.select_related('order').get(pk=case_id)
    if case.benefits_applied or case.state != 'REFUND_CONFIRMED':
        return
    order = case.order
    case.allocations.update(refunded=True)
    target = order.allocations.filter(refunded=True).aggregate(total=Sum('points'))['total'] or 0
    restore_order_points(order, target)
    if not order.allocations.filter(refunded=False).exists():
        for wallet in UserVoucher.objects.filter(order=order, state='CONSUMED').select_related('voucher'):
            wallet.state, wallet.order = 'RESTORED', None
            wallet.save(update_fields=['state', 'order'])
            expiry = wallet.expires_at if wallet.expires_at > timezone.now() else timezone.now() + timedelta(days=7)
            grant_voucher(wallet.user, wallet.voucher, 'AFTERSALES_RESTORE', f'restore-voucher:{wallet.pk}', expiry, policy=wallet.policy)
    reconcile_order_loyalty(order.pk)
    case.benefits_applied, case.state = True, 'CLOSED'
    case.save(update_fields=['benefits_applied', 'state'])


@serialized
def create_replacement(case_id, actor):
    from .checkout import save_checkout
    from .models import Delivery, OrderItem, OrderItemTopping, OrderItemCustomization
    from .services import inventory_deductions
    from .stock import reserve_inventory
    case = ServiceRequest.objects.select_related('order').get(pk=case_id)
    if case.replacement_id:
        return case.replacement
    if case.state != 'APPROVED' or case.remedy != 'REPLACE':
        raise BusinessError('Yêu cầu chưa được duyệt giao bù.')
    original = case.order
    order = Order.objects.create(order_code=f'BU-{uuid.uuid4().hex[:10].upper()}', customer=original.customer,
        guest_name=original.guest_name, order_type=original.order_type, delivery_address=original.delivery_address,
        customer_location=original.customer_location, delivery_snapshot=original.delivery_snapshot,
        purpose='SERVICE_REPLACEMENT', replacement_for=original, payable_amount=0,
        expires_at=timezone.now() + timedelta(minutes=15), benefits_state='RESERVED')
    deductions, snapshot = [], []
    for item_id in case.allocations.values_list('item_id', flat=True).distinct():
        item = original.items.get(pk=item_id)
        qty = case.allocations.filter(item_id=item_id).count()
        replacement = OrderItem.objects.create(order=order, menu_item=item.menu_item, quantity=qty, item_price=0, note=f'Giao bù yêu cầu #{case.pk}')
        extras = []
        for extra in item.toppings.select_related('topping'):
            per_unit = extra.quantity // item.quantity
            OrderItemTopping.objects.create(order_item=replacement, topping=extra.topping, quantity=per_unit * qty)
            extras.append((extra.topping, per_unit * qty))
        OrderItemCustomization.objects.bulk_create([OrderItemCustomization(order_item=replacement, customization=c.customization) for c in item.customizations.all()])
        deductions.extend(inventory_deductions([(item.menu_item, qty, extras)]))
    reserve_inventory(order, deductions)
    if order.order_type == 'DELIVERY':
        Delivery.objects.create(order=order)
    order.payment_status, order.order_status = 'PAID', 'PENDING_KITCHEN'
    order.save(update_fields=['payment_status', 'order_status'])
    case.replacement, case.state = order, 'REPLACING'
    case.save(update_fields=['replacement', 'state'])
    audit(actor, 'REPLACEMENT_CREATED', case, order=order.pk)
    return order
