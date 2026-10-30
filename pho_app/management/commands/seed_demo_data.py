import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from pho_app.models import (
    User,
    Table,
    QueueTicket,
    MenuItem,
    Topping,
    CustomizationOption,
    Ingredient,
    Recipe,
    Order,
    OrderItem,
    OrderItemTopping,
    OrderItemCustomization,
    Review,
    InventoryTransaction,
)


class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu demo đầy đủ cho quản lý quán phở: thực đơn, bàn, đơn hàng, topping, tồn kho, đánh giá.'

    def handle(self, *args, **options):
        self.stdout.write('Xóa dữ liệu demo cũ nếu có để seed lại an toàn...')
        Review.objects.all().delete()
        OrderItemTopping.objects.all().delete()
        OrderItemCustomization.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Recipe.objects.all().delete()
        InventoryTransaction.objects.all().delete()
        Ingredient.objects.all().delete()
        CustomizationOption.objects.all().delete()
        Topping.objects.all().delete()
        MenuItem.objects.all().delete()
        QueueTicket.objects.all().delete()
        Table.objects.all().delete()

        self.stdout.write('Khởi tạo thư mục media và sao chép ảnh mẫu...')
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

        # 1) Users
        self.stdout.write('Tạo tài khoản mẫu...')
        users_info = [
            ('admin', 'admin123', User.Role.ADMIN, 'Quản Trị Viên'),
            ('quanly', 'admin123', User.Role.ADMIN, 'Quản Lý Quán Phở'),
            ('thungan', 'thungan123', User.Role.STAFF, 'Thu Ngân & Điều Phối'),
            ('bep', 'bep123', User.Role.KITCHEN, 'Bếp Trưởng'),
            ('khachhang', 'khach123', User.Role.CUSTOMER, 'Khách Hàng Mẫu'),
            ('khach_1', 'khach123', User.Role.CUSTOMER, 'Nguyễn Văn A'),
            ('khach_2', 'khach123', User.Role.CUSTOMER, 'Trần Thị B'),
            ('khach_3', 'khach123', User.Role.CUSTOMER, 'Lê Văn C'),
        ]
        created_users = {}
        for username, password, role, full_name in users_info:
            user, created = User.objects.get_or_create(username=username, defaults={'full_name': full_name, 'role': role})
            user.full_name = full_name
            user.role = role
            user.set_password(password)
            user.is_active = True
            user.save()
            created_users[username] = user

        # 2) Tables (15 bàn, phân bổ đều)
        self.stdout.write('Tạo danh sách bàn ăn - 15 bàn...')
        table_capacities = [4, 4, 4, 6, 4, 4, 6, 4, 4, 6, 4, 6, 4, 6, 4]
        for index, capacity in enumerate(table_capacities, start=1):
            table, _ = Table.objects.get_or_create(
                table_number=str(index),
                defaults={'capacity': capacity, 'status': Table.Status.AVAILABLE}
            )
            table.capacity = capacity
            table.status = Table.Status.AVAILABLE
            table.qr_code_url = f'https://example.test/qr/table/{index}'
            table.save()

        # 3) Customization options
        self.stdout.write('Khởi tạo tùy chọn món miễn phí...')
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

        # 4) Toppings (10 cái)
        self.stdout.write('Khởi tạo topping - tối thiểu 10 loại...')
        topping_data = [
            ('Trứng chần', Decimal('5000')),
            ('Bò viên', Decimal('20000')),
            ('Thịt bò tái thêm', Decimal('25000')),
            ('Bò nạm thêm', Decimal('25000')),
            ('Hành phi', Decimal('5000')),
            ('Ngò gai', Decimal('3000')),
            ('Quẩy giòn', Decimal('8000')),
            ('Tiết luộc', Decimal('12000')),
            ('Rau thơm', Decimal('4000')),
            ('Chả cá', Decimal('18000')),
        ]
        topping_objs = {}
        for name, price in topping_data:
            topping, _ = Topping.objects.get_or_create(name=name, defaults={'price': price, 'is_active': True})
            topping.price = price
            topping.is_active = True
            topping.save()
            topping_objs[name] = topping

        # 5) Menu items: 6 phở + 10 drinks
        self.stdout.write('Khởi tạo thực đơn: 6 món phở + 10 đồ uống...')
        pho_items = [
            ('Phở Bò Tái', Decimal('55000')),
            ('Phở Bò Nạm', Decimal('60000')),
            ('Phở Bò Đặc Biệt', Decimal('75000')),
            ('Phở Gà', Decimal('60000')),
            ('Phở Xá Xíu', Decimal('65000')),
            ('Phở Tái Nạm', Decimal('70000')),
        ]
        drink_items = [
            ('Trà đá', Decimal('5000')),
            ('Cà phê sữa đá', Decimal('18000')),
            ('Coca Cola', Decimal('15000')),
            ('Pepsi', Decimal('15000')),
            ('Sting', Decimal('20000')),
            ('7Up', Decimal('15000')),
            ('Nước cam', Decimal('20000')),
            ('Nước ép táo', Decimal('22000')),
            ('Nước suối', Decimal('8000')),
            ('Sinh tố bơ', Decimal('25000')),
        ]
        menu_item_objs = {}
        for name, price in pho_items + drink_items:
            category = MenuItem.Category.PHO if name in {item[0] for item in pho_items} else MenuItem.Category.DRINK
            item, _ = MenuItem.objects.get_or_create(
                name=name,
                defaults={
                    'base_price': price,
                    'category': category,
                    'is_active': True,
                    'image_primary': 'menu_items/default.jpg',
                },
            )
            item.base_price = price
            item.category = category
            item.is_active = True
            item.image_primary = item.image_primary or 'menu_items/default.jpg'
            item.save()
            menu_item_objs[name] = item

        # 6) Ingredients and recipes for inventory logic
        self.stdout.write('Thiết kế tồn kho phù hợp với thực đơn...')
        ingredient_specs = [
            ('Thịt bò tươi', 'kg', Decimal('50.0'), Decimal('15.0')),
            ('Bánh phở tươi', 'kg', Decimal('80.0'), Decimal('25.0')),
            ('Nước hầm xương', 'lit', Decimal('120.0'), Decimal('40.0')),
            ('Trứng gà', 'quả', Decimal('90.0'), Decimal('20.0')),
            ('Hành lá', 'kg', Decimal('15.0'), Decimal('5.0')),
            ('Rau thơm', 'kg', Decimal('12.0'), Decimal('4.0')),
            ('Cà phê hạt', 'kg', Decimal('10.0'), Decimal('3.0')),
            ('Nước ngọt', 'thùng', Decimal('25.0'), Decimal('8.0')),
        ]
        ingredient_objs = {}
        for name, unit, stock, minimum in ingredient_specs:
            ingredient, _ = Ingredient.objects.get_or_create(name=name, defaults={'unit': unit, 'current_stock': stock, 'minimum_stock': minimum})
            ingredient.unit = unit
            ingredient.current_stock = stock
            ingredient.minimum_stock = minimum
            ingredient.save()
            ingredient_objs[name] = ingredient

        recipe_map = {
            'Phở Bò Tái': [('Thịt bò tươi', Decimal('0.18')), ('Bánh phở tươi', Decimal('0.22')), ('Nước hầm xương', Decimal('0.55'))],
            'Phở Bò Nạm': [('Thịt bò tươi', Decimal('0.20')), ('Bánh phở tươi', Decimal('0.22')), ('Nước hầm xương', Decimal('0.60'))],
            'Phở Bò Đặc Biệt': [('Thịt bò tươi', Decimal('0.28')), ('Bánh phở tươi', Decimal('0.25')), ('Nước hầm xương', Decimal('0.75')), ('Trứng gà', Decimal('1'))],
            'Phở Gà': [('Thịt gà', Decimal('0.20')), ('Bánh phở tươi', Decimal('0.20')), ('Nước hầm xương', Decimal('0.50'))],
            'Phở Xá Xíu': [('Thịt xá xíu', Decimal('0.20')), ('Bánh phở tươi', Decimal('0.22')), ('Nước hầm xương', Decimal('0.60'))],
            'Phở Tái Nạm': [('Thịt bò tươi', Decimal('0.25')), ('Bánh phở tươi', Decimal('0.25')), ('Nước hầm xương', Decimal('0.62'))],
            'Cà phê sữa đá': [('Cà phê hạt', Decimal('0.02')), ('Nước ngọt', Decimal('0.08'))],
            'Coca Cola': [('Nước ngọt', Decimal('0.15'))],
            'Pepsi': [('Nước ngọt', Decimal('0.15'))],
            'Sting': [('Nước ngọt', Decimal('0.18'))],
            '7Up': [('Nước ngọt', Decimal('0.15'))],
            'Nước cam': [('Nước ngọt', Decimal('0.12'))],
            'Nước ép táo': [('Nước ngọt', Decimal('0.12'))],
            'Nước suối': [('Nước ngọt', Decimal('0.08'))],
            'Sinh tố bơ': [('Nước ngọt', Decimal('0.10'))],
        }

        # NOTE: Tạo Ingredient thật cho các nguyên liệu nội dung recipe nếu chưa tồn tại
        for ingredient_name, unit, stock, minimum in ingredient_specs:
            # Ensure duplicate ingredient names won't break; already created above.
            pass

        for item_name, ingredients in recipe_map.items():
            item = menu_item_objs.get(item_name)
            if not item:
                continue
            for ingredient_name, qty in ingredients:
                ingredient = ingredient_objs.get(ingredient_name)
                if ingredient is None:
                    ingredient = Ingredient.objects.create(
                        name=ingredient_name,
                        unit='kg',
                        current_stock=Decimal('50.0'),
                        minimum_stock=Decimal('10.0'),
                    )
                    ingredient_objs[ingredient_name] = ingredient
                Recipe.objects.get_or_create(menu_item=item, ingredient=ingredient, defaults={'quantity_required': qty})

        for ingredient in ingredient_objs.values():
            categories = set(Recipe.objects.filter(ingredient=ingredient, menu_item__isnull=False).values_list('menu_item__category', flat=True))
            if categories:
                ingredient.usage = Ingredient.Usage.SHARED if len(categories) > 1 else next(iter(categories))
                ingredient.save(update_fields=['usage'])

        # 7) Orders (10 đơn) - spread by status
        self.stdout.write('Tạo 10 đơn hàng với trạng thái phân bổ hợp lý...')
        customer_users = [created_users['khach_1'], created_users['khach_2'], created_users['khach_3'], created_users['khachhang']]
        order_specs = [
            ('PO-1001', customer_users[0], 'Nguyễn Văn A', Order.OrderType.DINE_IN, 1, Order.OrderStatus.PENDING_KITCHEN, Order.PaymentMethod.CASH, Order.PaymentStatus.PENDING, Decimal('110000')),
            ('PO-1002', customer_users[1], 'Trần Thị B', Order.OrderType.DINE_IN, 2, Order.OrderStatus.COOKING, Order.PaymentMethod.CASH, Order.PaymentStatus.PAID, Decimal('140000')),
            ('PO-1003', customer_users[2], 'Lê Văn C', Order.OrderType.DINE_IN, 3, Order.OrderStatus.READY, Order.PaymentMethod.CASH, Order.PaymentStatus.PAID, Decimal('175000')),
            ('PO-1004', customer_users[0], 'Nguyễn Văn A', Order.OrderType.DELIVERY, 4, Order.OrderStatus.DELIVERING, Order.PaymentMethod.VIETQR, Order.PaymentStatus.PAID, Decimal('200000')),
            ('PO-1005', customer_users[3], 'Khách Hàng Mẫu', Order.OrderType.DINE_IN, 5, Order.OrderStatus.COMPLETED, Order.PaymentMethod.CASH, Order.PaymentStatus.PAID, Decimal('125000')),
            ('PO-1006', None, 'Khách vãng lai', Order.OrderType.QUEUE_CART, 6, Order.OrderStatus.PENDING_KITCHEN, Order.PaymentMethod.VIETQR, Order.PaymentStatus.PENDING, Decimal('96000')),
            ('PO-1007', customer_users[1], 'Trần Thị B', Order.OrderType.DINE_IN, 7, Order.OrderStatus.COOKING, Order.PaymentMethod.CASH, Order.PaymentStatus.PAID, Decimal('138000')),
            ('PO-1008', customer_users[0], 'Nguyễn Văn A', Order.OrderType.DELIVERY, 8, Order.OrderStatus.READY, Order.PaymentMethod.VIETQR, Order.PaymentStatus.PAID, Decimal('165000')),
            ('PO-1009', customer_users[2], 'Lê Văn C', Order.OrderType.DINE_IN, 9, Order.OrderStatus.COMPLETED, Order.PaymentMethod.CASH, Order.PaymentStatus.PAID, Decimal('180000')),
            ('PO-1010', customer_users[3], 'Khách Hàng Mẫu', Order.OrderType.DINE_IN, 10, Order.OrderStatus.CANCELLED, Order.PaymentMethod.CASH, Order.PaymentStatus.FAILED, Decimal('82000')),
        ]

        for order_code, customer, guest_name, order_type, table_number, status, payment_method, payment_status, total_amount in order_specs:
            table = Table.objects.get(table_number=str(table_number))
            order = Order.objects.create(
                order_code=order_code,
                customer=customer,
                guest_name=guest_name,
                table=table,
                order_type=order_type,
                payment_method=payment_method,
                payment_status=payment_status,
                order_status=status,
                total_amount=total_amount,
                delivery_address='123 Nguyễn Huệ, Quận 1, TP.HCM' if order_type == Order.OrderType.DELIVERY else '',
                delivery_fee=Decimal('30000') if order_type == Order.OrderType.DELIVERY else Decimal('0'),
                created_at=timezone.now(),
            )

            item_names = ['Phở Bò Tái', 'Trà đá']
            if order_type == Order.OrderType.DELIVERY:
                item_names = ['Phở Bò Nạm', 'Coca Cola']
            if order_code in {'PO-1003', 'PO-1009'}:
                item_names = ['Phở Bò Đặc Biệt', 'Sinh tố bơ']
            if order_code == 'PO-1007':
                item_names = ['Phở Gà', 'Cà phê sữa đá']

            for item_name in item_names:
                item = menu_item_objs[item_name]
                qty = 2 if item_name.startswith('Phở') else 1
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=item,
                    quantity=qty,
                    item_price=item.base_price,
                )
                if item.category == MenuItem.Category.PHO:
                    topping = list(topping_objs.values())[qty % len(topping_objs)]
                    OrderItemTopping.objects.get_or_create(order_item=order_item, topping=topping, defaults={'quantity': 1})

        # 8) Reviews positive
        self.stdout.write('Tạo đánh giá tích cực cho nhà hàng...')
        review_specs = [
            ('khach_1', 'Phở Bò Tái', 5, 'Nước dùng rất đậm vị, bánh phở mềm và thơm. Sẽ quay lại.'),
            ('khach_2', 'Phở Bò Nạm', 5, 'Phở ngon, nhân viên vui vẻ, không gian sạch sẽ.'),
            ('khach_3', 'Trà đá', 4, 'Trà đá mát, phục vụ nhanh.'),
            ('khachhang', 'Phở Bò Đặc Biệt', 5, 'Món đặc biệt rất hợp khẩu vị, thịt bò mềm.'),
            ('khach_1', 'Sinh tố bơ', 5, 'Sinh tố bơ ngon, mát và đáng tiền.'),
            ('khach_2', 'Phở Gà', 4, 'Phở gà thơm, nước dùng ngọt nhẹ.'),
        ]
        for username, item_name, rating, comment in review_specs:
            user = created_users[username]
            menu_item = menu_item_objs.get(item_name)
            if menu_item is None:
                continue
            Review.objects.get_or_create(
                customer=user,
                menu_item=menu_item,
                defaults={'rating': rating, 'comment': comment},
            )

        # 9) Inventory transactions to make stock realistic
        self.stdout.write('Tạo biến động kho mẫu cho quản lý tồn kho...')
        for ingredient_name, _, stock, _ in ingredient_specs:
            ingredient = ingredient_objs[ingredient_name]
            InventoryTransaction.objects.get_or_create(
                ingredient=ingredient,
                transaction_type=InventoryTransaction.TransactionType.IMPORT,
                quantity_changed=Decimal('20.0'),
                created_by=created_users['admin'],
            )

        self.stdout.write(self.style.SUCCESS('Hoàn tất khởi tạo dữ liệu demo thành công.'))
        self.stdout.write(f'Tổng số bàn: {Table.objects.count()}')
        self.stdout.write(f'Tổng số món phở: {MenuItem.objects.filter(category=MenuItem.Category.PHO).count()}')
        self.stdout.write(f'Tổng số đồ uống: {MenuItem.objects.filter(category=MenuItem.Category.DRINK).count()}')
        self.stdout.write(f'Tổng số topping: {Topping.objects.count()}')
        self.stdout.write(f'Tổng số đơn hàng: {Order.objects.count()}')
        self.stdout.write(f'Tổng số đánh giá: {Review.objects.count()}')
