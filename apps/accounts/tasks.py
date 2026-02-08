# apps/accounts/tasks.py - COMPLETE REWRITE FOR CELERY
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from apps.accounts.models import UserPlan, ROIHistory, BinaryCommission
from apps.investments.models import UserInvestment

User = get_user_model()
logger = logging.getLogger(__name__)


# =============================================
# 1️⃣ محاسبه ROI روزانه (هر شب ساعت 00:05)
# =============================================
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def calculate_daily_roi_for_all(self):
    """
    محاسبه سود روزانه (ROI) برای همه کاربران با سرمایه‌گذاری فعال.
    
    منطق:
    - پیدا کردن تمام UserInvestment های فعال
    - محاسبه سود روزانه بر اساس ROI ماهیانه پلن
    - واریز به cash_balance یا reinvest_balance (بر اساس auto_compound)
    - ثبت تاریخچه در ROIHistory
    """
    try:
        logger.info("🚀 شروع محاسبه ROI روزانه برای تمام کاربران...")
        
        # پیدا کردن سرمایه‌گذاری‌های فعال
        active_investments = UserInvestment.objects.filter(
            status='active',
            maturity_date__gte=timezone.now()
        ).select_related('user', 'plan')
        
        success_count = 0
        total_paid = Decimal('0')
        
        for invest in active_investments:
            try:
                with transaction.atomic():
                    user = invest.user
                    plan = invest.plan
                    
                    # محاسبه ROI ماهیانه
                    monthly_roi = (invest.amount * plan.roi_percent) / Decimal('100')
                    
                    # تبدیل به روزانه (30 روز)
                    daily_roi = monthly_roi / Decimal('30')
                    
                    if daily_roi <= 0:
                        continue
                    
                    # واریز به کیف پول مناسب
                    if user.auto_compound:
                        user.reinvest_balance += daily_roi
                        wallet_type = 'reinvest'
                    else:
                        user.cash_balance += daily_roi
                        wallet_type = 'cash'
                    
                    user.save(update_fields=['cash_balance', 'reinvest_balance'])
                    
                    # ثبت تاریخچه ROI
                    ROIHistory.objects.create(
                        user=user,
                        plan=plan,
                        amount=daily_roi,
                        percent=plan.roi_percent
                    )
                    
                    success_count += 1
                    total_paid += daily_roi
                    
                    logger.debug(
                        f"✅ ROI پرداخت شد: {user.username} → ${daily_roi:.2f} "
                        f"(پلن: {plan.name}, کیف: {wallet_type})"
                    )
                    
            except Exception as e:
                logger.error(f"❌ خطا در محاسبه ROI برای {invest.user.username}: {str(e)}")
                continue
        
        logger.info(f"✅ ROI کامل شد: {success_count} کاربر، ${total_paid:.2f} پرداخت شد")
        return {
            'success': success_count,
            'total_paid': float(total_paid),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ خطای کلی در محاسبه ROI: {str(e)}")
        raise self.retry(exc=e)


# =============================================
# 2️⃣ Flush کمیسیون Binary هفتگی (دوشنبه‌ها 01:00)
# =============================================
@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def flush_binary_commissions_weekly(self):
    """
    پاکسازی و پرداخت کمیسیون Binary هفتگی.
    
    منطق:
    - پیدا کردن کاربرانی که هم left_volume و هم right_volume دارند
    - محاسبه حجم matched (کمترین حجم بین دو طرف)
    - پرداخت کمیسیون بر اساس درصد Binary پلن
    - کم کردن حجم matched از هر دو طرف
    - ثبت تاریخچه در BinaryCommission
    """
    try:
        logger.info("🚀 شروع Binary Flush هفتگی...")
        
        # پیدا کردن کاربرانی که حجم در هر دو طرف دارند
        users_with_volume = User.objects.filter(
            left_volume__gt=0,
            right_volume__gt=0
        ).select_related('active_plan__plan')
        
        flushed_count = 0
        total_paid = Decimal('0')
        
        for user in users_with_volume:
            try:
                with transaction.atomic():
                    # محاسبه حجم matched
                    matched_volume = min(user.left_volume, user.right_volume)
                    
                    if matched_volume <= 0:
                        continue
                    
                    # گرفتن درصد Binary از پلن فعال یا پیش‌فرض
                    if hasattr(user, 'active_plan') and user.active_plan and user.active_plan.is_active:
                        binary_rate = user.active_plan.plan.binary_percentage or Decimal('10')
                    else:
                        # اگر پلن فعال نداره، از پلن اولین سرمایه‌گذاری استفاده کن
                        first_invest = user.investments.filter(status='active').first()
                        if first_invest:
                            binary_rate = first_invest.plan.binary_percentage or Decimal('10')
                        else:
                            binary_rate = Decimal('10')  # پیش‌فرض
                    
                    # محاسبه کمیسیون
                    commission = (matched_volume * binary_rate) / Decimal('100')
                    
                    # پرداخت به کیف پول نقدی
                    user.cash_balance += commission
                    
                    # کم کردن حجم matched از دو طرف
                    user.left_volume -= matched_volume
                    user.right_volume -= matched_volume
                    
                    user.save(update_fields=['cash_balance', 'left_volume', 'right_volume'])
                    
                    # ثبت تاریخچه Binary
                    BinaryCommission.objects.create(
                        user=user,
                        matched_volume=matched_volume,
                        percentage=binary_rate,
                        calc_amount=commission,
                        paid_amount=commission,
                        flushed_amount=Decimal('0')
                    )
                    
                    flushed_count += 1
                    total_paid += commission
                    
                    logger.debug(
                        f"✅ Binary فلاش شد: {user.username} → ${commission:.2f} "
                        f"(حجم: {matched_volume}, درصد: {binary_rate}%)"
                    )
                    
            except Exception as e:
                logger.error(f"❌ خطا در Binary Flush برای {user.username}: {str(e)}")
                continue
        
        logger.info(f"✅ Binary Flush کامل شد: {flushed_count} کاربر، ${total_paid:.2f} پرداخت شد")
        return {
            'flushed': flushed_count,
            'total_paid': float(total_paid),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ خطای کلی در Binary Flush: {str(e)}")
        raise self.retry(exc=e)


# =============================================
# 3️⃣ محاسبه Level Commission (اختیاری - فعلاً غیرفعال)
# =============================================
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def calculate_level_commissions(self):
    """
    محاسبه کمیسیون سطحی برای کاربران.
    
    ⚠️ این Task فعلاً در Beat Schedule غیرفعال است.
    اگر نیاز به فعال‌سازی داری، کد آن را در celery.py uncomment کن.
    """
    logger.info("🚀 شروع محاسبه Level Commissions...")
    
    # منطق محاسبه Level Commission اینجا اضافه می‌شه
    # (به صورت پیش‌فرض خالی گذاشته شده)
    
    logger.info("⚠️ Level Commission فعلاً پیاده‌سازی نشده است.")
    return {'status': 'not_implemented'}


# =============================================
# 4️⃣ تسک تستی (برای چک کردن Celery)
# =============================================
@shared_task
def test_celery():
    """
    تسک ساده برای تست اینکه Celery درست کار می‌کنه.
    
    استفاده:
    >>> from apps.accounts.tasks import test_celery
    >>> result = test_celery.delay()
    >>> result.get()
    """
    logger.info("✅ Celery کار می‌کند! تسک تستی با موفقیت اجرا شد.")
    return "Success - Celery is working properly!"
