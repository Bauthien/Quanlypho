from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Order, Recipe, Ingredient, InventoryTransaction

@receiver(pre_save, sender=Order)
def cache_previous_payment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Order.objects.get(pk=instance.pk)
            instance._previous_payment_status = previous.payment_status
        except Order.DoesNotExist:
            pass

@receiver(post_save, sender=Order)
def deduct_inventory_on_paid(sender, instance, created, **kwargs):
    prev_status = getattr(instance, '_previous_payment_status', None)
    
    if instance.payment_status == Order.PaymentStatus.PAID and prev_status != Order.PaymentStatus.PAID:
        with transaction.atomic():
            for order_item in instance.items.all():
                # 1. Deduct for main menu item
                recipes = Recipe.objects.filter(menu_item=order_item.menu_item)
                for recipe in recipes:
                    deduct_amount = recipe.quantity_required * order_item.quantity
                    ingredient = recipe.ingredient
                    ingredient.current_stock -= deduct_amount
                    ingredient.save(update_fields=['current_stock'])
                    
                    InventoryTransaction.objects.create(
                        ingredient=ingredient,
                        transaction_type=InventoryTransaction.TransactionType.EXPORT,
                        quantity_changed=-deduct_amount
                    )
                
                # 2. Deduct for toppings
                for item_topping in order_item.toppings.all():
                    topping_recipes = Recipe.objects.filter(topping=item_topping.topping)
                    for tr in topping_recipes:
                        deduct_amount = tr.quantity_required * item_topping.quantity
                        ingredient = tr.ingredient
                        ingredient.current_stock -= deduct_amount
                        ingredient.save(update_fields=['current_stock'])
                        
                        InventoryTransaction.objects.create(
                            ingredient=ingredient,
                            transaction_type=InventoryTransaction.TransactionType.EXPORT,
                            quantity_changed=-deduct_amount
                        )
