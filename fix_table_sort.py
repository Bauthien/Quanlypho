import re

with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add natural sort helper
if 'def natural_sort_table' not in text:
    sort_helper = '''
import re
def natural_sort_table(tables_qs):
    tables = list(tables_qs)
    tables.sort(key=lambda t: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(t.table_number))])
    return tables
'''
    # insert after imports
    text = text.replace('from django.contrib import messages', 'from django.contrib import messages\n' + sort_helper.strip())

# menu_view
text = re.sub(
    r'tables = \(tables \| Table\.objects\.filter\(pk=selected_table, status=Table\.Status\.OCCUPIED\)\)\.distinct\(\)',
    'tables = (tables | Table.objects.filter(pk=selected_table, status=Table.Status.OCCUPIED)).distinct()\n    tables = natural_sort_table(tables)',
    text
)
# if selected_table wasn't present logic fallback
if 'tables = natural_sort_table(tables)' not in text:
    text = text.replace(
        "tables = Table.objects.filter(status=Table.Status.AVAILABLE)",
        "tables = Table.objects.filter(status=Table.Status.AVAILABLE)\n    tables = natural_sort_table(tables)"
    )

# staff_home
text = re.sub(
    r"'tables': Table\.objects\.all\(\)\.order_by\('table_number'\),",
    "'tables': natural_sort_table(Table.objects.all()),",
    text
)
text = re.sub(
    r"'available_tables': Table\.objects\.filter\(status=Table\.Status\.AVAILABLE\)\.order_by\('table_number'\),",
    "'available_tables': natural_sort_table(Table.objects.filter(status=Table.Status.AVAILABLE)),",
    text
)

# admin_table_list
text = re.sub(
    r"tables = Table\.objects\.all\(\)\.order_by\('table_number'\)",
    "tables = natural_sort_table(Table.objects.all())",
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
