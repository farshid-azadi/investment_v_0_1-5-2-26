from django.db import models
from django.utils.translation import gettext_lazy as _

class NetworkLevel(models.Model):
    level_number = models.PositiveIntegerField(unique=True, verbose_name=_("Level Number"))
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Commission (%)"))
    
    # شرط اختیاری: برای باز شدن این سطح، کاربر باید خودش چقدر سرمایه داشته باشد؟
    required_personal_investment = models.DecimalField(default=0, max_digits=20, decimal_places=2, verbose_name=_("Required Investment (USDT)"))

    class Meta:
        ordering = ['level_number']
        verbose_name = _("Network Level")
        verbose_name_plural = _("Network Levels (MLM)")

    def __str__(self):
        return f"Level {self.level_number} - {self.commission_percentage}%"
