import re
with open('pho_app/templates/pho_app/customer/order_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove old unconditional clear cart script
text = re.sub(
    r'// Xóa tất cả các giỏ hàng.*?localStorage\.removeItem\(key\);\n\s*}\n\s*}',
    '',
    text,
    flags=re.DOTALL
)

# Insert it conditionally when order is READY or COMPLETED
replacement = '''{% elif order.order_status == 'READY' or order.order_status == 'COMPLETED' %}
    <section class="panel" style="background-color: #d4edda; border-color: #c3e6cb;">
        <h2 style="color: #155724;">Đơn hàng của bạn đã hoàn thành!</h2>
        <p style="color: #155724;">Bếp đã chuẩn bị xong món. Vui lòng nhận món và thưởng thức!</p>
        <a class="checkout-btn" href="{% url 'menu' %}">Về trang chủ</a>
    </section>
    <script>
        // Xóa giỏ hàng vì đơn đã hoàn thành
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('pho-order-cart-v1')) {
                localStorage.removeItem(key);
            }
        }
    </script>'''

text = re.sub(
    r'{%\s*elif\s+order\.order_status\s*==\s*\'READY\'\s*or\s*order\.order_status\s*==\s*\'COMPLETED\'\s*%}.*?<a class="checkout-btn" href="{% url \'menu\' %}">Về trang chủ</a>\n\s*</section>',
    replacement,
    text,
    flags=re.DOTALL
)

with open('pho_app/templates/pho_app/customer/order_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)
