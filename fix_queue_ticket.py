import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_text = '''    active_ticket = QueueTicket.objects.filter(
        customer=request.user if request.user.is_authenticated else None,
            guest_name=request.POST.get('guest_name', '')[:100] if not request.user.is_authenticated else '',
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).select_related('table').first() if request.user.is_authenticated else None'''

good_text = '''    active_ticket = QueueTicket.objects.filter(
        customer=request.user,
        status__in=[QueueTicket.Status.WAITING, QueueTicket.Status.CALLED],
    ).select_related('table').first() if request.user.is_authenticated else None'''

text = text.replace(bad_text, good_text)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
