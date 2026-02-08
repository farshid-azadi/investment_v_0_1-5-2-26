# apps/lottery/models.py

from django.db import models
from django.conf import settings

class LotterySetting(models.Model):
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    jackpot_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Lottery Settings"

class LotteryRound(models.Model):
    round_number = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    jackpot_carry_over = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pot = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    participants_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Round {self.round_number}"

class LotteryTicket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lottery_tickets')
    lottery_round = models.ForeignKey(LotteryRound, on_delete=models.CASCADE, related_name='tickets')
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_winner = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket {self.id}"

class LotteryWinner(models.Model):
    lottery_round = models.ForeignKey(LotteryRound, on_delete=models.CASCADE, related_name='winners')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket = models.OneToOneField(LotteryTicket, on_delete=models.CASCADE)
    prize_amount = models.DecimalField(max_digits=20, decimal_places=2)
    won_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Winner {self.user.username}"
