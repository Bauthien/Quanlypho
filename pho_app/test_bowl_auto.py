import json
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Ingredient, MenuItem, Recipe, Topping, User
from .nlp_bom import suggest_recipe_bom
from .recipes import recipe_revision


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BowlAutoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=User.objects.create_user(username='bowl-auto-admin',role='ADMIN')
        cls.food=MenuItem.objects.create(name='Phở bò tái',base_price=50000)
        cls.noodle=Ingredient.objects.create(name='Bánh phở tươi',unit='kg',current_stock=10)
        cls.broth=Ingredient.objects.create(name='Nước dùng',unit='lit',current_stock=20)
        cls.beef=Ingredient.objects.create(name='Thịt bò',unit='gram',current_stock=1000)
        cls.egg=Ingredient.objects.create(name='Trứng gà',unit='quả',current_stock=20)
        cls.drink=MenuItem.objects.create(name='Trà thử',category='DRINK',base_price=20000)
        cls.tea=Ingredient.objects.create(name='Cốt trà',unit='lit',usage='DRINK',current_stock=10)
        cls.topping=Topping.objects.create(name='Thịt bò thêm',price=10000)

    def setUp(self):self.client.force_login(self.admin)

    def suggest(self,size='M',product=None,target='MENU'):
        product=product or self.food
        return self.client.get(reverse('admin_recipe_auto_suggest'),{'target':target,'id':product.pk,'bowl_size':size})

    def quantities(self,result):
        return {row['ingredient_id']:Decimal(row['quantity']) for row in result['rows']}

    def test_selected_size_changes_standard_suggestion_to_80_100_120_percent(self):
        results={size:self.suggest(size).json() for size in ['S','M','L']}
        self.assertEqual([self.quantities(results[size])[self.noodle.pk] for size in ['S','M','L']],
                         [Decimal('160'),Decimal('200'),Decimal('240')])
        self.assertEqual([self.quantities(results[size])[self.broth.pk] for size in ['S','M','L']],
                         [Decimal('520'),Decimal('650'),Decimal('780')])
        self.assertEqual([self.quantities(results[size])[self.beef.pk] for size in ['S','M','L']],
                         [Decimal('64'),Decimal('80'),Decimal('96')])
        self.assertFalse(Recipe.objects.exists())

    def test_saved_medium_is_reference_and_repeated_clicks_do_not_compound(self):
        Recipe.objects.create(menu_item=self.food,ingredient=self.noodle,quantity_required='.3')
        Recipe.objects.create(menu_item=self.food,ingredient=self.broth,quantity_required='.5')
        Recipe.objects.create(menu_item=self.food,ingredient=self.beef,quantity_required=70)
        Recipe.objects.create(menu_item=self.food,ingredient=self.egg,quantity_required=1)
        Recipe.objects.create(menu_item=self.food,ingredient=self.noodle,quantity_required='.99',bowl_size='S')
        first=self.suggest('S').json();second=self.suggest('S').json();large=self.suggest('L').json()
        self.assertEqual(self.quantities(first),self.quantities(second))
        self.assertEqual(self.quantities(first),{self.noodle.pk:Decimal('240'),self.broth.pk:Decimal('400'),self.beef.pk:Decimal('56'),self.egg.pk:Decimal('1')})
        self.assertEqual(self.quantities(large)[self.noodle.pk],Decimal('360'))
        self.assertEqual(first['reference'],'saved_medium')
        self.assertEqual(first['bowl_size'],'S')
        self.assertEqual(Recipe.objects.filter(bowl_size='S').get().quantity_required,Decimal('.99'))

    def test_generated_quantities_round_to_stock_precision_and_save_three_sizes(self):
        self.beef.unit='kg';self.beef.save(update_fields=['unit'])
        medium=[Recipe.objects.create(menu_item=self.food,ingredient=self.noodle,quantity_required='.23'),
                Recipe.objects.create(menu_item=self.food,ingredient=self.beef,quantity_required='.08'),
                Recipe.objects.create(menu_item=self.food,ingredient=self.egg,quantity_required=1)]
        rows={size:self.suggest(size).json()['rows'] for size in ['S','M','L']}
        small={row['ingredient_id']:row['quantity'] for row in rows['S']}
        self.assertEqual(Decimal(small[self.noodle.pk]),Decimal('180'))
        self.assertEqual(Decimal(small[self.beef.pk]),Decimal('60'))
        self.assertEqual(Decimal(small[self.egg.pk]),Decimal('1'))
        response=self.client.post(reverse('admin_recipe_create'),{'recipe_target':'MENU','menu_item_id':self.food.pk,
            'rows':json.dumps(rows['M']),'size_rows':json.dumps(rows),'revision':recipe_revision(self.food)})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.food.recipes.count(),9)
        self.noodle.refresh_from_db();self.assertEqual(self.noodle.current_stock,10)

    def test_invalid_size_is_rejected_and_missing_size_defaults_to_medium(self):
        self.assertEqual(self.suggest('XL').status_code,422)
        response=self.client.get(reverse('admin_recipe_auto_suggest'),{'target':'MENU','id':self.food.pk})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['bowl_size'],'M')

    def test_drink_and_topping_quantities_do_not_use_bowl_multiplier(self):
        for product,target in [(self.drink,'DRINK'),(self.topping,'TOPPING')]:
            with self.subTest(target=target):
                self.assertEqual(self.quantities(self.suggest('S',product,target).json()),self.quantities(self.suggest('L',product,target).json()))

    def test_special_bowl_keeps_whole_eggs_for_every_size(self):
        ingredients=list(Ingredient.objects.values('id','name','unit','usage'))
        for size in ['S','M','L']:
            result=suggest_recipe_bom('Phở bò đặc biệt',available_ingredients=ingredients,bowl_size=size)
            self.assertEqual(self.quantities(result)[self.egg.pk],1)

    def test_suggestion_requires_admin_and_does_not_modify_data(self):
        before=list(Ingredient.objects.values_list('pk','current_stock'))
        for size in ['S','M','L']:self.assertEqual(self.suggest(size).status_code,200)
        self.assertEqual(list(Ingredient.objects.values_list('pk','current_stock')),before)
        self.assertFalse(Recipe.objects.exists())
        self.client.force_login(User.objects.create_user(username='bowl-auto-customer'))
        self.assertEqual(self.suggest('S').status_code,302)
