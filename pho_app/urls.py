from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dang-nhap/', views.login_view, name='login'),
    path('dang-ky/', views.register_view, name='register'),
    path('dang-xuat/', views.logout_view, name='logout'),

    path('thuc-don/', views.menu_view, name='menu'),
    path('thuc-don/dat-mon/', views.place_order, name='place_order'),
    path('thuc-don/don/<int:order_id>/', views.order_detail, name='order_detail'),
    path('hang-doi/lay-so/', views.take_queue_number, name='take_queue'),
    path('hang-doi/trang-thai/', views.queue_status, name='queue_status'),
    path('thanh-toan/vietqr/webhook/', views.vietqr_webhook, name='vietqr_webhook'),

    path('thu-ngan/', views.staff_home, name='staff_home'),
    path('thu-ngan/xac-nhan-tien-mat/<int:order_id>/', views.confirm_cash_payment, name='confirm_cash'),
    path('thu-ngan/goi-so/', views.call_next_queue, name='call_next_queue'),
    path('thu-ngan/ban-giao/<int:order_id>/', views.handover_delivery, name='handover_delivery'),
    path('thu-ngan/giao-xong/<int:order_id>/', views.complete_delivery, name='complete_delivery'),
    path('thu-ngan/phuc-vu-xong/<int:order_id>/', views.complete_dine_in, name='complete_dine_in'),
    path('thu-ngan/ban/<int:table_id>/da-don/', views.free_table, name='free_table'),

    path('bep/', views.kitchen_home, name='kitchen_home'),
    path('bep/bat-dau/<int:order_id>/', views.kitchen_start, name='kitchen_start'),
    path('bep/hoan-tat/<int:order_id>/', views.kitchen_complete, name='kitchen_complete'),
    path('bep/tem-giao-hang/<int:order_id>/', views.delivery_labels, name='delivery_labels'),

    path('quan-ly/', views.admin_home, name='admin_home'),
    path('quan-ly/nguoi-dung/', views.admin_users, name='admin_users'),
    path('quan-ly/nguoi-dung/<int:user_id>/vai-tro/', views.admin_update_role, name='admin_update_role'),
    path('quan-ly/thuc-don/', views.admin_menu_list, name='admin_menu'),
    path('quan-ly/thuc-don/them/', views.admin_menu_create, name='admin_menu_create'),
    path('quan-ly/thuc-don/<int:item_id>/sua/', views.admin_menu_edit, name='admin_menu_edit'),
    path('quan-ly/thuc-don/<int:item_id>/xoa/', views.admin_menu_delete, name='admin_menu_delete'),
    path('quan-ly/topping/them/', views.admin_topping_create, name='admin_topping_create'),
    path('quan-ly/topping/<int:topping_id>/sua/', views.admin_topping_edit, name='admin_topping_edit'),
    path('quan-ly/topping/<int:topping_id>/xoa/', views.admin_topping_delete, name='admin_topping_delete'),
]
