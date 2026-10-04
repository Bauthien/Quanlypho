from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegistrationForm, RoleUpdateForm
from .models import User


def home(request):
	if request.user.is_authenticated:
		return redirect('pho_app:role_home')
	return redirect('pho_app:login')


def register(request):
	if request.user.is_authenticated:
		return redirect('pho_app:role_home')

	form = RegistrationForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user)
		messages.success(request, 'Đăng ký tài khoản thành công.')
		return redirect('pho_app:role_home')
	return render(request, 'pho_app/register.html', {'form': form})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('pho_app:role_home')

	form = LoginForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		return redirect('pho_app:role_home')
	return render(request, 'pho_app/login.html', {'form': form})


@login_required
def role_home(request):
	if request.user.is_superuser or request.user.role == User.Role.ADMIN:
		return redirect('pho_app:admin_dashboard')
	return render(request, 'pho_app/welcome.html', {
		'role_name': request.user.get_role_display(),
	})


@login_required
def admin_dashboard(request):
	if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
		messages.error(request, 'Bạn không có quyền truy cập trang quản trị.')
		return redirect('pho_app:role_home')

	users = User.objects.order_by('-date_joined')
	return render(request, 'pho_app/admin_dashboard.html', {
		'users': users,
		'role_choices': User.Role.choices,
		'total_users': users.count(),
		'customer_count': users.filter(role=User.Role.CUSTOMER).count(),
		'staff_count': users.filter(role=User.Role.STAFF).count(),
		'kitchen_count': users.filter(role=User.Role.KITCHEN).count(),
		'admin_count': users.filter(role=User.Role.ADMIN).count(),
	})


@login_required
@require_POST
def update_user_role(request, user_id):
	if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
		messages.error(request, 'Bạn không có quyền thay đổi vai trò tài khoản.')
		return redirect('pho_app:role_home')

	user = get_object_or_404(User, pk=user_id)
	form = RoleUpdateForm(request.POST)
	if form.is_valid():
		user.role = form.cleaned_data['role']
		user.save(update_fields=['role'])
		messages.success(request, f'Đã cập nhật vai trò của {user.username}.')
	else:
		messages.error(request, 'Vai trò được chọn không hợp lệ.')
	return redirect('pho_app:admin_dashboard')


@login_required
@require_POST
def logout_view(request):
	logout(request)
	return redirect('pho_app:login')
