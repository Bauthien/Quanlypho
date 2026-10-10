import re
with open('pho_app/templates/pho_app/admin/table_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

header_rep = '''<th>Số Bàn / Tên Bàn</th>
                    <th>Mã QR</th>
                    <th>Trạng thái hiện tại</th>'''
text = text.replace('<th>Số Bàn / Tên Bàn</th>\n                    <th>Trạng thái hiện tại</th>', header_rep)

row_rep = '''<td>Bàn {{ table.table_number }}</td>
                    <td>
                        {% if table.qr_code_url %}
                        <a href="{{ table.qr_code_url }}" target="_blank">
                            <img src="{{ table.qr_code_url }}" alt="QR" width="50" height="50" style="border-radius: 4px; border: 1px solid #ccc;">
                        </a>
                        {% else %}
                        <form method="post" action="{% url 'admin_table_edit' table.id %}" style="display:inline;">
                            {% csrf_token %}
                            <input type="hidden" name="table_number" value="{{ table.table_number }}">
                            <button type="submit" class="ghost-btn" style="padding: 2px 5px; font-size: 0.8rem;">Tạo QR</button>
                        </form>
                        {% endif %}
                    </td>
                    <td>{{ table.get_status_display }}</td>'''
text = text.replace('<td>Bàn {{ table.table_number }}</td>\n                    <td>{{ table.get_status_display }}</td>', row_rep)

with open('pho_app/templates/pho_app/admin/table_list.html', 'w', encoding='utf-8') as f:
    f.write(text)
