"""Append sample menu data safely; preserve existing prices, balances and recipes."""
import hashlib
import json
import shutil
import unicodedata
from decimal import Decimal
from pathlib import Path

from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pho_app.catalog_sample_data import INGREDIENTS, MENU, PHOTO_SLUGS, TOPPINGS
from pho_app.domain import serialized
from pho_app.models import AuditEvent, Ingredient, InventoryTransaction, MenuItem, Recipe, Topping
from pho_app.nlp_bom import scale_food_recipe
from pho_app.stock import convert_stock_units


FOLDER='catalog_samples_20261030'


def normalized(value):
    value=unicodedata.normalize('NFKD',value).casefold().replace('đ','d')
    return ' '.join(''.join(char for char in value if not unicodedata.combining(char)).split())


class Command(BaseCommand):
    help='Bổ sung phở, đồ uống, topping, ảnh riêng và nguyên liệu mẫu; không xóa dữ liệu hiện tại.'

    def add_arguments(self,parser):
        parser.add_argument('--assets-dir',type=Path)
        parser.add_argument('--replace-images',action='store_true',help='Gán ảnh mẫu riêng cho các món có trong bộ dữ liệu.')
        parser.add_argument('--dry-run',action='store_true',help='Kiểm tra dữ liệu rồi hoàn tác toàn bộ thay đổi; không sao chép ảnh.')

    def handle(self,*args,**options):
        source=(options['assets_dir'] or Path(settings.MEDIA_ROOT)/FOLDER).resolve()
        try:
            manifest=json.loads((source/'catalog-assets.json').read_text(encoding='utf-8'))
            assets=manifest['assets']
            if set(assets)!=set(PHOTO_SLUGS):raise ValueError('Thiếu hoặc dư ảnh trong bộ dữ liệu.')
            hashes=set()
            for slug,item in assets.items():
                path=(source/item['file']).resolve()
                if not path.is_relative_to(source) or not path.is_file():raise ValueError(f'Đường dẫn ảnh không hợp lệ: {slug}')
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                if digest!=item['sha256'] or digest in hashes:raise ValueError(f'Ảnh lỗi hoặc trùng nội dung: {slug}')
                hashes.add(digest)
                with Image.open(path) as image:image.verify()
        except (OSError,ValueError,KeyError) as exc:
            raise CommandError(f'Không thể kiểm tra bộ ảnh: {exc}') from exc
        report=self.seed(source,manifest,options['replace_images'],options['dry_run'])
        self.stdout.write(json.dumps(report,ensure_ascii=False,indent=2))

    @serialized
    def seed(self,source,manifest,replace_images,dry_run):
        destination=(Path(settings.MEDIA_ROOT)/FOLDER).resolve()
        report={'dry_run':dry_run,'menu_created':0,'toppings_created':0,'ingredients_created':0,
                'recipes_created':0,'photos_updated':0,'opening_transactions_created':0,'media_folder':str(destination)}

        def lookup(model,name,aliases=()):
            keys={normalized(value) for value in (name,*aliases)}
            matches=[obj for obj in model.objects.all() if normalized(obj.name) in keys]
            if len(matches)>1:raise CommandError(f'Có nhiều dòng trùng tên {name}; không tự ý gộp dữ liệu.')
            return matches[0] if matches else None

        ingredient_map={}
        for key,name,unit,usage,stock,minimum,aliases in INGREDIENTS:
            ingredient=lookup(Ingredient,name,aliases)
            if ingredient is None:
                ingredient=Ingredient.objects.create(name=name,unit=unit,usage=usage,current_stock=Decimal(stock),minimum_stock=Decimal(minimum))
                InventoryTransaction.objects.create(ingredient=ingredient,transaction_type='IMPORT',quantity_changed=Decimal(stock))
                report['ingredients_created']+=1;report['opening_transactions_created']+=1
            if ingredient.usage not in (usage,'SHARED'):
                raise CommandError(f'Nguyên liệu {ingredient.name} đang thuộc nhóm khác. Không thay đổi phân nhóm hiện có.')
            ingredient_map[key]=ingredient

        def photo_for(slug):
            item=manifest['assets'][slug]
            relative=Path(FOLDER)/item['file']
            target=(Path(settings.MEDIA_ROOT)/relative).resolve()
            if not target.is_relative_to(destination):raise CommandError('Ảnh nằm ngoài thư mục cho phép.')
            if not dry_run:
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:
                    raise CommandError(f'Ảnh đã bị thay đổi, không ghi đè: {target.name}')
                if not target.exists():shutil.copy2(source/item['file'],target)
            return relative.as_posix()

        def assign_photo(product,entry,field,created):
            if created or replace_images or not getattr(product,field):
                path=photo_for(entry['photo'])
                if str(getattr(product,field))!=path:
                    setattr(product,field,path);product.save(update_fields=[field]);report['photos_updated']+=1

        def create_rows(product,rows,size='M',converted=False):
            if product.recipes.filter(bowl_size=size).exists():return
            prepared=[]
            for row in rows:
                if converted:
                    ingredient=Ingredient.objects.get(pk=row['ingredient_id']);quantity=row['quantity'];unit=row['input_unit']
                else:
                    key,quantity,unit=row;ingredient=ingredient_map[key]
                quantity=convert_stock_units(quantity,unit,ingredient.unit)
                prepared.append(Recipe(ingredient=ingredient,quantity_required=quantity,bowl_size=size,
                                       **({'menu_item':product} if isinstance(product,MenuItem) else {'topping':product})))
            Recipe.objects.bulk_create(prepared);report['recipes_created']+=len(prepared)

        for entry in MENU:
            product=lookup(MenuItem,entry['name'],entry.get('aliases',()))
            created=product is None
            if created:
                product=MenuItem.objects.create(name=entry['name'],category=entry['category'],base_price=entry['price'],inventory_mode=entry.get('mode','BOM'))
                report['menu_created']+=1
            if product.category!=entry['category']:raise CommandError(f'Món {product.name} đang thuộc nhóm khác.')
            assign_photo(product,entry,'image_primary',created)
            create_rows(product,entry['rows'])
            if product.category=='PHO':
                medium=[{'ingredient_id':row.ingredient_id,'quantity':str(row.quantity_required),'input_unit':row.ingredient.unit}
                        for row in product.recipes.filter(bowl_size='M').select_related('ingredient').order_by('pk')]
                catalog=list(Ingredient.objects.values('id','name','unit','usage'))
                for size in ['S','L']:
                    if product.recipes.filter(bowl_size=size).exists():continue
                    result=scale_food_recipe({'rows':medium},catalog,size,reference='saved_medium')
                    if not result['ok']:raise CommandError(result.get('error','Không tạo được công thức theo cỡ tô.'))
                    create_rows(product,result['rows'],size,converted=True)

        for entry in TOPPINGS:
            product=lookup(Topping,entry['name'],entry.get('aliases',()))
            created=product is None
            if created:
                product=Topping.objects.create(name=entry['name'],price=entry['price'],category='PHO',inventory_mode='BOM')
                report['toppings_created']+=1
            if product.category!='PHO':raise CommandError(f'Topping {product.name} đang thuộc nhóm khác.')
            assign_photo(product,entry,'image_thumbnail',created)
            create_rows(product,entry['rows'])

        changed=any(report[key] for key in ['menu_created','toppings_created','ingredients_created','recipes_created','photos_updated'])
        if not dry_run:
            if destination.exists():
                manifest_path=destination/'catalog-assets.json'
                manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
            if changed:AuditEvent.objects.create(action='CATALOG_SAMPLES_ADDED',object_type='Catalog',object_id=FOLDER,detail=report)
        else:
            transaction.set_rollback(True)
        return report
