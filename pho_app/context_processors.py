from django.db.models import F
from .models import Ingredient


def inventory_alerts(request):
    """Cung cấp số lượng và danh sách nguyên liệu sắp hết hàng cho Admin/Staff trong thời gian thực."""
    if request.user.is_authenticated and (request.user.is_admin_role() or request.user.is_staff_role()):
        try:
            low_stock_qs = Ingredient.objects.filter(current_stock__lte=F('minimum_stock')).order_by('current_stock')
            return {
                'low_stock_count': low_stock_qs.count(),
                'low_stock_ingredients': list(low_stock_qs[:5]),
            }
        except Exception:
            return {'low_stock_count': 0, 'low_stock_ingredients': []}
    return {'low_stock_count': 0, 'low_stock_ingredients': []}
