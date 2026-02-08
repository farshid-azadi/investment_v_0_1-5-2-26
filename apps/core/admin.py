# apps/core/admin.py
from django.contrib import admin
from .models import Plan, MLMSettings, WithdrawalSetting, LevelCommissionSetting


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'binary_percentage', 'roi_percent', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'description']
    ordering = ['order', 'price']


@admin.register(LevelCommissionSetting)
class LevelCommissionSettingAdmin(admin.ModelAdmin):
    list_display = ['level', 'percent', 'is_active', 'description']
    list_filter = ['is_active']
    list_editable = ['percent', 'is_active']
    ordering = ['level']


@admin.register(MLMSettings)
class MLMSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('⚙️ تنظیمات باینری', {
            'fields': ('binary_percentage', 'binary_match_type', 'binary_carry_forward')
        }),
        ('📊 تنظیمات سطح‌بندی', {
            'fields': ('max_level_depth', 'level_commission_from')
        }),
        ('💰 تنظیمات ROI', {
            'fields': ('roi_payment_time', 'roi_payment_on_weekends')
        }),
        ('🔧 سایر تنظیمات', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
    )
    
    def has_add_permission(self, request):
        # فقط یک رکورد مجاز است
        return not MLMSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # جلوگیری از حذف تنظیمات
        return False


@admin.register(WithdrawalSetting)
class WithdrawalSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('💵 محدودیت‌های مبلغ', {
            'fields': ('min_withdrawal_amount', 'max_withdrawal_amount')
        }),
        ('💸 کارمزد', {
            'fields': ('withdrawal_fee_percentage', 'withdrawal_fee_fixed')
        }),
        ('⏱️ محدودیت‌های زمانی', {
            'fields': ('daily_withdrawal_limit', 'withdrawal_processing_days')
        }),
        ('✅ تأیید خودکار', {
            'fields': ('auto_approve_threshold',)
        }),
    )
    
    def has_add_permission(self, request):
        return not WithdrawalSetting.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
