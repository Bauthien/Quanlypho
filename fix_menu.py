with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace(
    '<script src="{% static ''pho_app/js/menu.js'' %}"></script>',
    '<script>const currentUserId = "{{ user.id|default:''guest'' }}";</script>\n<script src="{% static ''pho_app/js/menu.js'' %}"></script>'
)
with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
