from django import template

register = template.Library()


@register.simple_tag
def delivery_destination(order):
    from pho_app.locations import delivery_destination as destination_for
    return destination_for(order)


@register.filter
def compact_amount(value):
    from decimal import Decimal, InvalidOperation
    try:
        amount = Decimal(str(value))
        if amount >= 1000 and amount % 1000 == 0:
            return f'{int(amount // 1000)}K'
        return f'{int(amount)}đ'
    except (InvalidOperation, ValueError, TypeError):
        return value


@register.filter
def state_tone(state):
    if state in ('CLOSED', 'SUCCEEDED', 'COMPLETED', 'DELIVERED', 'PAID', 'AVAILABLE'):
        return 'green'
    if state in ('APPROVED', 'REPLACING', 'IN_TRANSIT', 'DELIVERING', 'REFUND_CONFIRMED'):
        return 'blue'
    if state in ('REJECTED', 'CANCELLED', 'FAILED_FINAL', 'FAILED', 'EXPIRED'):
        return 'red'
    return 'orange'
