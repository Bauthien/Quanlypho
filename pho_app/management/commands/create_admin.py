import os

from django.core.management.base import BaseCommand, CommandError

from pho_app.models import User


class Command(BaseCommand):
    help = 'Tạo hoặc cập nhật tài khoản quản lý (không dùng Django admin).'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default=os.environ.get('ADMIN_INITIAL_PASSWORD'))
        parser.add_argument('--name', default='Quản lý')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        if not password:
            raise CommandError('Cần truyền --password hoặc đặt biến môi trường ADMIN_INITIAL_PASSWORD.')
        full_name = options['name']
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'full_name': full_name,
                'role': User.Role.ADMIN,
                'is_staff': False,
                'is_superuser': False,
            },
        )
        user.full_name = full_name
        user.role = User.Role.ADMIN
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} admin user: {username}'))
