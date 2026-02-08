# apps/investments/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, InvalidOperation
import warnings

from .models import InvestmentPlan, UserInvestment


# =============================================================================
# 🛠️ فرم ادمین InvestmentPlan - حل مشکل Number Input
# =============================================================================

class InvestmentPlanAdminForm(forms.ModelForm):
    """
    فرم سفارشی برای پنل ادمین InvestmentPlan
    
    🎯 اهداف:
    - تبدیل فیلدهای عددی از NumberInput به TextInput (حذف فلش‌ها)
    - اعتبارسنجی دقیق مقادیر ورودی
    - پشتیبانی از autocomplete (نیاز به search_fields در admin.py)
    
    ✅ فیلدهای تحت تأثیر:
    - min_amount, max_amount
    - daily_interest_rate, max_total_return_percent
    - duration_days, binary_retention_days
    """
    
    class Meta:
        model = InvestmentPlan
        fields = '__all__'
        widgets = {
            # ─────────────────────────────────────────────────────────────────
            # 💰 محدوده سرمایه‌گذاری
            # ─────────────────────────────────────────────────────────────────
            'min_amount': forms.TextInput(attrs={
                'placeholder': '100.00',
                'class': 'vTextField',
                'style': 'width: 200px; font-family: monospace; font-size: 14px;',
                'title': 'حداقل مبلغ سرمایه‌گذاری به دلار (مثال: 100.00)'
            }),
            'max_amount': forms.TextInput(attrs={
                'placeholder': '10000.00',
                'class': 'vTextField',
                'style': 'width: 200px; font-family: monospace; font-size: 14px;',
                'title': 'حداکثر مبلغ سرمایه‌گذاری به دلار (مثال: 10000.00)'
            }),
            
            # ─────────────────────────────────────────────────────────────────
            # 📊 تنظیمات ROI
            # ─────────────────────────────────────────────────────────────────
            'daily_interest_rate': forms.TextInput(attrs={
                'placeholder': '2.5',
                'class': 'vTextField',
                'style': 'width: 120px; font-family: monospace; font-size: 14px;',
                'title': 'درصد سود روزانه (مثال: 2.5 برای 2.5%)'
            }),
            'max_total_return_percent': forms.TextInput(attrs={
                'placeholder': '200',
                'class': 'vTextField',
                'style': 'width: 120px; font-family: monospace; font-size: 14px;',
                'title': 'سقف کل برداشت به درصد (مثال: 200 یعنی دو برابر)'
            }),
            'duration_days': forms.TextInput(attrs={
                'placeholder': '365',
                'class': 'vTextField',
                'style': 'width: 100px; font-family: monospace; font-size: 14px;',
                'title': 'مدت زمان پلن به روز (مثال: 365 برای یک سال)'
            }),
            
            # ─────────────────────────────────────────────────────────────────
            # 🌳 تنظیمات باینری تری
            # ─────────────────────────────────────────────────────────────────
            'binary_retention_days': forms.TextInput(attrs={
                'placeholder': '365',
                'class': 'vTextField',
                'style': 'width: 100px; font-family: monospace; font-size: 14px;',
                'title': 'تعداد روزهای نگهداری حجم باینری (پیش‌فرض: 365)'
            }),
            
            # ─────────────────────────────────────────────────────────────────
            # 📝 اطلاعات متنی
            # ─────────────────────────────────────────────────────────────────
            'name': forms.TextInput(attrs={
                'class': 'vTextField',
                'style': 'width: 100%; max-width: 400px;',
                'placeholder': 'نام پلن (مثال: پلن برنزی)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'vLargeTextField',
                'style': 'width: 100%; max-width: 600px;',
                'placeholder': 'توضیحات کامل پلن...'
            }),
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🔍 اعتبارسنجی فیلدهای جداگانه
    # ─────────────────────────────────────────────────────────────────────────
    
    def clean_min_amount(self):
        """اعتبارسنجی حداقل مبلغ"""
        value = self.cleaned_data.get('min_amount')
        
        if value is None or value == '':
            raise ValidationError(_("❌ حداقل مبلغ الزامی است."))
        
        try:
            decimal_value = Decimal(str(value))
            
            if decimal_value < 0:
                raise ValidationError(_("❌ مبلغ نمی‌تواند منفی باشد."))
            
            if decimal_value == 0:
                raise ValidationError(_("❌ حداقل مبلغ باید بیشتر از صفر باشد."))
            
            # حداقل منطقی (مثلاً 1 دلار)
            if decimal_value < Decimal('1.00'):
                raise ValidationError(_("❌ حداقل مبلغ باید حداقل $1.00 باشد."))
            
            return decimal_value
            
        except (ValueError, InvalidOperation):
            raise ValidationError(_("❌ لطفاً یک عدد اعشاری معتبر وارد کنید (مثال: 100 یا 100.50)"))
    
    def clean_max_amount(self):
        """اعتبارسنجی حداکثر مبلغ"""
        value = self.cleaned_data.get('max_amount')
        
        if value is None or value == '':
            raise ValidationError(_("❌ حداکثر مبلغ الزامی است."))
        
        try:
            decimal_value = Decimal(str(value))
            
            if decimal_value < 0:
                raise ValidationError(_("❌ مبلغ نمی‌تواند منفی باشد."))
            
            if decimal_value == 0:
                raise ValidationError(_("❌ حداکثر مبلغ باید بیشتر از صفر باشد."))
            
            # بررسی تطابق با min_amount (اگر قبلاً validate شده)
            min_amt = self.cleaned_data.get('min_amount')
            if min_amt and decimal_value < min_amt:
                raise ValidationError(
                    _("❌ حداکثر مبلغ (%(max)s) نمی‌تواند کمتر از حداقل (%(min)s) باشد.") % {
                        'max': decimal_value,
                        'min': min_amt
                    }
                )
            
            return decimal_value
            
        except (ValueError, InvalidOperation):
            raise ValidationError(_("❌ عدد نامعتبر. مثال صحیح: 10000.00"))
    
    def clean_daily_interest_rate(self):
        """اعتبارسنجی نرخ سود روزانه"""
        value = self.cleaned_data.get('daily_interest_rate')
        
        if value is None or value == '':
            raise ValidationError(_("❌ نرخ سود روزانه الزامی است."))
        
        try:
            decimal_value = Decimal(str(value))
            
            if decimal_value < 0:
                raise ValidationError(_("❌ نرخ سود نمی‌تواند منفی باشد."))
            
            if decimal_value == 0:
                raise ValidationError(_("❌ نرخ سود باید بیشتر از صفر باشد."))
            
            if decimal_value > 100:
                raise ValidationError(_("❌ نرخ سود نمی‌تواند بیشتر از 100% باشد."))
            
            # هشدار برای نرخ‌های خطرناک (بالای 10% در روز)
            if decimal_value > Decimal('10.0'):
                warnings.warn(
                    f"⚠️ نرخ سود {decimal_value}% در روز بسیار بالاست و ممکن است در بلندمدت پایدار نباشد!",
                    UserWarning
                )
            
            return decimal_value
            
        except (ValueError, InvalidOperation):
            raise ValidationError(_("❌ عدد نامعتبر. مثال صحیح: 2.5"))
    
    def clean_max_total_return_percent(self):
        """اعتبارسنجی سقف کل برداشت"""
        value = self.cleaned_data.get('max_total_return_percent')
        
        if value is None or value == '':
            raise ValidationError(_("❌ سقف کل برداشت الزامی است."))
        
        try:
            decimal_value = Decimal(str(value))
            
            if decimal_value < 0:
                raise ValidationError(_("❌ درصد نمی‌تواند منفی باشد."))
            
            if decimal_value == 0:
                raise ValidationError(_("❌ سقف برداشت باید بیشتر از صفر باشد."))
            
            # منطق کسب‌وکار: سقف معمولاً بین 100% تا 300% است
            if decimal_value < Decimal('100.0'):
                raise ValidationError(
                    _("⚠️ سقف کمتر از 100%% یعنی کاربر حتی اصل سرمایه‌اش را هم نمی‌تواند کامل بردارد! آیا مطمئنید?")
                )
            
            if decimal_value > Decimal('1000.0'):
                warnings.warn(
                    f"⚠️ سقف برداشت {decimal_value}% بسیار بالاست و ممکن است غیرواقعی باشد.",
                    UserWarning
                )
            
            return decimal_value
            
        except (ValueError, InvalidOperation):
            raise ValidationError(_("❌ عدد نامعتبر. مثال صحیح: 200"))
    
    def clean_duration_days(self):
        """اعتبارسنجی مدت زمان پلن"""
        value = self.cleaned_data.get('duration_days')
        
        if value is None or value == '':
            raise ValidationError(_("❌ مدت زمان پلن الزامی است."))
        
        try:
            int_value = int(value)
            
            if int_value < 1:
                raise ValidationError(_("❌ مدت زمان باید حداقل 1 روز باشد."))
            
            if int_value > 3650:  # 10 سال
                raise ValidationError(_("❌ حداکثر مدت زمان مجاز 3650 روز (10 سال) است."))
            
            return int_value
            
        except (ValueError, TypeError):
            raise ValidationError(_("❌ لطفاً یک عدد صحیح وارد کنید (مثال: 365)"))
    
    def clean_binary_retention_days(self):
        """اعتبارسنجی تعداد روزهای نگهداری حجم باینری"""
        value = self.cleaned_data.get('binary_retention_days')
        
        # مقدار پیش‌فرض اگر خالی باشد
        if value is None or value == '':
            return 365
        
        try:
            int_value = int(value)
            
            if int_value < 0:
                raise ValidationError(_("❌ تعداد روز نمی‌تواند منفی باشد."))
            
            if int_value > 3650:  # 10 سال
                raise ValidationError(_("❌ حداکثر 3650 روز (10 سال) مجاز است."))
            
            return int_value
            
        except (ValueError, TypeError):
            raise ValidationError(_("❌ لطفاً یک عدد صحیح وارد کنید (مثال: 365)"))
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🔧 اعتبارسنجی ترکیبی (Cross-field validation)
    # ─────────────────────────────────────────────────────────────────────────
    
    def clean(self):
        """اعتبارسنجی منطق کلی بین فیلدها"""
        cleaned_data = super().clean()
        
        min_amt = cleaned_data.get('min_amount')
        max_amt = cleaned_data.get('max_amount')
        daily_rate = cleaned_data.get('daily_interest_rate')
        duration = cleaned_data.get('duration_days')
        max_return = cleaned_data.get('max_total_return_percent')
        
        # ─────────────────────────────────────────────────────────────────────
        # بررسی محدوده مبلغ
        # ─────────────────────────────────────────────────────────────────────
        if min_amt and max_amt:
            if max_amt < min_amt:
                raise ValidationError({
                    'max_amount': _("❌ حداکثر مبلغ باید بزرگتر یا مساوی حداقل مبلغ باشد.")
                })
        
        # ─────────────────────────────────────────────────────────────────────
        # بررسی منطق سود (هشدار، نه خطا)
        # ─────────────────────────────────────────────────────────────────────
        if daily_rate and duration and max_return:
            # محاسبه کل سود نظری اگر تمام روزها سود داده شود
            total_theoretical_return = daily_rate * Decimal(str(duration))
            
            # اگر سود نظری بیشتر از سقف برداشت باشد
            if total_theoretical_return > max_return:
                warnings.warn(
                    f"⚠️ توجه: سود نظری کل ({total_theoretical_return:.1f}%) بیشتر از سقف برداشت ({max_return}%) است.\n"
                    f"این یعنی کاربران نمی‌توانند تمام سود خود را بردارند و پلن زودتر متوقف می‌شود.",
                    UserWarning
                )
            
            # اگر سود نظری خیلی کمتر از سقف باشد (احتمال خطا در تنظیمات)
            if total_theoretical_return < (max_return / Decimal('2')):
                warnings.warn(
                    f"⚠️ سود نظری ({total_theoretical_return:.1f}%) خیلی کمتر از سقف برداشت ({max_return}%) است.\n"
                    f"آیا مطمئنید تنظیمات صحیح است?",
                    UserWarning
                )
        
        return cleaned_data


# =============================================================================
# 🛒 فرم خرید پلن توسط کاربران (برای آینده)
# =============================================================================

class BuyPlanForm(forms.Form):
    """
    فرم ساده برای خرید پلن توسط کاربران
    
    💡 نکته: فعلاً از طریق PaymentRequest کار می‌شود،
    اما این فرم برای صفحات عمومی یا API آماده است.
    """
    
    plan = forms.ModelChoiceField(
        queryset=InvestmentPlan.objects.filter(is_active=True),
        label=_("پلن مورد نظر"),
        empty_label=_("انتخاب کنید..."),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 100%; max-width: 300px;'
        })
    )
    
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=Decimal('1.00'),
        label=_("مبلغ سرمایه‌گذاری (USD)"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1000.00',
            'style': 'font-family: monospace; width: 100%; max-width: 200px;'
        })
    )
    
    def clean(self):
        """بررسی تطابق مبلغ با محدوده پلن"""
        cleaned_data = super().clean()
        plan = cleaned_data.get('plan')
        amount = cleaned_data.get('amount')
        
        if plan and amount:
            # بررسی حداقل
            if amount < plan.min_amount:
                raise ValidationError({
                    'amount': _(
                        "❌ حداقل مبلغ برای این پلن $%(min_amount).2f است."
                    ) % {'min_amount': plan.min_amount}
                })
            
            # بررسی حداکثر
            if amount > plan.max_amount:
                raise ValidationError({
                    'amount': _(
                        "❌ حداکثر مبلغ برای این پلن $%(max_amount).2f است."
                    ) % {'max_amount': plan.max_amount}
                })
        
        return cleaned_data


# =============================================================================
# 📊 فرم ادمین UserInvestment (اختیاری - برای ویرایش دستی)
# =============================================================================

class UserInvestmentAdminForm(forms.ModelForm):
    """
    فرم ادمین برای ویرایش دستی سرمایه‌گذاری‌ها
    
    ⚠️ هشدار: تغییرات دستی روی amount یا total_profit_earned
    می‌تواند باعث اختلال در محاسبات ROI و باینری شود!
    
    💡 توصیه: فقط برای رفع مشکلات اضطراری استفاده شود.
    """
    
    class Meta:
        model = UserInvestment
        fields = '__all__'
        widgets = {
            'amount': forms.TextInput(attrs={
                'class': 'vTextField',
                'style': 'width: 200px; font-family: monospace; background: #fff9e6;',
                'title': 'مبلغ اصلی سرمایه‌گذاری (تغییر آن خطرناک است!)'
            }),
            'reinvested_amount': forms.TextInput(attrs={
                'class': 'vTextField',
                'style': 'width: 200px; font-family: monospace;',
                'readonly': 'readonly',  # فقط خواندنی
                'title': 'مبلغ سرمایه‌گذاری مجدد (محاسبه خودکار)'
            }),
            'total_profit_earned': forms.TextInput(attrs={
                'class': 'vTextField',
                'style': 'width: 200px; font-family: monospace; background: #e6f7ff;',
                'title': 'کل سود دریافت شده (تغییر آن ممکن است منجر به اشتباه شود)'
            }),
        }
    
    def clean_amount(self):
        """جلوگیری از تغییر مبلغ اولیه بعد از ایجاد"""
        instance = getattr(self, 'instance', None)
        
        # اگر سرمایه‌گذاری از قبل وجود دارد
        if instance and instance.pk:
            # فقط مقدار اصلی را برگردان، تغییر نده
            warnings.warn(
                "⚠️ تغییر مبلغ اصلی سرمایه‌گذاری بعد از ایجاد توصیه نمی‌شود!",
                UserWarning
            )
            return instance.amount
        
        # سرمایه‌گذاری جدید - اعتبارسنجی معمولی
        value = self.cleaned_data.get('amount')
        
        if value is None or value <= 0:
            raise ValidationError(_("❌ مبلغ باید بیشتر از صفر باشد."))
        
        return value
    
    def clean_total_profit_earned(self):
        """هشدار برای تغییر دستی سود"""
        value = self.cleaned_data.get('total_profit_earned')
        instance = getattr(self, 'instance', None)
        
        # اگر مقدار تغییر کرده
        if instance and instance.pk and value != instance.total_profit_earned:
            warnings.warn(
                f"⚠️ در حال تغییر سود از ${instance.total_profit_earned} به ${value}!\n"
                f"این ممکن است باعث اختلال در محاسبات ROI شود.",
                UserWarning
            )
        
        if value is not None and value < 0:
            raise ValidationError(_("❌ سود نمی‌تواند منفی باشد."))
        
        return value
