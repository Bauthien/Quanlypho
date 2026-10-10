import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
django.setup()

from pho_app.models import Table
for i in range(1, 16):
    Table.objects.get_or_create(table_number=str(i), defaults={'status': Table.Status.AVAILABLE})
print('Tables created.')
