import re

with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the clean tag
text = re.sub(
    r'<label>Bàn</label>\s*<select class="form-input" name="table_id" id="tableSelect">\s*<option value="">Chọn bàn trống</option>',
    '<label>Bàn <small class="muted" style="font-weight:normal;">(chọn số có ghi trên bàn của bạn)</small></label>\n                <select class="form-input" name="table_id" id="tableSelect">\n                    <option value="">-- Chọn số bàn --</option>',
    text
)

with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
