from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from .domain import serialized

@receiver(pre_save, sender=Order)
def cache_previous_payment_status(sender, instance, using, raw=False, **kwargs):
    if raw:
        return
    instance._previous_payment_status = None
    if instance.pk:
        instance._previous_payment_status = (
            Order.objects.using(using).select_for_update().filter(pk=instance.pk)
            .values_list('payment_status', flat=True).first()
        )

@receiver(post_save, sender=Order)
@serialized
def deduct_inventory_on_paid(sender, instance, created, using, raw=False, update_fields=None, **kwargs):
    if raw or (update_fields is not None and 'payment_status' not in update_fields):
        return
    prev_status = getattr(instance, '_previous_payment_status', None)
    if instance.payment_status != Order.PaymentStatus.PAID or prev_status == Order.PaymentStatus.PAID:
        return

    from .checkout import consume_benefits
    from .stock import commit_reserved_inventory
    from .domain import BusinessError
    from .services import InvalidOrderTransition
    try:
        consume_benefits(instance)
        commit_reserved_inventory(instance)
    except BusinessError as exc:
        if isinstance(exc, InvalidOrderTransition):
            raise
        raise InvalidOrderTransition(str(exc)) from exc
