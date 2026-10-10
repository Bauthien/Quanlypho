import re
with open('pho_app/templates/pho_app/admin/shell.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
        <a class="{% if 'admin_menu' in request.resolver_match.url_name or 'topping' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'admin_menu' %}">
            <i class="fa-solid fa-bowl-food"></i> Thực đơn & topping
        </a>
        <a class="{% if 'table' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'admin_table_list' %}">
            <i class="fa-solid fa-table"></i> Quản lý bàn
        </a>
'''

text = re.sub(
    r'<a class="{% if \'admin_menu\'.*?<\/a>',
    replacement.strip(),
    text,
    flags=re.DOTALL
)

with open('pho_app/templates/pho_app/admin/shell.html', 'w', encoding='utf-8') as f:
    f.write(text)
