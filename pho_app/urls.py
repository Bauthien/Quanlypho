from django.urls import path

from . import views

app_name = 'pho_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('dang-ky/', views.register, name='register'),
    path('dang-nhap/', views.login_view, name='login'),
    path('trang-chu/', views.role_home, name='role_home'),
    path('quan-tri/', views.admin_dashboard, name='admin_dashboard'),
    path('quan-tri/tai-khoan/<int:user_id>/vai-tro/', views.update_user_role, name='update_user_role'),
    path('dang-xuat/', views.logout_view, name='logout'),
]
