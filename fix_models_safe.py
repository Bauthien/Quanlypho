import re
with open('pho_app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Put back Table CharField fix
text = re.sub(
    r'table_number\s*=\s*models\.IntegerField\(unique=True,\s*verbose_name="S[^"]*"\)',
    'table_number = models.CharField(max_length=50, unique=True, verbose_name="Số bàn")',
    text
)

# Add guest_name to Order only!
# Find the exact lines in Order
order_regex = r'(class Order\(gis_models\.Model\):[\s\S]*?)(customer = models\.ForeignKey\(User, on_delete=models\.SET_NULL, null=True, blank=True, verbose_name="Khách hàng"\))'
replacement = r'\1\2\n    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Tên khách (nếu không đăng nhập)")'

# Use python string find instead of regex to avoid unicode issues
idx = text.find('class Order(gis_models.Model):')
if idx != -1:
    customer_idx = text.find('customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")', idx)
    if customer_idx != -1:
        end_idx = customer_idx + len('customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")')
        new_text = text[:end_idx] + '\n    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Tên khách (nếu không đăng nhập)")' + text[end_idx:]
        text = new_text

with open('pho_app/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
