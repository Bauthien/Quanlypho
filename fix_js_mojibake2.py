import io, re
with io.open('pho_app/static/pho_app/js/menu.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r'const isTableFull = .*?checkoutBtn\.style\.backgroundColor = \'\';\n    \}',
    '''const isTableFull = (typeof remainingCapacity !== 'undefined') && (totalQty > remainingCapacity) && (document.getElementById('orderType').value === 'DINE_IN');
    
    if (isTableFull) {
        checkoutBtn.disabled = true;
        checkoutBtn.textContent = 'Quá giới hạn của bàn (' + remainingCapacity + ' phần)';
        checkoutBtn.style.backgroundColor = '#dc3545';
    } else {
        checkoutBtn.disabled = totalQty === 0;
        checkoutBtn.textContent = 'Tiến Hành Đặt Món';
        checkoutBtn.style.backgroundColor = '';
    }''',
    text,
    flags=re.DOTALL
)

with io.open('pho_app/static/pho_app/js/menu.js', 'w', encoding='utf-8') as f:
    f.write(text)
