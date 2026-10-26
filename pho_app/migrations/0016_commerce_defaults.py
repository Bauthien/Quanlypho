from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def seed(apps, schema_editor):
    Tier = apps.get_model('pho_app', 'TierConfig')
    for rank, code, name, spend, rate, monthly, nearby, value in [
        (0, 'MEMBER', 'Thành viên', 0, 0, 0, False, 0),
        (1, 'BRONZE', 'Đồng', 500000, 2, 0, False, 100000),
        (2, 'SILVER', 'Bạc', 2000000, 5, 2, False, 300000),
        (3, 'GOLD', 'Vàng', 5000000, 7, 3, True, 400000),
        (4, 'DIAMOND', 'Kim Cương', 12000000, 10, 10, True, 950000),
    ]:
        Tier.objects.get_or_create(code=code, defaults={'rank': rank, 'name': name, 'minimum_spend': spend,
            'good_reviews': 2 if rank else 0, 'discount_percent': rate, 'monthly_shipping': monthly,
            'nearby_shipping': nearby, 'maximum_pack_value': value})
    Voucher = apps.get_model('pho_app', 'Voucher')
    Reward = apps.get_model('pho_app', 'RewardCatalog')
    now = timezone.now()
    for cost, value in [(100, 10000), (200, 20000), (500, 50000)]:
        voucher, _ = Voucher.objects.get_or_create(code=f'POINTS_{value}', defaults={'name': f'Giảm {value:,}đ',
            'kind': 'FIXED', 'value': value, 'starts_at': now, 'ends_at': now + timedelta(days=3650)})
        Reward.objects.get_or_create(voucher=voucher, defaults={'name': f'Voucher {value:,}đ', 'points_cost': cost})
    # Preserve explicit legacy behavior only for existing non-phở products that
    # never had BOM rows. New products default to BOM and require configuration.
    for model in ('MenuItem', 'Topping'):
        Product = apps.get_model('pho_app', model)
        qs = Product.objects.filter(recipes__isnull=True)
        if model == 'MenuItem':
            qs = qs.filter(category='DRINK')
        qs.update(inventory_mode='UNTRACKED')


class Migration(migrations.Migration):
    dependencies = [('pho_app', '0015_browseraccountvault_domainevent_tierconfig_voucher_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
