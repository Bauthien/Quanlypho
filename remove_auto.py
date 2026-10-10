import re
with open('pho_app/templates/pho_app/customer/order_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove auto-simulate script
text = re.sub(
    r'{% if order\.payment_status == \'PENDING\' and order\.payment_method == \'VIETQR\' %}\s*<script>\s*// DEV: Tự động mô phỏng.*?<\/script>\s*{% endif %}',
    '',
    text,
    flags=re.DOTALL
)

# Rename the button
text = text.replace(
    '[DEV] Mô phỏng quét QR thành công',
    'Chuyển tiếp (Test - Đã chuyển khoản)'
)

with open('pho_app/templates/pho_app/customer/order_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)
