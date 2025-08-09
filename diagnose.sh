#!/bin/bash

# سكريبت التشخيص السريع
# Quick Diagnostic Script

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

echo "=============================================="
echo "     تشخيص سريع لنظام الرسائل المصرفية"
echo "=============================================="
echo ""

# فحص حالة الخدمات الأساسية
echo "1. فحص حالة الخدمات:"
echo "------------------------"

services=("gunicorn" "celery" "celerybeat" "nginx" "postgresql" "redis-server")
failed_services=()

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        print_status "$service متاح"
    else
        print_error "$service متوقف أو غير مثبت"
        failed_services+=("$service")
    fi
done

echo ""

# فحص المنافذ
echo "2. فحص المنافذ:"
echo "---------------"

ports=("8000:Gunicorn" "80:Nginx" "5432:PostgreSQL" "6379:Redis")
for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    service_name=$(echo $port_info | cut -d: -f2)
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        print_status "المنفذ $port ($service_name) مفتوح"
    else
        print_error "المنفذ $port ($service_name) مغلق"
    fi
done

echo ""

# فحص العمليات
echo "3. فحص العمليات النشطة:"
echo "------------------------"

processes=("gunicorn" "celery" "nginx" "postgres" "redis")
for process in "${processes[@]}"; do
    if pgrep -f $process > /dev/null 2>&1; then
        count=$(pgrep -f $process | wc -l)
        print_status "$process يعمل ($count عملية)"
    else
        print_error "$process لا يعمل"
    fi
done

echo ""

# فحص الاتصال بقاعدة البيانات
echo "4. فحص قاعدة البيانات:"
echo "---------------------"

if command -v psql > /dev/null 2>&1; then
    if sudo -u postgres psql -d banking_system -c "SELECT 1;" > /dev/null 2>&1; then
        print_status "قاعدة البيانات banking_system متاحة"
    elif sudo -u postgres psql -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
        print_warning "PostgreSQL يعمل لكن قاعدة البيانات banking_system غير موجودة"
    else
        print_error "لا يمكن الاتصال بـ PostgreSQL"
    fi
else
    print_error "PostgreSQL غير مثبت"
fi

echo ""

# فحص Redis
echo "5. فحص Redis:"
echo "-------------"

if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli ping > /dev/null 2>&1; then
        print_status "Redis يعمل بشكل صحيح"
    else
        print_error "Redis لا يستجيب"
    fi
else
    print_error "Redis غير مثبت"
fi

echo ""

# فحص الاتصال بالتطبيق
echo "6. فحص التطبيق:"
echo "---------------"

if command -v curl > /dev/null 2>&1; then
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "التطبيق يستجيب على المنفذ 8000"
    else
        print_error "التطبيق لا يستجيب على المنفذ 8000"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "Nginx يستجيب على المنفذ 80"
    else
        print_error "Nginx لا يستجيب على المنفذ 80"
    fi
else
    print_warning "curl غير مثبت - لا يمكن فحص الاتصال"
fi

echo ""

# فحص السجلات الأخيرة للأخطاء
echo "7. آخر الأخطاء في السجلات:"
echo "----------------------------"

if [ ${#failed_services[@]} -gt 0 ]; then
    echo "الخدمات المتوقفة: ${failed_services[*]}"
    echo ""
    
    for service in "${failed_services[@]}"; do
        echo "--- آخر أخطاء $service ---"
        if systemctl list-units --type=service | grep -q "^$service.service"; then
            sudo journalctl -u $service --no-pager -n 5 --since "1 hour ago" 2>/dev/null || echo "لا توجد سجلات متاحة"
        else
            echo "الخدمة غير مثبتة أو غير موجودة"
        fi
        echo ""
    done
fi

# فحص مساحة القرص
echo "8. معلومات النظام:"
echo "------------------"

echo "مساحة القرص:"
df -h / | awk 'NR==2{printf "المستخدم: %s من %s (%s)\n", $3, $2, $5}'

echo "الذاكرة:"
free -h | awk 'NR==2{printf "المستخدم: %s من %s\n", $3, $2}'

echo "الحمولة على النظام:"
uptime | awk '{print "متوسط الحمولة: " $(NF-2) " " $(NF-1) " " $NF}'

echo ""

# التوصيات
echo "=============================================="
echo "              التوصيات والحلول"
echo "=============================================="

if [ ${#failed_services[@]} -gt 0 ]; then
    echo "🔧 الخدمات المتوقفة التي تحتاج إعادة تشغيل:"
    for service in "${failed_services[@]}"; do
        echo "   sudo systemctl start $service"
        echo "   sudo systemctl enable $service"
    done
    echo ""
fi

echo "📋 أوامر مفيدة لحل المشاكل:"
echo "   sudo systemctl restart gunicorn celery nginx"
echo "   sudo journalctl -u gunicorn -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo "   ./ubuntu_maintenance.sh health"
echo ""

echo "📊 لعرض حالة مفصلة:"
echo "   ./ubuntu_maintenance.sh status"
echo "   ./ubuntu_maintenance.sh logs"

echo ""
echo "=============================================="