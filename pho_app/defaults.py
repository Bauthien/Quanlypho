"""Idempotent built-in configuration, also restored after a Django test flush."""
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_builtin_configuration(sender, using, **kwargs):
    if sender.name != 'pho_app':
        return
    from .models import CustomizationOption, TierConfig
    for category, names in [('BROTH', ['Nước dùng trong', 'Nước dùng béo']),
        ('VEGGIE', ['Có hành, giá sống', 'Không hành', 'Không giá', 'Giá chín']),
        ('NOODLE', ['Bánh phở thường', 'Ít bánh', 'Nhiều bánh'])]:
        if not CustomizationOption.objects.using(using).filter(category=category).exists():
            for name in names:
                CustomizationOption.objects.using(using).get_or_create(category=category, name=name)
    for rank, code, name, spend, rate, monthly, nearby, value in [
        (0, 'MEMBER', 'Thành viên', 0, 0, 0, False, 0), (1, 'BRONZE', 'Đồng', 500000, 2, 0, False, 100000),
        (2, 'SILVER', 'Bạc', 2000000, 5, 2, False, 300000), (3, 'GOLD', 'Vàng', 5000000, 7, 3, True, 400000),
        (4, 'DIAMOND', 'Kim Cương', 12000000, 10, 10, True, 950000)]:
        TierConfig.objects.using(using).get_or_create(code=code, defaults={'rank': rank, 'name': name,
            'minimum_spend': spend, 'good_reviews': 2 if rank else 0, 'discount_percent': rate,
            'monthly_shipping': monthly, 'nearby_shipping': nearby, 'maximum_pack_value': value})
