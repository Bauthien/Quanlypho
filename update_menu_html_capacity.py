import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

cap_warning = '''
    {% if table_obj and remaining_capacity == 0 %}
    <div style="padding: 15px; background: #f8d7da; color: #721c24; border-bottom: 1px solid #f5c6cb; text-align: center;">
        <strong>Bàn {{ table_obj.table_number }} hiện đã hết chỗ!</strong><br>
        Quý khách vui lòng liên hệ nhân viên hoặc chọn bàn khác.
    </div>
    {% elif table_obj %}
    <div style="padding: 10px; background: #e2e3e5; color: #383d41; border-bottom: 1px solid #d6d8db; text-align: center; font-size: 0.9rem;">
        Bàn {{ table_obj.table_number }} - Còn {{ remaining_capacity }} chỗ (tô).
    </div>
    {% endif %}
'''

if 'remaining_capacity' not in text:
    text = text.replace(
        '<div class="workspace" style="display: flex; height: calc(100vh - 60px);">',
        cap_warning + '\n<div class="workspace" style="display: flex; height: calc(100vh - 60px);">'
    )
    with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
        f.write(text)
