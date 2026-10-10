import io, re
with io.open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update free_table
text = re.sub(
    r'def free_table\(request, table_id\):\s*table = get_object_or_404\(Table, pk=table_id, status__in=\[Table\.Status\.CLEANING, Table\.Status\.OCCUPIED\]\)\s*table\.status = Table\.Status\.AVAILABLE\s*table\.save\(update_fields=\[\'status\'\]\)',
    '''def free_table(request, table_id):
    table = get_object_or_404(Table, pk=table_id, status__in=[Table.Status.CLEANING, Table.Status.OCCUPIED])
    table.status = Table.Status.AVAILABLE
    table.save(update_fields=['status'])
    Order.objects.filter(table=table, is_cleared=False).update(is_cleared=True)''',
    text
)

# Update menu_view
text = re.sub(
    r'active_orders_q = Q\(order__order_status__in=\[Order\.OrderStatus\.CART, Order\.OrderStatus\.PENDING_KITCHEN, Order\.OrderStatus\.COOKING, Order\.OrderStatus\.READY\]\)',
    "active_orders_q = Q(order__is_cleared=False) & ~Q(order__order_status=Order.OrderStatus.CANCELLED)",
    text
)
# Update the table_obj manual calc in menu_view just in case
text = re.sub(
    r'order__order_status__in=\[Order\.OrderStatus\.CART, Order\.OrderStatus\.PENDING_KITCHEN, Order\.OrderStatus\.COOKING, Order\.OrderStatus\.READY\]',
    "is_cleared=False",
    text
)

# Wait, order__order_status__in=[Order.OrderStatus.CART... was used in place_order as well!
text = text.replace(
    'order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY]',
    'is_cleared=False'
)

with io.open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
