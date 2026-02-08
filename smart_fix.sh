#!/bin/bash

# رنگ‌ها برای خروجی بهتر
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🔍 تشخیص هوشمند و رفع مشکل Django           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# ═══════════════════════════════════════════════════
# بررسی venv
# ═══════════════════════════════════════════════════
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ خطا: venv فعال نیست!${NC}"
    echo -e "${YELLOW}لطفاً ابتدا venv را فعال کنید:${NC}"
    echo -e "  ${GREEN}source venv/bin/activate${NC}"
    exit 1
fi

echo -e "${GREEN}✓ venv فعال است${NC}"
echo -e "  مسیر: ${CYAN}$VIRTUAL_ENV${NC}"
echo ""

# ═══════════════════════════════════════════════════
# بررسی نسخه Django نصب شده
# ═══════════════════════════════════════════════════
echo -e "${YELLOW}📦 بررسی نسخه Django نصب شده...${NC}"

DJANGO_VERSION=$(pip show django 2>/dev/null | grep Version | cut -d ' ' -f 2)

if [ -z "$DJANGO_VERSION" ]; then
    echo -e "${RED}❌ Django نصب نشده!${NC}"
    exit 1
fi

echo -e "  نسخه فعلی: ${RED}$DJANGO_VERSION${NC}"
echo ""

# ═══════════════════════════════════════════════════
# تست ماژول migrations
# ═══════════════════════════════════════════════════
echo -e "${YELLOW}🔬 تست ماژول migrations...${NC}"

MIGRATION_TEST=$(python3 << 'PYEOF'
import sys
try:
    from django.db.migrations.migration import Migration
    print("OK")
    sys.exit(0)
except ModuleNotFoundError as e:
    print(f"ERROR: {e}")
    sys.exit(1)
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYEOF
)

if [[ $MIGRATION_TEST == OK ]]; then
    echo -e "${GREEN}✓ ماژول migrations سالم است${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ Django به درستی نصب شده است!             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}مشکل احتمالاً در migration های قدیمی است.${NC}"
    echo ""
    
    # پیشنهاد حذف migration ها
    read -p "$(echo -e ${YELLOW}آیا می‌خواهید migration های قدیمی را حذف کنید؟ [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  حذف migration های قدیمی...${NC}"
        find . -path "*/migrations/*.py" -not -name "__init__.py" -delete 2>/dev/null
        find . -path "*/migrations/*.pyc" -delete 2>/dev/null
        echo -e "${GREEN}✓ migration ها حذف شدند${NC}"
        echo ""
        echo -e "${CYAN}حالا می‌توانید:${NC}"
        echo -e "  1. ${GREEN}python manage.py makemigrations${NC}"
        echo -e "  2. ${GREEN}python manage.py migrate${NC}"
    fi
    exit 0
fi

# اگر ماژول مشکل داشت
echo -e "${RED}✗ مشکل در ماژول migrations:${NC}"
echo -e "  ${MIGRATION_TEST}"
echo ""

# بررسی نسخه Django
MAJOR_VERSION=$(echo $DJANGO_VERSION | cut -d '.' -f 1)
MINOR_VERSION=$(echo $DJANGO_VERSION | cut -d '.' -f 2)

if [ "$MAJOR_VERSION" -ge 5 ]; then
    echo -e "${RED}⚠️  شما Django $DJANGO_VERSION نصب کرده‌اید${NC}"
    echo -e "${YELLOW}پروژه شما برای Django 4.2.7 طراحی شده است${NC}"
    echo ""
    
    # پیشنهاد نصب مجدد
    read -p "$(echo -e ${YELLOW}آیا می‌خواهید Django 4.2.7 را نصب کنید؟ [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}📥 در حال نصب Django 4.2.7...${NC}"
        pip uninstall -y django
        pip install Django==4.2.7
        
        echo ""
        echo -e "${GREEN}✓ Django 4.2.7 نصب شد${NC}"
        
        # تست مجدد
        echo -e "${YELLOW}🔬 تست مجدد...${NC}"
        MIGRATION_TEST2=$(python3 << 'PYEOF'
import sys
try:
    from django.db.migrations.migration import Migration
    import django
    print(f"OK - Django {django.VERSION}")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYEOF
)
        
        if [[ $MIGRATION_TEST2 == OK* ]]; then
            echo -e "${GREEN}✓ مشکل حل شد!${NC}"
            echo -e "  ${MIGRATION_TEST2}"
            echo ""
            echo -e "${CYAN}مراحل بعدی:${NC}"
            echo -e "  1. حذف migration های قدیمی"
            echo -e "  2. ${GREEN}python manage.py makemigrations${NC}"
            echo -e "  3. ${GREEN}python manage.py migrate${NC}"
            echo ""
            
            # پیشنهاد حذف migration ها
            read -p "$(echo -e ${YELLOW}آیا می‌خواهید migration های قدیمی را الان حذف کنید؟ [y/N]: ${NC})" -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}🗑️  حذف migration ها...${NC}"
                find . -path "*/migrations/*.py" -not -name "__init__.py" -delete 2>/dev/null
                find . -path "*/migrations/*.pyc" -delete 2>/dev/null
                echo -e "${GREEN}✓ انجام شد${NC}"
            fi
        else
            echo -e "${RED}✗ هنوز مشکل وجود دارد:${NC}"
            echo -e "  ${MIGRATION_TEST2}"
        fi
    fi
else
    echo -e "${YELLOW}نسخه Django شما $DJANGO_VERSION است${NC}"
    echo -e "${YELLOW}احتمالاً مشکل در جای دیگری است${NC}"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   اسکریپت تشخیص به پایان رسید                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
