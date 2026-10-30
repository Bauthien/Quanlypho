"""Durable ledgers and snapshots for checkout, aftersales and membership."""
from django.db import models
from django.db.models import Q


FLOW_STATES = [(key, label) for key, label in {
    'OPEN': 'Chờ xét duyệt', 'APPROVED': 'Đã duyệt', 'REJECTED': 'Từ chối',
    'REFUND_CONFIRMED': 'Đã xác nhận hoàn, đang xử lý ưu đãi', 'CLOSED': 'Đã hoàn tất', 'REPLACING': 'Đang giao bù',
    'RESERVED': 'Đã giữ ngân sách', 'SUBMITTED': 'Đã gửi lệnh, chờ đối soát', 'UNKNOWN': 'Chưa rõ kết quả',
    'SUCCEEDED': 'Thành công', 'FAILED_FINAL': 'Thất bại đã xác minh', 'VOID': 'Đã hủy nghĩa vụ',
    'NOT_READY': 'Chưa sẵn sàng', 'READY_FOR_PICKUP': 'Sẵn sàng bàn giao', 'IN_TRANSIT': 'Đang giao',
    'DELIVERED': 'Giao thành công', 'FAILED': 'Giao thất bại', 'RETRY_PENDING': 'Chờ giao lại',
    'RETURNED_TO_SHOP': 'Đã mang về cửa hàng', 'CANCELLED': 'Đã hủy',
}.items()]


class UserAddress(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    ward = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100)
    codes = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=10, choices=[('HOME', 'Nhà riêng'), ('OFFICE', 'Văn phòng'), ('OTHER', 'Khác')], default='HOME')
    note = models.CharField(max_length=500, blank=True)
    is_default = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-is_default', 'pk']
        constraints = [models.UniqueConstraint(fields=['user'], condition=Q(is_default=True), name='one_default_address')]

    @property
    def full_address(self):
        return ', '.join(filter(None, [self.street, self.ward, self.district, self.province]))


class BrowserAccountVault(models.Model):
    token_digest = models.CharField(max_length=64, unique=True)
    active_slot = models.ForeignKey('SavedAccountSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    generation = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedAccountSession(models.Model):
    vault = models.ForeignKey(BrowserAccountVault, on_delete=models.CASCADE, related_name='slots')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    auth_epoch = models.PositiveIntegerField()
    verified_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['vault', 'user'], name='vault_user_once')]


class RequestKey(models.Model):
    scope = models.CharField(max_length=100)
    key = models.CharField(max_length=80)
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['scope', 'key'], name='request_key_once')]


class TierConfig(models.Model):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=50)
    rank = models.PositiveSmallIntegerField(unique=True)
    minimum_spend = models.PositiveBigIntegerField(default=0)
    good_reviews = models.PositiveSmallIntegerField(default=0)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    monthly_shipping = models.PositiveSmallIntegerField(default=0)
    nearby_shipping = models.BooleanField(default=False)
    maximum_pack_value = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['rank']


class LoyaltyAccount(models.Model):
    user = models.OneToOneField('User', on_delete=models.PROTECT, related_name='loyalty')
    total_qualifying_spend = models.PositiveBigIntegerField(default=0)
    tier = models.ForeignKey(TierConfig, on_delete=models.PROTECT, null=True)
    highest_rank = models.PositiveSmallIntegerField(default=0)
    good_review_count = models.PositiveIntegerField(default=0)
    debt = models.PositiveIntegerField(default=0)


class PointLot(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.PROTECT, related_name='lots')
    source = models.CharField(max_length=150, unique=True)
    earned_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    original = models.PositiveIntegerField()
    available = models.PositiveIntegerField()
    reserved = models.PositiveIntegerField(default=0)
    spent = models.PositiveIntegerField(default=0)
    expired = models.PositiveIntegerField(default=0)
    revoked = models.PositiveIntegerField(default=0)
    pending_revocation = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(original=models.F('available') + models.F('reserved') + models.F('spent') + models.F('expired') + models.F('revoked')), name='point_lot_conserves_units'),
            models.CheckConstraint(condition=Q(pending_revocation__lte=models.F('reserved')), name='point_pending_within_reserved'),
        ]


class PointTransaction(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.PROTECT, related_name='transactions')
    key = models.CharField(max_length=180, unique=True)
    kind = models.CharField(max_length=30)
    amount = models.IntegerField()
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pk']


class PointHold(models.Model):
    order = models.ForeignKey('Order', on_delete=models.PROTECT, related_name='point_holds')
    lot = models.ForeignKey(PointLot, on_delete=models.PROTECT)
    amount = models.PositiveIntegerField()
    state = models.CharField(max_length=12, default='RESERVED')
    restored = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['order', 'lot'], name='one_point_hold_per_lot_order'),
            models.CheckConstraint(condition=Q(restored__lte=models.F('amount')), name='point_hold_restore_bounded')]


class Voucher(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=12, choices=[('PERCENT', 'Giảm phần trăm'), ('FIXED', 'Giảm tiền'), ('SHIPPING', 'Miễn phí giao'), ('FREE_ITEM', 'Tặng một món')])
    value = models.PositiveIntegerField(default=0)
    cap = models.PositiveIntegerField(default=0)
    minimum = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    quota = models.PositiveIntegerField(default=0, help_text='0 = không giới hạn')
    per_user_limit = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    public = models.BooleanField(default=False)
    eligible_menu_ids = models.JSONField(default=list, blank=True)
    shipping_scope = models.CharField(max_length=8, default='ANY', choices=[('ANY', 'Mọi khoảng cách'), ('FAR', 'Trên 5km')])


class UserVoucher(models.Model):
    user = models.ForeignKey('User', on_delete=models.PROTECT, related_name='vouchers')
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT)
    grant_key = models.CharField(max_length=180, unique=True)
    source = models.CharField(max_length=30)
    policy = models.JSONField(default=dict)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    state = models.CharField(max_length=12, default='AVAILABLE')
    order = models.ForeignKey('Order', on_delete=models.PROTECT, null=True, blank=True, related_name='voucher_uses')

    class Meta:
        ordering = ['expires_at', 'pk']


class RewardCatalog(models.Model):
    name = models.CharField(max_length=100)
    points_cost = models.PositiveIntegerField()
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT)
    validity_days = models.PositiveIntegerField(default=30)
    active = models.BooleanField(default=True)
    quota = models.PositiveIntegerField(default=0)


class BenefitGrant(models.Model):
    user = models.ForeignKey('User', on_delete=models.PROTECT)
    key = models.CharField(max_length=120)
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'key'], name='benefit_grant_once')]


class DailyCheckin(models.Model):
    user = models.ForeignKey('User', on_delete=models.PROTECT)
    date = models.DateField()
    streak = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'date'], name='one_checkin_per_day')]


class LoyaltyOrderContribution(models.Model):
    order = models.OneToOneField('Order', on_delete=models.PROTECT, related_name='loyalty_contribution')
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.PROTECT)
    original_spend = models.PositiveBigIntegerField(default=0)
    current_spend = models.PositiveBigIntegerField(default=0)
    points_target = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)


class ReferralReward(models.Model):
    newcomer = models.OneToOneField('User', on_delete=models.PROTECT, related_name='referral_reward')
    inviter = models.ForeignKey('User', on_delete=models.PROTECT, related_name='referral_rewards')
    order = models.OneToOneField('Order', on_delete=models.PROTECT)
    reversed = models.BooleanField(default=False)


class StockReservation(models.Model):
    order = models.OneToOneField('Order', on_delete=models.PROTECT, related_name='stock_reservation')
    state = models.CharField(max_length=12, default='ACTIVE', db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    bom_snapshot = models.JSONField(default=list)


class BOMVersion(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True)
    product_type = models.CharField(max_length=12)
    product_id = models.PositiveBigIntegerField()
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class InventoryRequirement(models.Model):
    reservation = models.ForeignKey(StockReservation, on_delete=models.PROTECT, related_name='lines')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    returned = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['reservation', 'ingredient'], name='one_requirement_per_ingredient')]


class StockMovement(models.Model):
    order = models.ForeignKey('Order', on_delete=models.PROTECT, null=True, blank=True)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.PROTECT)
    key = models.CharField(max_length=150, unique=True)
    kind = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    evidence = models.TextField(blank=True)
    actor = models.ForeignKey('User', on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InventoryIncident(models.Model):
    ingredient = models.ForeignKey('Ingredient', on_delete=models.PROTECT)
    detail = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Delivery(models.Model):
    order = models.OneToOneField('Order', on_delete=models.PROTECT, related_name='delivery')
    state = models.CharField(max_length=24, default='NOT_READY', choices=FLOW_STATES)
    version = models.PositiveIntegerField(default=1)
    delivered_at = models.DateTimeField(null=True)


class DeliveryAttempt(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.PROTECT, related_name='attempts')
    sequence = models.PositiveIntegerField()
    state = models.CharField(max_length=24, default='IN_TRANSIT', choices=FLOW_STATES)
    courier = models.CharField(max_length=100, blank=True)
    evidence = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['delivery', 'sequence'], name='delivery_attempt_sequence')]


class PaymentReceipt(models.Model):
    order = models.ForeignKey('Order', on_delete=models.PROTECT, related_name='receipts')
    provider = models.CharField(max_length=30)
    external_id = models.CharField(max_length=120)
    amount = models.PositiveBigIntegerField()
    allocated = models.BooleanField(default=False)
    requires_reconciliation = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    received_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['provider', 'external_id'], name='unique_actual_payment')]


class OrderAllocation(models.Model):
    order = models.ForeignKey('Order', on_delete=models.PROTECT, related_name='allocations')
    item = models.ForeignKey('OrderItem', on_delete=models.PROTECT, null=True, blank=True)
    unit = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=180)
    net_before_points = models.PositiveBigIntegerField()
    points = models.PositiveIntegerField(default=0)
    cash = models.PositiveBigIntegerField()
    case = models.ForeignKey('ServiceRequest', on_delete=models.PROTECT, null=True, blank=True, related_name='allocations')
    refunded = models.BooleanField(default=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(net_before_points=models.F('cash') + 100 * models.F('points')), name='allocation_cash_points_equal_net')]


class ServiceRequest(models.Model):
    order = models.ForeignKey('Order', on_delete=models.PROTECT, related_name='service_requests')
    request_key = models.CharField(max_length=100, unique=True)
    kind = models.CharField(max_length=12, choices=[('CANCEL', 'Hủy đơn'), ('ISSUE', 'Món lỗi / giao thiếu')])
    reason = models.TextField()
    evidence = models.TextField(blank=True)
    remedy = models.CharField(max_length=12, choices=[('REFUND', 'Hoàn tiền'), ('REPLACE', 'Giao bù')], default='REFUND')
    state = models.CharField(max_length=24, default='OPEN', choices=FLOW_STATES)
    decision_note = models.TextField(blank=True)
    benefits_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey('User', on_delete=models.PROTECT, null=True, blank=True)
    replacement = models.OneToOneField('Order', on_delete=models.PROTECT, null=True, blank=True, related_name='service_origin')


class RefundPlan(models.Model):
    case = models.ForeignKey(ServiceRequest, on_delete=models.PROTECT, null=True, related_name='refund_plans')
    receipt = models.ForeignKey(PaymentReceipt, on_delete=models.PROTECT, related_name='refund_plans')
    amount = models.PositiveBigIntegerField()
    state = models.CharField(max_length=24, default='RESERVED', choices=FLOW_STATES)
    key = models.CharField(max_length=150, unique=True)


class RefundAttempt(models.Model):
    plan = models.ForeignKey(RefundPlan, on_delete=models.PROTECT, related_name='attempts')
    state = models.CharField(max_length=24, default='SUBMITTED', choices=FLOW_STATES)
    reference = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    actor = models.ForeignKey('User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)


class DomainEvent(models.Model):
    key = models.CharField(max_length=180, unique=True)
    kind = models.CharField(max_length=30)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditEvent(models.Model):
    actor = models.ForeignKey('User', on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=80)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
