import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.middleware.csrf import rotate_token
from django.utils import timezone

from .domain import BusinessError, serialized
from .models import BrowserAccountVault, SavedAccountSession, User, UserAddress

VAULT_COOKIE = 'pho_accounts'


def find_vault(request):
    token = request.COOKIES.get(VAULT_COOKIE, '')
    if not token or len(token) > 100:
        return None
    return BrowserAccountVault.objects.filter(token_digest=hashlib.sha256(token.encode()).hexdigest()).first()


def valid_slots(vault):
    if not vault:
        return SavedAccountSession.objects.none()
    from django.db.models import F
    return vault.slots.filter(revoked=False, expires_at__gt=timezone.now(), user__is_active=True,
                              auth_epoch=F('user__auth_epoch')).select_related('user')


@serialized
def remember_login(request, user):
    vault = find_vault(request)
    if not vault:
        token = secrets.token_urlsafe(32)
        vault = BrowserAccountVault.objects.create(token_digest=hashlib.sha256(token.encode()).hexdigest())
        request.new_vault_token = token
    else:
        # Explicit password authentication extends the cookie to the new slot's
        # absolute lifetime. Switching alone never extends either lifetime.
        request.new_vault_token = request.COOKIES[VAULT_COOKIE]
    now = timezone.now()
    slot, _ = SavedAccountSession.objects.update_or_create(vault=vault, user=user, defaults={
        'auth_epoch': user.auth_epoch, 'verified_at': now,
        'expires_at': now + timedelta(days=getattr(settings, 'SAVED_ACCOUNT_DAYS', 7)), 'revoked': False})
    activate_slot(request, vault, slot)


def activate_slot(request, vault, slot):
    # Flush first: login() alone can preserve data from an anonymous guest session.
    request.session.flush()
    login(request, slot.user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.set_expiry(slot.expires_at)
    rotate_token(request)
    vault.active_slot, vault.generation = slot, vault.generation + 1
    vault.save(update_fields=['active_slot', 'generation'])
    request.session['vault_generation'] = vault.generation
    request.session['vault_slot'] = slot.pk
    request.account_vault = vault


@serialized
def switch_account(request, slot_id):
    vault = find_vault(request)
    slot = valid_slots(vault).filter(pk=slot_id).first()
    if not slot:
        raise BusinessError('Phiên tài khoản đã hết hạn hoặc bị thu hồi. Hãy đăng nhập lại.')
    activate_slot(request, vault, slot)
    return slot.user


@serialized
def logout_current(request):
    vault = find_vault(request)
    if vault:
        if vault.active_slot_id:
            SavedAccountSession.objects.filter(pk=vault.active_slot_id).update(revoked=True)
        vault.active_slot, vault.generation = None, vault.generation + 1
        vault.save(update_fields=['active_slot', 'generation'])
    logout(request)
    request.account_vault = vault


@serialized
def save_address(user, data, address_id=None, version=None):
    User.objects.select_for_update().get(pk=user.pk)
    address = UserAddress.objects.filter(pk=address_id, user=user).first() if address_id else UserAddress(user=user)
    if not address or (address_id and int(version or 0) != address.version):
        raise BusinessError('Địa chỉ đã thay đổi hoặc không thuộc tài khoản. Hãy tải lại.')
    for field in ('recipient_name', 'phone', 'street', 'ward', 'district', 'province', 'label', 'note', 'latitude', 'longitude'):
        if field in data:
            setattr(address, field, data[field])
    make_default = data.get('is_default') or not user.addresses.exists() or address.is_default
    if make_default:
        user.addresses.filter(is_default=True).update(is_default=False)
    address.is_default = bool(make_default)
    address.version += bool(address_id)
    address.full_clean()
    address.save()
    return address


@serialized
def delete_address(user, address_id, version):
    User.objects.select_for_update().get(pk=user.pk)
    address = UserAddress.objects.filter(pk=address_id, user=user).first()
    if not address or address.version != int(version or 0):
        raise BusinessError('Địa chỉ đã thay đổi hoặc không thuộc tài khoản.')
    if address.is_default and user.addresses.count() > 1:
        raise BusinessError('Chọn địa chỉ mặc định khác trước khi xóa địa chỉ này.')
    address.delete()
