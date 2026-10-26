from django.utils import timezone

from .domain import BusinessError, serialized, audit
from .loyalty import enqueue
from .models import Delivery, DeliveryAttempt, Order, ServiceRequest


@serialized
def delivery_action(order_id, action, actor=None, evidence='', courier='', expected_version=None):
    order = Order.objects.get(pk=order_id)
    if order.order_type != 'DELIVERY' or order.payment_status != 'PAID' or order.order_status == 'CANCELLED':
        raise BusinessError('Đơn không đủ điều kiện giao hàng.')
    delivery, _ = Delivery.objects.get_or_create(order=order)
    if expected_version is not None and delivery.version != int(expected_version):
        raise BusinessError('Trạng thái giao hàng đã thay đổi; hãy tải lại.')
    if delivery.state == 'DELIVERED':
        if action == 'delivered':
            return delivery
        raise BusinessError('Không thể lùi trạng thái đơn đã giao thành công.')
    if not evidence.strip():
        raise BusinessError('Cần ghi người bàn giao, bằng chứng giao hàng hoặc lý do sự cố.')
    now = timezone.now()
    attempt = delivery.attempts.filter(state='IN_TRANSIT').first()
    if action in ('handover', 'retry'):
        allowed = ('READY_FOR_PICKUP',) if action == 'handover' else ('FAILED', 'RETRY_PENDING', 'RETURNED_TO_SHOP')
        if delivery.state not in allowed or attempt or (action == 'handover' and order.order_status != 'READY'):
            raise BusinessError('Chưa thể bàn giao hoặc tạo lượt giao lại.')
        DeliveryAttempt.objects.create(delivery=delivery, sequence=delivery.attempts.count() + 1, courier=courier[:100], evidence=evidence[:2000])
        delivery.state, order.order_status = 'IN_TRANSIT', 'DELIVERING'
    elif action == 'delivered':
        if delivery.state != 'IN_TRANSIT' or not attempt:
            raise BusinessError('Đơn chưa có lượt giao đang thực hiện.')
        attempt.state, attempt.finished_at, attempt.evidence = 'DELIVERED', now, evidence[:2000]
        attempt.save()
        delivery.state, delivery.delivered_at = 'DELIVERED', now
        order.order_status, order.completed_at = 'COMPLETED', now
        enqueue(f'complete:{order.pk}', 'ORDER_COMPLETED', order_id=order.pk)
        ServiceRequest.objects.filter(replacement=order, state='REPLACING').update(state='CLOSED')
    elif action in ('failed', 'returned'):
        if action == 'failed' and (delivery.state != 'IN_TRANSIT' or not attempt):
            raise BusinessError('Không có lượt giao đang thực hiện.')
        if action == 'returned' and delivery.state not in ('FAILED', 'RETRY_PENDING'):
            raise BusinessError('Chỉ ghi trả về cửa hàng sau một sự cố giao.')
        if attempt:
            attempt.state, attempt.finished_at, attempt.evidence = 'FAILED', now, evidence[:2000]
            attempt.save()
        delivery.state = 'FAILED' if action == 'failed' else 'RETURNED_TO_SHOP'
        order.order_status = 'DELIVERY_EXCEPTION'
    else:
        raise BusinessError('Thao tác giao hàng không hợp lệ.')
    delivery.version += 1
    delivery.save()
    order.version += 1
    order.save(update_fields=['order_status', 'completed_at', 'version', 'updated_at'])
    audit(actor, f'DELIVERY_{action.upper()}', delivery, evidence=evidence, courier=courier)
    return delivery
