import io
with io.open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('TAn c a bn (TA1y ch?n)', 'Tên của bạn (Tùy chọn)')
text = text.replace('? nhAn viAn d. g?i mA3n', 'Để nhân viên dễ gọi món')

with io.open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
