import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

menu_logic = '''
    from django.db.models import Sum, Q, F
    from django.db.models.functions import Coalesce

    selected_table = request.GET.get('table', '')
    
    active_orders_q = Q(order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY])
    tables_qs = Table.objects.annotate(
        used_capacity=Coalesce(Sum('order__items__quantity', filter=active_orders_q), 0),
        remaining_cap=F('capacity') - Coalesce(Sum('order__items__quantity', filter=active_orders_q), 0)
    )

    if selected_table.isdigit():
        tables = tables_qs.filter(Q(remaining_cap__gt=0) | Q(pk=selected_table))
    else:
        tables = tables_qs.filter(remaining_cap__gt=0)
        
    tables = natural_sort_table(tables)
    
    table_obj = None
    remaining_capacity = -1

    if selected_table.isdigit():
        table_obj = next((t for t in tables if str(t.pk) == selected_table), None)
        if not table_obj:
            table_obj = Table.objects.filter(pk=selected_table).first()

    if table_obj:
        if hasattr(table_obj, 'remaining_cap'):
            remaining_capacity = table_obj.remaining_cap
        else:
            used_capacity = OrderItem.objects.filter(
                order__table=table_obj,
                order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            remaining_capacity = max(0, table_obj.capacity - used_capacity)
        
        if remaining_capacity <= 0:
            messages.warning(request, f'Bàn {table_obj.table_number} hiện đã hết chỗ. Vui lòng chọn bàn khác.')
'''

# The previous logic to replace:
old_logic_regex = r"\s*tables = Table\.objects\.filter\(status=Table\.Status\.AVAILABLE\)\s*table_obj = None\s*remaining_capacity = -1\s*if selected_table\.isdigit\(\):\s*tables = \(tables \| Table\.objects\.filter\(pk=selected_table, status=Table\.Status\.OCCUPIED\)\)\.distinct\(\)\s*table_obj = Table\.objects\.filter\(pk=selected_table\)\.first\(\)\s*if table_obj:\s*used_capacity = OrderItem\.objects\.filter\(\s*order__table=table_obj,\s*order__order_status__in=\[Order\.OrderStatus\.CART, Order\.OrderStatus\.PENDING_KITCHEN, Order\.OrderStatus\.COOKING, Order\.OrderStatus\.READY\]\s*\)\.aggregate\(total=Sum\('quantity'\)\)\['total'\] or 0\s*remaining_capacity = max\(0, table_obj\.capacity - used_capacity\)\s*if remaining_capacity == 0:\s*messages\.warning\(request, f'Bàn \{table_obj\.table_number\} hiện đã hết chỗ\. Vui lòng chọn bàn khác\.'\)"

# wait, I can just find the bounds manually
idx_start = text.find("    tables = Table.objects.filter(status=Table.Status.AVAILABLE)")
if idx_start != -1:
    idx_end = text.find("    tables = natural_sort_table(tables)", idx_start)
    if idx_end != -1:
        # Also need to replace the table_obj stuff which was before tables = natural_sort_table(tables) previously? No, wait.
        pass
