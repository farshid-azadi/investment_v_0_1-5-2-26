"""
Wallet Admin Panel
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.wallet.models import Wallet, Transaction, WithdrawalRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """مدیریت Wallet در پنل ادمین"""
    
    list_display = [
        'user_mobile',
        'balance_display',
        'investment_balance_display',
        'commission_balance_display',
        'locked_balance_display',
        'total_balance_display',
        'created_at'
    ]
    
    list_filter = ['created_at']
    search_fields = ['user__mobile', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'total_balance_display']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('موجودی‌ها', {
            'fields': (
                'balance',
                'investment_balance',
                'commission_balance',
                'locked_balance',
                'total_balance_display',
            )
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_mobile(self, obj):
        return obj.user.mobile
    user_mobile.short_description = 'شماره موبایل'
    
    def balance_display(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">{:,.0f}</span>',
            obj.balance
        )
    balance_display.short_description = 'موجودی نقدی'
    
    def investment_balance_display(self, obj):
        return format_html(
            '<span style="color: blue;">{:,.0f}</span>',
            obj.investment_balance
        )
    investment_balance_display.short_description = 'موجودی سرمایه‌گذاری'
    
    def commission_balance_display(self, obj):
        return format_html(
            '<span style="color: orange;">{:,.0f}</span>',
            obj.commission_balance
        )
    commission_balance_display.short_description = 'کمیسیون'
    
    def locked_balance_display(self, obj):
        return format_html(
            '<span style="color: red;">{:,.0f}</span>',
            obj.locked_balance
        )
    locked_balance_display.short_description = 'قفل‌شده'
    
    def total_balance_display(self, obj):
        return format_html(
            '<span style="color: purple; font-weight: bold;">{:,.0f}</span>',
            obj.total_balance
        )
    total_balance_display.short_description = 'مجموع کل'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """مدیریت Transaction در پنل ادمین"""
    
    list_display = [
        'id',
        'wallet_user',
        'transaction_type',
        'amount_display',
        'status',
        'created_at'
    ]
    
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = [
        'wallet__user__mobile',
        'reference_id',
        'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('wallet', 'transaction_type', 'amount', 'status')
        }),
        ('جزئیات', {
            'fields': ('description', 'reference_id', 'metadata')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def wallet_user(self, obj):
        return obj.wallet.user.mobile
    wallet_user.short_description = 'کاربر'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type in ['deposit', 'roi', 'commission_binary', 'commission_level'] else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:,.0f}</span>',
            color,
            obj.amount
        )
    amount_display.short_description = 'مبلغ'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    """مدیریت WithdrawalRequest در پنل ادمین"""
    
    list_display = [
        'id',
        'wallet_user',
        'amount_display',
        'status_display',
        'bank_name',
        'created_at',
        'processed_at'
    ]
    
    list_filter = ['status', 'created_at', 'bank_name']
    search_fields = [
        'wallet__user__mobile',
        'bank_account',
        'account_holder',
        'payment_reference'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('wallet', 'amount', 'status')
        }),
        ('اطلاعات بانکی', {
            'fields': (
                'bank_name',
                'bank_account',
                'bank_card',
                'account_holder'
            )
        }),
        ('توضیحات', {
            'fields': (
                'user_description',
                'admin_note',
                'rejection_reason'
            )
        }),
        ('پرداخت', {
            'fields': ('payment_reference',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'processed_at', 'paid_at')
        }),
    )
    
    actions = ['approve_requests', 'reject_requests', 'mark_as_paid']
    
    def wallet_user(self, obj):
        return obj.wallet.user.mobile
    wallet_user.short_description = 'کاربر'
    
    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{:,.0f}</span>',
            obj.amount
        )
    amount_display.short_description = 'مبلغ'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'blue',
            'rejected': 'red',
            'paid': 'green',
            'cancelled': 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def approve_requests(self, request, queryset):
        """تایید درخواست‌های انتخاب شده"""
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='approved',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{count} درخواست تایید شد.')
    approve_requests.short_description = 'تایید درخواست‌های انتخابی'
    
    def reject_requests(self, request, queryset):
        """رد درخواست‌های انتخاب شده"""
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='rejected',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{count} درخواست رد شد.')
    reject_requests.short_description = 'رد درخواست‌های انتخابی'
    
    def mark_as_paid(self, request, queryset):
        """علامت‌گذاری به عنوان پرداخت شده"""
        from django.utils import timezone
        count = queryset.filter(status='approved').update(
            status='paid',
            paid_at=timezone.now()
        )
        self.message_user(request, f'{count} درخواست به عنوان پرداخت شده علامت‌گذاری شد.')
    mark_as_paid.short_description = 'علامت‌گذاری به عنوان پرداخت شده'
