import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

create_replace = '''
@admin_required
def admin_table_create(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number', '').strip()
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exists():
                messages.error(request, f'Lỗi: Tên bàn "{table_number}" đã tồn tại! Vui lòng chọn tên khác.')
            else:
                Table.objects.create(table_number=table_number, status=Table.Status.AVAILABLE)
                messages.success(request, 'Đã thêm bàn mới thành công.')
                return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html')
'''

edit_replace = '''
@admin_required
def admin_table_edit(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    if request.method == 'POST':
        table_number = request.POST.get('table_number', '').strip()
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exclude(pk=table.pk).exists():
                messages.error(request, f'Lỗi: Tên bàn "{table_number}" đã tồn tại ở bàn khác!')
            else:
                table.table_number = table_number
                table.save()
                messages.success(request, 'Đã cập nhật bàn thành công.')
                return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html', {'table': table})
'''

# Use regex to find and replace the functions
text = re.sub(
    r'@admin_required\s*\n\s*def admin_table_create.*?return render\(request, \'pho_app/admin/table_form\.html\'\)',
    create_replace.strip(),
    text,
    flags=re.DOTALL
)

text = re.sub(
    r'@admin_required\s*\n\s*def admin_table_edit.*?return render\(request, \'pho_app/admin/table_form\.html\', {\'table\': table}\)',
    edit_replace.strip(),
    text,
    flags=re.DOTALL
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
