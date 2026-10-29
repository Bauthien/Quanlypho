from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator
from django.db import models, router, transaction


# ==========================================
# 1. MODULE QUẢN LÝ NGƯỜI DÙNG & PHÂN QUYỀN
# ==========================================
class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Khách hàng'
        STAFF = 'STAFF', 'Thu ngân / Điều phối'
        KITCHEN = 'KITCHEN', 'Bếp'
        ADMIN = 'ADMIN', 'Quản lý'

    full_name = models.CharField(max_length=255, verbose_name="Họ và tên", blank=True, null=True)
    phone_number = models.CharField(max_length=20, verbose_name="Số điện thoại", blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER, verbose_name="Vai trò")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Ảnh đại diện")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=12, blank=True, choices=[('', 'Không cung cấp'), ('MALE', 'Nam'), ('FEMALE', 'Nữ'), ('OTHER', 'Khác')])
    profile_version = models.PositiveIntegerField(default=1)
    auth_epoch = models.PositiveIntegerField(default=1)
    referral_code = models.CharField(max_length=24, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='referrals')

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values('password', 'role', 'is_active', 'auth_epoch').first()
            if previous and any(previous[key] != getattr(self, key) for key in ('password', 'role', 'is_active')):
                self.auth_epoch = previous['auth_epoch'] + 1
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {'auth_epoch'}
        if self.is_superuser and self.role == self.Role.CUSTOMER:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def display_name(self):
        return self.full_name or self.username

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def is_staff_role(self):
        return self.role == self.Role.STAFF

    def is_kitchen(self):
        return self.role == self.Role.KITCHEN

    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def home_url_name(self):
        mapping = {
            self.Role.CUSTOMER: 'menu',
            self.Role.STAFF: 'staff_home',
            self.Role.KITCHEN: 'kitchen_home',
            self.Role.ADMIN: 'admin_home',
        }
        return mapping.get(self.role, 'menu')


# ==========================================
# 2. MODULE QUẢN LÝ BÀN & XẾP HÀNG (VIRTUAL QUEUE)
# ==========================================
class Table(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Trống'
        OCCUPIED = 'OCCUPIED', 'Đang có khách'
        CLEANING = 'CLEANING', 'Đang dọn dẹp'
    table_number = models.CharField(max_length=50, unique=True, verbose_name="Số bàn")
    capacity = models.IntegerField(default=4, validators=[MinValueValidator(1)], verbose_name="Số lượng chỗ (Tô) tối đa")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Trạng thái bàn")
    qr_code_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Đường dẫn QR")
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="Ảnh mã QR")

    class Meta:
        verbose_name = "Bàn ăn"
        verbose_name_plural = "Danh sách Bàn ăn"
        constraints = [models.CheckConstraint(condition=models.Q(capacity__gte=1), name='table_capacity_positive')]

    def __str__(self):
        return f"Bàn số {self.table_number} - {self.get_status_display()}"


class QueueTicket(models.Model):
    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Đang chờ'
        CALLED = 'CALLED', 'Đã gọi số'
        SEATED = 'SEATED', 'Đã vào bàn'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Tên khách (không đăng nhập)")
    ticket_number = models.CharField(max_length=50, verbose_name="Số thứ tự (VD: P-015)")
    people_count = models.PositiveIntegerField(default=1, verbose_name="Số người")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING, verbose_name="Trạng thái hàng đợi")
    table = models.ForeignKey('Table', on_delete=models.PROTECT, null=True, blank=True, related_name='queue_tickets', verbose_name="Bàn được gọi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian lấy số")

    class Meta:
        verbose_name = "Số thứ tự xếp hàng"
        verbose_name_plural = "Danh sách Xếp hàng"
        ordering = ['created_at']  # Xử lý theo thứ tự FIFO (Vào trước ra trước)

    def __str__(self):
        return f"Vé {self.ticket_number} - {self.get_status_display()}"


# ==========================================
# 3. MODULE QUẢN LÝ THỰC ĐƠN (MENU MANAGEMENT)
# ==========================================
class MenuItem(models.Model):
    class Category(models.TextChoices):
        PHO = 'PHO', 'Phở'
        DRINK = 'DRINK', 'Đồ uống'

    name = models.CharField(max_length=255, verbose_name="Tên món (VD: Phở Tái)")
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.PHO, verbose_name='Nhóm món')
    base_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá gốc (VNĐ)")
    is_active = models.BooleanField(default=True, verbose_name="Còn kinh doanh")
    inventory_mode = models.CharField(max_length=10, choices=[('BOM', 'Theo định lượng'), ('DIRECT', 'Bán nguyên chai / lon'), ('UNTRACKED', 'Không theo dõi kho')], default='BOM')

    # 3 Hình ảnh trực quan cho Món chính
    image_primary = models.ImageField(upload_to='menu_items/', verbose_name="Ảnh đại diện chính")
    image_detail_1 = models.ImageField(upload_to='menu_items/', blank=True, null=True, verbose_name="Ảnh chi tiết 1 (Cận cảnh)")
    image_detail_2 = models.ImageField(upload_to='menu_items/', blank=True, null=True, verbose_name="Ảnh chi tiết 2 (Không gian/Góc rộng)")

    class Meta:
        verbose_name = "Món ăn"
        verbose_name_plural = "Danh mục Món ăn"

    def __str__(self):
        return self.name


class Topping(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên Topping (VD: Trứng chần)")
    is_active = models.BooleanField(default=True, verbose_name='Còn kinh doanh')
    inventory_mode = models.CharField(max_length=10, choices=[('BOM', 'Theo định lượng'), ('UNTRACKED', 'Không theo dõi kho')], default='BOM')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá tính thêm (VNĐ)")
    image_thumbnail = models.ImageField(upload_to='toppings/', blank=True, null=True, verbose_name="Ảnh minh họa nhỏ")
    category = models.CharField(max_length=10, choices=MenuItem.Category.choices, default=MenuItem.Category.PHO, verbose_name='Topping dùng cho')
    applies_to_all = models.BooleanField(default=True, verbose_name='Dùng cho tất cả món trong nhóm')
    allowed_menu_items = models.ManyToManyField(MenuItem, blank=True, related_name='available_toppings', verbose_name='Món được gọi kèm')

    def is_available_for(self, menu_item):
        return self.category == menu_item.category and (
            self.applies_to_all or any(item.pk == menu_item.pk for item in self.allowed_menu_items.all())
        )

    class Meta:
        verbose_name = "Topping tính phí"
        verbose_name_plural = "Danh mục Topping"

    def __str__(self):
        return f"{self.name} (+{self.price:,}đ)"


class CustomizationOption(models.Model):
    class Category(models.TextChoices):
        BROTH = 'BROTH', 'Nước dùng (Béo/Trong)'
        VEGGIE = 'VEGGIE', 'Rau / Giá (Không hành/Giá chín...)'
        NOODLE = 'NOODLE', 'Bánh phở (Nhiều/Ít bánh)'

    category = models.CharField(max_length=20, choices=Category.choices, verbose_name="Phân loại tùy chọn")
    name = models.CharField(max_length=255, verbose_name="Tên tùy chọn (VD: Không hành)")

    class Meta:
        verbose_name = "Tùy chọn miễn phí"
        verbose_name_plural = "Danh mục Tùy chọn miễn phí"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"


# ==========================================
# 4. MODULE QUẢN LÝ ĐƠN HÀNG & DELIVERY (CORE)
# ==========================================
class Order(gis_models.Model):  # Sử dụng gis_models để hỗ trợ PostGIS PointField
    class OrderType(models.TextChoices):
        DINE_IN = 'DINE_IN', 'Tại bàn'
        DELIVERY = 'DELIVERY', 'Giao tận nơi'
        QUEUE_CART = 'QUEUE_CART', 'Giỏ hàng chờ vào bàn'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Tiền mặt'
        VIETQR = 'VIETQR', 'Chuyển khoản VietQR'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Chờ thanh toán'
        PAID = 'PAID', 'Đã thanh toán'
        FAILED = 'FAILED', 'Thanh toán thất bại'

    class OrderStatus(models.TextChoices):
        CART = 'CART', 'Chờ thanh toán'
        DELIVERING = 'DELIVERING', 'Đang giao hàng'
        DELIVERY_EXCEPTION = 'DELIVERY_EXCEPTION', 'Giao hàng cần xử lý'
        PENDING_KITCHEN = 'PENDING_KITCHEN', 'Đang gửi Bếp'
        COOKING = 'COOKING', 'Bếp đang làm'
        READY = 'READY', 'Đã xong (Chờ bưng/Giao)'
        COMPLETED = 'COMPLETED', 'Hoàn tất'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    order_code = models.CharField(max_length=50, unique=True, verbose_name="Mã đơn hàng")
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Tên khách (nếu không đăng nhập)")
    queue_ticket = models.ForeignKey(QueueTicket, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Vé xếp hàng")
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN, verbose_name="Loại đơn")
    table = models.ForeignKey(Table, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Bàn số")

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.VIETQR, verbose_name="Phương thức thanh toán")
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Trạng thái thanh toán")
    is_cleared = models.BooleanField(default=False, verbose_name="Đã dọn bàn")
    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CART, verbose_name="Trạng thái đơn")

    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền món (VNĐ)")

    # Dữ liệu phục vụ Luồng Delivery & PostGIS
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ giao hàng")
    customer_location = gis_models.PointField(srid=4326, blank=True, null=True, verbose_name="Tọa độ GPS khách hàng (PostGIS)")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí giao hàng (VNĐ)")
    delivery_distance_km = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Khoảng cách giao (km)")
    shipping_code = models.CharField(max_length=50, blank=True, verbose_name="Mã vận đơn")
    checkout_snapshot = models.JSONField(default=dict, blank=True)
    payable_amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    benefits_state = models.CharField(max_length=12, default='LEGACY')
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    purpose = models.CharField(max_length=24, default='REGULAR', choices=[('REGULAR', 'Đơn mua hàng'), ('SERVICE_REPLACEMENT', 'Giao bù')])
    replacement_for = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='replacements')
    delivery_snapshot = models.JSONField(default=dict, blank=True)
    distance_raw_km = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)

    @property
    def amount_due(self):
        return self.payable_amount if self.payable_amount is not None else self.total_amount + self.delivery_fee

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Danh sách Đơn hàng"

    def __str__(self):
        return f"Đơn {self.order_code} - {self.get_order_status_display()}"

    def save(self, *args, **kwargs):
        # Payment and the inventory signal must commit or roll back together,
        # including direct saves outside the payment views.
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            from django.db import connections
            connection = connections[using]
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_advisory_xact_lock(%s)', [70420261023])
            return super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Đơn hàng")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name="Món chính")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    item_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Đơn giá thời điểm đặt")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú thêm")

    class Meta:
        verbose_name = "Chi tiết món đặt"
        verbose_name_plural = "Chi tiết các món đặt"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (Đơn {self.order.order_code})"


class OrderItemTopping(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='toppings', verbose_name="Món ăn")
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE, verbose_name="Topping")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng topping")

    def __str__(self):
        return f"+{self.quantity} {self.topping.name}"


class OrderItemCustomization(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='customizations', verbose_name="Món ăn")
    customization = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE, verbose_name="Tùy chọn tick chọn")

    def __str__(self):
        return f"Tùy chọn: {self.customization.name}"


# ==========================================
# 5. MODULE QUẢN LÝ TỒN KHO & ĐỊNH LƯỢNG (INVENTORY & RECIPE - BOM)
# ==========================================
class Ingredient(models.Model):
    class Usage(models.TextChoices):
        PHO = 'PHO', 'Bếp phở / món chính'
        DRINK = 'DRINK', 'Pha chế / nước uống'
        SHARED = 'SHARED', 'Dùng chung'

    name = models.CharField(max_length=255, verbose_name="Tên nguyên liệu (VD: Bánh phở, Thịt bò)")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính (kg, gram, lít...)")
    usage = models.CharField(max_length=10, choices=Usage.choices, default=Usage.PHO, verbose_name='Nhóm sử dụng')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Số lượng tồn hiện tại")
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Ngưỡng cảnh báo hết hàng")
    ingredient_image = models.ImageField(upload_to='ingredients/', blank=True, null=True, verbose_name="Ảnh minh họa")

    class Meta:
        verbose_name = "Nguyên liệu kho"
        verbose_name_plural = "Danh mục Nguyên liệu"
        constraints = [
            models.CheckConstraint(condition=models.Q(current_stock__gte=0), name='ingredient_stock_nonnegative'),
            models.CheckConstraint(condition=models.Q(minimum_stock__gte=0), name='ingredient_minimum_nonnegative'),
        ]

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"


class Recipe(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, blank=True, null=True, related_name='recipes', verbose_name="Dùng cho Món chính")
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE, blank=True, null=True, related_name='recipes', verbose_name="Dùng cho Topping")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Nguyên liệu hao phí")
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Định lượng hao phí/1 đơn vị bán")

    class Meta:
        verbose_name = "Định lượng sản phẩm (BOM)"
        verbose_name_plural = "Công thức Định lượng kho"
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(menu_item__isnull=False, topping__isnull=True)
                           | models.Q(menu_item__isnull=True, topping__isnull=False)),
                name='recipe_exactly_one_target',
                violation_error_message='Mỗi định lượng phải gắn với đúng một món chính hoặc topping.',
            ),
        ]

    def __str__(self):
        target = self.menu_item.name if self.menu_item else (self.topping.name if self.topping else 'N/A')
        return f"1x {target} cần {self.quantity_required} {self.ingredient.unit} {self.ingredient.name}"


class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        IMPORT = 'IMPORT', 'Nhập kho'
        EXPORT = 'EXPORT', 'Xuất bán (Tự động)'
        ADJUST = 'ADJUST', 'Điều chỉnh / Khấu hao hư hỏng'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Nguyên liệu")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices, verbose_name="Loại giao dịch")
    quantity_changed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Số lượng thay đổi (+/-)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Người thực hiện")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")

    class Meta:
        verbose_name = "Biến động kho"
        verbose_name_plural = "Lịch sử Kho"

    def __str__(self):
        return f"[{self.get_transaction_type_display()}] {self.ingredient.name}: {self.quantity_changed} {self.ingredient.unit}"


# ==========================================
# 6. MODULE ĐÁNH GIÁ KHÁCH HÀNG (REVIEWS)
# ==========================================
class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Khách hàng")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews', blank=True, null=True, verbose_name="Món ăn (nếu có)")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', blank=True, null=True, verbose_name="Đơn hàng")
    rating = models.IntegerField(choices=[(1, '1★'), (2, '2★'), (3, '3★'), (4, '4★'), (5, '5★')], verbose_name="Đánh giá")
    comment = models.TextField(blank=True, verbose_name="Nhận xét")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")
    is_published = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Đánh giá"
        verbose_name_plural = "Danh sách Đánh giá"
        ordering = ['-created_at']

    def __str__(self):
        item_name = self.menu_item.name if self.menu_item else 'Đơn hàng'
        return f"{self.customer.display_name} - {item_name} - {self.rating}★"


# Kept in a separate module to keep the original catalog and table models readable.
from .commerce_models import *  # noqa: E402,F403
