import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''@require_POST
def simulate_vietqr_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, payment_method=Order.PaymentMethod.VIETQR)
    if order.customer:
        if not request.user.is_authenticated or order.customer != request.user:
            return redirect('menu')
    else:
        if order.pk not in request.session.get('guest_orders', []):
            return redirect('menu')
    if order.payment_status == Order.PaymentStatus.PENDING:
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
        messages.success(request, 'Đã mô phỏng thanh toán thành công! Đơn đã chuyển xuống bếp.')
    return redirect('order_detail', order_id=order.pk)
'''

text = re.sub(
    r'@require_POST\ndef simulate_vietqr_payment\(request, order_id\):.*?return redirect\(\'order_detail\', order_id=order\.pk\)',
    replacement.strip(),
    text,
    flags=re.DOTALL
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
