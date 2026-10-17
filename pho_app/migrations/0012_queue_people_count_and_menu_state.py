from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pho_app', '0011_review'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE pho_app_menuitem
                            ADD COLUMN IF NOT EXISTS category varchar(10) DEFAULT 'PHO' NOT NULL;
                        ALTER TABLE pho_app_topping
                            ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT TRUE NOT NULL;
                        ALTER TABLE pho_app_queueticket
                            ADD COLUMN IF NOT EXISTS people_count integer DEFAULT 1 NOT NULL;
                        UPDATE pho_app_queueticket SET people_count = 1 WHERE people_count IS NULL;
                        ALTER TABLE pho_app_queueticket
                            ALTER COLUMN people_count SET DEFAULT 1;
                        ALTER TABLE pho_app_queueticket
                            ALTER COLUMN people_count SET NOT NULL;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='menuitem',
                    name='category',
                    field=models.CharField(
                        choices=[('PHO', 'Phở'), ('DRINK', 'Đồ uống')],
                        default='PHO',
                        max_length=10,
                        verbose_name='Nhóm món',
                    ),
                ),
                migrations.AddField(
                    model_name='topping',
                    name='is_active',
                    field=models.BooleanField(default=True, verbose_name='Còn kinh doanh'),
                ),
                migrations.AddField(
                    model_name='queueticket',
                    name='people_count',
                    field=models.PositiveIntegerField(default=1, verbose_name='Số người'),
                ),
            ],
        ),
    ]
