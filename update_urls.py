import re
with open('pho_app/urls.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'cancel_order' not in text:
    text = text.replace(
        "path('thu-ngan/xac-nhan-tien-mat/<int:order_id>/', views.confirm_cash_payment, name='confirm_cash'),",
        "path('thu-ngan/xac-nhan-tien-mat/<int:order_id>/', views.confirm_cash_payment, name='confirm_cash'),\n    path('thu-ngan/huy-don/<int:order_id>/', views.cancel_cash_order, name='cancel_order'),"
    )
    with open('pho_app/urls.py', 'w', encoding='utf-8') as f:
        f.write(text)
