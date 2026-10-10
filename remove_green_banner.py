import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the green completed banner and script from menu.html
text = re.sub(
    r'{% if latest_order and latest_order\.order_status == \'COMPLETED\' %}.*?{% endif %}',
    '',
    text,
    flags=re.DOTALL
)

with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
