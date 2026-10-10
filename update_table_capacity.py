import re
with open('pho_app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''    table_number = models.CharField(max_length=50, unique=True, verbose_name="Số bàn")
    capacity = models.IntegerField(default=4, verbose_name="Số lượng chỗ (Tô) tối đa")'''

text = re.sub(
    r'\s*table_number = models\.CharField\(max_length=50, unique=True, verbose_name="Số bàn"\)',
    '\n' + replacement,
    text
)

with open('pho_app/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
