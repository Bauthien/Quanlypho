import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# place_order
text = text.replace('@login_required\n@require_POST\ndef place_order(request):', '@require_POST\ndef place_order(request):')
text = re.sub(
    r'if not request\.user\.is_customer\(\):\s*messages\.error\(request, \'Chỉ khách hàng mới được đặt món\.\'\)\s*return redirect\(request\.user\.home_url_name\(\)\)',
    "if request.user.is_authenticated and not request.user.is_customer():\n        messages.error(request, 'Chỉ khách hàng mới được đặt món.')\n        return redirect(request.user.home_url_name())",
    text
)

# Replace request.user with customer in Order creation
text = re.sub(
    r'customer=request\.user,',
    "customer=request.user if request.user.is_authenticated else None,\n            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',",
    text
)

# In place_order, save the order to session if guest
replacement_session = '''
        messages.info(request, f'Đơn {order.order_code} đã tạo. Trạng thái: chờ thanh toán.')
        if not request.user.is_authenticated:
            guest_orders = request.session.get('guest_orders', [])
            guest_orders.append(order.pk)
            request.session['guest_orders'] = guest_orders
            request.session['latest_order_id'] = order.pk
        return redirect('order_detail', order_id=order.pk)
'''
text = re.sub(
    r'messages\.info\(request,.*?Trạng thái: chờ thanh toán\.\'\)\s*return redirect\(\'order_detail\', order_id=order\.pk\)',
    replacement_session.strip(),
    text
)


# order_detail
text = text.replace('@login_required\ndef order_detail(request, order_id):', 'def order_detail(request, order_id):')
replacement_detail = '''def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item', 'items__toppings__topping', 'items__customizations__customization'), pk=order_id)
    if order.customer:
        if not request.user.is_authenticated or order.customer != request.user:
            return redirect('menu')
    else:
        if order.pk not in request.session.get('guest_orders', []):
            return redirect('menu')
'''
text = re.sub(
    r'def order_detail\(request, order_id\):\s*order = get_object_or_404\(Order\.objects\.prefetch_related[^\)]*\), pk=order_id, customer=request\.user\)',
    replacement_detail,
    text
)

# simulate_vietqr_payment
text = text.replace('@login_required\n@require_POST\ndef simulate_vietqr_payment(request, order_id):', '@require_POST\ndef simulate_vietqr_payment(request, order_id):')
replacement_simulate = '''def simulate_vietqr_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, payment_method=Order.PaymentMethod.VIETQR)
    if order.customer:
        if not request.user.is_authenticated or order.customer != request.user:
            return redirect('menu')
    else:
        if order.pk not in request.session.get('guest_orders', []):
            return redirect('menu')
'''
text = re.sub(
    r'def simulate_vietqr_payment\(request, order_id\):\s*order = get_object_or_404\(Order, pk=order_id, customer=request\.user, payment_method=Order\.PaymentMethod\.VIETQR\)',
    replacement_simulate,
    text
)

# menu_view latest_order fix
text = text.replace(
    "latest_order = Order.objects.filter(customer=request.user).order_by('-created_at').first() if request.user.is_authenticated else None",
    "latest_order = Order.objects.filter(customer=request.user).order_by('-created_at').first() if request.user.is_authenticated else Order.objects.filter(pk=request.session.get('latest_order_id')).first()"
)
# active_ticket fix
text = text.replace(
    "customer=request.user,\n        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],\n    ).select_related('table').first() if request.user.is_authenticated else None",
    "customer=request.user if request.user.is_authenticated else None,\n        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],\n    ).select_related('table').first() if request.user.is_authenticated else None"
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
