import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

qr_replace = '''
            if not has_other_active:
                Table.objects.filter(pk=order.table_id).update(status=Table.Status.AVAILABLE)

    messages.success(request, f'Đã hủy đơn {order.order_code}.')
    return redirect('staff_home')

def _generate_table_qr(request, table):
    # Dùng API qrserver.com để tạo mã QR
    from urllib.parse import urlencode
    domain = request.build_absolute_uri('/')[:-1] # Bỏ dấu / ở cuối
    menu_url = f"{domain}/thuc-don/?table={table.id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={menu_url}"
    return qr_url

@admin_required
def admin_table_list(request):
'''

text = re.sub(
    r'\s*if not has_other_active:\s*Table\.objects\.filter\(pk=order\.table_id\)\.update\(status=Table\.Status\.AVAILABLE\)\s*messages\.success\(request, f\'Đã hủy đơn {order\.order_code}\.\'\)\s*return redirect\(\'staff_home\'\)\s*@admin_required\s*\n\s*def admin_table_list\(request\):',
    qr_replace,
    text
)

# In create
create_qr = '''
            else:
                table = Table.objects.create(table_number=table_number, status=Table.Status.AVAILABLE)
                table.qr_code_url = _generate_table_qr(request, table)
                table.save(update_fields=['qr_code_url'])
                messages.success(request, 'Đã thêm bàn mới thành công.')
'''
text = re.sub(
    r'else:\s*Table\.objects\.create\(table_number=table_number, status=Table\.Status\.AVAILABLE\)\s*messages\.success\(request, \'Đã thêm bàn mới thành công\.\'\)',
    create_qr.strip(),
    text
)

# In edit
edit_qr = '''
            else:
                table.table_number = table_number
                table.qr_code_url = _generate_table_qr(request, table)
                table.save()
                messages.success(request, 'Đã cập nhật bàn thành công.')
'''
text = re.sub(
    r'else:\s*table\.table_number = table_number\s*table\.save\(\)\s*messages\.success\(request, \'Đã cập nhật bàn thành công\.\'\)',
    edit_qr.strip(),
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
