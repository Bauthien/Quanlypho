import re

with open('pho_app/templates/pho_app/customer/order_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add "Đơn hàng của bạn đã hoàn thành!" message
text = re.sub(
    r'{%\s*elif\s+order.payment_status\s*==\s*\'PAID\'\s*%}.*?(?={%\s*else\s*%})',
    '''{% elif order.order_status == 'READY' or order.order_status == 'COMPLETED' %}
    <section class="panel" style="background-color: #d4edda; border-color: #c3e6cb;">
        <h2 style="color: #155724;">Đơn hàng của bạn đã hoàn thành!</h2>
        <p style="color: #155724;">Bếp đã chuẩn bị xong món. Vui lòng nhận món và thưởng thức!</p>
        <a class="checkout-btn" href="{% url 'menu' %}">Về trang chủ</a>
    </section>
    {% elif order.payment_status == 'PAID' %}
    <section class="panel"><h2>Đã nhận thanh toán</h2><p>Đơn hiện ở trạng thái: <strong>{{ order.get_order_status_display }}</strong>. Tải lại trang để xem cập nhật mới nhất.</p><a class="ghost-btn primary" href="{% url 'order_detail' order.id %}">Cập nhật trạng thái</a></section>
    ''',
    text,
    flags=re.DOTALL
)

# 2. Add simulate payment button to VietQR
text = re.sub(
    r'(<p class="muted">Đơn chỉ được chuyển xuống bếp.*?)</p>',
    r'\1</p>\n            <form method="POST" action="{% url \'simulate_vietqr_payment\' order.id %}">{% csrf_token %}<button type="submit" class="ghost-btn primary" style="margin-top: 10px; width: 100%;">[DEV] Mô phỏng quét QR thành công</button></form>',
    text
)

# 3. Add script to clear cart
script_clear_cart = '''
<script>
    // Xóa giỏ hàng sau khi đã tạo đơn thành công
    localStorage.removeItem('pho_cart');
</script>
'''

text = re.sub(
    r'{%\s*block\s+extra_js\s*%}',
    '{% block extra_js %}\n' + script_clear_cart,
    text
)

with open('pho_app/templates/pho_app/customer/order_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)
