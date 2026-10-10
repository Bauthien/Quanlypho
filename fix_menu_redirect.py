import re
with open('pho_app/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

menu_redirect_old = '''def menu_view(request):
    if request.user.is_authenticated and request.user.role in (User.Role.STAFF, User.Role.KITCHEN, User.Role.ADMIN):
        return redirect(request.user.home_url_name())'''

menu_redirect_new = '''def menu_view(request):
    selected_table = request.GET.get('table', '')
    if request.user.is_authenticated and request.user.role in (User.Role.STAFF, User.Role.KITCHEN, User.Role.ADMIN):
        if not selected_table:
            return redirect(request.user.home_url_name())'''

text = text.replace(menu_redirect_old, menu_redirect_new)

# Since selected_table is now extracted at the top of menu_view, we need to remove the second extraction later in the function.
text = re.sub(
    r"\s*selected_table = request\.GET\.get\('table', ''\)\s*tables = Table\.objects\.filter\(status=Table\.Status\.AVAILABLE\)",
    "\n    tables = Table.objects.filter(status=Table.Status.AVAILABLE)",
    text
)

with open('pho_app/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
