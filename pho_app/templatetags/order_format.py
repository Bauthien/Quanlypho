from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def vnd(value):
    """Render saved Decimal amounts consistently, including when JavaScript is off."""
    try:
        amount = Decimal(value)
        if not amount.is_finite():
            return '—'
        return f'{amount:,.0f}'.replace(',', '.') + ' ₫'
    except (InvalidOperation, TypeError, ValueError):
        return '—'
