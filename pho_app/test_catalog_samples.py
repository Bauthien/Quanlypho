import hashlib
import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from PIL import Image
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .catalog_sample_data import INGREDIENTS, MENU, PHOTO_SLUGS, TOPPINGS
from .models import AuditEvent, Ingredient, InventoryTransaction, MenuItem, Order, Recipe, Topping
from .services import catalog_stock_limits


class CatalogSampleTests(TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='pho-catalog-test-')
        self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name).resolve()
        self.assets=self.root/'assets';self.assets.mkdir()
        self.media=self.root/'media'
        self.settings_override=override_settings(MEDIA_ROOT=str(self.media))
        self.settings_override.enable();self.addCleanup(self.settings_override.disable)
        manifest={'version':1,'assets':{}}
        for index,slug in enumerate(PHOTO_SLUGS):
            name=slug+'.webp';path=self.assets/name
            Image.new('RGB',(16,16),(index*37%256,index*67%256,index*97%256)).save(path,lossless=True)
            manifest['assets'][slug]={'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'origin':'unit-test'}
        (self.assets/'catalog-assets.json').write_text(json.dumps(manifest),encoding='utf-8')

    def seed(self,**options):
        output=StringIO()
        call_command('add_menu_samples',assets_dir=self.assets,stdout=output,**options)
        return json.loads(output.getvalue())

    def test_complete_catalog_has_distinct_images_recipes_and_opening_stock(self):
        result=self.seed()
        self.assertEqual(MenuItem.objects.filter(category='PHO').count(),7)
        self.assertEqual(MenuItem.objects.filter(category='DRINK').count(),5)
        self.assertEqual(Topping.objects.count(),7)
        self.assertEqual(Ingredient.objects.count(),len(INGREDIENTS))
        self.assertEqual(InventoryTransaction.objects.filter(transaction_type='IMPORT').count(),len(INGREDIENTS))
        self.assertEqual(result['menu_created'],12)
        self.assertEqual(result['toppings_created'],7)
        photos=[item.image_primary.name for item in MenuItem.objects.all()]+[item.image_thumbnail.name for item in Topping.objects.all()]
        self.assertEqual(len(photos),len(set(photos)))
        for photo in photos:
            self.assertTrue((self.media/photo).is_file())
            with Image.open(self.media/photo) as image:image.verify()
        for product in MenuItem.objects.filter(category='PHO'):
            self.assertEqual(set(product.recipes.values_list('bowl_size',flat=True)),{'S','M','L'})
            small=product.recipes.get(bowl_size='S',ingredient__name='Bánh phở tươi').quantity_required
            medium=product.recipes.get(bowl_size='M',ingredient__name='Bánh phở tươi').quantity_required
            large=product.recipes.get(bowl_size='L',ingredient__name='Bánh phở tươi').quantity_required
            self.assertLess(small,medium);self.assertGreater(large,medium)
        self.assertTrue(all(value>0 for value in catalog_stock_limits(MenuItem.objects.all()).values()))

    def test_repeat_does_not_duplicate_or_reset_user_prices_stock_and_recipes(self):
        self.seed()
        item=MenuItem.objects.get(name='Phở Bò Tái');item.base_price=77777;item.save(update_fields=['base_price'])
        ingredient=Ingredient.objects.get(name='Bánh phở tươi');ingredient.current_stock=Decimal('7.25');ingredient.save(update_fields=['current_stock'])
        recipe=item.recipes.get(bowl_size='S',ingredient=ingredient);recipe.quantity_required=Decimal('.99');recipe.save(update_fields=['quantity_required'])
        before=(MenuItem.objects.count(),Topping.objects.count(),Ingredient.objects.count(),Recipe.objects.count(),InventoryTransaction.objects.count(),AuditEvent.objects.count())
        result=self.seed(replace_images=True)
        self.assertEqual(before,(MenuItem.objects.count(),Topping.objects.count(),Ingredient.objects.count(),Recipe.objects.count(),InventoryTransaction.objects.count(),AuditEvent.objects.count()))
        for key in ['menu_created','toppings_created','ingredients_created','recipes_created','photos_updated','opening_transactions_created']:
            self.assertEqual(result[key],0,key)
        item.refresh_from_db();ingredient.refresh_from_db();recipe.refresh_from_db()
        self.assertEqual(item.base_price,77777);self.assertEqual(ingredient.current_stock,Decimal('7.25'));self.assertEqual(recipe.quantity_required,Decimal('.99'))

    def test_existing_case_insensitive_names_orders_and_configuration_are_preserved(self):
        item=MenuItem.objects.create(name='phở bò tái',base_price=43210,image_primary='own-photo.jpg',is_active=False)
        ingredient=Ingredient.objects.create(name='bánh phở tươi',unit='kg',current_stock=8,minimum_stock=2)
        recipe=Recipe.objects.create(menu_item=item,ingredient=ingredient,quantity_required='.33')
        order=Order.objects.create(order_code='KEEP-EXISTING-ORDER')
        self.seed()
        item.refresh_from_db();ingredient.refresh_from_db();recipe.refresh_from_db()
        self.assertEqual(item.base_price,43210);self.assertFalse(item.is_active);self.assertEqual(item.image_primary.name,'own-photo.jpg')
        self.assertEqual(ingredient.current_stock,8);self.assertEqual(ingredient.minimum_stock,2);self.assertEqual(recipe.quantity_required,Decimal('.33'))
        self.assertEqual(MenuItem.objects.filter(name__iexact='phở bò tái').count(),1)
        self.assertTrue(Order.objects.filter(pk=order.pk,order_code='KEEP-EXISTING-ORDER').exists())

    def test_dry_run_keeps_database_and_media_untouched(self):
        report=self.seed(dry_run=True,replace_images=True)
        self.assertTrue(report['dry_run']);self.assertEqual(report['menu_created'],12)
        self.assertFalse(MenuItem.objects.exists());self.assertFalse(Ingredient.objects.exists());self.assertFalse(Recipe.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists());self.assertFalse(self.media.exists())

    def test_missing_photo_and_conflicting_group_do_not_leave_partial_data(self):
        manifest_path=self.assets/'catalog-assets.json'
        original=manifest_path.read_text()
        manifest=json.loads(original);manifest['assets'].pop(PHOTO_SLUGS[0]);manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(CommandError):self.seed()
        self.assertFalse(Ingredient.objects.exists())
        manifest_path.write_text(original)
        Ingredient.objects.create(name='Cà phê',usage='PHO',unit='kg',current_stock=9)
        with self.assertRaises(CommandError):self.seed()
        self.assertEqual(Ingredient.objects.count(),1);self.assertFalse(MenuItem.objects.exists());self.assertFalse(InventoryTransaction.objects.exists())
