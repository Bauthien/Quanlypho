import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

guest_name_field = '''
                {% if not request.user.is_authenticated %}
                <div class="form-group" style="margin-top:15px;">
                    <label>Tên của bạn (Tùy chọn)</label>
                    <input type="text" name="guest_name" class="form-input" placeholder="Để nhân viên dễ gọi món">
                </div>
                {% endif %}
'''

if 'name="guest_name"' not in text:
    text = text.replace(
        '<input type="hidden" name="cart" id="cartPayload">',
        '<input type="hidden" name="cart" id="cartPayload">' + guest_name_field
    )
    with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
        f.write(text)
