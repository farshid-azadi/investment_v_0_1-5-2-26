# apps/dashboard/urls.py
from django.urls import path
from . import views

# ✅ اصلاح: تغییر app_name از 'admin_dashboard' به 'dashboard'
app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('plans/', views.plans_view, name='plans'),
    path('buy-plan/', views.buy_plan_view, name='buy_plan'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('network/', views.network_view, name='network'),
    path('my-team/', views.my_team_view, name='my_team'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
