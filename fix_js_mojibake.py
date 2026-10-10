import io
with io.open('pho_app/static/pho_app/js/menu.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "'Vượt quá số lượng tô cho phép của bàn ('",
    "'Vượt quá số lượng cho phép của bàn ('"
).replace(
    "'Vt quA s lng tA\' cho phAcp c a bAn ('",
    "'Vượt quá số lượng cho phép của bàn ('"
).replace(
    "+ ' tA')'",
    "+ ' phần)'"
).replace(
    "+ ' tô)'",
    "+ ' phần)'"
)

with io.open('pho_app/static/pho_app/js/menu.js', 'w', encoding='utf-8') as f:
    f.write(text)
