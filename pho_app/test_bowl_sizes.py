import json
from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .checkout import resolve_cart
from .domain import BusinessError
from .models import CustomizationOption, Ingredient, MenuItem, Order, OrderItem, Recipe, Topping, User
from .recipes import recipe_revision
from .services import inventory_deductions, inventory_totals, order_inventory_deductions


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BowlRecipeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='bowl-admin',role='ADMIN')
        cls.food = MenuItem.objects.create(name='Phở theo cỡ tô',base_price=50000)
        cls.other = MenuItem.objects.create(name='Phở khác',base_price=45000)
        cls.drink = MenuItem.objects.create(name='Trà',category='DRINK',base_price=20000)
        cls.noodle = Ingredient.objects.create(name='Bánh phở',unit='kg',current_stock=10)
        cls.broth = Ingredient.objects.create(name='Nước dùng',unit='lit',current_stock=20)
        cls.topping = Topping.objects.create(name='Trứng thêm',price=10000)
        cls.egg = Ingredient.objects.create(name='Trứng',unit='quả',current_stock=20)
        cls.choices = [CustomizationOption.objects.create(category=category,name=category).pk for category in ['BROTH','VEGGIE','NOODLE']]

    def setUp(self):
        self.client.force_login(self.admin)

    def rows(self,amount):
        return [{'ingredient_id':self.noodle.pk,'quantity':amount,'input_unit':'g'}]

    def save(self,sizes=None,**overrides):
        payload={'recipe_target':'MENU','menu_item_id':self.food.pk,'revision':recipe_revision(self.food),
                 'rows':json.dumps(self.rows('200')),'size_rows':json.dumps(sizes or {'S':self.rows('150'),'M':self.rows('200'),'L':self.rows('250')})}
        payload.update(overrides)
        return self.client.post(reverse('admin_recipe_create'),payload)

    def test_three_sizes_saved_and_reloaded_without_changing_stock(self):
        response=self.save()
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.food.recipes.count(),3)
        self.assertEqual(dict(self.food.recipes.values_list('bowl_size','quantity_required')),
                         {'S':Decimal('.15'),'M':Decimal('.20'),'L':Decimal('.25')})
        data=self.client.get(reverse('admin_inventory')).context['recipe_editor_data']
        product=next(p for p in data['products'] if p['kind']=='menu' and p['id']==self.food.pk)
        self.assertEqual(product['size_rows']['S'][0]['quantity'],'0.15')
        self.assertEqual(product['size_rows']['M'][0]['quantity'],'0.20')
        self.assertEqual(product['size_rows']['L'][0]['quantity'],'0.25')
        self.noodle.refresh_from_db();self.assertEqual(self.noodle.current_stock,10)

    def test_invalid_size_is_atomic_and_stale_revision_is_rejected(self):
        self.save()
        before=list(self.food.recipes.values_list('pk','bowl_size','quantity_required'))
        for sizes in [{'S':self.rows('100'),'M':self.rows('200'),'L':self.rows('0')},
                      {'S':[],'M':[],'L':[]},{'S':self.rows('100'),'M':self.rows('200'),'XL':self.rows('300')}]:
            response=self.save(sizes)
            self.assertEqual(response.status_code,422,response.content)
            self.assertEqual(list(self.food.recipes.values_list('pk','bowl_size','quantity_required')),before)
        previous=recipe_revision(self.food)
        self.food.recipes.filter(bowl_size='L').update(quantity_required='.30')
        self.assertEqual(self.save(revision=previous).status_code,409)

    def test_unconfigured_sizes_and_legacy_medium_edit(self):
        response=self.save({'S':[],'M':self.rows('180'),'L':[]})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.food.recipes.get().bowl_size,'M')
        self.save()
        response=self.client.post(reverse('admin_recipe_create'),{'recipe_target':'MENU','menu_item_id':self.food.pk,
            'revision':recipe_revision(self.food),'rows':json.dumps(self.rows('220'))})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(dict(self.food.recipes.values_list('bowl_size','quantity_required')),
                         {'S':Decimal('.15'),'M':Decimal('.22'),'L':Decimal('.25')})

    def test_drinks_toppings_and_bad_units_cannot_receive_food_sizes(self):
        response=self.save(recipe_target='DRINK',menu_item_id=self.drink.pk,revision=recipe_revision(self.drink))
        self.assertEqual(response.status_code,422)
        response=self.save(recipe_target='TOPPING',menu_item_id='',topping_id=self.topping.pk,applies_to_all='1',revision=recipe_revision(self.topping))
        self.assertEqual(response.status_code,422)
        sizes={'S':self.rows('100'),'M':self.rows('200'),'L':[{'ingredient_id':self.noodle.pk,'quantity':'250','input_unit':'ml'}]}
        self.assertEqual(self.save(sizes).status_code,422)
        self.assertFalse(Recipe.objects.exists())

    def test_depletion_uses_only_chosen_size_and_toppings_once(self):
        self.save()
        Recipe.objects.create(topping=self.topping,ingredient=self.egg,quantity_required=1)
        deductions=inventory_deductions([(self.food,2,[(self.topping,2)],'S'),(self.food,1,[],'L')])
        self.assertEqual(dict(inventory_totals(deductions)),{self.noodle.pk:Decimal('.55'),self.egg.pk:Decimal('2')})
        self.assertEqual(dict(inventory_totals(inventory_deductions([(self.food,1,[])]))),{self.noodle.pk:Decimal('.20')})
        self.food.recipes.filter(bowl_size='S').delete()
        self.food.refresh_from_db()
        with self.assertRaises(BusinessError):inventory_deductions([(self.food,1,[],'S')])

    def test_checkout_keeps_size_and_reserves_exact_amount(self):
        self.save()
        customer=User.objects.create_user(username='bowl-customer')
        self.client.force_login(customer)
        cart=[{'id':self.food.pk,'qty':2,'bowl_size':'S','customizations':self.choices},
              {'id':self.food.pk,'qty':1,'bowl_size':'L','customizations':self.choices}]
        response=self.client.post(reverse('place_order'),{'cart':json.dumps(cart),'order_type':'DINE_IN','payment_method':'CASH','request_key':'bowl-mixed'})
        self.assertEqual(response.status_code,302)
        order=Order.objects.get(customer=customer)
        self.assertEqual(list(order.items.values_list('bowl_size',flat=True)),['S','L'])
        self.assertEqual(dict(order_inventory_deductions(order)),{self.noodle.pk:Decimal('.55')})
        versions=[entry['bom_version'] for entry in order.stock_reservation.bom_snapshot]
        from .models import BOMVersion
        self.assertEqual(set(BOMVersion.objects.filter(pk__in=versions).values_list('snapshot__bowl_size',flat=True)),{'S','L'})
        self.food.recipes.update(quantity_required=2)
        from .services import apply_order_action
        apply_order_action(order.pk,'confirm_cash')
        self.noodle.refresh_from_db();self.assertEqual(self.noodle.current_stock,Decimal('9.45'))

    def test_cart_rejects_invalid_or_drink_size_and_defaults_old_cart_to_medium(self):
        line=resolve_cart([{'id':self.food.pk,'customizations':self.choices}])[0]
        self.assertEqual(line['bowl_size'],'M')
        for size in ['XL','',[],None]:
            with self.subTest(size=size),self.assertRaises(BusinessError):
                resolve_cart([{'id':self.food.pk,'customizations':self.choices,'bowl_size':size}])
        with self.assertRaises(BusinessError):resolve_cart([{'id':self.drink.pk,'bowl_size':'L'}])

    def test_permissions_and_csrf_apply_to_batch_of_sizes(self):
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.admin)
        self.assertEqual(secure.post(reverse('admin_recipe_create'),{'rows':'[]','size_rows':'{}'}).status_code,403)
        self.client.force_login(User.objects.create_user(username='bowl-non-admin'))
        self.assertEqual(self.save().status_code,302)
        self.assertFalse(Recipe.objects.exists())

    def test_database_defaults_keep_older_writers_compatible(self):
        from django.db import connection
        order=Order.objects.create(order_code='BOWL-LEGACY-WRITER')
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO pho_app_recipe (menu_item_id,ingredient_id,quantity_required) VALUES (%s,%s,%s) RETURNING id',
                           [self.food.pk,self.noodle.pk,Decimal('.2')])
            recipe_id=cursor.fetchone()[0]
            cursor.execute('INSERT INTO pho_app_orderitem (order_id,menu_item_id,quantity,item_price) VALUES (%s,%s,%s,%s) RETURNING id',
                           [order.pk,self.food.pk,1,50000])
            item_id=cursor.fetchone()[0]
        self.assertEqual(Recipe.objects.get(pk=recipe_id).bowl_size,'M')
        self.assertEqual(OrderItem.objects.get(pk=item_id).bowl_size,'M')

    def test_menu_only_offers_configured_sizes_with_separate_limits(self):
        self.save({'S':self.rows('100'),'M':[],'L':self.rows('500')})
        response=self.client.get(reverse('menu'))
        product=next(item for item in response.context['menu_payload'] if item['id']==self.food.pk)
        self.assertEqual([(size['value'],size['max_quantity']) for size in product['bowl_sizes']],[('S',99),('L',20)])
        self.assertTrue(product['is_available'])
