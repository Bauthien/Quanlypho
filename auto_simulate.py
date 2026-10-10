import re
with open('pho_app/templates/pho_app/customer/order_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure the form has an ID
text = text.replace(
    '<form method="POST" action="{% url \'simulate_vietqr_payment\' order.id %}">',
    '<form id="simulate-payment-form" method="POST" action="{% url \'simulate_vietqr_payment\' order.id %}">'
)

# Add the auto-submit script for DEV purposes
if 'autoSimulate' not in text:
    script = '''
    {% if order.payment_status == 'PENDING' and order.payment_method == 'VIETQR' %}
    <script>
        // DEV: Tự động mô phỏng thanh toán VietQR thành công sau 8 giây để test luồng
        setTimeout(() => {
            const form = document.getElementById('simulate-payment-form');
            if(form) form.submit();
        }, 8000);
    </script>
    {% endif %}
'''
    text = text.replace('{% block extra_js %}', '{% block extra_js %}' + script)
    with open('pho_app/templates/pho_app/customer/order_detail.html', 'w', encoding='utf-8') as f:
        f.write(text)
