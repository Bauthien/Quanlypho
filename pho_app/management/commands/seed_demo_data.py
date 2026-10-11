import os
import shutil
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from pho_app.models import (
    User, Table, MenuItem, Topping, CustomizationOption,
    Ingredient, Recipe
)

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu mẫu (Tài khoản, Bàn ăn, Thực đơn, Topping, Nguyên liệu kho).'

    def handle(self, *args, **options):
        self.stdout.write("Khởi tạo thư mục media và sao chép ảnh mẫu...")
        media_root = Path(settings.MEDIA_ROOT)
        menu_media_dir = media_root / 'menu_items'
        toppings_media_dir = media_root / 'toppings'
        menu_media_dir.mkdir(parents=True, exist_ok=True)
        toppings_media_dir.mkdir(parents=True, exist_ok=True)

        dist_images = Path(settings.BASE_DIR) / 'dist' / 'images'
        if dist_images.exists():
            for img in dist_images.glob('*.*'):
                shutil.copy2(img, menu_media_dir / img.name)
                shutil.copy2(img, toppings_media_dir / img.name)

        # 1. Tạo tài khoản mẫu
        self.stdout.write("Tạo tài khoản mẫu...")
        users_info = [
            ('admin', 'admin123', User.Role.ADMIN, 'Quản Trị Viên'),
            ('quanly', 'admin123', User.Role.ADMIN, 'Quản Lý Quán Phở'),
            ('thungan', 'thungan123', User.Role.STAFF, 'Thu Ngân & Điều Phối'),
            ('bep', 'bep123', User.Role.KITCHEN, 'Bếp Trưởng'),
            ('khachhang', 'khach123', User.Role.CUSTOMER, 'Khách Hàng Mẫu'),
        ]
        for uname, pwd, role, fname in users_info:
            u, created = User.objects.get_or_create(username=uname, defaults={'full_name': fname, 'role': role})
            u.full_name = fname
            u.role = role
            u.set_password(pwd)
            u.is_active = True
            u.save()
            action = 'Tạo mới' if created else 'Cập nhật'
            self.stdout.write(f"  - [{action}] {uname} (mật khẩu: {pwd}, vai trò: {role})")

        # 2. Tạo bàn ăn
        self.stdout.write("Tạo danh sách bàn ăn...")
        for i in range(1, 16):
            cap = 6 if i > 10 else 4
            t, created = Table.objects.get_or_create(
                table_number=str(i),
                defaults={'capacity': cap, 'status': Table.Status.AVAILABLE}
            )
            if not created:
                t.capacity = cap
                t.save()
        self.stdout.write(f"  - Đã có {Table.objects.count()} bàn ăn (Bàn 1 -> 15).")

        # 3. Tạo Tùy chọn miễn phí
        self.stdout.write("Khởi tạo tùy chọn món miễn phí...")
        options = [
            (CustomizationOption.Category.BROTH, 'Nước dùng béo ngậy'),
            (CustomizationOption.Category.BROTH, 'Nước dùng thanh trong'),
            (CustomizationOption.Category.BROTH, 'Nước dùng vừa vị'),
            (CustomizationOption.Category.VEGGIE, 'Đầy đủ hành giá'),
            (CustomizationOption.Category.VEGGIE, 'Không hành hoa'),
            (CustomizationOption.Category.VEGGIE, 'Nhiều hành tây & hành hoa'),
            (CustomizationOption.Category.VEGGIE, 'Giá chần chín'),
            (CustomizationOption.Category.NOODLE, 'Bánh phở bình thường'),
            (CustomizationOption.Category.NOODLE, 'Nhiều bánh phở'),
            (CustomizationOption.Category.NOODLE, 'Ít bánh phở'),
        ]
        for cat, name in options:
            CustomizationOption.objects.get_or_create(category=cat, name=name)

        # 4. Tạo Topping
        self.stdout.write("Khởi tạo danh sách Topping...")
        toppings_data = [
            ('Trứng chần nước béo', Decimal('5000'), 'toppings/pho-tai.jpg'),
            ('Quẩy giòn (1 đĩa)', Decimal('10000'), 'toppings/nuoc-uong.jpg'),
            ('Thịt bò tái thêm', Decimal('25000'), 'toppings/pho-tai.jpg'),
            ('Bò nạm thêm', Decimal('25000'), 'toppings/pho-nam.jpg'),
            ('Tiết luộc', Decimal('10000'), 'toppings/pho-dac-biet.jpg'),
        ]
        for name, price, img in toppings_data:
            Topping.objects.get_or_create(
                name=name,
                defaults={'price': price, 'image_thumbnail': img}
            )

        # 5. Tạo Món ăn
        self.stdout.write("Khởi tạo danh sách Món ăn...")
        menu_items_data = [
            {
                'name': 'Phở Bò Tái',
                'base_price': Decimal('55000'),
                'image_primary': 'menu_items/pho-tai.jpg',
                'image_detail_1': 'menu_items/pho-dac-biet.jpg',
            },
            {
                'name': 'Phở Bò Nạm',
                'base_price': Decimal('60000'),
                'image_primary': 'menu_items/pho-nam.jpg',
                'image_detail_1': 'menu_items/pho-dac-biet.jpg',
            },
            {
                'name': 'Phở Bò Đặc Biệt (Tái + Nạm + Trứng)',
                'base_price': Decimal('75000'),
                'image_primary': 'menu_items/pho-dac-biet.jpg',
                'image_detail_1': 'menu_items/pho-tai.jpg',
            },
            {
                'name': 'Trà Đá Hà Nội',
                'base_price': Decimal('5000'),
                'image_primary': 'menu_items/nuoc-uong.jpg',
            },
            {
                'name': 'Nước Ngọt Lon',
                'base_price': Decimal('15000'),
                'image_primary': 'menu_items/nuoc-uong.jpg',
            },
        ]
        for item in menu_items_data:
            MenuItem.objects.get_or_create(
                name=item['name'],
                defaults={
                    'base_price': item['base_price'],
                    'category': MenuItem.Category.DRINK if item['name'].startswith(('Nước', 'Trà')) else MenuItem.Category.PHO,
                    'image_primary': item['image_primary'],
                    'image_detail_1': item.get('image_detail_1', ''),
                    'is_active': True,
                }
            )
        self.stdout.write(f"  - Đã có {MenuItem.objects.count()} món ăn trên thực đơn.")

        # 6. Nguyên liệu & Công thức (BOM)
        self.stdout.write("Khởi tạo nguyên vật liệu tồn kho...")
        ingredients = [
            ('Thịt bò tươi', 'kg', Decimal('50.0')),
            ('Bánh phở tươi', 'kg', Decimal('100.0')),
            ('Nước hầm xương', 'lit', Decimal('200.0')),
            ('Trứng gà', 'qua', Decimal('150.0')),
            ('Quẩy chiên', 'dia', Decimal('80.0')),
            ('Hành lá, rau thơm', 'kg', Decimal('20.0')),
        ]
        ing_objs = {}
        for name, unit, stock in ingredients:
            obj, _ = Ingredient.objects.get_or_create(
                name=name,
                defaults={'unit': unit, 'current_stock': stock}
            )
            ing_objs[name] = obj

        # Gán công thức mẫu cho Phở Bò Tái
        pho_tai = MenuItem.objects.filter(name='Phở Bò Tái').first()
        if pho_tai:
            Recipe.objects.get_or_create(
                menu_item=pho_tai,
                ingredient=ing_objs['Thịt bò tươi'],
                defaults={'quantity_required': Decimal('0.15')} # 150g
            )
            Recipe.objects.get_or_create(
                menu_item=pho_tai,
                ingredient=ing_objs['Bánh phở tươi'],
                defaults={'quantity_required': Decimal('0.20')} # 200g
            )
            Recipe.objects.get_or_create(
                menu_item=pho_tai,
                ingredient=ing_objs['Nước hầm xương'],
                defaults={'quantity_required': Decimal('0.50')} # 0.5 lit
            )

        self.stdout.write(self.style.SUCCESS("Hoàn tất khởi tạo dữ liệu mẫu thành công!"))
