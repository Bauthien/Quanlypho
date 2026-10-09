from django.db import migrations, models
import django.db.models.deletion


def add_default_customizations(apps, schema_editor):
    CustomizationOption = apps.get_model('pho_app', 'CustomizationOption')
    defaults = [
        ('BROTH', 'Nước dùng trong'),
        ('BROTH', 'Nước dùng béo'),
        ('VEGGIE', 'Có hành, giá sống'),
        ('VEGGIE', 'Không hành'),
        ('VEGGIE', 'Không giá'),
        ('VEGGIE', 'Giá chín'),
        ('NOODLE', 'Bánh phở thường'),
        ('NOODLE', 'Ít bánh'),
        ('NOODLE', 'Nhiều bánh'),
    ]
    for category, name in defaults:
        CustomizationOption.objects.get_or_create(category=category, name=name)


def remove_default_customizations(apps, schema_editor):
    CustomizationOption = apps.get_model('pho_app', 'CustomizationOption')
    names = [
        'Nước dùng trong', 'Nước dùng béo', 'Có hành, giá sống', 'Không hành',
        'Không giá', 'Giá chín', 'Bánh phở thường', 'Ít bánh', 'Nhiều bánh',
    ]
    CustomizationOption.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pho_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='queueticket',
            name='table',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='queue_tickets', to='pho_app.table', verbose_name='Bàn được gọi'),
        ),
        migrations.AddField(
            model_name='order',
            name='queue_ticket',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='pho_app.queueticket', verbose_name='Vé xếp hàng'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('CART', 'Chờ thanh toán'), ('DELIVERING', 'Đang giao hàng'), ('PENDING_KITCHEN', 'Đang gửi Bếp'), ('COOKING', 'Bếp đang làm'), ('READY', 'Đã xong (Chờ bưng/Giao)'), ('COMPLETED', 'Hoàn tất'), ('CANCELLED', 'Đã hủy')], default='CART', max_length=20, verbose_name='Trạng thái đơn'),
        ),
        migrations.RunPython(add_default_customizations, remove_default_customizations),
    ]
