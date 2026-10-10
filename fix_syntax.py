import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "return redirect('menu')        order = Order.objects.create(",
    "return redirect('menu')\n        order = Order.objects.create("
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
