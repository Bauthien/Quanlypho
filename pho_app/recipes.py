"""Batch recipe editing; validate every line before replacing the saved formula."""
import hashlib
import json
from collections import defaultdict
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .domain import BusinessError
from .models import Ingredient, MenuItem, Recipe, Topping
from .stock import convert_stock_units


COUNT_UNITS = {'chai', 'lon', 'hộp', 'gói', 'cái', 'quả', 'viên', 'phần'}


def recipe_revision(product, rows=None, allowed_ids=None):
    if rows is None:
        rows = list(product.recipes.order_by('pk').values_list('pk', 'ingredient_id', 'quantity_required'))
    value = [rows, product.inventory_mode]
    if isinstance(product, Topping):
        value += [product.category, product.applies_to_all, sorted(allowed_ids if allowed_ids is not None else product.allowed_menu_items.values_list('pk', flat=True))]
    return hashlib.sha256(json.dumps(value, default=str).encode()).hexdigest()


def recipe_editor_data(ingredients, menu_items, toppings, recipes):
    formulas = defaultdict(lambda: defaultdict(Decimal))
    snapshots = defaultdict(list)
    ingredient_units = {i.pk: i.unit for i in ingredients}
    for recipe in recipes:
        key = f'topping:{recipe.topping_id}' if recipe.topping_id else f'menu:{recipe.menu_item_id}'
        formulas[key][recipe.ingredient_id] += recipe.quantity_required
        snapshots[key].append((recipe.pk, recipe.ingredient_id, recipe.quantity_required))
    products = []
    for kind, items in [('menu', menu_items), ('topping', toppings)]:
        for item in items:
            key = f'{kind}:{item.pk}'
            allowed_ids = [p.pk for p in item.allowed_menu_items.all()] if kind == 'topping' else []
            products.append({
                'id': item.pk, 'kind': kind, 'name': item.name, 'category': item.category,
                'inventory_mode': item.inventory_mode,
                'rows': [{'ingredient_id': pk, 'quantity': str(qty), 'input_unit': ingredient_units[pk]}
                         for pk, qty in formulas[key].items()],
                'revision': recipe_revision(item, rows=sorted(snapshots[key]), allowed_ids=allowed_ids),
                'applies_to_all': item.applies_to_all if kind == 'topping' else True,
                'allowed_menu_items': [p.pk for p in item.allowed_menu_items.all() if p.is_active] if kind == 'topping' else [],
            })
    return {'ingredients': [{'id': i.pk, 'name': i.name, 'unit': i.unit, 'usage': i.usage} for i in ingredients],
            'products': products}


class RecipeBatchForm(forms.Form):
    recipe_target = forms.ChoiceField(choices=[('MENU', 'Món chính'), ('DRINK', 'Nước uống'), ('TOPPING', 'Topping')])
    menu_item_id = forms.ModelChoiceField(queryset=MenuItem.objects.filter(is_active=True), required=False)
    topping_id = forms.ModelChoiceField(queryset=Topping.objects.filter(is_active=True), required=False)
    rows = forms.JSONField()
    revision = forms.CharField(max_length=64)
    inventory_mode = forms.ChoiceField(choices=[('BOM', 'Pha chế'), ('DIRECT', 'Đóng chai / lon')], required=False)
    applies_to_all = forms.BooleanField(required=False)
    allowed_menu_items = forms.ModelMultipleChoiceField(queryset=MenuItem.objects.filter(is_active=True), required=False)

    def clean(self):
        data = super().clean()
        menu, topping, kind = data.get('menu_item_id'), data.get('topping_id'), data.get('recipe_target')
        if bool(menu) == bool(topping) or (kind == 'TOPPING') != bool(topping):
            raise ValidationError('Chọn đúng một sản phẩm còn kinh doanh để thiết lập định lượng.')
        target = topping or menu
        if not target:
            return data
        category = target.category
        if kind in ('MENU', 'DRINK') and category != ('PHO' if kind == 'MENU' else 'DRINK'):
            raise ValidationError('Món được chọn không thuộc nhóm sản phẩm này.')
        self.target = target
        if topping and not data.get('applies_to_all') and not data.get('allowed_menu_items'):
            self.add_error('allowed_menu_items', 'Chọn ít nhất một món được gọi kèm topping.')
        if topping and any(item.category != category for item in data.get('allowed_menu_items', [])):
            self.add_error('allowed_menu_items', 'Món gọi kèm phải cùng nhóm với topping.')
        rows = data.get('rows')
        if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
            self.add_error('rows', 'Thêm từ 1 đến 200 nguyên liệu trước khi lưu.')
            return data
        ids = [str(row.get('ingredient_id', '')) for row in rows if isinstance(row, dict)]
        ingredients = {str(i.pk): i for i in Ingredient.objects.filter(pk__in=[pk for pk in ids if pk.isascii() and pk.isdigit() and len(pk) < 19])}
        seen, cleaned_rows = set(), []
        amount_field = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('.01'))
        for index, row in enumerate(rows, 1):
            try:
                if not isinstance(row, dict):
                    raise ValidationError('Dòng nguyên liệu không hợp lệ.')
                ingredient = ingredients.get(str(row.get('ingredient_id')))
                if not ingredient or ingredient.usage not in (category, Ingredient.Usage.SHARED):
                    raise ValidationError('Chọn nguyên liệu phù hợp với nhóm sản phẩm.')
                if ingredient.pk in seen:
                    raise ValidationError('Nguyên liệu đã có trong công thức.')
                seen.add(ingredient.pk)
                quantity = amount_field.clean(str(row.get('quantity', '')).replace(',', '.'))
                input_unit = str(row.get('input_unit') or ingredient.unit)[:50]
                quantity = convert_stock_units(quantity, input_unit, ingredient.unit)
                if ingredient.unit.strip().lower() in COUNT_UNITS and quantity != quantity.to_integral_value():
                    raise ValidationError('Đơn vị chai, lon, quả hoặc viên phải là số nguyên.')
                cleaned_rows.append((ingredient, quantity))
            except (ValidationError, BusinessError) as exc:
                self.add_error('rows', f'Dòng {index}: {"; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)}')
        mode = data.get('inventory_mode') or 'BOM'
        if menu and category == 'DRINK' and mode == 'DIRECT':
            if len(cleaned_rows) != 1 or cleaned_rows[0][1] != 1 or cleaned_rows[0][0].unit.strip().lower() not in COUNT_UNITS:
                self.add_error('rows', 'Nước đóng chai / lon cần đúng một hàng trong kho, số lượng 1 và đơn vị chai / lon tương ứng.')
        data['cleaned_rows'] = cleaned_rows
        return data
