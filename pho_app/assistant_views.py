"""Read-only assistance grounded in the current menu; no external AI is configured.

The Figma chat UI uses this catalog mode honestly, without inventing stock,
prices or order data. Financial actions remain in checkout/support screens.
"""
import json
import re
import unicodedata
from collections import Counter

from django.http import JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import MenuItem, OrderItem
from .services import catalog_stock_limits, inventory_deductions, inventory_totals, InvalidOrderTransition
from .stock import available_balances


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn').replace('đ', 'd')


@require_POST
def assistant_reply(request):
    if request.user.is_authenticated and not request.user.is_customer():
        return JsonResponse({'ok': False, 'error': 'Trợ lý dành cho không gian khách hàng.'}, status=403)
    try:
        if len(request.body) > 5000:
            raise ValueError()
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError()
        message = payload.get('message', '')
        people, budget = payload.get('people', 2), payload.get('budget', 150000)
        if not isinstance(message, str) or not message.strip() or len(message) > 1000:
            raise ValueError()
        if type(people) is not int or not 1 <= people <= 8 or type(budget) is not int or not 1000 <= budget <= 10000000:
            raise ValueError()
        if type(payload.get('use_history', False)) is not bool:
            raise ValueError()
    except (ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Nhập câu hỏi tối đa 1.000 ký tự, 1–8 người và ngân sách từ 1.000đ đến 10.000.000đ.'}, status=400)

    text = normalize(message)
    result = {'ok': True, 'mode': 'catalog', 'updated_at': timezone.localtime().strftime('%H:%M · %d/%m/%Y'),
              'products': [], 'links': [], 'history_used': False,
              'notice': 'Gợi ý theo quy tắc từ dữ liệu Phở Nhà; chưa kết nối mô hình AI.'}
    account_url = reverse('account') if request.user.is_authenticated else reverse('login')
    if any(term in text for term in ('di ung', 'allergy', 'an toan suc khoe')):
        result['text'] = 'Mình chưa có thông tin thành phần và dị ứng đã được cửa hàng xác nhận. Hãy trao đổi trực tiếp với cửa hàng trước khi chọn món; mình không thể xác nhận món an toàn chỉ từ tên món.'
    elif any(term in text for term in ('hoan tien', 'huy don', 'giao thieu', 'giao bu', 'doi tra', 'nhan vien', 'ho tro', 'don hang', 'ma don')):
        result['text'] = 'Mở đúng đơn của bạn và chọn “Yêu cầu hỗ trợ” để hủy đơn, báo món lỗi hoặc theo dõi hoàn tiền. Cửa hàng kiểm tra theo trạng thái đơn. Mình không tự tạo yêu cầu hoặc xác nhận đã hoàn tiền trong hội thoại.'
        result['links'] = [{'label': 'Mở đơn của tôi' if request.user.is_authenticated else 'Đăng nhập để xem đơn', 'url': account_url + ('?tab=my-orders' if request.user.is_authenticated else '')}]
    elif any(term in text for term in ('voucher', 'khuyen mai', 'ma giam')):
        result['text'] = 'Mỗi đơn dùng một voucher trong ví hoặc một mã khuyến mãi. Ưu đãi hạng áp dụng tự động. Có thể dùng thêm điểm còn khả dụng sau ưu đãi, tối đa 50% số tiền còn lại; điều kiện mã và tổng phải trả được kiểm tra tại giỏ hàng.'
        result['links'] = [{'label': 'Xem ví voucher' if request.user.is_authenticated else 'Đăng nhập để xem ví', 'url': account_url + ('?tab=wallet' if request.user.is_authenticated else '')}]
    elif any(term in text for term in ('quyen loi', 'hang', 'tich diem', 'diem danh', 'thanh vien')):
        result['text'] = 'Điểm khả dụng và tổng chi tiêu xét hạng là hai chỉ số riêng. 10.000đ thực trả tiền món được tính 1 điểm khi đơn hoàn tất; phí giao không tích điểm. Điểm có hạn 12 tháng. Bạc có 2 mã freeship/tháng; Vàng miễn giao gần và 3 mã giao xa; Kim Cương miễn giao gần và 10 mã giao xa.'
        result['links'] = [{'label': 'Xem quyền lợi của tôi' if request.user.is_authenticated else 'Đăng nhập thành viên', 'url': account_url + ('?tab=membership' if request.user.is_authenticated else '')}]
    elif not any(term in text for term in ('pho', 'mon', 'ngan sach', 'nguoi', 'goi y', 'an', 'nuoc', 'do uong')):
        result['text'] = 'Mình có thể gợi ý món theo ngân sách, tìm món còn phục vụ và giải thích voucher hoặc quyền lợi thành viên. Bạn muốn tìm món cho bao nhiêu người?'
    else:
        match = re.search(r'\b(\d{1,2})\s*(?:nguoi|phan|to)\b', text)
        if match:
            people = int(match.group(1))
            if not 1 <= people <= 8:
                return JsonResponse({'ok': False, 'error': 'Hiện trợ lý hỗ trợ gợi ý cho 1–8 người. Hãy chọn lại số người.'}, status=400)
        match = re.search(r'(-?\d+(?:[.,]\d+)?)\s*(k|nghin|ngan|trieu)\b', text)
        if match:
            budget = int(float(match.group(1).replace(',', '.')) * (1000000 if match.group(2) == 'trieu' else 1000))
        else:
            match = re.search(r'(-?\d{1,3}(?:[.,]\d{3})+|-?\d{4,8})\s*(?:d|dong|vnd)?\b', text)
            if match:
                budget = int(match.group(1).replace('.', '').replace(',', ''))
        if not 1000 <= budget <= 10000000:
            return JsonResponse({'ok': False, 'error': 'Chọn ngân sách tiền món từ 1.000đ đến 10.000.000đ.'}, status=400)
        drink = any(term in text for term in ('do uong', 'nuoc uong', 'nuoc ngot'))
        products = list(MenuItem.objects.filter(is_active=True, base_price__gt=0, category='DRINK' if drink else 'PHO').order_by('base_price', 'pk')[:30])
        limits = catalog_stock_limits(products)
        products = [product for product in products if limits.get(product.pk, 0) > 0]
        if payload.get('use_history') and request.user.is_authenticated:
            favorites = set(OrderItem.objects.filter(order__customer=request.user, order__order_status='COMPLETED').order_by('-order__created_at').values_list('menu_item_id', flat=True)[:30])
            products.sort(key=lambda product: (product.pk not in favorites, product.base_price, product.pk))
            result['history_used'] = True
        selected, remaining = Counter(), budget
        balances = available_balances()
        for _ in range(people):
            options = sorted(products, key=lambda product: (selected[product.pk] > 0, products.index(product)))
            for product in options:
                if selected[product.pk] >= limits[product.pk] or product.base_price > remaining:
                    continue
                remaining_slots = people - sum(selected.values()) - 1
                minimum_price = min((p.base_price for p in products), default=0)
                if remaining_slots and remaining - product.base_price < minimum_price * remaining_slots:
                    continue
                proposed = selected.copy(); proposed[product.pk] += 1
                try:
                    required = inventory_totals(inventory_deductions([(p, proposed[p.pk], []) for p in products if proposed[p.pk]]))
                except InvalidOrderTransition:
                    continue
                if any(balances.get(ingredient_id, 0) < amount for ingredient_id, amount in required.items()):
                    continue
                selected = proposed; remaining -= int(product.base_price)
                break
        for product in products:
            if not selected[product.pk]:
                continue
            filename = 'nuoc-uong.jpg' if drink else 'pho-tai.jpg'
            result['products'].append({'id': product.pk, 'name': product.name, 'price': int(product.base_price),
                'quantity': selected[product.pk], 'image': product.image_primary.url if product.image_primary else static('pho_app/images/' + filename),
                'url': reverse('menu') + '?dish=' + str(product.pk), 'reason': 'Giá món hiện tại, chưa gồm topping và phí giao.'})
        quantity = sum(selected.values())
        total = budget - remaining
        if quantity:
            result['text'] = f'Có thể chọn {quantity} phần trong ngân sách {budget:,.0f}đ. Tổng tiền món dự tính {total:,.0f}đ, chưa gồm topping và phí giao. Giá và tồn được kiểm tra lại khi bạn đặt món.'.replace(',', '.')
            if quantity < people:
                result['text'] += ' Hiện chưa đủ số phần cho mọi người trong ngân sách và lượng món còn phục vụ; bạn có thể đổi ngân sách hoặc số người.'
            result['subtotal'] = total
        else:
            result['text'] = 'Chưa có món còn phục vụ phù hợp ngân sách này. Bạn có thể tăng ngân sách, giảm số người hoặc xem thực đơn để chọn món khác.'
        result['links'] = [{'label': 'Xem thực đơn', 'url': reverse('menu')}]
    response = JsonResponse(result)
    response['Cache-Control'] = 'no-store'
    return response
