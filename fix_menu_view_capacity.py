import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx_start = text.find('    tables = Table.objects.filter(status=Table.Status.AVAILABLE)')
idx_end = text.find('    tables = natural_sort_table(tables)')

new_logic = '''    from django.db.models import Sum, Q, F
    from django.db.models.functions import Coalesce

    active_orders_q = Q(order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY])
    tables_qs = Table.objects.annotate(
        used_capacity=Coalesce(Sum('order__items__quantity', filter=active_orders_q), 0),
        remaining_cap=F('capacity') - Coalesce(Sum('order__items__quantity', filter=active_orders_q), 0)
    )

    if selected_table.isdigit():
        tables = tables_qs.filter(Q(remaining_cap__gt=0) | Q(pk=selected_table))
    else:
        tables = tables_qs.filter(remaining_cap__gt=0)

    table_obj = None
    remaining_capacity = -1

    if selected_table.isdigit():
        table_obj = next((t for t in tables if str(t.pk) == selected_table), None)
        if not table_obj:
            table_obj = tables_qs.filter(pk=selected_table).first()
            
    if table_obj:
        remaining_capacity = getattr(table_obj, 'remaining_cap', 0)
        if remaining_capacity <= 0:
            messages.warning(request, f'Bàn {table_obj.table_number} hiện đã hết chỗ. Vui lòng chọn bàn khác.')

'''

if idx_start != -1 and idx_end != -1:
    text = text[:idx_start] + new_logic + text[idx_end:]
    with open('pho_app/views.py', 'w', encoding='utf-8') as f:
        f.write(text)
