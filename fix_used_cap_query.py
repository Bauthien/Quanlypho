import io, re
with io.open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix place_order
text = re.sub(
    r'used_capacity = OrderItem\.objects\.filter\(\s*order__table=table,\s*is_cleared=False\s*\)\.aggregate',
    "used_capacity = OrderItem.objects.filter(order__table=table, order__is_cleared=False).exclude(order__order_status=Order.OrderStatus.CANCELLED).aggregate",
    text
)

# Fix menu_view table_obj manual calc
text = re.sub(
    r'used_capacity = OrderItem\.objects\.filter\(\s*order__table=table_obj,\s*is_cleared=False\s*\)\.aggregate',
    "used_capacity = OrderItem.objects.filter(order__table=table_obj, order__is_cleared=False).exclude(order__order_status=Order.OrderStatus.CANCELLED).aggregate",
    text
)

with io.open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
