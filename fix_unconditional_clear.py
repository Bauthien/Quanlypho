import re
with open('pho_app/templates/pho_app/customer/order_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make it clear unconditionally on order_detail load
replacement_script = '''{% block extra_js %}
<script>
    // Xóa giỏ hàng ngay khi đơn hàng đã được tạo thành công
    for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith('pho-order-cart-v1')) {
            localStorage.removeItem(key);
        }
    }
</script>'''

text = re.sub(
    r'{%\s*block\s+extra_js\s*%}',
    replacement_script,
    text
)

# Remove the conditional clear script from the READY section to avoid duplicates
text = re.sub(
    r'<script>\s*// Xóa giỏ hàng vì đơn đã hoàn thành.*?<\/script>',
    '',
    text,
    flags=re.DOTALL
)

with open('pho_app/templates/pho_app/customer/order_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)
