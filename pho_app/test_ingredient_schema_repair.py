from decimal import Decimal
from importlib import import_module
from unittest import skipUnless

from django.apps import apps
from django.db import IntegrityError, connection
from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from .models import Ingredient, InventoryTransaction, User


@skipUnless(connection.vendor == 'postgresql', 'Legacy schema repair targets PostgreSQL.')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IngredientSchemaRepairTests(TransactionTestCase):
    def setUp(self):
        self.changed_active_default = False
        self.admin = User.objects.create_user(username='schema-repair-admin', role=User.Role.ADMIN)
        self.client.force_login(self.admin)
        self.payload = {
            'name': 'Đá', 'unit': 'kg', 'usage': 'DRINK',
            'current_stock': '20', 'minimum_stock': '5',
        }

    def tearDown(self):
        if self.changed_active_default:
            with connection.cursor() as cursor:
                cursor.execute('ALTER TABLE pho_app_ingredient ALTER COLUMN is_active SET DEFAULT TRUE')
        super().tearDown()

    def add_legacy_column(self):
        with connection.cursor() as cursor:
            # is_active is now a modeled field. Reproduce the legacy defect by
            # removing only its database default, without adding it a second time.
            cursor.execute('ALTER TABLE pho_app_ingredient ALTER COLUMN is_active DROP DEFAULT')
            self.changed_active_default = True

    def repair_schema(self):
        migration = import_module('pho_app.migrations.0021_repair_ingredient_is_active_default')
        with connection.schema_editor() as editor:
            migration.repair_legacy_is_active_default(apps, editor)

    def assert_ingredient_created(self):
        response = self.client.post(reverse('admin_ingredient_create') + '?usage=DRINK', self.payload)
        self.assertRedirects(response, reverse('admin_inventory'), fetch_redirect_response=False)
        ingredient = Ingredient.objects.get(name='Đá')
        self.assertEqual(ingredient.usage, 'DRINK')
        self.assertEqual(ingredient.current_stock, Decimal('20'))
        self.assertEqual(ingredient.minimum_stock, Decimal('5'))
        entry = InventoryTransaction.objects.get(ingredient=ingredient)
        self.assertEqual(entry.transaction_type, 'IMPORT')
        self.assertEqual(entry.quantity_changed, Decimal('20'))
        self.assertEqual(entry.created_by, self.admin)
        return ingredient

    def test_legacy_required_column_is_repaired_before_creating_ingredient(self):
        self.add_legacy_column()
        with self.assertRaises(IntegrityError):
            # An older application omits the extra column; current Django models
            # correctly supply is_active themselves, so use an actual legacy INSERT.
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO pho_app_ingredient (name,unit,usage,current_stock,minimum_stock,ingredient_image) VALUES ('Legacy test','kg','PHO',0,0,'')")
        self.assertFalse(Ingredient.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists())

        self.repair_schema()
        ingredient = self.assert_ingredient_created()
        with connection.cursor() as cursor:
            cursor.execute('SELECT is_active FROM pho_app_ingredient WHERE id = %s', [ingredient.pk])
            self.assertIs(cursor.fetchone()[0], True)

    def test_fresh_database_does_not_gain_a_legacy_column(self):
        with connection.cursor() as cursor:
            cursor.execute('ALTER TABLE pho_app_ingredient RENAME COLUMN is_active TO repair_test_active')
        try:
            self.repair_schema()
            with connection.cursor() as cursor:
                columns = connection.introspection.get_table_description(cursor, Ingredient._meta.db_table)
            self.assertNotIn('is_active', [column.name for column in columns])
        finally:
            with connection.cursor() as cursor:
                cursor.execute('ALTER TABLE pho_app_ingredient RENAME COLUMN repair_test_active TO is_active')
        self.assert_ingredient_created()

    def test_repair_preserves_existing_flags_and_can_be_repeated(self):
        active = Ingredient.objects.create(name='Existing active', unit='kg')
        inactive = Ingredient.objects.create(name='Existing inactive', unit='kg')
        self.add_legacy_column()
        with connection.cursor() as cursor:
            cursor.execute('UPDATE pho_app_ingredient SET is_active = FALSE WHERE id = %s', [inactive.pk])
        self.repair_schema()
        self.repair_schema()
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, is_active FROM pho_app_ingredient ORDER BY id')
            flags = dict(cursor.fetchall())
        self.assertEqual(flags, {active.pk: True, inactive.pk: False})
        self.assert_ingredient_created()
