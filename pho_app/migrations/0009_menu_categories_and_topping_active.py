import re
import unicodedata

from django.db import migrations, models


def classify_existing_drinks(apps, schema_editor):
    MenuItem = apps.get_model('pho_app', 'MenuItem')
    items = MenuItem.objects.using(schema_editor.connection.alias)
    drink_ids = []
    for item in items.only('pk', 'name').iterator():
        name = unicodedata.normalize('NFD', item.name.lower()).replace('đ', 'd')
        name = ''.join(char for char in name if not unicodedata.combining(char))
        if re.search(r'\b(nuoc|tra|ca phe|cafe|bia|coca|pepsi|sinh to)\b', name):
            drink_ids.append(item.pk)
    items.filter(pk__in=drink_ids).update(category='DRINK')


class Migration(migrations.Migration):
    dependencies = [('pho_app', '0008_queue_guest_and_shipping')]

    operations = [
        migrations.AddField(
            model_name='menuitem', name='category',
            field=models.CharField(choices=[('PHO', 'Phở'), ('DRINK', 'Đồ uống')], default='PHO', max_length=10, verbose_name='Nhóm món'),
        ),
        migrations.AddField(
            model_name='topping', name='is_active',
            field=models.BooleanField(default=True, verbose_name='Còn kinh doanh'),
        ),
        migrations.RunPython(classify_existing_drinks, migrations.RunPython.noop),
    ]
