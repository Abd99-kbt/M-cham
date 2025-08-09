#!/bin/bash

# سكريبت الصيانة للنشر التقليدي على Ubuntu
# Ubuntu Traditional Deployment Maintenance Script

PROJECT_NAME="banking-system"
PROJECT_USER="banking"
PROJECT_DIR="/opt/$PROJECT_NAME"

# الألوان للطباعة
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# دالة طباعة ملونة
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# عرض حالة النظام
show_system_status() {
    print_status "=== حالة النظام ==="
    
    echo "حالة الخدمات:"
    systemctl is-active --quiet gunicorn && echo "✓ Gunicorn: يعمل" || echo "✗ Gunicorn: متوقف"
    systemctl is-active --quiet celery && echo "✓ Celery: يعمل" || echo "✗ Celery: متوقف"
    systemctl is-active --quiet celerybeat && echo "✓ Celery Beat: يعمل" || echo "✗ Celery Beat: متوقف"
    systemctl is-active --quiet nginx && echo "✓ Nginx: يعمل" || echo "✗ Nginx: متوقف"
    systemctl is-active --quiet postgresql && echo "✓ PostgreSQL: يعمل" || echo "✗ PostgreSQL: متوقف"
    systemctl is-active --quiet redis-server && echo "✓ Redis: يعمل" || echo "✗ Redis: متوقف"
    
    echo ""
    echo "استخدام الموارد:"
    echo "المعالج: $(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')%"
    echo "الذاكرة: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "القرص: $(df $PROJECT_DIR | awk 'NR==2{printf "%s", $5}')"
    
    echo ""
    echo "الاتصالات النشطة:"
    netstat -an | grep :8000 | grep ESTABLISHED | wc -l | awk '{print "Gunicorn: " $1 " اتصال"}'
    netstat -an | grep :80 | grep ESTABLISHED | wc -l | awk '{print "Nginx: " $1 " اتصال"}'
}

# عرض السجلات
show_logs() {
    local service=$1
    local lines=${2:-50}
    
    case $service in
        "gunicorn"|"")
            print_info "سجلات Gunicorn (آخر $lines سطر):"
            sudo journalctl -u gunicorn --no-pager -n $lines
            ;;
        "celery")
            print_info "سجلات Celery (آخر $lines سطر):"
            sudo journalctl -u celery --no-pager -n $lines
            ;;
        "nginx")
            print_info "سجلات Nginx (آخر $lines سطر):"
            sudo tail -n $lines /var/log/nginx/${PROJECT_NAME}_error.log
            ;;
        "access")
            print_info "سجلات الوصول (آخر $lines سطر):"
            sudo tail -n $lines /var/log/nginx/${PROJECT_NAME}_access.log
            ;;
        "django")
            print_info "سجلات Django (آخر $lines سطر):"
            sudo tail -n $lines $PROJECT_DIR/logs/django.log 2>/dev/null || echo "ملف سجل Django غير موجود"
            ;;
        *)
            print_error "خدمة غير معروفة: $service"
            echo "الخدمات المتاحة: gunicorn, celery, nginx, access, django"
            ;;
    esac
}

# إعادة تشغيل الخدمات
restart_services() {
    local service=$1
    
    case $service in
        "all"|"")
            print_status "إعادة تشغيل جميع الخدمات..."
            sudo systemctl restart gunicorn celery celerybeat nginx
            ;;
        "app")
            print_status "إعادة تشغيل خدمات التطبيق..."
            sudo systemctl restart gunicorn celery celerybeat
            ;;
        *)
            if systemctl list-units --type=service | grep -q "^$service.service"; then
                print_status "إعادة تشغيل $service..."
                sudo systemctl restart $service
            else
                print_error "خدمة غير معروفة: $service"
            fi
            ;;
    esac
    
    sleep 3
    show_system_status
}

# فحص صحة النظام
health_check() {
    print_status "=== فحص صحة النظام ==="
    
    local healthy=true
    
    # فحص الخدمات
    services=("gunicorn" "celery" "nginx" "postgresql" "redis-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo "✓ $service: يعمل بشكل صحيح"
        else
            echo "✗ $service: متوقف أو يواجه مشاكل"
            healthy=false
        fi
    done
    
    # فحص قاعدة البيانات
    print_info "فحص قاعدة البيانات..."
    if sudo -u postgres psql -d banking_system -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✓ قاعدة البيانات: متاحة"
    else
        echo "✗ قاعدة البيانات: غير متاحة"
        healthy=false
    fi
    
    # فحص Redis
    print_info "فحص Redis..."
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis: يعمل بشكل صحيح"
    else
        echo "✗ Redis: غير متاح"
        healthy=false
    fi
    
    # فحص التطبيق
    print_info "فحص التطبيق..."
    if curl -f http://localhost:8000 > /dev/null 2>&1; then
        echo "✓ التطبيق: يستجيب بشكل صحيح"
    else
        echo "✗ التطبيق: لا يستجيب"
        healthy=false
    fi
    
    # فحص Nginx
    print_info "فحص Nginx..."
    if curl -f http://localhost > /dev/null 2>&1; then
        echo "✓ Nginx: يعمل بشكل صحيح"
    else
        echo "✗ Nginx: لا يعمل بشكل صحيح"
        healthy=false
    fi
    
    # فحص المساحة
    print_info "فحص مساحة القرص..."
    usage=$(df $PROJECT_DIR | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$usage" -lt 80 ]; then
        echo "✓ مساحة القرص: كافية ($usage%)"
    else
        echo "⚠ مساحة القرص: ممتلئة ($usage%)"
        print_warning "مساحة القرص ممتلئة!"
    fi
    
    if $healthy; then
        print_status "النظام يعمل بحالة جيدة ✓"
    else
        print_error "النظام يواجه مشاكل! يرجى المراجعة"
    fi
}

# تنظيف النظام
cleanup_system() {
    print_status "=== تنظيف النظام ==="
    
    # تنظيف ملفات السجلات القديمة
    print_info "تنظيف ملفات السجلات القديمة..."
    sudo find /var/log/nginx/ -name "*.log" -mtime +30 -delete
    sudo journalctl --vacuum-time=30d
    
    # تنظيف ملفات Python المؤقتة
    print_info "تنظيف ملفات Python المؤقتة..."
    sudo find $PROJECT_DIR -name "*.pyc" -delete
    sudo find $PROJECT_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # تنظيف ملفات التخزين المؤقت
    print_info "تنظيف ملفات التخزين المؤقت..."
    sudo rm -rf /var/cache/nginx/banking/*
    
    # تحديث قاعدة البيانات
    print_info "تحسين قاعدة البيانات..."
    sudo -u postgres psql -d banking_system -c "VACUUM ANALYZE;" > /dev/null 2>&1
    
    print_status "تم تنظيف النظام"
}

# تحديث التطبيق
update_application() {
    print_status "=== تحديث التطبيق ==="
    
    cd $PROJECT_DIR
    
    # إيقاف الخدمات
    print_info "إيقاف خدمات التطبيق..."
    sudo systemctl stop gunicorn celery celerybeat
    
    # سحب آخر التحديثات (إذا كان Git متاحاً)
    if [ -d ".git" ]; then
        print_info "سحب آخر التحديثات من Git..."
        sudo -u $PROJECT_USER git pull origin main
    fi
    
    # تحديث المتطلبات
    print_info "تحديث المتطلبات..."
    sudo -u $PROJECT_USER $PROJECT_DIR/venv/bin/pip install -r requirements.txt --upgrade
    
    # تطبيق الهجرات
    print_info "تطبيق الهجرات..."
    sudo -u $PROJECT_USER $PROJECT_DIR/venv/bin/python manage.py migrate
    
    # جمع الملفات الثابتة
    print_info "جمع الملفات الثابتة..."
    sudo -u $PROJECT_USER $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput
    
    # إعادة تشغيل الخدمات
    print_info "إعادة تشغيل الخدمات..."
    sudo systemctl start gunicorn celery celerybeat
    sudo systemctl reload nginx
    
    print_status "تم تحديث التطبيق"
    
    # فحص الحالة
    sleep 5
    health_check
}

# إنشاء نسخة احتياطية
create_backup() {
    print_status "=== إنشاء نسخة احتياطية ==="
    
    BACKUP_DIR="/opt/backups"
    DATE=$(date +%Y%m%d_%H%M%S)
    
    sudo mkdir -p $BACKUP_DIR
    
    # نسخ احتياطي لقاعدة البيانات
    print_info "إنشاء نسخة احتياطية لقاعدة البيانات..."
    sudo -u postgres pg_dump banking_system | gzip > $BACKUP_DIR/database_$DATE.sql.gz
    
    # نسخ احتياطي للوسائط
    print_info "إنشاء نسخة احتياطية للوسائط..."
    if [ -d "$PROJECT_DIR/media" ]; then
        sudo tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $PROJECT_DIR media/
    fi
    
    # نسخ احتياطي للإعدادات
    print_info "إنشاء نسخة احتياطية للإعدادات..."
    sudo tar -czf $BACKUP_DIR/config_$DATE.tar.gz \\
        --exclude='venv' \\
        --exclude='__pycache__' \\
        --exclude='*.pyc' \\
        --exclude='staticfiles' \\
        --exclude='media' \\
        --exclude='.git' \\
        -C $PROJECT_DIR .
    
    print_status "تم إنشاء النسخة الاحتياطية في $BACKUP_DIR"
    ls -lh $BACKUP_DIR/*$DATE*
}

# القائمة الرئيسية
show_menu() {
    clear
    echo "=================================================="
    echo "       سكريبت صيانة نظام الرسائل المصرفية"
    echo "=================================================="
    echo "1. عرض حالة النظام"
    echo "2. عرض السجلات"
    echo "3. إعادة تشغيل الخدمات"
    echo "4. فحص صحة النظام"
    echo "5. تنظيف النظام"
    echo "6. تحديث التطبيق"
    echo "7. إنشاء نسخة احتياطية"
    echo "8. مراقبة السجلات المباشرة"
    echo "0. خروج"
    echo "=================================================="
    read -p "اختر الخيار: " choice
}

# تشغيل مراقبة السجلات المباشرة
monitor_logs() {
    echo "أي سجلات تريد مراقبتها؟"
    echo "1. Gunicorn"
    echo "2. Nginx Error"
    echo "3. Nginx Access"
    echo "4. جميع الخدمات"
    read -p "اختر: " log_choice
    
    case $log_choice in
        1) sudo journalctl -u gunicorn -f ;;
        2) sudo tail -f /var/log/nginx/${PROJECT_NAME}_error.log ;;
        3) sudo tail -f /var/log/nginx/${PROJECT_NAME}_access.log ;;
        4) sudo journalctl -u gunicorn -u celery -f ;;
        *) print_error "خيار غير صحيح" ;;
    esac
}

# تشغيل السكريبت
if [ $# -eq 0 ]; then
    # تشغيل القائمة التفاعلية
    while true; do
        show_menu
        case $choice in
            1) show_system_status ;;
            2) 
                echo "أدخل اسم الخدمة (gunicorn/celery/nginx/access/django أو اتركه فارغاً):"
                read service
                echo "عدد الأسطر (افتراضي 50):"
                read lines
                show_logs "$service" "${lines:-50}"
                ;;
            3) 
                echo "أدخل اسم الخدمة (all/app/gunicorn/celery/nginx أو اتركه فارغاً لجميع الخدمات):"
                read service
                restart_services "$service"
                ;;
            4) health_check ;;
            5) cleanup_system ;;
            6) update_application ;;
            7) create_backup ;;
            8) monitor_logs ;;
            0) exit 0 ;;
            *) print_error "خيار غير صحيح" ;;
        esac
        echo ""
        read -p "اضغط Enter للمتابعة..."
    done
else
    # تشغيل الأوامر مباشرة
    case $1 in
        status) show_system_status ;;
        logs) show_logs "$2" "$3" ;;
        restart) restart_services "$2" ;;
        health) health_check ;;
        cleanup) cleanup_system ;;
        update) update_application ;;
        backup) create_backup ;;
        *) 
            echo "الاستخدام: $0 [status|logs|restart|health|cleanup|update|backup]"
            echo "أو قم بتشغيل السكريبت بدون معاملات للقائمة التفاعلية"
            ;;
    esac
fi