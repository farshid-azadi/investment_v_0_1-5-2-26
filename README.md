# 💰 Investment MLM Platform

سیستم مدیریت سرمایه‌گذاری چند سطحی (MLM) با قابلیت‌های پیشرفته Binary Tree، ROI خودکار و Anti-Ponzi Protection.

---

## 🌟 **ویژگی‌های کلیدی**

### **۱. سیستم درآمدزایی چندگانه**
- ✅ **ROI روزانه خودکار**: محاسبه و پرداخت سود روزانه بر اساس پلن‌های سرمایه‌گذاری
- ✅ **کمیسیون باینری**: درآمد از تعادل تیم چپ و راست (با الگوریتم Flush)
- ✅ **کمیسیون سطحی (Level)**: پورسانت از معرفی‌های مستقیم و غیرمستقیم
- ✅ **سود مرکب خودکار**: امکان تجمیع خودکار سود به اصل سرمایه

### **۲. Anti-Ponzi Protection** 🛡️
- محدودیت درآمد روزانه (۳۰٪ اصل سرمایه)
- سقف کل درآمد (۲۰۰٪ اصل سرمایه)
- غیرفعال‌سازی خودکار پلن‌های منقضی شده
- قطع درآمد برای کاربران بدون پلن فعال

### **۳. Binary Tree System** 🌳
- جایگاه‌یابی خودکار در درخت (الگوریتم BFS)
- تسویه‌حساب هوشمند حجم‌ها (Volume Flush)
- نمایش گرافیکی درخت تا ۳ سطح در Admin
- محاسبه Real-time آمار درآمد هر نود

### **۴. Scheduled Tasks با Django-Q2**
- اجرای خودکار ROI روزانه (۰۰:۰۵ صبح)
- Flush حجم‌های باینری (۰۰:۱۰ صبح)
- Worker Pool قابل تنظیم برای پردازش موازی
- لاگ‌گذاری کامل تمام فرآیندها

---

## 🛠️ **نصب و راه‌اندازی**

### **پیش‌نیازها**
```bash
Python 3.11+
MySQL 8.0+
Redis 7.0+

### **۱. کلون کردن پروژه**
bash
git clone <repository-url>
cd invest-10-05-04-week-day

### **۲. ایجاد محیط مجازی**
bash
python -m venv venv

# لینوکس/مک:
source venv/bin/activate

# ویندوز:
venv\Scripts\activate

### **۳. نصب پکیج‌ها**
bash
pip install -r requirements.txt

**لیست پکیج‌های اصلی:**
txt
Django==5.1.4
django-q2==1.7.4
mysqlclient==2.2.6
redis==5.2.1
celery==5.4.0
django-cors-headers==4.6.0
djangorestframework==3.15.2

### **۴. تنظیم دیتابیس MySQL**
sql
CREATE DATABASE investment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'invest_user'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON investment_db.* TO 'invest_user'@'localhost';
FLUSH PRIVILEGES;

### **۵. پیکربندی فایل `.env`**
env
DEBUG=True
SECRET_KEY='django-insecure-CHANGE-THIS-IN-PRODUCTION'
ALLOWED_HOSTS=*

# Database
DB_NAME=investment_db
DB_USER=invest_user
DB_PASSWORD=YOUR_SECURE_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Redis (برای Django-Q2)
REDIS_URL=redis://127.0.0.1:6379/1

### **۶. مایگریشن و ایجاد Superuser**
bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

### **۷. راه‌اندازی Redis**
bash
# لینوکس/مک:
redis-server

# ویندوز (با WSL):
sudo service redis-server start

### **۸. اجرای سرور توسعه**
bash
# ترمینال ۱: Django Server
python manage.py runserver

# ترمینال ۲: Django-Q2 Worker
python manage.py qcluster

🎉 **پروژه آماده است!**  
Admin Panel: `http://127.0.0.1:8000/admin/`

---

## ⚙️ **تنظیمات Scheduled Tasks**

### **روش ۱: Django-Q2 Scheduler (توصیه شده برای Production)**

تسک‌ها به صورت خودکار از طریق **Django Admin** برنامه‌ریزی شده‌اند. برای بررسی:


Admin Panel → Django Q → Scheduled Tasks

**تسک‌های پیش‌فرض:**

| تسک | زمان اجرا | توضیح |
|-----|----------|-------|
| `process_all_daily_roi` | روزانه ۰۰:۰۵ | پرداخت سود روزانه به تمام سرمایه‌گذاری‌های فعال |
| `process_all_binary_flush` | روزانه ۰۰:۱۰ | تسویه حجم‌های باینری و پرداخت کمیسیون |

**نحوه فعال‌سازی:**
bash
# در Production، QCluster باید به عنوان سرویس اجرا شود
python manage.py qcluster

### **روش ۲: Cron Jobs (جایگزین برای سرورهای لینوکس)**

اگر ترجیح می‌دهید از Cron استفاده کنید:

bash
crontab -e

افزودن این خطوط:
cron
# ROI روزانه ساعت ۰۰:۰۵
5 0 * * * cd /path/to/project && /path/to/venv/bin/python manage.py shell -c "from apps.accounts.tasks import process_all_daily_roi; process_all_daily_roi()"

# Binary Flush ساعت ۰۰:۱۰
10 0 * * * cd /path/to/project && /path/to/venv/bin/python manage.py shell -c "from apps.accounts.tasks import process_all_binary_flush; process_all_binary_flush()"

---

## 📊 **Architecture - معماری سیستم**

### **ساختار اپلیکیشن‌ها**


invest-10-05-04-week-day/
├── apps/
│   ├── accounts/           # مدیریت کاربران و شبکه
│   │   ├── services/
│   │   │   ├── binary_engine.py    # موتور محاسبات Binary
│   │   │   ├── plan_service.py     # سرویس مدیریت پلن‌ها
│   │   │   └── roi_service.py      # محاسبه ROI
│   │   ├── tasks.py               # Scheduled Tasks
│   │   └── models.py              # مدل‌های User, Binary, ROI
│   │
│   ├── investments/        # مدیریت سرمایه‌گذاری‌ها
│   │   ├── models.py      # InvestmentPlan, UserInvestment
│   │   └── views.py       # خرید پلن
│   │
│   ├── core/              # تنظیمات و مدل‌های مشترک
│   │   └── models.py      # MLMSettings, Transaction
│   │
│   └── wallet/            # سیستم کیف پول
│       └── models.py      # Wallet, Deposit, Withdraw
│
├── config/                # تنظیمات Django
│   ├── settings.py
│   └── urls.py
│
└── requirements.txt

---

## 🔍 **راهنمای Admin Panel**

### **۱. مدیریت کاربران**

Admin → Accounts → Users

**قابلیت‌ها:**
- ✅ مشاهده درخت باینری هر کاربر (دکمه 🌳 مشاهده درخت)
- ✅ بررسی Volume های چپ و راست
- ✅ تولید دستی کد رفرال (Action → تولید دستی کد)
- ✅ مشاهده موجودی نقد و سرمایه‌گذاری مجدد

### **۲. گزارش کمیسیون‌ها**

**Binary Commissions:**

Admin → Accounts → Binary Commissions
- مبلغ پرداخت شده
- مبلغ سوخت شده (Flushed)
- حجم Match شده

**Level Commissions:**

Admin → Accounts → Level Commission History
- فیلتر بر اساس سطح (Level 1-3)
- جستجو بر اساس کاربر

**ROI History:**

Admin → Accounts → ROI History
- تاریخچه سودهای روزانه
- درصد و مبلغ پرداختی

### **۳. Scheduled Tasks**

Admin → Django Q → Scheduled Tasks

**نکات مهم:**
- ✅ Status باید `Scheduled` باشه
- ✅ Next Run نشان‌دهنده زمان اجرای بعدی
- ✅ در صورت خطا، Last Run رنگ قرمز می‌شه

---

## 🧪 **تست دستی سیستم**

### **تست ROI:**
python
# Django Shell
from apps.accounts.tasks import process_all_daily_roi
process_all_daily_roi()

**بررسی نتیجه:**
python
from apps.core.models import Transaction
Transaction.objects.filter(transaction_type='roi').latest('created_at')

### **تست Binary Flush:**
python
from apps.accounts.tasks import process_all_binary_flush
process_all_binary_flush()

**بررسی Volume ها:**
python
from apps.accounts.models import User
user = User.objects.get(username='testuser')
print(f"Left: {user.left_volume}, Right: {user.right_volume}")
# باید صفر شده باشن

---

## 🐛 **رفع مشکلات رایج (Troubleshooting)**

### **مشکل ۱: QCluster اجرا نمی‌شه**
bash
# چک کردن Redis
redis-cli ping
# باید جواب PONG بده

# بررسی لاگ Django-Q2
python manage.py qcluster --verbose

### **مشکل ۲: تسک‌ها اجرا نمی‌شن**
python
# بررسی Scheduled Tasks در Admin
# مطمئن شوید:
# - Schedule Type = Cron
# - Cron Expression صحیح است
# - Enabled = True

### **مشکل ۳: خطای Import در Tasks**
python
# مطمئن شوید تمام مدل‌ها در داخل تابع Import شدن
def task_example():
from apps.accounts.models import User  # ✅ داخل تابع
# نه در بالای فایل

---

## 📈 **استقرار در Production (Deployment)**

### **۱. تنظیمات امنیتی**
python
# settings.py
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

### **۲. راه‌اندازی QCluster به عنوان سرویس**

**ایجاد فایل Systemd:**
bash
sudo nano /etc/systemd/system/django-qcluster.service

**محتوا:**
ini
[Unit]
Description=Django-Q2 Cluster
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python manage.py qcluster
Restart=always

[Install]
WantedBy=multi-user.target

**فعال‌سازی:**
bash
sudo systemctl enable django-qcluster
sudo systemctl start django-qcluster
sudo systemctl status django-qcluster

### **۳. استفاده از Supervisor (جایگزین)**
bash
sudo apt install supervisor

فایل کانفیگ:
ini
[program:qcluster]
command=/path/to/venv/bin/python /path/to/project/manage.py qcluster
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

---

## 📞 **پشتیبانی و مستندات**

- 📧 **ایمیل**: support@yourcompany.com
- 📚 **مستندات کامل**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 🐛 **گزارش باگ**: [GitHub Issues](#)

---

## 📜 **لایسنس**

This project is proprietary and confidential.

---

## 🙏 **قدردانی**

Built with ❤️ using:
- Django 5.1
- Django-Q2
- MySQL
- Redis

---

**نسخه**: 1.0.0  
**آخرین بروزرسانی**: 1404/10/14


---

## ✅ **این README شامل چیه؟**

1. ✅ **معرفی کامل** ویژگی‌ها
2. ✅ **راهنمای نصب** قدم به قدم
3. ✅ **تنظیمات Cron/Scheduler** 
4. ✅ **Architecture** کامل
5. ✅ **راهنمای Admin Panel**
6. ✅ **تست دستی**
7. ✅ **Troubleshooting**
8. ✅ **راهنمای Deployment**

---

**حالا بگو این فایل رو کجا Save کنم؟** 
می‌خوای بریم سراغ **ARCHITECTURE.md** هم یا همین README کافیه؟ 🚀📝