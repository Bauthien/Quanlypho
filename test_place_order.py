import urllib.request
import urllib.parse

req = urllib.request.Request('http://127.0.0.1:8000/thuc-don/')
with urllib.request.urlopen(req) as response:
    cookies = response.headers.get('Set-Cookie')
    csrf = cookies.split('csrftoken=')[1].split(';')[0] if cookies else ''

data = urllib.parse.urlencode({
    'cart': '[{"id":1,"qty":5,"customizations":[],"toppings":[]}]',
    'payment_method': 'VIETQR',
    'order_type': 'DINE_IN',
    'table_id': '1',
    'guest_name': 'Anh Khoa Test',
    'csrfmiddlewaretoken': csrf
}).encode('utf-8')

req2 = urllib.request.Request('http://127.0.0.1:8000/thuc-don/dat-mon/', data=data)
req2.add_header('Cookie', f'csrftoken={csrf}')
try:
    with urllib.request.urlopen(req2) as response2:
        print("Success!", response2.geturl())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.reason)
    print(e.headers.get('Location'))
except Exception as e:
    print(e)
