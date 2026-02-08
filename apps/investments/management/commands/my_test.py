from apps.accounts.models import BinaryCommission, User

# دریافت کاربر fafa
user = User.objects.get(username='fafa')

# دریافت آخرین کمیسیون باینری
last_comm = BinaryCommission.objects.filter(user=user).order_by('-created_at').first()

if last_comm:
    print(f"✅ رکورد پیدا شد! تاریخ: {last_comm.created_at}")
    print(f"💰 مبلغ فعلی ثبت شده: {last_comm.paid_amount}")
    print(f"⚖️ حجم مچ شده: {last_comm.matched_volume}")
    
    # اصلاح مبلغ اگر صفر باشد
    if last_comm.paid_amount == 0 and last_comm.matched_volume > 0:
        last_comm.paid_amount = 450  # تنظیم دستی روی ۴۵۰ دلار
        last_comm.save()
        print("🎉 اصلاح شد! مبلغ به 450 تغییر یافت.")
    elif last_comm.paid_amount > 0:
        print("👍 مبلغ از قبل درست است.")
    else:
        print("❌ حجم مچ شده صفر است، شاید محاسبه‌ای انجام نشده.")
else:
    print("❌ هیچ رکورد کمیسیون باینری برای این کاربر یافت نشد.")

