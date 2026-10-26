from django.core.management.base import BaseCommand
from django.utils import timezone

from pho_app.domain import serialized
from pho_app.loyalty import expire_points, evaluate_and_upgrade_tier, process_events
from pho_app.models import LoyaltyAccount, User
from pho_app.stock import expire_orders


class Command(BaseCommand):
    help = 'Hết hạn giữ đơn/điểm, phát quyền lợi định kỳ, xử lý sự kiện hoàn/hoàn tất. Chạy mỗi phút bằng trình lập lịch triển khai.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1000)

    def handle(self, *args, **options):
        limit = max(1, min(options['limit'], 10000))
        expired = expire_orders(limit)
        process_events(limit)
        ids = User.objects.filter(is_active=True, role='CUSTOMER').order_by('pk').values_list('pk', flat=True)
        for user_id in ids.iterator(chunk_size=100):
            self.process_user(user_id)
        # ASCII output also works in Windows task schedulers using legacy code pages.
        self.stdout.write(self.style.SUCCESS(f'Processed {expired} expired orders and due benefits.'))

    @serialized
    def process_user(self, user_id):
        account = evaluate_and_upgrade_tier(user_id)
        expire_points(account)
