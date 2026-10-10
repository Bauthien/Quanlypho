import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace active_order with latest_order
if 'latest_order = Order.objects' not in text:
    text = text.replace(
        "active_order = Order.objects.filter(customer=request.user, order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING]).order_by('-created_at').first() if request.user.is_authenticated else None",
        "latest_order = Order.objects.filter(customer=request.user).order_by('-created_at').first() if request.user.is_authenticated else None"
    )
    text = text.replace(
        "'active_order': active_order,",
        "'latest_order': latest_order,"
    )
    with open('pho_app/views.py', 'w', encoding='utf-8') as f:
        f.write(text)
