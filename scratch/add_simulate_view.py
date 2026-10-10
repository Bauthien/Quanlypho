import re

# 1. Update urls.py
with open('pho_app/urls.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'simulate_vietqr_payment' not in text:
    text = text.replace(
        "path('thanh-toan/vietqr/webhook/', views.vietqr_webhook, name='vietqr_webhook'),",
        "path('thanh-toan/vietqr/webhook/', views.vietqr_webhook, name='vietqr_webhook'),\n    path('thanh-toan/vietqr/simulate/<int:order_id>/', views.simulate_vietqr_payment, name='simulate_vietqr_payment'),"
    )
    with open('pho_app/urls.py', 'w', encoding='utf-8') as f:
        f.write(text)

# 2. Add the view to views.py
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    views_text = f.read()

if 'def simulate_vietqr_payment' not in views_text:
    simulate_view = """
@login_required
@require_POST
def simulate_vietqr_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user, payment_method=Order.PaymentMethod.VIETQR)
    if order.payment_status == Order.PaymentStatus.PENDING:
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
        messages.success(request, 'Đã mô phỏng thanh toán thành công! Đơn đã chuyển xuống bếp.')
    return redirect('order_detail', order_id=order.pk)
"""
    with open('pho_app/views.py', 'a', encoding='utf-8') as f:
        f.write(simulate_view)

