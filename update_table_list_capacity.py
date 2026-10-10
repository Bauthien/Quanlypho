import re
with open('pho_app/templates/pho_app/admin/table_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add header
text = text.replace('<th>Số Bàn / Tên Bàn</th>', '<th>Số Bàn / Tên Bàn</th>\n                    <th>Sức chứa</th>')
# Add column data
text = text.replace('<td>Bàn {{ table.table_number }}</td>', '<td>Bàn {{ table.table_number }}</td>\n                    <td>{{ table.capacity }} tô</td>')

with open('pho_app/templates/pho_app/admin/table_list.html', 'w', encoding='utf-8') as f:
    f.write(text)
