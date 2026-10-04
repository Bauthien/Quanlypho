from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import User


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mật khẩu',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Nhập lại mật khẩu',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ('username', 'full_name', 'phone_number')
        labels = {
            'username': 'Tên đăng nhập',
            'full_name': 'Họ và tên',
            'phone_number': 'Số điện thoại',
        }
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'full_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'phone_number': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Hai mật khẩu không khớp.')
        validate_password(password2, self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # Không nhận role từ form đăng ký; tài khoản mới luôn là khách hàng.
        user.role = User.Role.CUSTOMER
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Mật khẩu',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class RoleUpdateForm(forms.Form):
    role = forms.ChoiceField(choices=User.Role.choices)
