import re
import unicodedata

from django.db import migrations, models


def classify_existing_drinks(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('SELECT id, name FROM pho_app_menuitem')
        for item_id, name in cursor.fetchall():
            normalized_name = unicodedata.normalize('NFD', (name or '').lower()).replace('đ', 'd')
            normalized_name = ''.join(char for char in normalized_name if not unicodedata.combining(char))
            if re.search(r'\b(nuoc|tra|ca phe|cafe|bia|coca|pepsi|sinh to)\b', normalized_name):
                cursor.execute('UPDATE pho_app_menuitem SET category = %s WHERE id = %s', ['DRINK', item_id])


class Migration(migrations.Migration):
    dependencies = [('pho_app', '0008_queue_guest_and_shipping')]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE pho_app_menuitem
                ADD COLUMN IF NOT EXISTS category varchar(10) DEFAULT 'PHO' NOT NULL;

                ALTER TABLE pho_app_topping
                ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE pho_app_topping DROP COLUMN IF EXISTS is_active;
                ALTER TABLE pho_app_menuitem DROP COLUMN IF EXISTS category;
            """,
        ),
        migrations.RunPython(classify_existing_drinks, migrations.RunPython.noop),
    ]
