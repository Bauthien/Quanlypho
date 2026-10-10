import re
with open('pho_app/templates/pho_app/staff/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
                    <td>
                        <div style="display: flex; gap: 8px;">
                            <form method="post" action="{% url 'confirm_cash' order.id %}">
                                {% csrf_token %}
                                <button class="ghost-btn primary" type="submit">Đã nhận tiền</button>
                            </form>
                            <form method="post" action="{% url 'cancel_order' order.id %}" onsubmit="return confirm('Bạn có chắc chắn muốn hủy đơn này không?');">
                                {% csrf_token %}
                                <button class="ghost-btn" style="color: red; border-color: red;" type="submit">Hủy đơn</button>
                            </form>
                        </div>
                    </td>
'''
if 'cancel_order' not in text:
    text = re.sub(
        r'<td>\s*<form method="post" action="{% url \'confirm_cash\' order\.id %}">\s*{% csrf_token %}\s*<button class="ghost-btn primary" type="submit">Đã nhận tiền</button>\s*</form>\s*</td>',
        replacement,
        text
    )
    with open('pho_app/templates/pho_app/staff/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
