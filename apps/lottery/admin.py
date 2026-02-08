# apps/lottery/admin.py

from django.contrib import admin
from .models import LotterySetting, LotteryRound, LotteryTicket, LotteryWinner

@admin.register(LotterySetting)
class LotterySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_price', 'jackpot_percentage', 'updated_at')
    list_editable = ('ticket_price', 'jackpot_percentage')
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

class LotteryTicketInline(admin.TabularInline):
    model = LotteryTicket
    extra = 0
    readonly_fields = ('user', 'purchased_at', 'ticket_price', 'is_winner')
    can_delete = False
    ordering = ('-purchased_at',)

@admin.register(LotteryRound)
class LotteryRoundAdmin(admin.ModelAdmin):
    list_display = ('round_number', 'is_active', 'total_pot', 'participants_count', 'start_date')
    list_filter = ('is_active',)
    readonly_fields = ('participants_count', 'total_pot')
    inlines = [LotteryTicketInline]

@admin.register(LotteryTicket)
class LotteryTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'lottery_round', 'ticket_price', 'is_winner', 'purchased_at')
    list_filter = ('is_winner', 'lottery_round')
    readonly_fields = ('user', 'lottery_round', 'ticket_price', 'purchased_at')

@admin.register(LotteryWinner)
class LotteryWinnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'lottery_round', 'prize_amount', 'won_at')
