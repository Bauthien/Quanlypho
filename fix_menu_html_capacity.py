import io, re
with io.open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace <option> in select
text = re.sub(
    r'<option value="\{\{ t\.id \}\}" \{\% if selected_table == t\.id\|stringformat:"s" \%\}selected\{\% endif \%\}>Bàn \{\{ t\.table_number \}\}</option>',
    '<option value="{{ t.id }}" data-remaining="{{ t.remaining_cap }}" {% if selected_table == t.id|stringformat:"s" %}selected{% endif %}>Bàn {{ t.table_number }}</option>',
    text
)

# Change const remainingCapacity to let
text = text.replace(
    'const remainingCapacity = {{ remaining_capacity|default:999 }};',
    'let remainingCapacity = {{ remaining_capacity|default:999 }};'
)

with io.open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(text)
