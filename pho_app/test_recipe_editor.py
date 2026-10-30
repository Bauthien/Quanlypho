import json
from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .checkout import resolve_cart
from .domain import BusinessError
from .models import Ingredient, MenuItem, Recipe, Topping, User
from .recipes import recipe_revision


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class RecipeEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='recipe-editor-admin', role=User.Role.ADMIN)
        cls.food = MenuItem.objects.create(name='Phở thử', base_price=50000)
        cls.other_food = MenuItem.objects.create(name='Phở khác', base_price=50000)
        cls.drink = MenuItem.objects.create(name='Trà thử', category='DRINK', base_price=20000)
        cls.other_drink = MenuItem.objects.create(name='Cà phê thử', category='DRINK', base_price=20000)
        cls.noodle = Ingredient.objects.create(name='Bánh phở', unit='kg', current_stock=100)
        cls.beef = Ingredient.objects.create(name='Thịt bò', unit='gram', current_stock=1000)
        cls.tea = Ingredient.objects.create(name='Cốt trà', unit='lit', usage='DRINK', current_stock=100)
        cls.sugar = Ingredient.objects.create(name='Đường', unit='gram', usage='SHARED', current_stock=1000)
        cls.bottle = Ingredient.objects.create(name='Nước suối', unit='chai', usage='DRINK', current_stock=100)
        cls.topping = Topping.objects.create(name='Thêm sữa', category='DRINK', price=5000)
        cls.food_topping = Topping.objects.create(name='Bò thêm', price=10000)

    def setUp(self):
        self.client.force_login(self.admin)

    def line(self, ingredient, quantity, unit=None):
        return {'ingredient_id': ingredient.pk, 'quantity': quantity, 'input_unit': unit or ingredient.unit}

    def save_recipe(self, product, rows, **changes):
        topping = isinstance(product, Topping)
        payload = {
            'recipe_target': 'TOPPING' if topping else 'DRINK' if product.category == 'DRINK' else 'MENU',
            'topping_id' if topping else 'menu_item_id': product.pk,
            'revision': recipe_revision(product), 'rows': json.dumps(rows), 'inventory_mode': 'BOM',
            'applies_to_all': '1',
        }
        payload.update(changes)
        return self.client.post(reverse('admin_recipe_create'), payload)

    def test_batch_replaces_formula_and_converts_units_without_changing_stock(self):
        Recipe.objects.create(menu_item=self.food, ingredient=self.sugar, quantity_required=5)
        result = self.save_recipe(self.food, [self.line(self.noodle, '200', 'g'), self.line(self.beef, '80')])
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(dict(self.food.recipes.values_list('ingredient_id', 'quantity_required')),
                         {self.noodle.pk: Decimal('.20'), self.beef.pk: Decimal('80')})
        self.noodle.refresh_from_db()
        self.assertEqual(self.noodle.current_stock, 100)

    def test_invalid_line_keeps_entire_existing_formula(self):
        old = Recipe.objects.create(menu_item=self.food, ingredient=self.noodle, quantity_required='.3')
        for bad in ['0', '-1', 'NaN', 'Infinity', 'invalid', '0.001', '100000000']:
            with self.subTest(amount=bad):
                result = self.save_recipe(self.food, [self.line(self.beef, '50'), self.line(self.sugar, bad)])
                self.assertEqual(result.status_code, 422)
                self.assertEqual(list(self.food.recipes.values_list('pk', flat=True)), [old.pk])

    def test_cross_group_ingredients_and_duplicate_lines_are_rejected(self):
        for product, rows in [
            (self.food, [self.line(self.tea, '1')]),
            (self.drink, [self.line(self.noodle, '1')]),
            (self.food, [self.line(self.noodle, '1'), self.line(self.noodle, '2')]),
        ]:
            with self.subTest(product=product, rows=rows):
                self.assertEqual(self.save_recipe(product, rows).status_code, 422)
        self.assertFalse(Recipe.objects.exists())

    def test_shared_ingredient_can_be_used_for_both_groups(self):
        for product in [self.food, self.drink]:
            self.assertEqual(self.save_recipe(product, [self.line(self.sugar, '10')]).status_code, 200)

    def test_stale_editor_cannot_overwrite_formula(self):
        previous = recipe_revision(self.food)
        recipe = Recipe.objects.create(menu_item=self.food, ingredient=self.noodle, quantity_required='.2')
        response = self.save_recipe(self.food, [self.line(self.beef, '50')], revision=previous)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(list(self.food.recipes.values_list('pk', flat=True)), [recipe.pk])

    def test_small_conversion_is_rejected_instead_of_rounded(self):
        result = self.save_recipe(self.food, [self.line(self.noodle, '5', 'g')])
        self.assertEqual(result.status_code, 422)
        self.assertIn('0,01', result.json()['errors']['rows'][0]['message'])

    def test_drink_conversion_supports_existing_lit_unit(self):
        result = self.save_recipe(self.drink, [self.line(self.tea, '150', 'ml')])
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(self.drink.recipes.get().quantity_required, Decimal('.15'))

    def test_packaged_drink_has_one_counted_stock_item(self):
        result = self.save_recipe(self.drink, [self.line(self.bottle, '1')], inventory_mode='DIRECT')
        self.assertEqual(result.status_code, 200, result.content)
        self.drink.refresh_from_db()
        self.assertEqual(self.drink.inventory_mode, 'DIRECT')
        for rows in [[self.line(self.bottle, '2')], [self.line(self.tea, '1')], [self.line(self.bottle, '1'), self.line(self.sugar, '10')]]:
            self.assertEqual(self.save_recipe(self.drink, rows, inventory_mode='DIRECT').status_code, 422)
        self.assertEqual(self.drink.recipes.count(), 1)

    def test_topping_scope_and_eligible_drinks_are_saved_and_enforced(self):
        result = self.save_recipe(self.topping, [self.line(self.sugar, '10')], applies_to_all='', allowed_menu_items=[self.drink.pk])
        self.assertEqual(result.status_code, 200, result.content)
        self.topping.refresh_from_db()
        self.assertFalse(self.topping.applies_to_all)
        line = resolve_cart([{'id': self.drink.pk, 'toppings': [self.topping.pk]}])[0]
        self.assertEqual(line['price'], 25000)
        with self.assertRaises(BusinessError):
            resolve_cart([{'id': self.other_drink.pk, 'toppings': [self.topping.pk]}])
        with self.assertRaises(BusinessError):
            resolve_cart([{'id': self.drink.pk, 'toppings': [self.food_topping.pk]}])

    def test_empty_or_wrong_category_topping_scope_is_rejected(self):
        for allowed in [[], [self.food.pk]]:
            self.assertEqual(self.save_recipe(self.topping, [self.line(self.sugar, '10')], applies_to_all='', allowed_menu_items=allowed).status_code, 422)
        self.assertFalse(self.topping.recipes.exists())

    def test_empty_malformed_or_excessive_rows_are_rejected(self):
        for rows in [[], {}, [None], [self.line(self.beef, '1')]*201]:
            self.assertEqual(self.save_recipe(self.food, rows).status_code, 422)

    def test_target_type_cannot_be_spoofed(self):
        self.assertEqual(self.save_recipe(self.food, [self.line(self.sugar, '1')], recipe_target='DRINK').status_code, 422)
        self.assertEqual(self.save_recipe(self.food, [self.line(self.sugar, '1')], topping_id=self.topping.pk).status_code, 422)

    def test_inventory_editor_contains_real_groups_and_saved_formula(self):
        Recipe.objects.create(menu_item=self.food, ingredient=self.noodle, quantity_required='.2')
        response = self.client.get(reverse('admin_inventory'))
        self.assertContains(response, 'data-recipe-clear')
        self.assertContains(response, 'value="DRINK"')
        data = response.context['recipe_editor_data']
        saved = next(p for p in data['products'] if p['kind'] == 'menu' and p['id'] == self.food.pk)
        self.assertEqual(saved['rows'][0]['quantity'], '0.20')
        self.assertEqual(saved['revision'], recipe_revision(self.food))

    def test_inventory_groups_count_shared_stock_in_both_groups(self):
        response = self.client.get(reverse('admin_inventory'))
        self.assertEqual(response.context['food_ingredient_count'], 3)
        self.assertEqual(response.context['drink_ingredient_count'], 3)
        self.assertEqual(response.context['shared_ingredient_count'], 1)
        self.assertEqual(len(response.context['ingredients']), 5)
        self.assertContains(response, 'data-category="PHO DRINK"')
        self.assertContains(response, 'data-list-category="PHO"')
        self.assertContains(response, 'data-list-category="DRINK"')

    def test_new_ingredient_inherits_selected_inventory_group(self):
        for group in ['PHO', 'DRINK', 'SHARED']:
            with self.subTest(group=group):
                response = self.client.get(reverse('admin_ingredient_create'), {'usage': group})
                self.assertEqual(response.context['form']['usage'].value(), group)
        response = self.client.get(reverse('admin_ingredient_create'), {'usage': 'invalid'})
        self.assertEqual(response.context['form']['usage'].value(), 'PHO')

    def test_ingredient_group_cannot_invalidate_an_existing_recipe(self):
        Recipe.objects.create(menu_item=self.food, ingredient=self.sugar, quantity_required=10)
        payload = {'name': self.sugar.name, 'unit': self.sugar.unit, 'usage': 'DRINK',
                   'current_stock': '1000', 'minimum_stock': '0'}
        response = self.client.post(reverse('admin_ingredient_edit', args=[self.sugar.pk]), payload)
        self.assertFormError(response.context['form'], 'usage',
                             'Nguyên liệu đang dùng ở nhóm khác. Chọn “Dùng chung” hoặc cập nhật các công thức trước.')
        self.sugar.refresh_from_db()
        self.assertEqual(self.sugar.usage, 'SHARED')
        self.assertEqual(self.food.recipes.count(), 1)

    def test_batch_endpoint_requires_admin_and_csrf(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.admin)
        self.assertEqual(secure.post(reverse('admin_recipe_create'), {'rows':'[]'}).status_code, 403)
        customer = User.objects.create_user(username='recipe-customer')
        self.client.force_login(customer)
        self.assertEqual(self.save_recipe(self.food, [self.line(self.beef, '10')]).status_code, 302)
        self.assertFalse(Recipe.objects.exists())

    def test_data_migration_uses_existing_recipes_to_classify_shared_stock(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        Recipe.objects.create(menu_item=self.food, ingredient=self.sugar, quantity_required=10)
        Recipe.objects.create(menu_item=self.drink, ingredient=self.sugar, quantity_required=20)
        Recipe.objects.create(menu_item=self.drink, ingredient=self.tea, quantity_required=1)
        Ingredient.objects.filter(pk__in=[self.sugar.pk, self.tea.pk]).update(usage='PHO')
        migrate = import_module('pho_app.migrations.0020_recipe_groups').assign_ingredient_groups
        migrate(apps, SimpleNamespace(connection=connection))
        self.sugar.refresh_from_db()
        self.tea.refresh_from_db()
        self.assertEqual(self.sugar.usage, 'SHARED')
        self.assertEqual(self.tea.usage, 'DRINK')
        self.assertEqual(Recipe.objects.count(), 3)
