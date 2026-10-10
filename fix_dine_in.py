import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Don't change table to CLEANING when served
text = re.sub(
    r'if order\.table_id:\s*Table\.objects\.filter\(pk=order\.table_id\)\.update\(status=Table\.Status\.CLEANING\)\s*messages\.success\(request,.*?Bàn chuyển sang trạng thái cần dọn.*?\'\)',
    'messages.success(request, f\'Đã phục vụ xong đơn {order.order_code}. Khách đang dùng bữa.\')',
    text
)

# Allow free_table to free OCCUPIED tables as well
text = text.replace(
    'status=Table.Status.CLEANING',
    'status__in=[Table.Status.CLEANING, Table.Status.OCCUPIED]'
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
