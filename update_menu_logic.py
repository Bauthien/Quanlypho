import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'from django.db.models import Sum' not in text:
    text = text.replace('from django.db.models import Count, Q', 'from django.db.models import Count, Q, Sum')

menu_logic = '''
    selected_table = request.GET.get('table', '')
    tables = Table.objects.filter(status=Table.Status.AVAILABLE)
    table_obj = None
    remaining_capacity = -1

    if selected_table.isdigit():
        tables = (tables | Table.objects.filter(pk=selected_table, status=Table.Status.OCCUPIED)).distinct()
        table_obj = Table.objects.filter(pk=selected_table).first()

    if table_obj:
        used_capacity = OrderItem.objects.filter(
            order__table=table_obj,
            order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY]
        ).aggregate(total=Sum('quantity'))['total'] or 0
        remaining_capacity = max(0, table_obj.capacity - used_capacity)
        
        if remaining_capacity == 0:
            messages.warning(request, f'Bàn {table_obj.table_number} hiện đã hết chỗ. Vui lòng chọn bàn khác.')
'''

text = re.sub(
    r"\s*selected_table = request\.GET\.get\('table', ''\)\s*tables = Table\.objects\.filter\(status=Table\.Status\.AVAILABLE\)\s*if selected_table\.isdigit\(\):\s*tables = \(tables \| Table\.objects\.filter\(pk=selected_table, status=Table\.Status\.OCCUPIED\)\)\.distinct\(\)",
    menu_logic,
    text
)

text = re.sub(
    r"'selected_table': selected_table,",
    "'selected_table': selected_table,\n        'remaining_capacity': remaining_capacity,\n        'table_obj': table_obj,",
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
