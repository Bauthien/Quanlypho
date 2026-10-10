import os

with open('pho_app/urls.py', 'r', encoding='utf-8') as f:
    urls_text = f.read()

if 'admin_table_list' not in urls_text:
    urls_text = urls_text.replace(
        "path('quan-ly/', views.admin_home, name='admin_home'),",
        "path('quan-ly/', views.admin_home, name='admin_home'),\n    path('quan-ly/ban/', views.admin_table_list, name='admin_table_list'),\n    path('quan-ly/ban/them/', views.admin_table_create, name='admin_table_create'),\n    path('quan-ly/ban/<int:table_id>/sua/', views.admin_table_edit, name='admin_table_edit'),\n    path('quan-ly/ban/<int:table_id>/xoa/', views.admin_table_delete, name='admin_table_delete'),"
    )
    with open('pho_app/urls.py', 'w', encoding='utf-8') as f:
        f.write(urls_text)

views_append = '''
@admin_required
def admin_table_list(request):
    tables = Table.objects.all().order_by('table_number')
    return render(request, 'pho_app/admin/table_list.html', {'tables': tables})

@admin_required
def admin_table_create(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        if table_number:
            Table.objects.create(table_number=table_number, status=Table.Status.AVAILABLE)
            messages.success(request, 'Đã thêm bàn mới.')
            return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html')

@admin_required
def admin_table_edit(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        if table_number:
            table.table_number = table_number
            table.save()
            messages.success(request, 'Đã cập nhật bàn.')
            return redirect('admin_table_list')
    return render(request, 'pho_app/admin/table_form.html', {'table': table})

@admin_required
@require_POST
def admin_table_delete(request, table_id):
    table = get_object_or_404(Table, pk=table_id)
    table.delete()
    messages.success(request, 'Đã xóa bàn.')
    return redirect('admin_table_list')
'''

with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    views_text = f.read()

if 'admin_table_list' not in views_text:
    with open('pho_app/views.py', 'a', encoding='utf-8') as f:
        f.write(views_append)
