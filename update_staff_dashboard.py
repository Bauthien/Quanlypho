import re
with open('pho_app/templates/pho_app/staff/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.rfind('<div class="panel">')
end_idx = text.rfind('{% endblock %}')

replacement = '''<div class="panel">
        <h2>Bàn đang có khách</h2>
        {% for table in tables %}{% if table.status == 'OCCUPIED' or table.status == 'CLEANING' %}
        <div class="table-clean-row" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #ddd;">
            <strong>Bàn {{ table.table_number }}</strong>
            <form method="post" action="{% url 'free_table' table.id %}">
                {% csrf_token %}
                <button class="ghost-btn primary" type="submit">Khách ăn xong</button>
            </form>
        </div>
        {% endif %}{% endfor %}
    </div>
</div>
'''

if start_idx != -1 and end_idx != -1:
    new_text = text[:start_idx] + replacement + text[end_idx:]
    with open('pho_app/templates/pho_app/staff/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
