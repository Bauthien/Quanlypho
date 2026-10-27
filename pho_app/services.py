import math
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F, Prefetch, Q, Sum, prefetch_related_objects
from django.db.models.functions import Coalesce

from .models import Ingredient, MenuItem, Order, OrderItem, QueueTicket, Recipe, Table, Topping
from .domain import serialized, BusinessError


class InvalidOrderTransition(BusinessError):
    """The current persisted order no longer permits this action."""


class InsufficientStock(InvalidOrderTransition):
    """The complete order cannot be exported without making stock negative."""

    def __init__(self, shortages):
        self.shortages = shortages
        details = '; '.join(
            f'{ingredient.name}: cần {required:g} {ingredient.unit}, còn {ingredient.current_stock:g} {ingredient.unit}'
            for ingredient, required in shortages
        )
        super().__init__(f'Không đủ tồn kho. {details}. Vui lòng giảm số lượng, chọn món khác hoặc liên hệ nhân viên.')


def _prefetch_inventory_recipes(products, using):
    for model in (MenuItem, Topping):
        group = [product for product in products if isinstance(product, model)]
        if group:
            prefetch_related_objects(group, Prefetch('recipes', queryset=Recipe.objects.using(using).order_by('pk')))


def inventory_deductions(lines, using='default'):
    """Resolve (product, quantity, [(topping, total_quantity)]) into exact exports.

    Checkout and saved orders use the same rules. Topping quantities on saved
    order lines already include the number of bowls and must not be multiplied again.
    """
    lines = list(lines)
    products = [product for product, _, _ in lines]
    products.extend(topping for _, _, extras in lines for topping, _ in extras)
    _prefetch_inventory_recipes(products, using)
    deductions = []

    def add_product(product, quantity):
        if product.inventory_mode == 'UNTRACKED':
            if isinstance(product, MenuItem) and product.category == MenuItem.Category.PHO:
                raise InvalidOrderTransition('Món phở bắt buộc có định lượng nguyên liệu.')
            return
        recipes = list(product.recipes.all())
        if not recipes:
            raise InvalidOrderTransition(f'Món {product.name} hiện chưa thể phục vụ. Vui lòng chọn món khác hoặc liên hệ nhân viên.')
        for recipe in recipes:
            amount = recipe.quantity_required * quantity
            if not amount.is_finite() or amount <= 0:
                raise InvalidOrderTransition(f'Món {product.name} hiện chưa thể phục vụ. Vui lòng liên hệ nhân viên.')
            deductions.append((recipe.ingredient_id, amount))

    for product, quantity, extras in lines:
        add_product(product, quantity)
        for topping, topping_quantity in extras:
            add_product(topping, topping_quantity)
    return deductions


def order_inventory_deductions(order, using=None):
    using = using or order._state.db or 'default'
    from .models import StockReservation
    reservation = StockReservation.objects.filter(order=order).first()
    if reservation:
        return list(reservation.lines.values_list('ingredient_id', 'quantity'))
    items = order.items.using(using).select_related('menu_item').prefetch_related('toppings__topping')
    return inventory_deductions([
        (item.menu_item, item.quantity, [(extra.topping, extra.quantity) for extra in item.toppings.all()])
        for item in items
    ], using=using)


def inventory_totals(deductions):
    required = defaultdict(Decimal)
    for ingredient_id, amount in deductions:
        required[ingredient_id] += amount
    return required


def ensure_inventory_available(deductions, *, using='default', lock=False):
    from .stock import reserved_totals
    from .models import InventoryIncident
    required = inventory_totals(deductions)
    ingredients = Ingredient.objects.using(using).filter(pk__in=required).order_by('pk')
    if lock:
        ingredients = ingredients.select_for_update()
    ingredients = list(ingredients)
    if len(ingredients) != len(required):
        raise InvalidOrderTransition('Món đã chọn hiện chưa thể phục vụ. Vui lòng tải lại thực đơn.')
    held = reserved_totals()
    if InventoryIncident.objects.filter(ingredient_id__in=required, resolved=False).exists():
        raise InvalidOrderTransition('Nguyên liệu đang có chênh lệch kiểm kê chưa xử lý.')
    shortages = [(ingredient, required[ingredient.pk]) for ingredient in ingredients
                 if ingredient.current_stock - held.get(ingredient.pk, 0) < required[ingredient.pk]]
    if shortages:
        raise InsufficientStock(shortages)
    return ingredients, required


def catalog_stock_limits(products, using='default'):
    """Display limits are a snapshot; checkout and payment check fresh balances."""
    products = list(products)
    _prefetch_inventory_recipes(products, using)
    ingredient_ids = {recipe.ingredient_id for product in products for recipe in product.recipes.all()}
    from .stock import available_balances
    balances = available_balances()
    limits = {}
    for product in products:
        try:
            required = inventory_totals(inventory_deductions([(product, 1, [])], using=using))
        except InvalidOrderTransition:
            limits[product.pk] = 0
        else:
            limits[product.pk] = max(0, min([99] + [int(balances.get(pk, 0) // amount) for pk, amount in required.items()]))
    return limits


ORDER_ACTION_LABELS = {
    'confirm_cash': 'Xác nhận đã nhận tiền mặt',
    'cancel_cash': 'Hủy đơn tiền mặt',
    'start_cooking': 'Bắt đầu chế biến',
    'finish_cooking': 'Đánh dấu món đã xong',
    'handover_delivery': 'Bàn giao cho đơn vị giao hàng',
    'complete_delivery': 'Hoàn tất giao hàng',
    'complete_dine_in': 'Đã phục vụ cho khách',
}


def available_order_actions(order):
    """One set of rules for both the interface and all mutation endpoints."""
    actions = []
    supported_type = order.order_type in (Order.OrderType.DINE_IN, Order.OrderType.DELIVERY)
    if (order.payment_method == Order.PaymentMethod.CASH
            and order.payment_status == Order.PaymentStatus.PENDING
            and order.order_status == Order.OrderStatus.CART):
        if supported_type:
            actions.append('confirm_cash')
        actions.append('cancel_cash')
    if order.payment_status == Order.PaymentStatus.PAID and supported_type:
        if order.order_status == Order.OrderStatus.PENDING_KITCHEN:
            actions.append('start_cooking')
        # Existing kitchen workflow also allows finishing directly from PENDING_KITCHEN.
        if order.order_status in (Order.OrderStatus.PENDING_KITCHEN, Order.OrderStatus.COOKING):
            actions.append('finish_cooking')
        if order.order_status == Order.OrderStatus.READY:
            actions.append('handover_delivery' if order.order_type == Order.OrderType.DELIVERY else 'complete_dine_in')
        if order.order_type == Order.OrderType.DELIVERY and order.order_status == Order.OrderStatus.DELIVERING:
            actions.append('complete_delivery')
    return actions


@serialized
def apply_order_action(order_id, action):
    """Serialize changes before checking state; payment signals remain the sole stock writer.

    Cancellation locks the table before the order, matching checkout/table cleaning,
    so another checkout cannot occupy the table between checking and releasing it.
    """
    if action == 'cancel_cash':
        table_id = Order.objects.values_list('table_id', flat=True).get(pk=order_id)
        if table_id:
            Table.objects.select_for_update().filter(pk=table_id).first()
    order = Order.objects.select_for_update().get(pk=order_id)
    if action not in available_order_actions(order):
        raise InvalidOrderTransition(
            'Thao tác không hợp lệ với loại đơn hoặc trạng thái hiện tại. '
            'Đơn có thể vừa được người khác xử lý; vui lòng kiểm tra trạng thái mới nhất.'
        )
    fields = ['order_status', 'updated_at']
    if action == 'confirm_cash':
        order.payment_status = Order.PaymentStatus.PAID
        order.order_status = Order.OrderStatus.PENDING_KITCHEN
        fields.append('payment_status')
    elif action == 'cancel_cash':
        from .checkout import release_benefits
        release_benefits(order)
        order.payment_status = Order.PaymentStatus.FAILED
        order.order_status = Order.OrderStatus.CANCELLED
        fields.append('payment_status')
    else:
        order.order_status = {
            'start_cooking': Order.OrderStatus.COOKING,
            'finish_cooking': Order.OrderStatus.READY,
            'handover_delivery': Order.OrderStatus.DELIVERING,
            'complete_delivery': Order.OrderStatus.COMPLETED,
            'complete_dine_in': Order.OrderStatus.COMPLETED,
        }[action]
    if action == 'finish_cooking' and order.order_type == Order.OrderType.DELIVERY and not order.shipping_code:
        order.shipping_code = f'VD-{order.pk:05d}'
        fields.append('shipping_code')
    from django.utils import timezone
    if action == 'confirm_cash':
        from .models import PaymentReceipt
        PaymentReceipt.objects.get_or_create(provider='CASH', external_id=f'cash-order:{order.pk}', defaults={
            'order': order, 'amount': int(order.amount_due), 'allocated': True, 'received_at': timezone.now()})
    if action in ('handover_delivery', 'complete_delivery'):
        from .delivery import delivery_action
        delivery_action(order.pk, 'handover' if action == 'handover_delivery' else 'delivered',
                        evidence='Nhân viên xác nhận tại màn hình điều phối')
        order.refresh_from_db()
        return order
    if action == 'complete_dine_in':
        from .loyalty import enqueue
        from .models import ServiceRequest
        order.completed_at = timezone.now()
        fields.append('completed_at')
        enqueue(f'complete:{order.pk}', 'ORDER_COMPLETED', order_id=order.pk)
        ServiceRequest.objects.filter(replacement=order, state='REPLACING').update(state='CLOSED')
    if action == 'finish_cooking' and order.order_type == 'DELIVERY':
        from .models import Delivery
        delivery, _ = Delivery.objects.get_or_create(order=order)
        delivery.state = 'READY_FOR_PICKUP'
        delivery.version += 1
        delivery.save()
    order.version += 1
    fields.append('version')
    order.save(update_fields=fields)
    if action == 'cancel_cash' and order.table_id:
        # Completed diners still occupy their places until the separate cleaning action.
        occupied = Order.objects.filter(table_id=order.table_id, is_cleared=False).exclude(
            order_status=Order.OrderStatus.CANCELLED,
        ).exists()
        if not occupied:
            Table.objects.filter(pk=order.table_id).update(status=Table.Status.AVAILABLE)
    return order


def active_orders_q():
    return (
        Q(order__is_cleared=False)
        & ~Q(order__order_status=Order.OrderStatus.CANCELLED)
        & Q(order__items__menu_item__category=MenuItem.Category.PHO)
    )


def tables_with_capacity():
    return Table.objects.annotate(
        used_capacity=Coalesce(Sum('order__items__quantity', filter=active_orders_q()), 0),
        remaining_cap=F('capacity') - Coalesce(Sum('order__items__quantity', filter=active_orders_q()), 0),
    )


def tables_are_full():
    return not tables_with_capacity().filter(remaining_cap__gt=0).exists()


def used_bowls(table):
    return (
        OrderItem.objects.filter(
            order__table=table,
            order__is_cleared=False,
            menu_item__category=MenuItem.Category.PHO,
        )
        .exclude(order__order_status=Order.OrderStatus.CANCELLED)
        .aggregate(total=Sum('quantity'))['total']
        or 0
    )


def active_queue_ticket(request):
    waiting = QueueTicket.objects.filter(
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).select_related('table')
    if request.user.is_authenticated and getattr(request.user, 'is_customer', lambda: False)():
        ticket = waiting.filter(customer=request.user).first()
        if ticket:
            request.session['queue_ticket_id'] = ticket.pk
            return ticket
    ticket_id = request.session.get('queue_ticket_id')
    if ticket_id:
        return waiting.filter(pk=ticket_id).first()
    return None


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_coords(lat_raw, lng_raw):
    if isinstance(lat_raw, bool) or isinstance(lng_raw, bool):
        return None
    try:
        lat = float(str(lat_raw).strip().replace(',', '.'))
        lng = float(str(lng_raw).strip().replace(',', '.'))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def compute_delivery_fee(lat=None, lng=None):
    from .checkout import delivery_price
    coords = parse_coords(lat, lng)
    if coords is None:
        return None, None, False
    try:
        fee, distance = delivery_price(coords)
        return fee, distance, True
    except ValueError:
        distance = haversine_km(settings.RESTAURANT_LAT, settings.RESTAURANT_LNG, *coords)
        return None, Decimal(str(round(distance, 6))), False


def customer_point(lat, lng):
    try:
        from django.contrib.gis.geos import Point
        return Point(float(lng), float(lat), srid=4326)
    except Exception:
        return None
