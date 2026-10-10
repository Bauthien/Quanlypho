import io, re
with io.open('pho_app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'is_cleared = models.BooleanField' not in text:
    text = text.replace(
        'payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Trạng thái thanh toán")',
        'payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Trạng thái thanh toán")\n    is_cleared = models.BooleanField(default=False, verbose_name="Đã dọn bàn")'
    )
    with io.open('pho_app/models.py', 'w', encoding='utf-8') as f:
        f.write(text)
