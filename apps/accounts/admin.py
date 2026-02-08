# apps/accounts/admin.py
from .models import RegistrationSettings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
import uuid

# مدل‌های داخلی اپلیکیشن accounts
from .models import UserPlan, BinaryCommission, LevelCommissionHistory, ROIHistory, BurnedIncome

# مدل‌های اپلیکیشن investments (فقط ایمپورت می‌شوند، اما اینجا ثبت نمی‌شوند)
from apps.investments.models import InvestmentPlan, UserInvestment

User = get_user_model()

# -----------------------------------------------------------------------------
# 1. ثبت مدل‌های مرتبط با کمیسیون و درآمدهای کاربر
# توجه: InvestmentPlan حذف شد چون در اپلیکیشن خودش (investments) ثبت شده است.
# -----------------------------------------------------------------------------

@admin.register(BurnedIncome)
class BurnedIncomeAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['user', 'amount', 'reason', 'description', 'created_at']
    
    def has_add_permission(self, request):
        return False

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'principal_amount', 'is_active', 'activated_at', 'expires_at']
    list_filter = ['is_active', 'plan']
    search_fields = ['user__username', 'user__email']
    autocomplete_fields = ['user', 'plan']

@admin.register(BinaryCommission)
class BinaryCommissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'paid_amount', 'flushed_amount', 'matched_volume', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ROIHistory)
class ROIHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'percent', 'created_at']
    list_filter = ['created_at', 'plan']
    search_fields = ['user__username']

@admin.register(LevelCommissionHistory)
class LevelCommissionHistoryAdmin(admin.ModelAdmin):
    list_display = ['earner', 'from_user', 'level', 'amount', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['earner__username', 'from_user__username']
    ordering = ['-created_at']

# -----------------------------------------------------------------------------
# 2. ثبت مدل اصلی کاربر با قابلیت درخت باینری پیشرفته
# -----------------------------------------------------------------------------

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'mobile', 'balance_display', 'referral_code', 'active_plan_display', 'binary_tree_link']
    search_fields = ['username', 'email', 'referral_code', 'mobile']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    actions = ['generate_referral_code_manual']

    fieldsets = (
        ('اطلاعات احراز هویت', {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'mobile')}),
        ('شبکه و جایگاه (Network)', {
            'fields': (
                'referral_code',
                'referrer',
                'binary_parent',
                'binary_position'
            ),
            'description': 'تنظیمات مربوط به جایگاه کاربر در درخت باینری و معرف‌ها.'
        }),
        ('امور مالی و حجم‌ها', {
            'fields': (
                ('left_volume', 'right_volume'),
                'total_commission_earned',
                'cash_balance',
                'reinvest_balance'
            ),
            'description': 'حجم‌های باینری و موجودی کیف پول‌ها.'
        }),
        ('تنظیمات پیشرفته', {
            'fields': ('auto_compound', 'crypto_wallet_address', 'crypto_address_index', 'lottery_points'),
            'classes': ('collapse',),
        }),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )

    @admin.action(description='تولید دستی کد رفرال برای کاربران بدون کد')
    def generate_referral_code_manual(self, request, queryset):
        count = 0
        for user in queryset:
            if not user.referral_code:
                unique_code = str(uuid.uuid4())[:8].upper()
                while User.objects.filter(referral_code=unique_code).exists():
                    unique_code = str(uuid.uuid4())[:8].upper()
                user.referral_code = unique_code
                user.save(update_fields=['referral_code'])
                count += 1
        self.message_user(request, f"{count} کد رفرال جدید صادر شد.", level='SUCCESS')

    def balance_display(self, obj):
        return f"${obj.cash_balance:,.2f}"
    balance_display.short_description = "موجودی نقد"

    def active_plan_display(self, obj):
        active_inv = obj.investments.filter(status='active').first()
        if active_inv:
             return f"{active_inv.plan_type} (${active_inv.amount})"
        if hasattr(obj, 'active_plan') and obj.active_plan.is_active:
            return obj.active_plan.plan.name
        return "-"
    active_plan_display.short_description = "پلن فعال"

    def binary_tree_link(self, obj):
        url = reverse('admin:binary_tree_view_user', args=[obj.username])
        return format_html(
            '<a href="{}" class="button" style="background:#28a745; color:white; padding:4px 10px; border-radius:4px; text-decoration:none;">🌳 مشاهده درخت</a>',
            url
        )
    binary_tree_link.short_description = "درخت باینری"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('binary-tree/', self.admin_site.admin_view(self.binary_tree_view), name='binary_tree_view'),
            path('binary-tree/<str:username>/', self.admin_site.admin_view(self.binary_tree_view), name='binary_tree_view_user'),
        ]
        return custom_urls + urls

    def binary_tree_view(self, request, username=None):
        if username:
            root_user = get_object_or_404(User, username=username)
        else:
            root_user = User.objects.filter(binary_parent__isnull=True).first()
            if not root_user:
                root_user = User.objects.first()

        if not root_user:
            return render(request, "admin/binary_tree.html", {'error': 'کاربری یافت نشد.'})

        def attach_stats(u):
            if not u: return None
            bin_qs = BinaryCommission.objects.filter(user=u).aggregate(total=Sum('paid_amount'))
            u.stat_binary_income = bin_qs['total'] or 0
            ref_qs = LevelCommissionHistory.objects.filter(earner=u).aggregate(total=Sum('amount'))
            u.stat_referral_income = ref_qs['total'] or 0
            u.stat_total_calc = u.stat_binary_income + u.stat_referral_income
            return u

        root_user = attach_stats(root_user)

        l_child = attach_stats(root_user.binary_children.filter(binary_position='left').first())
        r_child = attach_stats(root_user.binary_children.filter(binary_position='right').first())

        ll_child = None; lr_child = None
        if l_child:
            ll_child = attach_stats(l_child.binary_children.filter(binary_position='left').first())
            lr_child = attach_stats(l_child.binary_children.filter(binary_position='right').first())

        rl_child = None; rr_child = None
        if r_child:
            rl_child = attach_stats(r_child.binary_children.filter(binary_position='left').first())
            rr_child = attach_stats(r_child.binary_children.filter(binary_position='right').first())

        lll_child = None; llr_child = None
        if ll_child:
            lll_child = attach_stats(ll_child.binary_children.filter(binary_position='left').first())
            llr_child = attach_stats(ll_child.binary_children.filter(binary_position='right').first())

        lrl_child = None; lrr_child = None
        if lr_child:
            lrl_child = attach_stats(lr_child.binary_children.filter(binary_position='left').first())
            lrr_child = attach_stats(lr_child.binary_children.filter(binary_position='right').first())

        rll_child = None; rlr_child = None
        if rl_child:
            rll_child = attach_stats(rl_child.binary_children.filter(binary_position='left').first())
            rlr_child = attach_stats(rl_child.binary_children.filter(binary_position='right').first())

        rrl_child = None; rrr_child = None
        if rr_child:
            rrl_child = attach_stats(rr_child.binary_children.filter(binary_position='left').first())
            rrr_child = attach_stats(rr_child.binary_children.filter(binary_position='right').first())

        context = dict(
            self.admin_site.each_context(request),
            title=f"نمایش درخت باینری: {root_user.username}",
            root_user=root_user,
            l_child=l_child, r_child=r_child,
            ll_child=ll_child, lr_child=lr_child, rl_child=rl_child, rr_child=rr_child,
            lll_child=lll_child, llr_child=llr_child, lrl_child=lrl_child, lrr_child=lrr_child,
            rll_child=rll_child, rlr_child=rlr_child, rrl_child=rrl_child, rrr_child=rrr_child,
        )
        return render(request, "admin/binary_tree.html", context)
@admin.register(RegistrationSettings)
class RegistrationSettingsAdmin(admin.ModelAdmin):
    # پنهان کردن دکمه حذف و اضافه برای جلوگیری از اشتباه
    def has_add_permission(self, request):
        # اگر رکوردی وجود دارد، اجازه ساخت نده
        return not RegistrationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ['__str__', 'is_referral_required', 'is_email_required', 'is_mobile_required']

# apps/accounts/admin.py
# ... کدهای قبلی موجود ...

# ============================================================================
# 💳 Payment Request Admin (اضافه شده در 1404/10/17)
# ============================================================================

from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import PaymentRequest

@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = [
        'status_badge',
        'user_link', 
        'plan', 
        'currency', 
        'verified_amount_display',
        'created_at',
        'processed_at',
        'actions_column'
    ]
    
    list_filter = [
        'status', 
        'currency', 
        'created_at', 
        'plan',
        ('processed_at', admin.EmptyFieldListFilter)
    ]
    
    search_fields = [
        'user__username', 
        'user__email',
        'txid_or_hash', 
        'admin_notes'
    ]
    
    readonly_fields = [
        'user', 
        'plan', 
        'currency', 
        'txid_or_hash', 
        'receipt_preview',
        'created_at',
        'related_investment_link'
    ]
    
    fieldsets = (
        ('📋 اطلاعات درخواست', {
            'fields': ('user', 'plan', 'currency', 'created_at')
        }),
        ('🔐 اطلاعات تراکنش کاربر', {
            'fields': ('txid_or_hash', 'receipt_preview'),
            'description': 'اطلاعاتی که کاربر ارسال کرده است'
        }),
        ('✅ بررسی و تأیید ادمین', {
            'fields': ('verified_amount', 'status', 'admin_notes', 'processed_at'),
            'classes': ('wide',),
            'description': '⚠️ ابتدا مبلغ را وارد کنید، سپس وضعیت را Approved کنید'
        }),
        ('🔗 ارتباطات سیستمی', {
            'fields': ('related_investment_link',),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_selected_payments', 'reject_selected_payments']
    
    # -------------------------------------------------------------------------
    # Custom Display Methods
    # -------------------------------------------------------------------------
    
    @admin.display(description='وضعیت', ordering='status')
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'approved': '#28a745',
            'rejected': '#dc3545'
        }
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '❓')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:12px; font-weight:bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    
    @admin.display(description='کاربر')
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" target="_blank" style="font-weight:bold;">👤 {}</a>',
            url, obj.user.username
        )
    
    @admin.display(description='مبلغ تأیید شده')
    def verified_amount_display(self, obj):
        if obj.verified_amount:
            return format_html(
                '<span style="color:#28a745; font-weight:bold; font-size:14px;">${:,.2f}</span>',
                obj.verified_amount
            )
        return format_html('<span style="color:#dc3545;">❌ وارد نشده</span>')
    
    @admin.display(description='رسید')
    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:300px; max-height:200px; border:2px solid #ddd; border-radius:8px;"/></a><br><small>کلیک برای بزرگنمایی</small>',
                obj.receipt_image.url, obj.receipt_image.url
            )
        return "تصویری آپلود نشده"
    
    @admin.display(description='Investment')
    def related_investment_link(self, obj):
        if obj.related_investment:
            url = reverse('admin:investments_userinvestment_change', args=[obj.related_investment.id])
            return format_html(
                '<a href="{}" target="_blank" style="color:#28a745; font-weight:bold;">✅ مشاهده Investment #{}</a>',
                url, obj.related_investment.id
            )
        return format_html('<span style="color:#999;">هنوز ساخته نشده</span>')
    
    @admin.display(description='عملیات')
    def actions_column(self, obj):
        if obj.status == 'pending' and obj.verified_amount:
            return format_html(
                '<span style="color:#28a745; font-weight:bold;">✅ آماده تأیید</span>'
            )
        elif obj.status == 'pending':
            return format_html(
                '<span style="color:#FFA500;">⚠️ مبلغ وارد کنید</span>'
            )
        return '—'
    
    # -------------------------------------------------------------------------
    # Admin Actions 17-10-1404 
    # -------------------------------------------------------------------------
    
    @admin.action(description='✅ تأیید درخواست‌های انتخاب شده')
    def approve_selected_payments(self, request, queryset):
        approved_count = 0
        errors = []
        
        for payment in queryset.filter(status='pending'):
            if not payment.verified_amount or payment.verified_amount <= 0:
                errors.append(f"❌ {payment.user.username}: مبلغ تأیید شده وارد نشده!")
                continue
            
            if payment.related_investment:
                errors.append(f"⚠️ {payment.user.username}: قبلاً Investment ساخته شده!")
                continue
            
            # تأیید
            payment.status = 'approved'
            payment.save()  # Signal خودکار Investment می‌سازد
            approved_count += 1
        
        # نمایش پیام‌ها
        if errors:
            for err in errors:
                self.message_user(request, err, level=messages.ERROR)
        
        if approved_count > 0:
            self.message_user(
                request,
                f"✅ {approved_count} درخواست تأیید شد. Investment‌ها ساخته خواهند شد.",
                level=messages.SUCCESS
            )
    
    @admin.action(description='❌ رد درخواست‌های انتخاب شده')
    def reject_selected_payments(self, request, queryset):
        rejected_count = queryset.filter(status='pending').update(status='rejected')
        if rejected_count > 0:
            self.message_user(
                request,
                f"❌ {rejected_count} درخواست رد شد.",
                level=messages.WARNING
            )
    
    # -------------------------------------------------------------------------
    # Optimizations
    # -------------------------------------------------------------------------
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'plan', 'related_investment'
        )
    
    def has_add_permission(self, request):
        """فقط کاربران از طریق فرم اضافه می‌کنند"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """فقط درخواست‌های rejected قابل حذف هستند"""
        if obj and obj.status == 'rejected':
            return True
        return False
