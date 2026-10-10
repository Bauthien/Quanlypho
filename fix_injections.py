import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_string = "            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',\n"

# We only want to keep it where it is immediately followed by order_type=order_type,
# which is the Order.objects.create call.

# Safest way: Just remove it everywhere, then insert it in Order.objects.create manually.
text = text.replace("            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',\n", "")
text = text.replace("            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',", "")

# Now inject it back ONLY in Order.objects.create
order_create = '''        order = Order.objects.create(
            order_code=_generate_order_code(),
            customer=request.user if request.user.is_authenticated else None,
            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',
            order_type=order_type,'''

text = re.sub(
    r'\s*order = Order\.objects\.create\(\s*order_code=_generate_order_code\(\),\s*customer=request\.user if request\.user\.is_authenticated else None,\s*order_type=order_type,',
    order_create,
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
