import re
with open('pho_app/templates/pho_app/admin/table_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = '''                    <td>
                        {% if table.qr_code_url %}
                        <a href="{{ table.qr_code_url }}" target="_blank">
                            <img src="{{ table.qr_code_url }}" alt="QR" width="50" height="50" style="border-radius: 4px; border: 1px solid #ccc;">
                        </a>
                        {% else %}'''

new_block = '''                    <td>
                        {% if table.qr_code_url %}
                        <div style="display: flex; flex-direction: column; align-items: center; gap: 5px;">
                            <a href="{{ table.qr_code_url }}" target="_blank" title="Xem ảnh QR lớn">
                                <img src="{{ table.qr_code_url }}" alt="QR" width="50" height="50" style="border-radius: 4px; border: 1px solid #ccc;">
                            </a>
                            <a href="{% url 'menu' %}?table={{ table.id }}" target="_blank" style="font-size: 0.8rem; color: #007bff; text-decoration: underline; white-space: nowrap;">
                                <i class="fa-solid fa-link"></i> Link Đặt Món
                            </a>
                        </div>
                        {% else %}'''

if old_block in text:
    text = text.replace(old_block, new_block)
else:
    print("Block not found. Printing current table content:")
    start = text.find('<td>\n                        {% if table.qr_code_url %}')
    print(text[start:start+500])

with open('pho_app/templates/pho_app/admin/table_list.html', 'w', encoding='utf-8') as f:
    f.write(text)
