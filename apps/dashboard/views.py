# apps/dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from decimal import Decimal

from apps.investments.models import InvestmentPlan, UserInvestment
from apps.accounts.models import PaymentRequest, User
from apps.wallet.models import Transaction


@login_required
def dashboard_view(request):
    """صفحه اصلی داشبورد"""
    user = request.user
    
    # آمار کلی
    total_investments = UserInvestment.objects.filter(user=user).count()
    
    # ✅ استفاده از status به جای is_active
    active_investments = UserInvestment.objects.filter(
        user=user, 
        status='ACTIVE'
    ).count()
    
    # ✅ استفاده از wallet__user به جای user مستقیم
    recent_transactions = Transaction.objects.filter(
        wallet__user=user
    ).order_by('-created_at')[:10]
    
    context = {
        'total_investments': total_investments,
        'active_investments': active_investments,
        'recent_transactions': recent_transactions,
    }
    
    # ✅ اصلاح: استفاده از home.html به جای dashboard.html
    return render(request, 'dashboard/home.html', context)


@login_required
def plans_view(request):
    """نمایش لیست پلن‌های سرمایه‌گذاری"""
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('min_amount')
    
    context = {
        'plans': plans,
        'user': request.user,
    }
    
    return render(request, 'dashboard/plans.html', context)


@login_required
def buy_plan_view(request):
    """خرید پلن سرمایه‌گذاری"""
    
    if request.method != 'POST':
        return redirect('dashboard:plans')
    
    try:
        plan_id = request.POST.get('plan_id')
        amount = Decimal(request.POST.get('amount', '0'))
        wallet_source = request.POST.get('wallet_source', 'cash')
        
        # پیدا کردن پلن
        plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
        
        # بررسی محدوده مبلغ
        if amount < plan.min_amount or amount > plan.max_amount:
            messages.error(
                request, 
                f'❌ مبلغ باید بین ${plan.min_amount} تا ${plan.max_amount} باشد'
            )
            return redirect('dashboard:plans')
        
        # بررسی موجودی
        user = request.user
        
        if wallet_source == 'cash':
            if user.cash_balance < amount:
                messages.error(
                    request,
                    f'❌ موجودی کافی نیست. موجودی فعلی: ${user.cash_balance}'
                )
                return redirect('dashboard:plans')
        elif wallet_source == 'reinvest':
            if user.reinvest_balance < amount:
                messages.error(
                    request,
                    f'❌ موجودی سرمایه‌گذاری مجدد کافی نیست. موجودی فعلی: ${user.reinvest_balance}'
                )
                return redirect('dashboard:plans')
        else:
            messages.error(request, '❌ منبع کیف پول نامعتبر است')
            return redirect('dashboard:plans')
        
        # ایجاد PaymentRequest با تایید خودکار
        payment = PaymentRequest.objects.create(
            user=user,
            plan=plan,
            amount=amount,
            payment_method='internal_wallet',
            wallet_source=wallet_source,
            status='approved'
        )
        
        # کسر موجودی
        if wallet_source == 'cash':
            user.cash_balance -= amount
        else:
            user.reinvest_balance -= amount
        
        user.save(update_fields=[f'{wallet_source}_balance'])
        
        messages.success(
            request,
            f'✅ سرمایه‌گذاری ${amount} در پلن {plan.name} با موفقیت انجام شد!'
        )
        
        return redirect('dashboard:plans')
        
    except InvestmentPlan.DoesNotExist:
        messages.error(request, '❌ پلن سرمایه‌گذاری یافت نشد')
        return redirect('dashboard:plans')
    
    except Exception as e:
        messages.error(request, f'❌ خطا: {str(e)}')
        return redirect('dashboard:plans')


@login_required
def transactions_view(request):
    """لیست تراکنش‌ها"""
    # ✅ استفاده از wallet__user به جای user
    transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).order_by('-created_at')
    
    context = {
        'transactions': transactions,
    }
    
    return render(request, 'dashboard/transactions.html', context)


@login_required
def network_view(request):
    """نمایش درخت باینری"""
    user_id = request.GET.get('user_id')
    
    if user_id:
        try:
            root_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            root_user = request.user
    else:
        root_user = request.user
    
    # لایه 2
    l2_left = root_user.binary_left.first() if hasattr(root_user, 'binary_left') else None
    l2_right = root_user.binary_right.first() if hasattr(root_user, 'binary_right') else None
    
    # لایه 3
    l3_ll = l2_left.binary_left.first() if l2_left and hasattr(l2_left, 'binary_left') else None
    l3_lr = l2_left.binary_right.first() if l2_left and hasattr(l2_left, 'binary_right') else None
    l3_rl = l2_right.binary_left.first() if l2_right and hasattr(l2_right, 'binary_left') else None
    l3_rr = l2_right.binary_right.first() if l2_right and hasattr(l2_right, 'binary_right') else None
    
    context = {
        'root_user': root_user,
        'l2_left': l2_left,
        'l2_right': l2_right,
        'l3_ll': l3_ll,
        'l3_lr': l3_lr,
        'l3_rl': l3_rl,
        'l3_rr': l3_rr,
    }
    
    return render(request, 'dashboard/binary_tree.html', context)


@login_required
def my_team_view(request):
    """لیست اعضای تیم"""
    # زیرمجموعه‌های مستقیم
    directs = User.objects.filter(referrer=request.user)
    
    context = {
        'directs': directs,
    }
    
    return render(request, 'dashboard/team.html', context)


@login_required
def profile_view(request):
    """پروفایل کاربر"""
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'dashboard/profile.html', context)


def logout_view(request):
    """خروج از سیستم"""
    logout(request)
    messages.success(request, '✅ با موفقیت خارج شدید')
    return redirect('accounts:login')
