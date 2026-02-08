#!/bin/bash

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🔧 رفع مشکل نصب خراب Django                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

# بررسی venv
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${RED}❌ venv فعال نیست!${NC}"
    echo -e "${YELLOW}لطفاً ابتدا venv را فعال کنید:${NC}"
    echo -e "  source venv/bin/activate"
    exit 1
fi

echo -e "\n${GREEN}✓${NC} venv فعال است"

# گام 1: حذف کامل Django
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 گام 1: حذف کامل Django${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

pip uninstall -y django
pip cache purge

# گام 2: حذف فایل‌های باقی‌مانده Django
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🗑️  گام 2: حذف فایل‌های باقی‌مانده${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
echo "مسیر site-packages: $SITE_PACKAGES"

if [ -d "$SITE_PACKAGES/django" ]; then
    echo "حذف پوشه django..."
    rm -rf "$SITE_PACKAGES/django"
fi

if [ -d "$SITE_PACKAGES/Django-"* ]; then
    echo "حذف پوشه‌های Django-*..."
    rm -rf "$SITE_PACKAGES"/Django-*
fi

# گام 3: نصب مجدد Django از صفر
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📥 گام 3: نصب مجدد Django 4.2.7${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

pip install --no-cache-dir --force-reinstall Django==4.2.7

# گام 4: تست نصب
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 گام 4: تست نصب جدید${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "تست 1: نسخه Django"
python -c "import django; print(f'✓ Django {django.get_version()} نصب شد')"

echo -e "\nتست 2: ماژول migrations"
if python -c "from django.db.migrations.migration import Migration" 2>/dev/null; then
    echo -e "${GREEN}✓ ماژول migrations سالم است${NC}"
    MIGRATIONS_OK=1
else
    echo -e "${RED}✗ ماژول migrations همچنان مشکل دارد${NC}"
    MIGRATIONS_OK=0
fi

# گام 5: نصب مجدد وابستگی‌های مرتبط
if [ $MIGRATIONS_OK -eq 1 ]; then
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📚 گام 5: نصب مجدد وابستگی‌های Django${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    pip install --no-cache-dir --force-reinstall \
        djangorestframework==3.14.0 \
        django-cors-headers==4.3.0 \
        django-filter==23.3 \
        django-jalali-date==1.0.2
    
    echo -e "\n${GREEN}✓ وابستگی‌ها نصب شدند${NC}"
fi

# گام 6: پاکسازی پروژه
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧹 گام 6: پاکسازی کش پروژه${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

echo -e "${GREEN}✓ کش پاک شد${NC}"

# گام 7: بررسی نهایی
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}✅ گام 7: بررسی نهایی پروژه${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $MIGRATIONS_OK -eq 1 ]; then
    python manage.py check
    CHECK_STATUS=$?
    
    if [ $CHECK_STATUS -eq 0 ]; then
        echo -e "\n${GREEN}╔════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║   ✅ همه چیز آماده است!                         ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
        
        echo -e "\n${BLUE}مراحل بعدی:${NC}"
        echo -e "  ${YELLOW}1️⃣${NC}  حذف migrations قدیمی:"
        echo -e "      find . -path \"*/migrations/*.py\" -not -name \"__init__.py\" -delete"
        echo -e "\n  ${YELLOW}2️⃣${NC}  ساخت migrations جدید:"
        echo -e "      python manage.py makemigrations"
        echo -e "\n  ${YELLOW}3️⃣${NC}  اعمال migrations:"
        echo -e "      python manage.py migrate"
    else
        echo -e "\n${RED}❌ هنوز مشکل وجود دارد${NC}"
        echo -e "${YELLOW}لطفاً خروجی بالا را بررسی کنید${NC}"
    fi
else
    echo -e "\n${RED}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ نصب Django ناموفق بود                      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${YELLOW}راه‌حل‌های جایگزین:${NC}"
    echo -e "  ${BLUE}1.${NC} حذف کامل venv و ساخت مجدد:"
    echo -e "      deactivate"
    echo -e "      rm -rf venv"
    echo -e "      python3 -m venv venv"
    echo -e "      source venv/bin/activate"
    echo -e "      pip install -r requirements.txt"
    
    echo -e "\n  ${BLUE}2.${NC} استفاده از Python نسخه دیگر:"
    echo -e "      python3.10 -m venv venv"
fi
