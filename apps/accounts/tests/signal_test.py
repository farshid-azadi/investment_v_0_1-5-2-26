# apps/accounts/tests/signal_test.py

from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal

from apps.accounts.models import User
from apps.investments.models import UserInvestment, InvestmentPlan


class BaseSignalTest(TestCase):
    """
    کلاس پایه برای تست‌های Signal با ایجاد داده‌های مشترک
    """
    
    def setUp(self):
        # ساخت پلن سرمایه‌گذاری با فیلدهای صحیح ✅
        self.plan = InvestmentPlan.objects.create(
            name="Gold",
            daily_interest_rate=Decimal('2.5'),  # ✅ فیلد صحیح
            min_amount=Decimal('100.00'),        # ✅ فیلد صحیح
            max_amount=Decimal('10000.00'),      # ✅ فیلد صحیح
            duration_days=365,
            is_active=True
        )

        # ساخت سه نسل کاربر (مستقیم + دو سطح بالا)
        self.root = User.objects.create_user(
            username='root',
            mobile='09100000001',
            password='test123',
            referral_code='ROOT1234'
        )

        self.parent = User.objects.create_user(
            username='parent',
            mobile='09100000002',
            password='test123',
            referrer=self.root
        )

        self.child = User.objects.create_user(
            username='child',
            mobile='09100000003',
            password='test123',
            referrer=self.parent
        )


# ========================================================================
# ✅ سناریو 1: تولید کد معرف برای کاربر بدون کد
# ========================================================================
class ReferralCodeGenerationTest(BaseSignalTest):
    
    def test_generate_code_on_first_investment(self):
        """✅ سناریو 1: تولید کد معرف برای کاربر بدون کد"""
        # کاربر بدون کد معرف
        user_without_code = User.objects.create_user(
            username='newuser',
            mobile='09111111111',
            password='test123'
        )
        self.assertIsNone(user_without_code.referral_code)

        # خرید پلن
        with patch('apps.accounts.tasks.task_distribute_level_commission') as mock_level, \
             patch('apps.accounts.tasks.task_propagate_volume') as mock_volume:
            
            investment = UserInvestment.objects.create(
                user=user_without_code,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )

        # بررسی: کد معرف تولید شده
        user_without_code.refresh_from_db()
        self.assertIsNotNone(user_without_code.referral_code)
        self.assertEqual(len(user_without_code.referral_code), 8)
        print(f"✅ کد معرف تولید شد: {user_without_code.referral_code}")

    def test_no_duplicate_code_generation(self):
        """✅ سناریو 2: عدم تولید کد مجدد برای کاربران دارای کد"""
        original_code = self.root.referral_code

        with patch('apps.accounts.tasks.task_distribute_level_commission'), \
             patch('apps.accounts.tasks.task_propagate_volume'):
            
            UserInvestment.objects.create(
                user=self.root,
                plan_type=self.plan.name,
                amount=Decimal('1000.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )

        self.root.refresh_from_db()
        self.assertEqual(self.root.referral_code, original_code)
        print(f"✅ کد معرف ثابت ماند: {self.root.referral_code}")


# ========================================================================
# ✅ سناریو 3 و 4: تست Task کمیسیون سطحی
# ========================================================================
class LevelCommissionSignalTest(BaseSignalTest):
    
    def test_level_commission_called_on_active_investment(self):
        """✅ سناریو 3: فراخوانی Task کمیسیون سطحی"""
        with patch('apps.accounts.tasks.task_distribute_level_commission') as mock_task:
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )
            
            mock_task.assert_called_once()
            print("✅ task_distribute_level_commission فراخوانی شد")

    def test_level_commission_not_called_on_pending(self):
        """✅ سناریو 4: عدم فراخوانی برای وضعیت pending"""
        with patch('apps.accounts.tasks.task_distribute_level_commission') as mock_task:
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='pending'  # وضعیت غیرفعال
            )
            
            mock_task.assert_not_called()
            print("✅ Task برای status=pending اجرا نشد (صحیح)")


# ========================================================================
# ✅ سناریو 5 و 6: تست Task انتشار حجم
# ========================================================================
class VolumePropagatioSignalTest(BaseSignalTest):
    
    def test_volume_propagation_called(self):
        """✅ سناریو 5: فراخوانی Task انتشار حجم"""
        with patch('apps.accounts.tasks.task_propagate_volume') as mock_task:
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )
            
            mock_task.assert_called_once()
            print("✅ task_propagate_volume فراخوانی شد")

    def test_volume_not_propagated_on_cancelled(self):
        """✅ سناریو 6: عدم انتشار حجم برای وضعیت cancelled"""
        with patch('apps.accounts.tasks.task_propagate_volume') as mock_task:
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='cancelled'
            )
            
            mock_task.assert_not_called()
            print("✅ Task برای status=cancelled اجرا نشد (صحیح)")


# ========================================================================
# ✅ سناریو 7: مدیریت خطا در Taskها
# ========================================================================
class ErrorHandlingSignalTest(BaseSignalTest):
    
    def test_signal_continues_after_task_error(self):
        """✅ سناریو 7: ادامه Signal حتی در صورت خطا در یکی از Taskها"""
        with patch('apps.accounts.tasks.task_distribute_level_commission', side_effect=Exception("❌ خطای شبیه‌سازی شده")), \
             patch('apps.accounts.tasks.task_propagate_volume') as mock_volume:
            
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )
            
            # بررسی: Task دوم اجرا شده
            mock_volume.assert_called_once()
            print("✅ Signal حتی با خطا در Task اول، Task دوم را اجرا کرد")


# ========================================================================
# ✅ سناریو 8: تست کامل جریان (Integration Test)
# ========================================================================
class IntegrationSignalTest(BaseSignalTest):
    
    def test_full_investment_flow(self):
        """✅ سناریو 8: تست کامل جریان خرید پلن"""
        # کاربر جدید بدون کد معرف
        new_user = User.objects.create_user(
            username='investor',
            mobile='09222222222',
            password='test123',
            referrer=self.parent
        )

        with patch('apps.accounts.tasks.task_distribute_level_commission') as mock_level, \
             patch('apps.accounts.tasks.task_propagate_volume') as mock_volume:
            
            investment = UserInvestment.objects.create(
                user=new_user,
                plan_type=self.plan.name,
                amount=Decimal('1000.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )

            # بررسی‌ها
            new_user.refresh_from_db()
            self.assertIsNotNone(new_user.referral_code)
            mock_level.assert_called_once()
            mock_volume.assert_called_once()
            
            print("✅ تست یکپارچگی کامل: همه مراحل اجرا شدند")


# ========================================================================
# ✅ سناریو 9: چند خرید متوالی
# ========================================================================
class MultipleInvestmentsSignalTest(BaseSignalTest):
    
    def test_multiple_investments_same_user(self):
        """✅ سناریو 9: چند خرید متوالی از یک کاربر"""
        with patch('apps.accounts.tasks.task_distribute_level_commission') as mock_level, \
             patch('apps.accounts.tasks.task_propagate_volume') as mock_volume:
            
            # خرید اول
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('500.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )
            
            first_code = self.child.referral_code
            
            # خرید دوم
            UserInvestment.objects.create(
                user=self.child,
                plan_type=self.plan.name,
                amount=Decimal('700.00'),
                daily_interest_rate=self.plan.daily_interest_rate,
                status='active'
            )
            
            self.child.refresh_from_db()
            
            # بررسی‌ها
            self.assertEqual(mock_level.call_count, 2)
            self.assertEqual(mock_volume.call_count, 2)
            self.assertEqual(self.child.referral_code, first_code)
            
            print("✅ چند خرید متوالی: Taskها چندبار اجرا شدند، کد معرف ثابت ماند")
# --- تنظیمات Celery برای تسک‌های زمان‌بندی شده ---