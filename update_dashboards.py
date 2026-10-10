import re

files = ['pho_app/templates/pho_app/kitchen/dashboard.html', 'pho_app/templates/pho_app/staff/dashboard.html']
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text = re.sub(
        r'\{\{\s*order\.customer\.full_name\|default:order\.customer\.username\s*\}\}',
        '{{ order.guest_name|default:order.customer.full_name|default:order.customer.username|default:"Khách tại bàn" }}',
        text
    )
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)
