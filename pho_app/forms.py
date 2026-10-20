from decimal import Decimal

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Ingredient, MenuItem, Order, Table, Topping, User


class TableForm(forms.ModelForm):
    capacity = forms.IntegerField(
        label='Sức chứa tối đa (tô)', min_value=1, max_value=2147483647, initial=4,
        error_messages={'min_value': 'Sức chứa phải từ 1 tô trở lên.', 'invalid': 'Sức chứa phải là số nguyên hợp lệ.'},
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
    )

    class Meta:
        model = Table
        fields = ['table_number', 'capacity']
        labels = {'table_number': 'Số bàn / tên bàn'}
        widgets = {'table_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: 1, 2, VIP1'})}

    def clean_table_number(self):
        number = self.cleaned_data['table_number']
        if Table.objects.filter(table_number__iexact=number).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Tên bàn đã tồn tại. Vui lòng chọn tên khác.')
        return number


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'current_stock', 'minimum_stock']
        labels = {'name': 'Tên nguyên liệu / vật tư', 'unit': 'Đơn vị tính',
                  'current_stock': 'Số lượng tồn kho hiện tại', 'minimum_stock': 'Ngưỡng cảnh báo tối thiểu'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'unit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'gram, ml, kg, lít, lon...'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
        }
        help_texts = {'unit': 'Nên dùng cùng đơn vị với công thức định lượng (ví dụ gram hoặc ml).'}


class RecipeForm(forms.Form):
    menu_item_id = forms.ModelChoiceField(queryset=MenuItem.objects.filter(is_active=True), required=False)
    topping_id = forms.ModelChoiceField(queryset=Topping.objects.filter(is_active=True), required=False)
    ingredient_id = forms.ModelChoiceField(queryset=Ingredient.objects.all())
    quantity_required = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

    def clean(self):
        data = super().clean()
        if bool(data.get('menu_item_id')) == bool(data.get('topping_id')):
            raise ValidationError('Vui lòng chọn đúng một món chính hoặc topping cần định lượng.')
        return data


class IngredientImportForm(forms.Form):
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))


class OrderFilterForm(forms.Form):
    q = forms.CharField(label='Tìm đơn hàng', required=False, max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Mã đơn, khách, số bàn, mã vận đơn', 'type': 'search',
    }))
    order_type = forms.ChoiceField(label='Loại đơn', required=False, choices=[('', 'Tất cả loại đơn'), *Order.OrderType.choices])
    order_status = forms.ChoiceField(label='Trạng thái đơn', required=False, choices=[('', 'Tất cả trạng thái'), *Order.OrderStatus.choices])
    payment_status = forms.ChoiceField(label='Thanh toán', required=False, choices=[('', 'Tất cả thanh toán'), *Order.PaymentStatus.choices])
    payment_method = forms.ChoiceField(label='Phương thức', required=False, choices=[('', 'Tất cả phương thức'), *Order.PaymentMethod.choices])
    date_from = forms.DateField(label='Từ ngày', required=False, input_formats=['%Y-%m-%d'], widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(label='Đến ngày', required=False, input_formats=['%Y-%m-%d'], widget=forms.DateInput(attrs={'type': 'date'}))
    sort = forms.ChoiceField(label='Sắp xếp', required=False, initial='newest', choices=[
        ('newest', 'Mới nhất trước'), ('oldest', 'Cũ nhất trước'),
        ('total_desc', 'Tổng tiền giảm dần'), ('total_asc', 'Tổng tiền tăng dần'),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
            field.error_messages['invalid'] = 'Giá trị không hợp lệ. Vui lòng kiểm tra lại.'
            field.error_messages['invalid_choice'] = 'Vui lòng chọn một giá trị trong danh sách.'
        self.fields['q'].error_messages['max_length'] = 'Nhập tối đa 200 ký tự để tìm kiếm.'

    def clean(self):
        data = super().clean()
        start, end = data.get('date_from'), data.get('date_to')
        if start and end and start > end:
            self.add_error('date_to', 'Ngày kết thúc phải bằng hoặc sau ngày bắt đầu.')
        return data


class StyledAuthForm(AuthenticationForm):
    username = forms.CharField(
        label='Tên đăng nhập hoặc Số điện thoại',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Tên đăng nhập hoặc SĐT',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mật khẩu',
        }),
    )

    error_messages = {
        'invalid_login': 'Tên đăng nhập (hoặc số điện thoại) hoặc mật khẩu chưa đúng. Vui lòng thử lại.',
        'inactive': 'Tài khoản này hiện đang bị khóa.',
    }

    def clean(self):
        username = self.cleaned_data.get('username', '').strip()
        password = self.cleaned_data.get('password')

        if username and password:
            user = User.objects.filter(
                Q(username__iexact=username) | Q(phone_number=username)
            ).first()
            if user:
                self.user_cache = authenticate(self.request, username=user.username, password=password)
            else:
                self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mật khẩu (tối thiểu 4 ký tự)'}),
    )
    password2 = forms.CharField(
        label='Nhập lại mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Nhập lại mật khẩu'}),
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'phone_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên đăng nhập'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Họ và tên'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Số điện thoại'}),
        }
        labels = {
            'username': 'Tên đăng nhập',
            'full_name': 'Họ và tên',
            'phone_number': 'Số điện thoại',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError('Vui lòng nhập tên đăng nhập.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.')
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1', '')
        if len(password1) < 4:
            raise ValidationError('Mật khẩu cần có ít nhất 4 ký tự.')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Mật khẩu nhập lại không khớp.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        user.is_staff = False
        user.is_superuser = False
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserRoleForm(forms.ModelForm):
    is_active = forms.BooleanField(required=False, label='Đang hoạt động')

    class Meta:
        model = User
        fields = ['role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }
        labels = {
            'role': 'Vai trò',
            'is_active': 'Đang hoạt động',
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'category', 'base_price', 'image_primary', 'image_detail_1', 'image_detail_2']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên món'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'category': forms.Select(attrs={'class': 'form-input'}),
        }


class ToppingForm(forms.ModelForm):
    class Meta:
        model = Topping
        fields = ['name', 'price', 'image_thumbnail']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên topping'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }
