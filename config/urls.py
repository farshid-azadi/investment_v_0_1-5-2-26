# #config/urls.py
# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     # خط زیر بسیار مهم است و باعث می‌شود جنگو مسیرهای API را بشناسد
#     path('accounts/', include('apps.accounts.urls')),
#     path('api/wallet/', include('apps.wallet.urls')),  
#     path('api/investments/', include('apps.investments.urls')),
#     path('api/lottery/', include('apps.lottery.urls')), 
#      path('dashboard/', include('apps.dashboard.urls')),
# #    path('accounts/', include('apps.accounts.urls')), 

# ]
 # config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect صفحه اصلی به Dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    
    # پنل ادمین
    path('admin/', admin.site.urls),
    
    # مسیرهای اپلیکیشن‌های مختلف
    path('accounts/', include('apps.accounts.urls')),
    path('api/wallet/', include('apps.wallet.urls')),  
    path('api/investments/', include('apps.investments.urls')),
    path('api/lottery/', include('apps.lottery.urls')), 
    path('dashboard/', include('apps.dashboard.urls')),
]

# تنظیمات برای محیط Development (DEBUG=True)
if settings.DEBUG:
    # مسیرهای فایل‌های Media (تصاویر آپلود شده توسط کاربران)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # مسیرهای فایل‌های Static (CSS, JS, Images)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
