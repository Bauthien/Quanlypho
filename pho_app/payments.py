from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .domain import BusinessError, serialized
from .models import Order, PaymentReceipt


@serialized
def receive_payment(order_id, amount, provider, external_id, received_at=None):
    """Receipt survives a rejected/late settlement. IDs must come from the payer."""
    amount = Decimal(str(amount))
    if not amount.is_finite() or amount < 0 or amount != int(amount) or amount > 999999999999 or not external_id or len(external_id) > 120:
        raise BusinessError('Cần số tiền nguyên hợp lệ và mã giao dịch ngân hàng/phiếu thu thực tế.')
    order = Order.objects.get(pk=order_id)
    receipt, created = PaymentReceipt.objects.get_or_create(provider=provider, external_id=external_id,
        defaults={'order': order, 'amount': int(amount), 'received_at': received_at or timezone.now()})
    if not created:
        if receipt.order_id != order_id or receipt.amount != amount:
            raise BusinessError('Mã giao dịch đã ghi nhận cho nội dung khác.')
        return receipt, True
    error = ''
    if order.payment_status != 'PENDING' or order.order_status != 'CART':
        error = 'Tiền đến khi đơn đã thanh toán hoặc kết thúc.'
    elif amount != order.amount_due:
        error = 'Số tiền khác báo giá đã lưu.'
    elif order.expires_at and timezone.now() >= order.expires_at:
        error = 'Tiền đến sau hạn giữ đơn.'
    else:
        try:
            with transaction.atomic():
                order.payment_status, order.order_status = 'PAID', 'PENDING_KITCHEN'
                order.version += 1
                order.save(update_fields=['payment_status', 'order_status', 'version', 'updated_at'])
                receipt.allocated = True
        except (BusinessError, ValueError) as exc:
            error = str(exc)
    receipt.requires_reconciliation, receipt.note = bool(error), error
    receipt.save(update_fields=['allocated', 'requires_reconciliation', 'note'])
    return receipt, False
