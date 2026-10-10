import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
        order.payment_status = Order.PaymentStatus.FAILED
        order.order_status = Order.OrderStatus.CANCELLED
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
        
        # Free the table if there are no other active orders on it
        if order.table_id:
            has_other_active = Order.objects.filter(
                table_id=order.table_id
            ).exclude(
                order_status__in=[Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]
            ).exclude(pk=order.pk).exists()
            
            if not has_other_active:
                Table.objects.filter(pk=order.table_id).update(status=Table.Status.AVAILABLE)
'''

text = re.sub(
    r'\s*order\.payment_status = Order\.PaymentStatus\.FAILED\s*\n\s*order\.order_status = Order\.OrderStatus\.CANCELLED\s*\n\s*order\.save\(update_fields=\[\'payment_status\', \'order_status\', \'updated_at\'\]\)',
    replacement,
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
