import io

path = r'd:\Quanlypho\pho_app\templates\pho_app\staff\dashboard.html'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Split the combined {% for %}{% if %} — add line break between them
content = content.replace(
    '        {% for table in tables %}{% if table.active_orders %}',
    '        {% for table in tables %}\r\n        {% if table.active_orders %}'
)

# Fix 2: Close {% if %} block before {% empty %}
# The empty-state paragraph uniquely identifies that location
EMPTY_MARKER = 'Hiện tại chưa có khách đang ngồi ăn tại các bàn.'
content = content.replace(
    '        {% empty %}\r\n        <p class="empty-state">' + EMPTY_MARKER,
    '        {% endif %}\r\n        {% empty %}\r\n        <p class="empty-state">' + EMPTY_MARKER
)

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! Checking result...')
# Verify
with io.open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'for table in tables' in line or 'if table.active_orders' in line or 'endif' in line or 'empty' in line.lower() and 'empty-state' not in line:
        print(f'Line {i}: {line.rstrip()}')
