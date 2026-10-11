from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pho_app', '0007_order_is_cleared'),
    ]

    operations = [
        migrations.AddField(
            model_name='queueticket',
            name='guest_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Tên khách (không đăng nhập)'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_distance_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Khoảng cách giao (km)'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_code',
            field=models.CharField(blank=True, max_length=50, verbose_name='Mã vận đơn'),
        ),
    ]
