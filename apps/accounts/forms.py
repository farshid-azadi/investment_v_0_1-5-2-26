# apps/accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
# فرض بر این است که مدل RegistrationSettings در models.py تعریف شده است
from .models import RegistrationSettings

User = get_user_model()

class UserRegisterForm(forms.ModelForm):
    # --- تعریف فیلدهای اضافی و بازنویسی فیلدها ---
    
    password = forms.CharField(
        label=_("رمز عبور"),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
            'placeholder': 'رمز عبور قوی انتخاب کنید'
        })
    )
    
    confirm_password = forms.CharField(
        label=_("تکرار رمز عبور"),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
            'placeholder': 'تکرار رمز عبور'
        })
    )
    
    referral_code = forms.CharField(
        label=_("کد معرف"),
        required=False, # پیش‌فرض False است، در __init__ بر اساس تنظیمات تغییر می‌کند
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
            'placeholder': 'کد معرف'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'mobile']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
                'placeholder': 'نام کاربری (انگلیسی)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
                'placeholder': 'example@email.com'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200',
                'placeholder': '0912...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. بارگذاری تنظیمات از دیتابیس
        try:
            settings = RegistrationSettings.load()
        except Exception:
            # اگر به هر دلیلی تنظیمات لود نشد (مثلاً مایگریشن اولیه)، خطا ندهد
            return

        # 2. اعمال تنظیمات روی فیلدها (اجباری/اختیاری بودن و متن placeholder)
        
        # --- تنظیمات کد معرف ---
        self.fields['referral_code'].required = settings.is_referral_required
        if not settings.is_referral_required:
            current_ph = self.fields['referral_code'].widget.attrs.get('placeholder', '')
            if "(اختیاری)" not in current_ph:
                self.fields['referral_code'].widget.attrs['placeholder'] = f"{current_ph} (اختیاری)"
        
        # --- تنظیمات ایمیل ---
        self.fields['email'].required = settings.is_email_required
        if not settings.is_email_required:
            current_ph = self.fields['email'].widget.attrs.get('placeholder', '')
            if "(اختیاری)" not in current_ph:
                self.fields['email'].widget.attrs['placeholder'] = f"{current_ph} (اختیاری)"
            
        # --- تنظیمات موبایل ---
        self.fields['mobile'].required = settings.is_mobile_required
        if not settings.is_mobile_required:
             current_ph = self.fields['mobile'].widget.attrs.get('placeholder', '')
             if "(اختیاری)" not in current_ph:
                self.fields['mobile'].widget.attrs['placeholder'] = f"{current_ph} (اختیاری)"

    # --- متدهای Clean برای تبدیل رشته خالی به None (حل مشکل Unique Constraint) ---

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile:
            return None  # ذخیره به عنوان NULL در دیتابیس
        return mobile

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if not code:
            return None
        return code
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return None
        return email

    # --- اعتبارسنجی اصلی و منطق باینری ---

    def clean(self):
        cleaned_data = super().clean()
        
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        referral_code = cleaned_data.get("referral_code")
        
        # بارگذاری تنظیمات برای چک کردن نهایی
        settings = RegistrationSettings.load()

        # 1. بررسی تطابق رمز عبور
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _("رمز عبور و تکرار آن مطابقت ندارند."))

        # 2. بررسی اجباری بودن کد معرف طبق تنظیمات
        if settings.is_referral_required and not referral_code:
             self.add_error('referral_code', _("وارد کردن کد معرف الزامی است."))

        # 3. منطق جایگذاری خودکار در درخت باینری
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                
                # بررسی جایگاه‌های خالی والد (در اینجا معرف همان والد باینری در نظر گرفته شده است)
                has_left = User.objects.filter(binary_parent=referrer, binary_position='left').exists()
                has_right = User.objects.filter(binary_parent=referrer, binary_position='right').exists()

                if not has_left:
                    # جایگاه چپ خالی است
                    self.instance.binary_position = 'left'
                    self.instance.binary_parent = referrer
                
                elif not has_right:
                    # جایگاه چپ پر است، اما راست خالی است
                    self.instance.binary_position = 'right'
                    self.instance.binary_parent = referrer
                
                else:
                    # هر دو جایگاه پر هستند
                    raise ValidationError(
                        _("ظرفیت جایگاه‌های مستقیم این معرف (چپ و راست) پر شده است. امکان ثبت نام مستقیم با این کد وجود ندارد.")
                    )

                # تنظیم معرف مستقیم
                self.instance.referrer = referrer
                
            except User.DoesNotExist:
                self.add_error('referral_code', _("کد معرف وارد شده نامعتبر است."))

        return cleaned_data

    def save(self, commit=True):
        # ساخت نمونه کاربر ولی ذخیره نکردن در دیتابیس فعلا
        user = super().save(commit=False)
        
        # تنظیم رمز عبور هش شده
        user.set_password(self.cleaned_data["password"])
        
        # نکته: فیلدهای referrer, binary_parent, binary_position قبلاً 
        # در متد clean روی self.instance (که همان user است) ست شده‌اند.
        
        if commit:
            user.save()
            
        return user
