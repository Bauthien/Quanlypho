import re
with open('pho_app/templates/pho_app/admin/table_form.html', 'r', encoding='utf-8') as f:
    text = f.read()

cap_field = '''        <div class="form-group" style="margin-top:15px;">
            <label>Số lượng chỗ (Tô) tối đa</label>
            <input type="number" class="form-input" name="capacity" value="{{ table.capacity|default:4 }}" min="1" required>
        </div>'''

text = text.replace('        <div style="display: flex; gap: 10px; margin-top: 20px;">', cap_field + '\n        <div style="display: flex; gap: 10px; margin-top: 20px;">')

with open('pho_app/templates/pho_app/admin/table_form.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update admin_table_create
text = re.sub(
    r"table_number = request\.POST\.get\('table_number', ''\)\.strip\(\)",
    "table_number = request.POST.get('table_number', '').strip()\n        capacity = int(request.POST.get('capacity', 4))",
    text
)

text = re.sub(
    r"table = Table\.objects\.create\(table_number=table_number, status=Table\.Status\.AVAILABLE\)",
    "table = Table.objects.create(table_number=table_number, capacity=capacity, status=Table.Status.AVAILABLE)",
    text
)

# Update admin_table_edit
text = re.sub(
    r"table\.table_number = table_number\s*\n\s*table\.qr_code_url = _generate_table_qr\(request, table\)",
    "table.table_number = table_number\n                table.capacity = capacity\n                table.qr_code_url = _generate_table_qr(request, table)",
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
