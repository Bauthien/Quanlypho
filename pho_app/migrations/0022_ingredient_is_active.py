from django.db import migrations, models


def ensure_active_column(apps, schema_editor):
    ingredient = apps.get_model('pho_app', 'Ingredient')
    connection = schema_editor.connection
    table = schema_editor.quote_name(ingredient._meta.db_table)
    column = schema_editor.quote_name('is_active')
    if connection.vendor == 'postgresql':
        schema_editor.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} boolean DEFAULT TRUE NOT NULL')
        schema_editor.execute(f'ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT TRUE')
    else:
        with connection.cursor() as cursor:
            exists = any(c.name == 'is_active' for c in connection.introspection.get_table_description(cursor, ingredient._meta.db_table))
        if not exists:
            field = models.BooleanField(default=True, verbose_name='Còn sử dụng')
            field.set_attributes_from_name('is_active')
            schema_editor.add_field(ingredient, field)


class Migration(migrations.Migration):
    dependencies = [('pho_app', '0021_repair_ingredient_is_active_default')]
    operations = [migrations.SeparateDatabaseAndState(
        # Preserve a pre-existing legacy column and its values. Keep its insertion
        # default on rollback, matching the preceding compatibility migration.
        database_operations=[migrations.RunPython(ensure_active_column, migrations.RunPython.noop)],
        state_operations=[migrations.AddField(model_name='ingredient', name='is_active',
                           field=models.BooleanField(default=True, verbose_name='Còn sử dụng'))],
    )]
