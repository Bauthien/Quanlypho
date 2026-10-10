import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add active order banner inside cart sidebar
if '{% if active_order %}' not in text:
    replacement = '''<aside class="cart-sidebar" id="cartSidebar">
    {% if active_order %}
    <div style="padding: 15px; background: #fff3cd; color: #856404; border-bottom: 1px solid #ffeeba; text-align: center;">
        <strong>Bạn có đơn hàng đang xử lý!</strong><br>
        Trạng thái: {{ active_order.get_order_status_display }}<br>
        <a href="{% url 'order_detail' active_order.id %}" style="color: #856404; text-decoration: underline; font-weight: bold;">Xem tiến độ</a>
    </div>
    {% endif %}
    <div class="cart-header">'''
    
    text = text.replace(
        '<aside class="cart-sidebar" id="cartSidebar">\n    <div class="cart-header">',
        replacement
    )
    with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
        f.write(text)
