import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

validation_logic = '''
        elif order_type == Order.OrderType.DINE_IN:
            try:
                table_pk = int(table_id)
            except (TypeError, ValueError):
                messages.error(request, 'Bàn không hợp lệ.')
                return redirect('menu')
            table = Table.objects.select_for_update().filter(
                pk=table_pk,
                status__in=[Table.Status.AVAILABLE, Table.Status.OCCUPIED],
            ).first()
            if not table:
                messages.error(request, 'Bàn này không còn trống. Vui lòng chọn bàn khác hoặc lấy số xếp hàng.')
                return redirect('menu')

            # Kiểm tra sức chứa
            used_capacity = OrderItem.objects.filter(
                order__table=table,
                order__order_status__in=[Order.OrderStatus.CART, Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING, Order.OrderStatus.READY]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            cart_qty = sum(item[1] for item in resolved_items)
            if used_capacity + cart_qty > table.capacity:
                messages.error(request, f'Bàn {table.table_number} chỉ còn tối đa {max(0, table.capacity - used_capacity)} chỗ (tô). Vui lòng giảm số lượng đặt.')
                return redirect('menu')
'''

text = re.sub(
    r'\s*elif order_type == Order\.OrderType\.DINE_IN:\s*try:\s*table_pk = int\(table_id\)\s*except \(TypeError, ValueError\):\s*messages\.error\(request, \'Bàn không hợp lệ\.\'\)\s*return redirect\(\'menu\'\)\s*table = Table\.objects\.select_for_update\(\)\.filter\(\s*pk=table_pk,\s*status__in=\[Table\.Status\.AVAILABLE, Table\.Status\.OCCUPIED\],\s*\)\.first\(\)\s*if not table:\s*messages\.error\(request, \'Bàn này không còn trống\. Vui lòng chọn bàn khác hoặc lấy số xếp hàng\.\'\)\s*return redirect\(\'menu\'\)',
    validation_logic,
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
