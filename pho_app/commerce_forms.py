from PIL import Image, UnidentifiedImageError
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import MenuItem, RewardCatalog, TierConfig, User, UserAddress, Voucher


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
            if isinstance(field, forms.ModelChoiceField):
                field.empty_label = '— Chọn một mục —'


class ProfileForm(StyledModelForm):
    version = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'email', 'date_of_birth', 'gender', 'avatar']
        labels = {'full_name': 'Họ và tên', 'phone_number': 'Điện thoại', 'email': 'Email', 'date_of_birth': 'Ngày sinh', 'gender': 'Giới tính', 'avatar': 'Ảnh đại diện'}
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def clean_date_of_birth(self):
        value = self.cleaned_data.get('date_of_birth')
        if value and value > timezone.localdate():
            raise ValidationError('Ngày sinh không được ở tương lai.')
        return value

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar or not hasattr(avatar, 'content_type'):
            return avatar
        if avatar.size > 5_000_000:
            raise ValidationError('Ảnh tối đa 5 MB.')
        if avatar.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise ValidationError('Chỉ nhận ảnh JPG, PNG hoặc WEBP.')
        try:
            with Image.open(avatar) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 25_000_000:
                    raise ValueError()
                image.verify()
            avatar.seek(0)
        except (OSError, ValueError, Image.DecompressionBombError, UnidentifiedImageError):
            raise ValidationError('Tệp ảnh hỏng hoặc kích thước ảnh không phù hợp.')
        return avatar


class AddressForm(StyledModelForm):
    version = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = UserAddress
        fields = ['recipient_name', 'phone', 'street', 'ward', 'district', 'province', 'label', 'note', 'latitude', 'longitude', 'is_default']
        labels = {'recipient_name': 'Người nhận', 'phone': 'Điện thoại', 'street': 'Số nhà, đường', 'ward': 'Phường / Xã',
            'district': 'Quận / Huyện (nếu có)', 'province': 'Tỉnh / Thành phố', 'label': 'Nhãn', 'note': 'Ghi chú',
            'latitude': 'Vĩ độ', 'longitude': 'Kinh độ', 'is_default': 'Địa chỉ mặc định'}

    def clean(self):
        data = super().clean()
        lat, lng = data.get('latitude'), data.get('longitude')
        if (lat is None) != (lng is None) or (lat is not None and (not -90 <= lat <= 90 or not -180 <= lng <= 180)):
            raise ValidationError('Nhập đủ tọa độ hợp lệ hoặc để trống cả hai trường.')
        return data


class VoucherForm(StyledModelForm):
    eligible_menu_items = forms.ModelMultipleChoiceField(label='Món áp dụng (trống = toàn bộ món)',
        queryset=MenuItem.objects.filter(is_active=True), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kind'].choices = [('', '— Chọn loại ưu đãi —')] + [(key, label) for key, label in self.fields['kind'].choices if key]
        self.fields['code'].widget.attrs.update(placeholder='VD: PHONHA20', autocomplete='off')
        self.fields['name'].widget.attrs['placeholder'] = 'Tên chương trình hiển thị cho khách'
        if self.instance.pk:
            self.fields['eligible_menu_items'].initial = self.instance.eligible_menu_ids

    def save(self, commit=True):
        self.instance.eligible_menu_ids = list(self.cleaned_data['eligible_menu_items'].values_list('pk', flat=True))
        return super().save(commit=commit)

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        if code.startswith(('TIER_', 'MONTHLY_SHIP_', 'POINTS_')):
            raise ValidationError('Tiền tố này dành riêng cho voucher quyền lợi hệ thống. Chọn mã chiến dịch khác.')
        return code

    class Meta:
        model = Voucher
        fields = ['code', 'name', 'kind', 'value', 'cap', 'minimum', 'starts_at', 'ends_at', 'quota', 'per_user_limit', 'public', 'active', 'shipping_scope']
        labels = {'code': 'Mã', 'name': 'Tên', 'kind': 'Loại', 'value': 'Giá trị (%, VNĐ)', 'cap': 'Giảm tối đa (0 = không giới hạn)',
            'minimum': 'Tiền món tối thiểu sau giảm hạng', 'starts_at': 'Bắt đầu', 'ends_at': 'Kết thúc', 'quota': 'Tổng lượt (0 = không giới hạn)',
            'per_user_limit': 'Lượt mỗi khách', 'public': 'Cho phép nhập mã tại checkout', 'active': 'Đang hoạt động', 'shipping_scope': 'Phạm vi giao'}
        widgets = {name: forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M') for name in ('starts_at', 'ends_at')}

    def clean(self):
        data = super().clean()
        if data.get('starts_at') and data.get('ends_at') and data['starts_at'] >= data['ends_at']:
            raise ValidationError('Hạn kết thúc phải sau thời gian bắt đầu.')
        if data.get('kind') == 'PERCENT' and not 1 <= data.get('value', 0) <= 100:
            raise ValidationError('Tỷ lệ giảm phải từ 1 đến 100%.')
        if data.get('kind') == 'FIXED' and not data.get('value'):
            raise ValidationError('Voucher giảm tiền cần giá trị lớn hơn 0.')
        if not data.get('per_user_limit'):
            raise ValidationError('Lượt mỗi khách tối thiểu 1.')
        return data


class RewardForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voucher'].label_from_instance = lambda voucher: f'{voucher.code} · {voucher.name}'

    class Meta:
        model = RewardCatalog
        fields = ['name', 'points_cost', 'voucher', 'validity_days', 'quota', 'active']
        labels = {'name': 'Tên quà', 'points_cost': 'Điểm cần đổi', 'voucher': 'Mẫu voucher', 'validity_days': 'Số ngày hiệu lực', 'quota': 'Số quà (0 = không giới hạn)', 'active': 'Đang mở đổi'}

    def clean(self):
        data = super().clean()
        if not data.get('points_cost') or not data.get('validity_days'):
            raise ValidationError('Điểm cần đổi và số ngày hiệu lực phải lớn hơn 0.')
        return data


class TierForm(StyledModelForm):
    class Meta:
        model = TierConfig
        fields = ['name', 'minimum_spend', 'good_reviews', 'discount_percent', 'monthly_shipping', 'nearby_shipping', 'maximum_pack_value']
        labels = {'name': 'Tên hạng', 'minimum_spend': 'Chi tiêu tối thiểu', 'good_reviews': 'Số đánh giá tốt',
            'discount_percent': 'Giảm tiền món (%)', 'monthly_shipping': 'Mã giao hàng mỗi tháng',
            'nearby_shipping': 'Miễn phí giao trong 5km', 'maximum_pack_value': 'Giá trị gói lên hạng tối đa'}

    def clean_discount_percent(self):
        value = self.cleaned_data['discount_percent']
        if value > 100:
            raise ValidationError('Tỷ lệ giảm không được vượt 100%.')
        return value
