import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace active_order banner
old_banner = '''{% if active_order %}
    <div style="padding: 15px; background: #fff3cd; color: #856404; border-bottom: 1px solid #ffeeba; text-align: center;">
        <strong>Bạn có đơn hàng đang xử lý!</strong><br>
        Trạng thái: {{ active_order.get_order_status_display }}<br>
        <a href="{% url 'order_detail' active_order.id %}" style="color: #856404; text-decoration: underline; font-weight: bold;">Xem tiến độ</a>
    </div>
    {% endif %}'''

new_banner = '''{% if latest_order and latest_order.order_status != 'COMPLETED' and latest_order.order_status != 'CANCELLED' %}
    <div style="padding: 15px; background: #fff3cd; color: #856404; border-bottom: 1px solid #ffeeba; text-align: center;">
        <strong>Bạn có đơn hàng đang xử lý!</strong><br>
        Trạng thái: {{ latest_order.get_order_status_display }}<br>
        <a href="{% url 'order_detail' latest_order.id %}" style="color: #856404; text-decoration: underline; font-weight: bold;">Xem tiến độ</a>
    </div>
    {% endif %}
    {% if latest_order and latest_order.order_status == 'COMPLETED' %}
    <div style="padding: 15px; background: #d4edda; color: #155724; border-bottom: 1px solid #c3e6cb; text-align: center;">
        <strong>Đơn hàng trước đó đã hoàn thành!</strong><br>
        Cảm ơn bạn đã dùng bữa.
    </div>
    <script>
        // Xóa giỏ hàng vì món đã phục vụ xong
        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && key.startsWith('pho-order-cart-v1')) {
                localStorage.removeItem(key);
            }
        }
    </script>
    {% endif %}'''

if '{% if active_order %}' in text:
    text = text.replace(old_banner, new_banner)
    with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
        f.write(text)
