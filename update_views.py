import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

cancel_view = """
@staff_required
@require_POST
def cancel_cash_order(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id, payment_method=Order.PaymentMethod.CASH)
        if order.payment_status != Order.PaymentStatus.PENDING or order.order_status != Order.OrderStatus.CART:
            messages.info(request, 'Đơn này đã được xử lý trước đó.')
            return redirect('staff_home')
        order.payment_status = Order.PaymentStatus.FAILED
        order.order_status = Order.OrderStatus.CANCELLED
        order.save(update_fields=['payment_status', 'order_status', 'updated_at'])
    messages.success(request, f'Đã hủy đơn {order.order_code}.')
    return redirect('staff_home')
"""
if 'def cancel_cash_order' not in text:
    text = text + cancel_view

vietqr_func_regex = r'def _vietqr_image_url\(order\):[\s\S]*?return f\'https://img\.vietqr\.io/image/\{bank\}-\{account\}-compact2\.png\?\{query\}\''
replacement_vietqr = '''def _vietqr_image_url(order):
    bank = getattr(settings, 'VIETQR_BANK_ID', '') or '970415'
    account = getattr(settings, 'VIETQR_ACCOUNT_NO', '') or '113366668888'
    account_name = getattr(settings, 'VIETQR_ACCOUNT_NAME', '') or 'TEST PHO GIA TRUYEN'
    query = urlencode({
        'amount': int(order.total_amount + order.delivery_fee),
        'addInfo': order.order_code,
        'accountName': account_name,
    })
    return f'https://img.vietqr.io/image/{bank}-{account}-compact2.png?{query}'\n'''

text = re.sub(vietqr_func_regex, replacement_vietqr, text)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
