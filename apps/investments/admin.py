# apps/investments/admin.py

from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from django.db.models import Sum

from .models import InvestmentPlan, UserInvestment
from .forms import InvestmentPlanAdminForm


# =============================================================================
# 📊 Investment Plan Admin
# =============================================================================

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    """
    پنل ادمین برای مدیریت پلن‌های سرمایه‌گذاری

    ویژگی‌ها:
    - فرم سفارشی برای ورودی‌های عددی
    - جست‌وجو روی نام و توضیحات
    - نمایش آمار به‌صورت پویا با تکیه بر UserInvestment.plan_type
    """
    form = InvestmentPlanAdminForm

    search_fields = ['name', 'description']

    list_display = [
        'name_with_status',
        'investment_range',
        'roi_display',
        'duration_display',
        'active_users_count',
        'total_invested',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'created_at',
    ]

    ordering = ['-created_at', 'name']

    fieldsets = (
        ('📋 اطلاعات پایه', {
            'fields': ('name', 'description', 'is_active'),
            'description': 'نام و توضیحات پلن که به کاربران نمایش داده می‌شود.'
        }),
        ('💰 محدوده سرمایه‌گذاری', {
            'fields': ('min_amount', 'max_amount'),
            'description': '⚠️ مبالغ به دلار آمریکا (USD) هستند.'
        }),
        ('📊 تنظیمات سود (ROI)', {
            'fields': (
                'daily_interest_rate',
                'max_total_return_percent',
                'duration_days',
            ),
            'description': (
                '• daily_interest_rate: درصد سود روزانه (مثال: 2.5 یعنی 2.5% در روز)\n'
                '• max_total_return_percent: سقف کل برداشت (مثال: 200 یعنی دو برابر)\n'
                '• duration_days: مدت زمان پلن به روز'
            )
        }),
        ('🌳 تنظیمات باینری تری', {
            'fields': ('binary_retention_days',),
            'classes': ('collapse',),
            'description': 'تعداد روزهایی که حجم باینری نگهداری می‌شود (پیش‌فرض: 30 روز)'
        }),
        ('📅 تاریخچه', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['created_at']

    # ---------------------- متدهای نمایش ----------------------

    @admin.display(description='نام پلن', ordering='name')
    def name_with_status(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        label = '✓ فعال' if obj.is_active else '✕ غیرفعال'
        return format_html(
            '<strong>{}</strong> <span style="background:{}; color:white; padding:3px 8px; border-radius:10px; font-size:11px; margin-right:8px;">{}</span>',
            obj.name,
            color,
            label
        )

    @admin.display(description='محدوده سرمایه')
    def investment_range(self, obj):
        min_amount = f"${obj.min_amount:,.0f}"
        max_amount = f"${obj.max_amount:,.0f}"
        return format_html(
            '<span style="color:#007bff; font-family:monospace; font-weight:bold;">{} - {}</span>',
            min_amount,
            max_amount
        )

    @admin.display(description='ROI روزانه')
    def roi_display(self, obj):
        roi_value = f"{obj.daily_interest_rate:.2f}"
        color = '#28a745' if obj.daily_interest_rate <= 5 else '#ffc107'
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:8px; font-weight:bold;">{}% / روز</span>',
            color,
            roi_value
        )

    @admin.display(description='مدت زمان')
    def duration_display(self, obj):
        years = obj.duration_days // 365
        remaining_days = obj.duration_days % 365
        if years > 0:
            text = f"{years} سال"
            if remaining_days > 0:
                text += f" و {remaining_days} روز"
        else:
            text = f"{obj.duration_days} روز"
        return format_html('<span style="color:#6c757d; font-weight:bold;">📅 {}</span>', text)

    @admin.display(description='کاربران فعال')
    def active_users_count(self, obj):
        count = UserInvestment.objects.filter(
            status='active',
            plan_type=obj.name
        ).count()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:12px; font-weight:bold;">👥 {}</span>',
            color,
            count
        )

    @admin.display(description='کل سرمایه')
    def total_invested(self, obj):
        total = UserInvestment.objects.filter(
            status='active',
            plan_type=obj.name
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if total > 0:
            total_display = f"${total:,.2f}"
            return format_html(
                '<span style="color:#28a745; font-weight:bold; font-size:13px;">{}</span>',
                total_display
            )
        return format_html('<span style="color:#999;">—</span>')

    def get_queryset(self, request):
        return super().get_queryset(request)

    def has_delete_permission(self, request, obj=None):
        if obj and UserInvestment.objects.filter(status='active', plan_type=obj.name).exists():
            return False
        return super().has_delete_permission(request, obj)


# =============================================================================
# 💼 User Investment Admin
# =============================================================================

@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    """
    پنل ادمین برای مشاهده سرمایه‌گذاری‌های کاربران
    ⚠️ این صفحه برای مشاهده است؛ تغییرات دستی می‌تواند سیستم را مختل کند.
    """

    list_display = [
        'id',
        'user_link',
        'plan_type',
        'amount_display',
        'status_badge',
        'profit_info',
        'created_at',
        'end_date',
    ]

    list_filter = [
        'status',
        'plan_type',
        'created_at',
        ('end_date', admin.EmptyFieldListFilter),
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__mobile'
    ]

    readonly_fields = [
        'user',
        'plan_type',
        'amount',
        'reinvested_amount',
        'total_profit_earned',
        'daily_interest_rate',
        'created_at',
        'updated_at',
        'end_date',
    ]

    fieldsets = (
        ('👤 اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('📊 جزئیات سرمایه‌گذاری', {
            'fields': (
                'plan_type',
                'amount',
                'reinvested_amount',
                'total_profit_earned',
                'daily_interest_rate',
            )
        }),
        ('⚙️ وضعیت', {
            'fields': ('status', 'end_date')
        }),
        ('📅 تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='کاربر')
    def user_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" target="_blank" style="font-weight:bold;">👤 {}</a>',
            url, obj.user.username
        )

    @admin.display(description='مبلغ')
    def amount_display(self, obj):
        amount_value = f"${obj.amount:,.2f}"
        return format_html(
            '<span style="color:#007bff; font-weight:bold; font-family:monospace;">{}</span>',
            amount_value
        )

    @admin.display(description='وضعیت')
    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
            'capped': '#17a2b8',
        }
        color = colors.get(obj.status, '#ffc107')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:10px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='سود')
    def profit_info(self, obj):
        if obj.total_profit_earned and obj.total_profit_earned > 0:
            profit_value = f"${obj.total_profit_earned:,.2f}"
            return format_html(
                '<span style="color:#28a745; font-weight:bold;">{}</span>',
                profit_value
            )
        return '—'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'active':
            return False
        return super().has_delete_permission(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
