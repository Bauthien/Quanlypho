import os

list_html = '''{% extends "pho_app/base.html" %}
{% block title %}Quản lý bàn - Phở Gia Truyền{% endblock %}
{% block content %}
<section class="hero-banner">
    <div class="hero-content">
        <h1>Quản lý Bàn</h1>
        <p>Thêm, sửa, xóa danh sách bàn ăn tại quán</p>
    </div>
</section>
<div class="workspace" style="flex-direction: column;">
    <div class="panel" style="width: 100%; max-width: 800px; margin: 0 auto;">
        <div class="page-title">
            <h2>Danh sách bàn</h2>
            <a class="checkout-btn" href="{% url 'admin_table_create' %}" style="display:inline-block; width:auto;">+ Thêm bàn mới</a>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Số Bàn / Tên Bàn</th>
                    <th>Trạng thái hiện tại</th>
                    <th>Thao tác</th>
                </tr>
            </thead>
            <tbody>
                {% for table in tables %}
                <tr>
                    <td>{{ table.id }}</td>
                    <td>Bàn {{ table.table_number }}</td>
                    <td>{{ table.get_status_display }}</td>
                    <td>
                        <div style="display: flex; gap: 8px;">
                            <a class="ghost-btn primary" href="{% url 'admin_table_edit' table.id %}" style="padding: 4px 12px; font-size: 0.85rem;">Sửa</a>
                            <form method="post" action="{% url 'admin_table_delete' table.id %}" onsubmit="return confirm('Bạn có chắc muốn xóa bàn này?');">
                                {% csrf_token %}
                                <button type="submit" class="ghost-btn" style="color: red; border-color: red; padding: 4px 12px; font-size: 0.85rem;">Xóa</button>
                            </form>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr><td colspan="4" style="text-align: center;">Chưa có bàn nào.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}'''

form_html = '''{% extends "pho_app/base.html" %}
{% block title %}{% if table %}Sửa bàn{% else %}Thêm bàn mới{% endif %} - Phở Gia Truyền{% endblock %}
{% block content %}
<div class="workspace" style="justify-content: center;">
    <form class="panel auth-form" method="post" style="width: 100%; max-width: 400px; margin-top: 40px;">
        {% csrf_token %}
        <h2 style="text-align: center; margin-bottom: 20px;">{% if table %}Sửa thông tin Bàn{% else %}Thêm Bàn Mới{% endif %}</h2>
        <div class="form-group">
            <label>Số bàn / Tên bàn (VD: 1, 2, VIP1...)</label>
            <input type="text" class="form-input" name="table_number" value="{{ table.table_number|default:'' }}" required>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 20px;">
            <a class="ghost-btn" href="{% url 'admin_table_list' %}" style="flex:1; text-align:center;">Hủy</a>
            <button class="checkout-btn" type="submit" style="flex:1;">Lưu</button>
        </div>
    </form>
</div>
{% endblock %}'''

os.makedirs('pho_app/templates/pho_app/admin', exist_ok=True)
with open('pho_app/templates/pho_app/admin/table_list.html', 'w', encoding='utf-8') as f:
    f.write(list_html)
with open('pho_app/templates/pho_app/admin/table_form.html', 'w', encoding='utf-8') as f:
    f.write(form_html)
