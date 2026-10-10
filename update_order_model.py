import re
with open('pho_app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Tên khách (nếu không đăng nhập)")
'''
text = re.sub(
    r'customer = models\.ForeignKey\(User, on_delete=models\.SET_NULL, null=True, blank=True, verbose_name="Khách hàng"\)\s*',
    replacement,
    text
)

with open('pho_app/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
