import io, re
with io.open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

bad_block = '''            {% if user.is_authenticated %}
                <button class="checkout-btn" id="checkoutBtn" type="submit" disabled><i class="fa-solid fa-paper-plane"></i> Tiến Hành Đặt Món</button>
            {% else %}
                <a class="checkout-btn checkout-link" id="checkoutBtn" href="{% url 'login' %}" aria-disabled="true"><i class="fa-solid fa-right-to-bracket"></i> Đăng nhập để đặt món</a>
            {% endif %}'''

good_block = '''            <button class="checkout-btn" id="checkoutBtn" type="submit" disabled><i class="fa-solid fa-paper-plane"></i> Tiến Hành Đặt Món</button>'''

text = text.replace(bad_block, good_block)

with io.open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
