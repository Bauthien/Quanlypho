from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from .accounts import VAULT_COOKIE, find_vault, valid_slots


class ShopTransactionMiddleware:
    """Includes SessionMiddleware's response save in the account transaction gate."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') or request.COOKIES.get(VAULT_COOKIE):
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_advisory_xact_lock(%s)', [70420261023])
                return self.get_response(request)
        return self.get_response(request)


class AccountContextMiddleware(MiddlewareMixin):
    def stale_response(self, request, reason):
        if request.method == 'GET':
            return render(request, 'pho_app/auth/session_expired.html', {'reason': reason}, status=409)
        return JsonResponse({'error': reason, 'login_url': '/dang-nhap/?switch=1'}, status=409)

    def process_view(self, request, view_func, view_args, view_kwargs):
        vault = find_vault(request)
        request.account_vault = vault
        if not vault or getattr(view_func, 'csrf_exempt', False):
            return
        auth_entry = view_func.__name__ in ('login_view', 'register_view', 'logout_view', 'account_switch', 'browser_context')
        if request.user.is_authenticated and not auth_entry:
            slot = valid_slots(vault).filter(pk=vault.active_slot_id, user=request.user).first()
            if not slot or request.session.get('vault_generation') != vault.generation or request.session.get('vault_slot') != slot.pk:
                return self.stale_response(request, 'Phiên tài khoản đã thay đổi hoặc hết hạn. Hãy xác thực lại hoặc chọn một tài khoản còn phiên.')
        elif not request.user.is_authenticated and vault.active_slot_id and not auth_entry:
            return self.stale_response(request, 'Phiên xác thực đã hết hạn hoặc bị thu hồi. Đăng nhập lại để tiếp tục.')
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            generation = request.POST.get('account_generation') or request.headers.get('X-Account-Generation')
            if str(generation) != str(vault.generation):
                return JsonResponse({'error': 'Trang thuộc phiên tài khoản cũ. Tải lại trước khi gửi.'}, status=409)

    def process_response(self, request, response):
        if getattr(request, 'new_vault_token', None):
            response.set_cookie(VAULT_COOKIE, request.new_vault_token,
                max_age=getattr(settings, 'SAVED_ACCOUNT_DAYS', 7) * 86400,
                httponly=True, secure=request.is_secure(), samesite='Lax')
        vault = getattr(request, 'account_vault', None)
        if vault:
            response['X-Account-Generation'] = str(vault.generation)
        return response
