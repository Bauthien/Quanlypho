import io, re
with io.open('pho_app/static/pho_app/js/menu.js', 'r', encoding='utf-8') as f:
    text = f.read()

table_change = '''
tableSelect.addEventListener('change', () => {
    const selectedOption = tableSelect.options[tableSelect.selectedIndex];
    if (selectedOption && selectedOption.dataset.remaining) {
        remainingCapacity = parseInt(selectedOption.dataset.remaining, 10);
    } else {
        remainingCapacity = 999;
    }
    renderCart();
});
'''

if 'tableSelect.addEventListener' not in text:
    text += table_change

with io.open('pho_app/static/pho_app/js/menu.js', 'w', encoding='utf-8') as f:
    f.write(text)
