from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import User


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, 'Vui lòng đăng nhập để tiếp tục.')
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'Bạn không có quyền truy cập trang này.')
                return redirect(request.user.home_url_name())
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def admin_required(view_func):
    return role_required(User.Role.ADMIN)(view_func)


def staff_required(view_func):
    return role_required(User.Role.STAFF, User.Role.ADMIN)(view_func)


def kitchen_required(view_func):
    return role_required(User.Role.KITCHEN, User.Role.ADMIN)(view_func)
