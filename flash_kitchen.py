import re
with open('pho_app/templates/pho_app/kitchen/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
                if (newWorkspace && currentWorkspace && newWorkspace.innerHTML !== currentWorkspace.innerHTML) {
                    currentWorkspace.innerHTML = newWorkspace.innerHTML;
                    
                    // Flash notification effect
                    const cards = currentWorkspace.querySelectorAll('.kitchen-card');
                    if (cards.length > 0) {
                        cards[0].style.transition = 'box-shadow 0.5s';
                        cards[0].style.boxShadow = '0 0 20px #28a745';
                        setTimeout(() => cards[0].style.boxShadow = '', 2000);
                    }
                    
                    if (navigator.vibrate) navigator.vibrate([250, 100, 250]);
                }
'''
if 'box-shadow' not in text:
    text = re.sub(r'if \(newWorkspace && currentWorkspace.*?vibrate\(\[250, 100, 250\]\);\s*}', replacement.strip(), text, flags=re.DOTALL)
    with open('pho_app/templates/pho_app/kitchen/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
