"""One transaction gate for financial/stock writers in this single-shop app.

The PostgreSQL transaction advisory lock precedes row locks, including legacy
views. It deliberately serializes shop mutations; do not hold it during network
I/O. A multi-shop deployment should partition this gate by shop ID.
"""
import hashlib
import json
from functools import wraps

from django.db import connection, transaction

from .models import AuditEvent, RequestKey


class BusinessError(ValueError):
    pass


def serialized(fn):
    @wraps(fn)
    def call(*args, **kwargs):
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_advisory_xact_lock(%s)', [70420261023])
            return fn(*args, **kwargs)
    return call


def request_key(scope, key, payload):
    if not key or len(key) > 80:
        raise BusinessError('Thiếu mã yêu cầu hợp lệ. Hãy tải lại trang và thử lại.')
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    obj, created = RequestKey.objects.get_or_create(scope=scope, key=key, defaults={'fingerprint': digest})
    if obj.fingerprint != digest:
        raise BusinessError('Mã yêu cầu đã dùng với nội dung khác.')
    return obj


def audit(actor, action, obj, **detail):
    AuditEvent.objects.create(actor=actor if getattr(actor, 'is_authenticated', False) else None,
                              action=action, object_type=type(obj).__name__, object_id=str(obj.pk), detail=detail)
