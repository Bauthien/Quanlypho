from datetime import timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (AuditEvent, Ingredient, InventoryIncident, InventoryRequirement, InventoryTransaction,
                     MenuItem, Order, Recipe, StockMovement, StockReservation, User)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IngredientDeletionPortTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='delete-port-admin', role='ADMIN')
        cls.customer = User.objects.create_user(username='delete-port-customer')
        cls.ingredient = Ingredient.objects.create(name='Trứng kiểm thử xóa', unit='quả', current_stock=50)
        cls.other = Ingredient.objects.create(name='Giữ nguyên', unit='g', current_stock=500)
        cls.menu = MenuItem.objects.create(name='Phở kiểm thử xóa', base_price=50000)
        cls.recipe = Recipe.objects.create(menu_item=cls.menu, ingredient=cls.ingredient, quantity_required=1)
        cls.entry = InventoryTransaction.objects.create(ingredient=cls.ingredient, transaction_type='IMPORT', quantity_changed=50)

    def setUp(self):
        self.client.force_login(self.admin)

    def delete_url(self):
        return reverse('admin_ingredient_delete', args=[self.ingredient.pk])

    def test_deactivate_preserves_formula_history_and_stock_then_can_activate(self):
        response = self.client.post(self.delete_url(), {'action':'deactivate'}, follow=True)
        self.assertContains(response, 'ngưng sử dụng')
        self.ingredient.refresh_from_db()
        self.assertFalse(self.ingredient.is_active)
        self.assertEqual(self.ingredient.current_stock, 50)
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())
        self.assertTrue(InventoryTransaction.objects.filter(pk=self.entry.pk).exists())
        response = self.client.post(reverse('admin_ingredient_activate',args=[self.ingredient.pk]),follow=True)
        self.assertContains(response, 'kích hoạt lại')
        self.ingredient.refresh_from_db()
        self.assertTrue(self.ingredient.is_active)

    def test_explicit_force_delete_removes_only_selected_ingredient_dependencies(self):
        order = Order.objects.create(order_code='DELETE-PORT-HISTORY')
        reservation = StockReservation.objects.create(order=order,state='CONSUMED',expires_at=timezone.now()+timedelta(minutes=15))
        requirement = InventoryRequirement.objects.create(reservation=reservation,ingredient=self.ingredient,quantity=1)
        movement = StockMovement.objects.create(ingredient=self.ingredient,order=order,key='delete-port-export',kind='EXPORT',quantity=-1)
        incident = InventoryIncident.objects.create(ingredient=self.ingredient,detail='Dữ liệu test')
        other_entry = InventoryTransaction.objects.create(ingredient=self.other,transaction_type='IMPORT',quantity_changed=500)
        response = self.client.post(self.delete_url(),{'action':'force_delete'},follow=True)
        self.assertContains(response,'xóa vĩnh viễn')
        self.assertFalse(Ingredient.objects.filter(pk=self.ingredient.pk).exists())
        for model,pk in [(Recipe,self.recipe.pk),(InventoryTransaction,self.entry.pk),(InventoryRequirement,requirement.pk),
                         (StockMovement,movement.pk),(InventoryIncident,incident.pk)]:
            self.assertFalse(model.objects.filter(pk=pk).exists())
        self.assertTrue(Ingredient.objects.filter(pk=self.other.pk).exists())
        self.assertTrue(InventoryTransaction.objects.filter(pk=other_entry.pk).exists())
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(action='INGREDIENT_FORCE_DELETED',object_id=str(self.ingredient.pk)).exists())

    def test_plain_delete_still_protects_history_and_unused_delete_still_works(self):
        self.client.post(self.delete_url())
        self.assertTrue(Ingredient.objects.filter(pk=self.ingredient.pk).exists())
        self.client.post(reverse('admin_ingredient_delete',args=[self.other.pk]))
        self.assertFalse(Ingredient.objects.filter(pk=self.other.pk).exists())

    def test_inventory_renders_choice_dialog_and_inactive_status(self):
        self.client.post(self.delete_url(),{'action':'deactivate'})
        response=self.client.get(reverse('admin_inventory'))
        self.assertContains(response,'deleteIngredientDialog')
        self.assertContains(response,'data-delete-url=')
        self.assertContains(response,'data-list-filter="inactive"')
        self.assertContains(response,'Dùng lại')
        self.assertEqual(response.context['inactive_count'],1)

    def test_delete_and_activate_require_post_admin_and_csrf(self):
        activate=reverse('admin_ingredient_activate',args=[self.ingredient.pk])
        for url in [self.delete_url(),activate]:
            self.assertEqual(self.client.get(url).status_code,405)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.admin)
        self.assertEqual(secure.post(self.delete_url(),{'action':'force_delete'}).status_code,403)
        self.client.force_login(self.customer)
        for url in [self.delete_url(),activate]:
            self.assertEqual(self.client.post(url,{'action':'force_delete'}).status_code,302)
        self.assertTrue(Ingredient.objects.filter(pk=self.ingredient.pk).exists())
