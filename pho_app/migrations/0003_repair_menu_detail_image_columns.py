from django.db import migrations


def ensure_menu_detail_image_columns(apps, schema_editor):
    MenuItem = apps.get_model('pho_app', 'MenuItem')
    table = MenuItem._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    for field_name in ('image_detail_1', 'image_detail_2'):
        field = MenuItem._meta.get_field(field_name)
        if field.column not in existing_columns:
            schema_editor.add_field(MenuItem, field)
            existing_columns.add(field.column)


class Migration(migrations.Migration):

    dependencies = [
        ('pho_app', '0002_order_queue_delivery_and_customizations'),
    ]

    operations = [
        migrations.RunPython(ensure_menu_detail_image_columns, migrations.RunPython.noop),
    ]
