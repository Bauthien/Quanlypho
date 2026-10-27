"""Delivery contact and navigation derived from the order's saved destination."""
import re
from urllib.parse import urlencode

from django.conf import settings

from .domain import BusinessError
from .services import parse_coords


def normalize_delivery_phone(value):
    phone = re.sub(r'[\s.()-]', '', str(value))
    if not re.fullmatch(r'\+?[0-9]{9,15}', phone):
        raise BusinessError('Số điện thoại nhận món cần 9–15 chữ số, có thể bắt đầu bằng +.')
    return phone


def delivery_destination(order):
    snapshot = order.delivery_snapshot or {}
    coords = parse_coords(snapshot.get('latitude'), snapshot.get('longitude'))
    if coords is None and order.customer_location:
        coords = parse_coords(order.customer_location.y, order.customer_location.x)
    destination = ','.join(str(value) for value in coords) if coords else order.delivery_address
    if not destination:
        return {}
    origin = parse_coords(snapshot.get('shop_latitude'), snapshot.get('shop_longitude')) or (settings.RESTAURANT_LAT, settings.RESTAURANT_LNG)
    try:
        phone = normalize_delivery_phone(snapshot.get('phone', ''))
    except BusinessError:
        phone = ''
    return {
        'coordinates': ', '.join(f'{value:.7f}' for value in coords) if coords else '',
        'map_url': 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': destination}),
        'directions_url': 'https://www.google.com/maps/dir/?' + urlencode({'api': 1, 'origin': ','.join(str(value) for value in origin), 'destination': destination, 'travelmode': 'driving'}),
        'phone': phone,
    }
