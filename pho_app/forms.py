from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import MenuItem, Topping, User


class StyledAuthForm(AuthenticationForm):
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Tên đăng nhập',
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


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mật khẩu'}),
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

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Mật khẩu nhập lại không khớp.')
        if password1:
            candidate = User(
                username=self.cleaned_data.get('username', ''),
                full_name=self.cleaned_data.get('full_name', ''),
                phone_number=self.cleaned_data.get('phone_number', ''),
            )
            validate_password(password1, candidate)
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
        fields = ['name', 'base_price', 'is_active', 'image_primary', 'image_detail_1', 'image_detail_2']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên món'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }


class ToppingForm(forms.ModelForm):
    class Meta:
        model = Topping
        fields = ['name', 'price', 'image_thumbnail']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên topping'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }
