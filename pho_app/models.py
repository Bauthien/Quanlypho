from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.db import models


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

    def save(self, *args, **kwargs):
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
    capacity = models.IntegerField(default=4, verbose_name="Số lượng chỗ (Tô) tối đa")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Trạng thái bàn")
    qr_code_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Đường dẫn QR")
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="Ảnh mã QR")

    class Meta:
        verbose_name = "Bàn ăn"
        verbose_name_plural = "Danh sách Bàn ăn"

    def __str__(self):
        return f"Bàn số {self.table_number} - {self.get_status_display()}"


class QueueTicket(models.Model):
    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Đang chờ'
        CALLED = 'CALLED', 'Đã gọi số'
        SEATED = 'SEATED', 'Đã vào bàn'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")
    ticket_number = models.CharField(max_length=20, verbose_name="Số thứ tự (VD: P-015)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING, verbose_name="Trạng thái hàng đợi")
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True, blank=True, related_name='queue_tickets', verbose_name="Bàn được gọi")
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
    name = models.CharField(max_length=255, verbose_name="Tên món (VD: Phở Tái)")
    base_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá gốc (VNĐ)")
    is_active = models.BooleanField(default=True, verbose_name="Còn kinh doanh")

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
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá tính thêm (VNĐ)")
    image_thumbnail = models.ImageField(upload_to='toppings/', blank=True, null=True, verbose_name="Ảnh minh họa nhỏ")

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
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bàn số")

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.VIETQR, verbose_name="Phương thức thanh toán")
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Trạng thái thanh toán")
    is_cleared = models.BooleanField(default=False, verbose_name="Đã dọn bàn")
    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CART, verbose_name="Trạng thái đơn")

    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền món (VNĐ)")

    # Dữ liệu phục vụ Luồng Delivery & PostGIS
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ giao hàng")
    customer_location = gis_models.PointField(srid=4326, blank=True, null=True, verbose_name="Tọa độ GPS khách hàng (PostGIS)")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí giao hàng (VNĐ)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Danh sách Đơn hàng"

    def __str__(self):
        return f"Đơn {self.order_code} - {self.get_order_status_display()}"


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
    name = models.CharField(max_length=255, verbose_name="Tên nguyên liệu (VD: Bánh phở, Thịt bò)")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính (kg, gram, lít...)")
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Số lượng tồn hiện tại")
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ngưỡng cảnh báo hết hàng")
    ingredient_image = models.ImageField(upload_to='ingredients/', blank=True, null=True, verbose_name="Ảnh minh họa")

    class Meta:
        verbose_name = "Nguyên liệu kho"
        verbose_name_plural = "Danh mục Nguyên liệu"

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"


class Recipe(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, blank=True, null=True, related_name='recipes', verbose_name="Dùng cho Món chính")
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE, blank=True, null=True, related_name='recipes', verbose_name="Dùng cho Topping")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="Nguyên liệu hao phí")
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Định lượng hao phí/1 đơn vị bán")

    class Meta:
        verbose_name = "Định lượng sản phẩm (BOM)"
        verbose_name_plural = "Công thức Định lượng kho"

    def __str__(self):
        target = self.menu_item.name if self.menu_item else (self.topping.name if self.topping else 'N/A')
        return f"1x {target} cần {self.quantity_required} {self.ingredient.unit} {self.ingredient.name}"


class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        IMPORT = 'IMPORT', 'Nhập kho'
        EXPORT = 'EXPORT', 'Xuất bán (Tự động)'
        ADJUST = 'ADJUST', 'Điều chỉnh / Khấu hao hư hỏng'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="Nguyên liệu")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices, verbose_name="Loại giao dịch")
    quantity_changed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Số lượng thay đổi (+/-)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Người thực hiện")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")

    class Meta:
        verbose_name = "Biến động kho"
        verbose_name_plural = "Lịch sử Kho"

    def __str__(self):
        return f"[{self.get_transaction_type_display()}] {self.ingredient.name}: {self.quantity_changed} {self.ingredient.unit}"