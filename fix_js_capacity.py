import re
with open('pho_app/templates/pho_app/customer/menu.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Pass remaining_capacity to JS
if 'const remainingCapacity =' not in text:
    js_var = '''<script>
    const currentUserId = "{{ request.user.id|default:'' }}";
    const remainingCapacity = {{ remaining_capacity|default:999 }};
    const customizationOptions = {{ customization_options|safe }};'''
    
    text = text.replace(
        '<script>\n    const currentUserId = "{{ request.user.id|default:\'\' }}";\n    const customizationOptions = {{ customization_options|safe }};',
        js_var
    )
    with open('pho_app/templates/pho_app/customer/menu.html', 'w', encoding='utf-8') as f:
        f.write(text)

with open('pho_app/static/pho_app/js/menu.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Disable button if totalQty > remainingCapacity
disable_logic = '''
    const isTableFull = (typeof remainingCapacity !== 'undefined') && (totalQty > remainingCapacity) && (document.getElementById('orderType').value === 'DINE_IN');
    
    if (isTableFull) {
        checkoutBtn.disabled = true;
        checkoutBtn.textContent = 'Vượt quá số lượng tô cho phép của bàn (' + remainingCapacity + ' tô)';
        checkoutBtn.style.backgroundColor = '#dc3545';
    } else {
        checkoutBtn.disabled = totalQty === 0;
        checkoutBtn.textContent = 'Tiến Hành Đặt Món';
        checkoutBtn.style.backgroundColor = '';
    }
'''

if 'const isTableFull' not in text:
    text = text.replace('checkoutBtn.disabled = totalQty === 0;', disable_logic)
    
    # Also trigger renderCart when orderType changes so it updates the button
    trigger_logic = '''orderType.addEventListener('change', (e) => {
    tableField.style.display = e.target.value === 'DINE_IN' ? 'block' : 'none';
    addressField.style.display = e.target.value === 'DELIVERY' ? 'block' : 'none';
    renderCart();
});'''
    text = re.sub(
        r"orderType\.addEventListener\('change', \(e\) => \{\s*tableField\.style\.display = e\.target\.value === 'DINE_IN' \? 'block' : 'none';\s*addressField\.style\.display = e\.target\.value === 'DELIVERY' \? 'block' : 'none';\s*\}\);",
        trigger_logic,
        text
    )

    with open('pho_app/static/pho_app/js/menu.js', 'w', encoding='utf-8') as f:
        f.write(text)

