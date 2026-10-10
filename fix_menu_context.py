import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "'tables': tables.order_by('table_number'),",
    "'tables': tables,"
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
