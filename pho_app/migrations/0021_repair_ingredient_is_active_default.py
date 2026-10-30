from django.db import migrations


def repair_legacy_is_active_default(apps, schema_editor):
    """Allow inserts when an older database has an extra required active flag."""
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return

    table = apps.get_model('pho_app', 'Ingredient')._meta.db_table
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, table)

    if any(column.name == 'is_active' for column in columns):
        schema_editor.execute(
            'ALTER TABLE {} ALTER COLUMN {} SET DEFAULT TRUE'.format(
                schema_editor.quote_name(table), schema_editor.quote_name('is_active'),
            )
        )


class Migration(migrations.Migration):
    dependencies = [
        ('pho_app', '0020_recipe_groups'),
    ]

    operations = [
        # Keep the compatibility default on rollback, too: removing it would
        # reintroduce failed inserts. Existing row values are never changed.
        migrations.RunPython(repair_legacy_is_active_default, migrations.RunPython.noop),
    ]
