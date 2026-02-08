# apps/accounts/views.py

from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe

# Models Imports
from .models import LevelCommissionHistory
from .forms import UserRegisterForm

# API Imports (DRF)
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

# ==========================================
#  MODEL IMPORTS (Safe Loading)
# ==========================================
Transaction = None
Plan = None

try:
    from apps.wallet.models import Transaction
    from apps.investments.models import InvestmentPlan as Plan 
except ImportError:
    try:
        from apps.wallet.models import Transaction
    except ImportError:
        pass 

# تلاش برای ایمپورت سرویس‌ها (اختیاری)
try:
    from apps.accounts.services.plan_service import purchase_plan
except ImportError:
    purchase_plan = None


# ==========================================
#  PART 1: API VIEWS (Rest Framework)
# ==========================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class PurchasePlanView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        if not purchase_plan:
             return Response({"error": "Service unavailable"}, status=503)

        plan_id = request.data.get("plan_id")
        try:
            if not Plan or not hasattr(Plan, 'objects'):
                return Response({"error": "Plan system is currently unavailable."}, status=503)

            plan = Plan.objects.get(id=plan_id)
            purchase_plan(user=request.user, plan=plan)
            return Response({"detail": "Plan purchased successfully"})
        except Plan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


# ==========================================
#  PART 2: UI VIEWS (Frontend / Dashboard)
# ==========================================

def register_view(request):
    """
    نمایش و پردازش فرم ثبت‌نام کاربر
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    initial_data = {}
    ref_param = request.GET.get('ref')
    if ref_param:
        initial_data['referral_code'] = ref_param

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])

            # لاجیک معرف
            ref_code = form.cleaned_data.get('referral_code')
            if ref_code:
                try:
                    referrer = User.objects.get(referral_code=ref_code)
                    user.referrer = referrer
                except User.DoesNotExist:
                    messages.warning(request, "کد معرف یافت نشد. ثبت نام بدون معرف انجام شد.")

            user.save()
            # لاگین خودکار بعد از ثبت نام
            login(request, user)
            messages.success(request, "ثبت نام با موفقیت انجام شد. به داشبورد خوش آمدید.")
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, "لطفاً خطاهای فرم را بررسی کنید.")
    else:
        form = UserRegisterForm(initial=initial_data)

    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    """
    صفحه ورود
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "ورود موفقیت‌آمیز بود.")
            
            # بررسی پارامتر next برای ریدایرکت هوشمند
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, "نام کاربری یا رمز عبور اشتباه است.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    """خروج از سیستم"""
    logout(request)
    messages.info(request, "با موفقیت خارج شدید.")
    return redirect('accounts:login')

@login_required(login_url='accounts:login')
def dashboard_view(request):
    user = request.user
    
    # دریافت 5 تراکنش آخر (با بررسی ایمن وجود مدل)
    recent_transactions = []
    if Transaction and hasattr(Transaction, 'objects'):
        recent_transactions = Transaction.objects.filter(wallet__user=user).order_by('-created_at')[:5]

    context = {
        'user': user,
        'cash_balance': getattr(user, 'cash_balance', 0),
        'total_commission': getattr(user, 'total_commission_earned', 0),
        'left_volume': getattr(user, 'left_volume', 0),
        'right_volume': getattr(user, 'right_volume', 0),
        'recent_transactions': recent_transactions,
        'page_title': 'داشبورد'
    }
    return render(request, 'dashboard/home.html', context)

@login_required(login_url='accounts:login')
def transactions_view(request):
    """نمایش لیست کامل تراکنش‌ها"""
    transactions = []
    if Transaction and hasattr(Transaction, 'objects'):
        transactions = Transaction.objects.filter(wallet__user=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/transactions.html', {'transactions': transactions})

@login_required(login_url='accounts:login')
def my_team_view(request):
    """نمایش لیست زیرمجموعه‌های مستقیم"""
    referrals = User.objects.filter(referrer=request.user)
    return render(request, 'dashboard/team.html', {'referrals': referrals})

@login_required(login_url='accounts:login')
def plans_view(request):
    """نمایش پلن‌های سرمایه‌گذاری"""
    plans = []
    if Plan and hasattr(Plan, 'objects'):
        plans = Plan.objects.filter(is_active=True)
        
    return render(request, 'dashboard/plans.html', {'plans': plans})

@login_required(login_url='accounts:login')
def profile_view(request):
    """نمایش پروفایل کاربر"""
    return render(request, 'dashboard/profile.html', {'user': request.user})

@login_required(login_url='accounts:login')
def network_view(request):
    """
    ویوی پیش‌فرض برای دکمه 'network' در منو
    این ویو درخواست را به باینری تری هدایت می‌کند.
    """
    return binary_tree_view(request)


# ==============================================================================
# PART 3: Binary Tree Logic & Visualization (Frontend)
# ==============================================================================

@login_required
def binary_tree_view(request):
    # گرفتن آی‌دی کاربری که می‌خواهیم درختش را ببینیم از پارامتر URL
    target_user_id = request.GET.get('user_id')
    
    if target_user_id:
        current_node = get_object_or_404(User, pk=target_user_id)
        # امنیت: چک کنیم آیا این کاربر واقعاً در زیرمجموعه فرد لاگین شده هست یا خیر
        # (این بخش ساده است، برای پروژه‌های بزرگ نیاز به الگوریتم پیشرفته‌تری دارد)
        # در اینجا فعلاً اجازه می‌دهیم هر کسی را ببیند یا صرفاً محدود به خودش می‌کنیم
        # اگر می‌خواهید محدود کنید، باید منطق تراورس درخت را اینجا بنویسید.
    else:
        current_node = request.user

    # تابع کمکی برای گرفتن فرزندان
    def get_children(user_node):
        if not user_node:
            return None, None
        left = user_node.binary_children.filter(binary_position='left').first()
        right = user_node.binary_children.filter(binary_position='right').first()
        return left, right

    # سطح ۱: کاربر جاری
    l1_user = current_node
    
    # سطح ۲: فرزندان چپ و راست
    l2_left, l2_right = get_children(l1_user)

    # سطح ۳: نوه‌ها
    l3_ll, l3_lr = get_children(l2_left) # فرزندانِ فرزند چپ
    l3_rl, l3_rr = get_children(l2_right) # فرزندانِ فرزند راست

    context = {
        'root_user': l1_user,
        # داده‌های سطح ۲
        'l2_left': l2_left,
        'l2_right': l2_right,
        # داده‌های سطح ۳
        'l3_ll': l3_ll, # چپِ چپ
        'l3_lr': l3_lr, # راستِ چپ
        'l3_rl': l3_rl, # چپِ راست
        'l3_rr': l3_rr, # راستِ راست
    }
    
    return render(request, 'dashboard/binary_tree.html', context)

# ==============================================================================
# PART 4: Network Levels Report (Multi-Select Filter)
# ==============================================================================

@login_required
def network_levels_view(request):
    """
    نمایش لیست پورسانت‌های سطحی با قابلیت فیلتر چندگانه.
    """
    # دریافت لیست سطوح انتخاب شده از URL (مثلاً ?levels=1&levels=3)
    selected_levels_str = request.GET.getlist('levels')
    
    selected_levels = []
    for level in selected_levels_str:
        if level.isdigit():
            selected_levels.append(int(level))
            
    # کوئری پایه: دریافت تمام سوابق مربوط به کاربر جاری
    queryset = LevelCommissionHistory.objects.filter(earner=request.user).select_related('from_user')

    # اعمال فیلتر اگر کاربر سطوحی را انتخاب کرده باشد
    if selected_levels:
        queryset = queryset.filter(level__in=selected_levels)

    # مرتب‌سازی: جدیدترین‌ها اول
    queryset = queryset.order_by('-created_at')

    context = {
        'commission_history': queryset,
        'selected_levels': selected_levels, # برای تیک زدن مجدد چک‌باکس‌ها در قالب
        'available_levels': range(1, 11),   # فرض می‌کنیم سیستم ۱۰ سطحی است
    }
    
    return render(request, 'dashboard/network_levels.html', context)
