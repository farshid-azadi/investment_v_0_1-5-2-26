# apps/accounts/urls.py

from django.urls import path
from . import views

# وجود app_name برای استفاده از Namespace الزامی است
app_name = 'accounts'

urlpatterns = [
    # --- بخش احراز هویت (Authentication) ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- داشبورد اصلی ---
    # نام‌های مختلف برای اطمینان از دسترسی از طریق آدرس‌های متفاوت
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/home/', views.dashboard_view, name='home'),

    # --- بخش‌های عملیاتی (Plans & Network) ---
    path('plans/', views.plans_view, name='plans'),
    
    # اصلاح شده: نام تابع در views.py برابر با binary_tree_view است
    path('network/', views.binary_tree_view, name='network'),
    path('dashboard/network/', views.binary_tree_view, name='network_alt'),

    # --- بخش تراکنش‌ها (Transactions) ---
    # اصلاح مهم: نام URL باید 'transactions' باشد تا با درخواست قالب HTML شما همخوانی داشته باشد
    # اصلاح مهم: نام تابع در views.py برابر با transactions_view است
    path('transactions/', views.transactions_view, name='transactions'),

    # --- تیم من و پروفایل ---
    path('my-team/', views.my_team_view, name='my_team'),
    path('team/', views.my_team_view, name='team'),
    path('profile/', views.profile_view, name='profile'),

    # --- بخش API (برای اپلیکیشن یا فرانت‌اند جدا) ---
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    path('api/profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('api/purchase/', views.PurchasePlanView.as_view(), name='api_purchase'),
    path('network/tree/', views.binary_tree_view, name='network_tree'),
    path('network/tree/<str:username>/', views.binary_tree_view, name='network_tree_user'),
    
    # مسیر برای گزارش سطوح (فیلتر چندگانه)
    path('network/levels/', views.network_levels_view, name='network_levels'),
]
