import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Pass active_order to menu.html
if 'active_order =' not in text:
    text = text.replace(
        "active_ticket = QueueTicket.objects.filter(",
        "active_order = Order.objects.filter(customer=request.user, order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING]).order_by('-created_at').first() if request.user.is_authenticated else None\n    active_ticket = QueueTicket.objects.filter("
    )
    text = text.replace(
        "'active_ticket': active_ticket,",
        "'active_order': active_order,\n        'active_ticket': active_ticket,"
    )
    with open('pho_app/views.py', 'w', encoding='utf-8') as f:
        f.write(text)
