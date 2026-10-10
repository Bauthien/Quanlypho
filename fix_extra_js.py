import io, re
with io.open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

new_block = '''{% block extra_js %}
{{ menu_payload|json_script:"menu-data" }}
{{ customization_options|json_script:"customization-data" }}
{{ toppings|json_script:"topping-data" }}
<script>
    const currentUserId = "{{ request.user.id|default:'' }}";
    const remainingCapacity = {{ remaining_capacity|default:999 }};
    const menuItems = JSON.parse(document.getElementById('menu-data').textContent);
    const customizationOptions = JSON.parse(document.getElementById('customization-data').textContent);
    const toppings = JSON.parse(document.getElementById('topping-data').textContent);
</script>
<script>const queueStatusUrl = "{% url 'queue_status' %}";</script>
<script src="{% static 'pho_app/js/menu.js' %}"></script>
{% endblock %}'''

text = re.sub(r'\{% block extra_js %\}.*?\{% endblock %\}', new_block, text, flags=re.DOTALL)

with io.open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
