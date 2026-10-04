from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.gis.admin import GISModelAdmin
from .models import (
    User, Table, QueueTicket, 
    MenuItem, Topping, CustomizationOption, 
    Order, OrderItem, OrderItemTopping, OrderItemCustomization,
    Ingredient, Recipe, InventoryTransaction
)

# 1. Quản lý Người dùng (Custom User Admin)
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'phone_number', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Thông tin bổ sung', {'fields': ('full_name', 'phone_number', 'role', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {'fields': ('full_name', 'phone_number', 'role', 'avatar')}),
    )

# 2. Quản lý Bàn ăn & Xếp hàng
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'status', 'qr_code_url')
    list_filter = ('status',)

@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'customer', 'status', 'created_at')
    list_filter = ('status', 'created_at')

# 3. Quản lý Thực đơn (Menu, Topping, Customization)
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')

@admin.register(CustomizationOption)
class CustomizationOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

# 4. Quản lý Đơn hàng & Delivery (Tích hợp bản đồ PostGIS)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(GISModelAdmin): # Sử dụng GISModelAdmin để hiển thị bản đồ chọn vị trí
    list_display = ('order_code', 'customer', 'order_type', 'order_status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('order_type', 'order_status', 'payment_status')
    search_fields = ('order_code', 'delivery_address')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'item_price')

# 5. Quản lý Kho & Định lượng (BOM)
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_stock', 'unit', 'minimum_stock')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'topping', 'ingredient', 'quantity_required')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'transaction_type', 'quantity_changed', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at')