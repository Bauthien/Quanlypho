from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Order, InventoryTransaction
from .services import ensure_inventory_available, order_inventory_deductions

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
def deduct_inventory_on_paid(sender, instance, created, using, raw=False, update_fields=None, **kwargs):
    if raw or (update_fields is not None and 'payment_status' not in update_fields):
        return
    prev_status = getattr(instance, '_previous_payment_status', None)
    if instance.payment_status != Order.PaymentStatus.PAID or prev_status == Order.PaymentStatus.PAID:
        return

    with transaction.atomic(using=using):
        deductions = order_inventory_deductions(instance, using=using)
        # Lock all shared ingredients in a consistent order and check the entire
        # order before writing any stock balance or export transaction.
        ingredients, required = ensure_inventory_available(deductions, using=using, lock=True)

        for ingredient in ingredients:
            ingredient.current_stock -= required[ingredient.pk]
            ingredient.save(using=using, update_fields=['current_stock'])
        InventoryTransaction.objects.using(using).bulk_create([
            InventoryTransaction(
                ingredient_id=ingredient_id,
                transaction_type=InventoryTransaction.TransactionType.EXPORT,
                quantity_changed=-amount,
                created_by_id=instance.customer_id,
            )
            for ingredient_id, amount in deductions
        ])
