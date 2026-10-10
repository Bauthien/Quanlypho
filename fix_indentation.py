import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_indent = '''    messages.info(request, f'Đơn {order.order_code} đã tạo. Trạng thái: chờ thanh toán.')
        if not request.user.is_authenticated:
            guest_orders = request.session.get('guest_orders', [])
            guest_orders.append(order.pk)
            request.session['guest_orders'] = guest_orders
            request.session['latest_order_id'] = order.pk
        return redirect('order_detail', order_id=order.pk)'''

good_indent = '''    messages.info(request, f'Đơn {order.order_code} đã tạo. Trạng thái: chờ thanh toán.')
    if not request.user.is_authenticated:
        guest_orders = request.session.get('guest_orders', [])
        guest_orders.append(order.pk)
        request.session['guest_orders'] = guest_orders
        request.session['latest_order_id'] = order.pk
    return redirect('order_detail', order_id=order.pk)'''

text = text.replace(bad_indent, good_indent)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
