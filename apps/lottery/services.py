# apps/lottery/services.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import LotteryRound, LotteryTicket, LotteryWinner, LotterySetting
from apps.accounts.models import User
from apps.wallet.models import Transaction

class LotteryService:
    
    @staticmethod
    def get_current_round():
        """
        دریافت دور فعال فعلی یا ایجاد دور جدید اگر وجود نداشت
        """
        round_obj = LotteryRound.objects.filter(is_active=True).first()
        if not round_obj:
            # اگر دوری وجود نداشت، اولین دور را میسازیم
            round_obj = LotteryRound.objects.create(
                round_number=1,
                start_date=timezone.now(),
                is_active=True
            )
        return round_obj

    @staticmethod
    @transaction.atomic
    def buy_ticket(user: User):
        """
        خرید بلیط برای کاربر
        """
        settings = LotterySetting.get_solo()
        ticket_price = settings.ticket_price
        
        # 1. بررسی موجودی (از Cash Balance کم می‌کنیم)
        if user.cash_balance < ticket_price:
            raise ValueError("موجودی کافی نیست (Cash Balance insufficient)")

        # 2. کسر موجودی
        user.cash_balance -= ticket_price
        user.save()

        # 3. ثبت تراکنش برداشت
        Transaction.objects.create(
            user=user,
            amount=ticket_price,
            transaction_type='withdraw',
            description=f"Purchase Lottery Ticket",
            reference=f"LOTTERY_TICKET"
        )

        # 4. دریافت دور فعال
        current_round = LotteryService.get_current_round()

        # 5. صدور بلیط
        ticket = LotteryTicket.objects.create(
            user=user,
            lottery_round=current_round,
            ticket_price=ticket_price
        )

        # 6. آپدیت موجودی صندوق لاتاری
        current_round.total_pot += ticket_price
        current_round.participants_count += 1
        current_round.save()

        return ticket

    @staticmethod
    @transaction.atomic
    def run_lottery_draw(round_id):
        """
        اجرای قرعه‌کشی، انتخاب برنده و انتقال پول به دور بعد
        """
        lottery_round = LotteryRound.objects.select_for_update().get(id=round_id)
        
        if not lottery_round.is_active:
            raise ValueError("این دور قبلاً قرعه‌کشی شده است.")

        if lottery_round.participants_count == 0:
             # اگر شرکت کننده‌ای نبود، دور را می‌بندیم و دور بعد را با همان موجودی باز می‌کنیم
            lottery_round.is_active = False
            lottery_round.end_date = timezone.now()
            lottery_round.save()
            
            LotteryRound.objects.create(
                round_number=lottery_round.round_number + 1,
                start_date=timezone.now(),
                jackpot_carry_over=lottery_round.total_pot, # انتقال کل پول
                total_pot=lottery_round.total_pot,
                is_active=True
            )
            return None

        # 1. انتخاب برنده تصادفی
        # نکته: برای عدالت بیشتر از random دیتابیس استفاده می‌کنیم
        winning_ticket = LotteryTicket.objects.filter(lottery_round=lottery_round).order_by('?').first()
        winner_user = winning_ticket.user

        # 2. محاسبه جایزه (50 درصد برنده، 50 درصد دور بعد)
        total_pot = lottery_round.total_pot
        winner_prize = total_pot / Decimal(2)
        carry_over = total_pot - winner_prize

        # 3. واریز جایزه به کاربر
        winner_user.cash_balance += winner_prize
        winner_user.save()

        # 4. ثبت تراکنش واریز
        Transaction.objects.create(
            user=winner_user,
            amount=winner_prize,
            transaction_type='lottery_win',
            description=f"Won Lottery Round {lottery_round.round_number}",
            reference=f"LOTTERY_WIN_{lottery_round.id}"
        )

        # 5. ثبت رکورد برنده
        LotteryWinner.objects.create(
            lottery_round=lottery_round,
            user=winner_user,
            ticket=winning_ticket,
            prize_amount=winner_prize
        )

        # 6. پایان دور فعلی
        lottery_round.is_active = False
        lottery_round.end_date = timezone.now()
        lottery_round.save()

        # 7. ایجاد دور جدید با موجودی منتقل شده
        LotteryRound.objects.create(
            round_number=lottery_round.round_number + 1,
            start_date=timezone.now(),
            jackpot_carry_over=carry_over,
            total_pot=carry_over, # شروع با پول دور قبل
            is_active=True
        )

        return winner_user
