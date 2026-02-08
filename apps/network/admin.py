from django.contrib import admin
from .models import NetworkLevel

@admin.register(NetworkLevel)
class NetworkLevelAdmin(admin.ModelAdmin):
    list_display = ('level_number', 'commission_percentage', 'required_personal_investment')
    ordering = ('level_number',)
