import re
with open('pho_app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'table_number = models.IntegerField(unique=True, verbose_name="Số bàn")',
    'table_number = models.CharField(max_length=50, unique=True, verbose_name="Số bàn")'
)

# Also handle the encoded version just in case
text = text.replace(
    'table_number = models.IntegerField(unique=True, verbose_name="S\u00f4\u0300 bA\u00a2n")',
    'table_number = models.CharField(max_length=50, unique=True, verbose_name="S\u00f4\u0300 bA\u00a2n")'
)
# Wait, let's use regex for safety
text = re.sub(
    r'table_number\s*=\s*models\.IntegerField\(unique=True,\s*verbose_name=.*?(\)|\]|\n)',
    'table_number = models.CharField(max_length=50, unique=True, verbose_name="Số bàn")\\n',
    text
)

with open('pho_app/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
