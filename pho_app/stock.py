from decimal import Decimal, ROUND_CEILING

from django.db.models import Sum
from django.utils import timezone

from .domain import BusinessError, serialized, audit
from .models import (Ingredient, InventoryIncident, InventoryRequirement, InventoryTransaction,
    Order, StockMovement, StockReservation)


def convert_stock_units(quantity, input_unit, stock_unit):
    """Reviewed same-dimension conversions; never infer mass from volume."""
    units = {'g': ('mass', Decimal(1)), 'gram': ('mass', Decimal(1)), 'kg': ('mass', Decimal(1000)),
             'gam': ('mass', Decimal(1)), 'gr': ('mass', Decimal(1)),
             'ml': ('volume', Decimal(1)), 'l': ('volume', Decimal(1000)), 'lít': ('volume', Decimal(1000)),
             'lit': ('volume', Decimal(1000)), 'liter': ('volume', Decimal(1000))}
    source, target = input_unit.strip().lower(), stock_unit.strip().lower()
    quantity = Decimal(str(quantity))
    if not quantity.is_finite() or quantity <= 0:
        raise BusinessError('Số lượng nhập phải dương và hữu hạn.')
    if source == target or not source:
        result = quantity
    elif source in units and target in units and units[source][0] == units[target][0]:
        result = quantity * units[source][1] / units[target][1]
    else:
        raise BusinessError('Không có quy đổi đã duyệt giữa hai đơn vị này; không đổi thể tích sang khối lượng.')
    rounded = result.quantize(Decimal('.01'))
    if rounded != result:
        raise BusinessError('Lượng quy đổi nhỏ hơn độ chính xác 0,01 đơn vị tồn; dùng đơn vị tồn nhỏ hơn hoặc nhập lượng phù hợp.')
    result = rounded
    if result > Decimal('99999999.99'):
        raise BusinessError('Số lượng sau quy đổi vượt giới hạn kho.')
    return result


def reserved_totals(exclude_order=None):
    qs = InventoryRequirement.objects.filter(reservation__state='ACTIVE', reservation__expires_at__gt=timezone.now())
    if exclude_order:
        qs = qs.exclude(reservation__order_id=exclude_order)
    return {row['ingredient_id']: row['total'] for row in qs.values('ingredient_id').annotate(total=Sum('quantity'))}


def available_balances():
    held = reserved_totals()
    blocked = set(InventoryIncident.objects.filter(resolved=False).values_list('ingredient_id', flat=True))
    return {ingredient.pk: Decimal(0) if ingredient.pk in blocked else max(Decimal(0), ingredient.current_stock - held.get(ingredient.pk, 0))
            for ingredient in Ingredient.objects.all()}


def reserve_inventory(order, deductions, snapshot=None):
    from .services import ensure_inventory_available, inventory_totals
    ingredients, required = ensure_inventory_available(deductions, lock=True)
    if snapshot is None:
        import hashlib
        import json
        from .models import BOMVersion
        snapshot = []
        for item in order.items.select_related('menu_item').prefetch_related('toppings__topping'):
            products = [(item.menu_item, item.quantity)] + [(extra.topping, extra.quantity) for extra in item.toppings.all()]
            for product, quantity in products:
                data = {'mode': product.inventory_mode, 'name': product.name, 'product_id': product.pk,
                    'type': type(product).__name__, 'recipes': [{'ingredient': row.ingredient_id,
                        'quantity': str(row.quantity_required), 'unit': row.ingredient.unit}
                        for row in product.recipes.select_related('ingredient').order_by('pk')]}
                fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                version, _ = BOMVersion.objects.get_or_create(fingerprint=fingerprint, defaults={
                    'product_type': type(product).__name__, 'product_id': product.pk, 'snapshot': data})
                snapshot.append({'item': item.pk, 'bom_version': version.pk, 'quantity': quantity})
    reservation = StockReservation.objects.create(order=order, expires_at=order.expires_at,
        bom_snapshot=snapshot)
    InventoryRequirement.objects.bulk_create([InventoryRequirement(reservation=reservation,
        ingredient_id=pk, quantity=qty.quantize(Decimal('.01'), rounding=ROUND_CEILING)) for pk, qty in required.items()])
    return reservation


def commit_reserved_inventory(order):
    from .services import order_inventory_deductions, inventory_totals, InvalidOrderTransition, InsufficientStock
    reservation = StockReservation.objects.filter(order=order).first()
    if reservation:
        if reservation.state == 'CONSUMED':
            return
        if reservation.state != 'ACTIVE' or timezone.now() >= reservation.expires_at:
            raise InvalidOrderTransition('Đã hết thời gian giữ nguyên liệu. Khoản chuyển tiền cần đối soát.')
        required = dict(reservation.lines.values_list('ingredient_id', 'quantity'))
    else:
        # Old pending orders must be revalidated against current available stock.
        # Old PAID orders never enter this transition again and are not re-exported.
        required = inventory_totals(order_inventory_deductions(order))
    held = reserved_totals(exclude_order=order.pk)
    ingredients = list(Ingredient.objects.select_for_update().filter(pk__in=required).order_by('pk'))
    if InventoryIncident.objects.filter(ingredient_id__in=required, resolved=False).exists():
        raise InvalidOrderTransition('Kho đang kiểm kê chênh lệch. Liên hệ điều phối để đối soát.')
    if len(ingredients) != len(required):
        raise InvalidOrderTransition('Cấu hình nguyên liệu đã thay đổi.')
    shortages = [(i, required[i.pk]) for i in ingredients if i.current_stock - held.get(i.pk, 0) < required[i.pk]]
    if shortages:
        raise InsufficientStock(shortages)
    for ingredient in ingredients:
        amount = required[ingredient.pk]
        movement, created = StockMovement.objects.get_or_create(key=f'export:{order.pk}:{ingredient.pk}', defaults={
            'order': order, 'ingredient': ingredient, 'kind': 'EXPORT', 'quantity': -amount, 'actor': order.customer})
        if created:
            ingredient.current_stock -= amount
            ingredient.save(update_fields=['current_stock'])
            InventoryTransaction.objects.create(ingredient=ingredient, transaction_type='EXPORT', quantity_changed=-amount,
                                                  created_by=order.customer)
    if reservation:
        reservation.state = 'CONSUMED'
        reservation.save(update_fields=['state'])


def release_inventory(order, expired=False):
    StockReservation.objects.filter(order=order, state='ACTIVE').update(state='EXPIRED' if expired else 'RELEASED')


@serialized
def return_unused(order_id, ingredient_id, quantity, actor, evidence, key):
    if not actor.is_admin_role() or not evidence.strip():
        raise BusinessError('Quản lý phải ghi bằng chứng xác nhận nguyên liệu chưa dùng với bếp.')
    qty = Decimal(str(quantity))
    if not qty.is_finite() or qty <= 0 or qty != qty.quantize(Decimal('.01')):
        raise BusinessError('Số lượng hoàn kho không hợp lệ.')
    if StockMovement.objects.filter(key=f'return:{key}').exists():
        return
    order = Order.objects.get(pk=order_id)
    if order.order_status != 'CANCELLED':
        raise BusinessError('Chỉ hoàn nguyên liệu chưa dùng của đơn đã hủy.')
    requirement = InventoryRequirement.objects.get(reservation__order=order, ingredient_id=ingredient_id, reservation__state='CONSUMED')
    wasted = StockMovement.objects.filter(order=order, ingredient_id=ingredient_id, kind='WASTE_EXPORTED').aggregate(total=Sum('quantity'))['total'] or 0
    if qty > requirement.quantity - requirement.returned - wasted:
        raise BusinessError('Số hoàn vượt nguyên liệu đã xuất còn lại.')
    ingredient = Ingredient.objects.select_for_update().get(pk=ingredient_id)
    ingredient.current_stock += qty
    ingredient.save(update_fields=['current_stock'])
    requirement.returned += qty
    requirement.save(update_fields=['returned'])
    StockMovement.objects.create(order=order, ingredient=ingredient, kind='RETURN_UNUSED', quantity=qty,
        key=f'return:{key}', actor=actor, evidence=evidence)
    InventoryTransaction.objects.create(ingredient=ingredient, transaction_type='IMPORT', quantity_changed=qty, created_by=actor)
    audit(actor, 'RETURN_UNUSED', order, ingredient=ingredient_id, quantity=str(qty), evidence=evidence)


@serialized
def record_waste(order_id, ingredient_id, quantity, actor, evidence, key):
    qty = Decimal(str(quantity))
    if not qty.is_finite() or qty <= 0 or not evidence.strip():
        raise BusinessError('Cần số lượng dương và lý do hao hụt.')
    if order_id:
        line = InventoryRequirement.objects.get(reservation__order_id=order_id, ingredient_id=ingredient_id, reservation__state='CONSUMED')
        wasted = StockMovement.objects.filter(order_id=order_id, ingredient_id=ingredient_id, kind='WASTE_EXPORTED').aggregate(total=Sum('quantity'))['total'] or 0
        if qty > line.quantity - line.returned - wasted:
            raise BusinessError('Hao hụt vượt lượng đã xuất chưa hoàn.')
        kind = 'WASTE_EXPORTED'  # Already deducted: informational, no second stock debit.
    else:
        kind = 'WASTE_WAREHOUSE'
    movement, created = StockMovement.objects.get_or_create(key=f'waste:{key}', defaults={
        'order_id': order_id, 'ingredient_id': ingredient_id, 'kind': kind, 'quantity': qty, 'actor': actor, 'evidence': evidence})
    if created and not order_id:
        ingredient = Ingredient.objects.select_for_update().get(pk=ingredient_id)
        if available_balances().get(ingredient_id, 0) < qty:
            raise BusinessError('Hao hụt kho vượt tồn khả dụng; cần kiểm kê chênh lệch.')
        ingredient.current_stock -= qty
        ingredient.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(ingredient=ingredient, transaction_type='ADJUST', quantity_changed=-qty, created_by=actor)
    return movement


@serialized
def expire_orders(limit=100):
    from .checkout import release_benefits
    from .models import Table
    ids = list(Order.objects.filter(payment_status='PENDING', order_status='CART', expires_at__lte=timezone.now()).order_by('pk').values_list('pk', flat=True)[:limit])
    for pk in ids:
        order = Order.objects.get(pk=pk)
        release_benefits(order, expired=True)
        order.order_status, order.payment_status = 'CANCELLED', 'FAILED'
        order.version += 1
        order.save(update_fields=['order_status', 'payment_status', 'version', 'updated_at'])
        if order.table_id and not Order.objects.filter(table_id=order.table_id, is_cleared=False).exclude(order_status='CANCELLED').exists():
            Table.objects.filter(pk=order.table_id).update(status='AVAILABLE')
    return len(ids)
