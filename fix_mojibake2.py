import io, re
with io.open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r'{% if not request\.user\.is_authenticated %}.*?{% endif %}',
    '''{% if not request.user.is_authenticated %}
                <div class="form-group" style="margin-top:15px;">
                    <label>Tên của bạn (Tùy chọn)</label>
                    <input type="text" name="guest_name" class="form-input" placeholder="Để nhân viên dễ gọi món">
                </div>
                {% endif %}''',
    text,
    flags=re.DOTALL
)

with io.open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
