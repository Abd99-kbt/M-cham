#!/bin/bash

# سكريبت الإصلاح السريع
# Quick Fix Script

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# إصلاح سريع للمشاكل الشائعة
quick_fix() {
    echo "=============================================="
    echo "        الإصلاح السريع للمشاكل الشائعة"
    echo "=============================================="
    echo ""
    
    print_status "بدء الإصلاح السريع..."
    echo ""
    
    # 1. إعادة تشغيل جميع الخدمات
    print_status "1. إعادة تشغيل جميع الخدمات..."
    
    services=("gunicorn" "celery" "celerybeat" "nginx" "postgresql" "redis-server")
    for service in "${services[@]}"; do
        if systemctl list-units --type=service | grep -q "^$service.service"; then
            echo "   إعادة تشغيل $service..."
            sudo systemctl restart $service
            sleep 2
            if systemctl is-active --quiet $service; then
                echo "   ✓ $service يعمل الآن"
            else
                echo "   ✗ $service لا يزال متوقف"
            fi
        else
            echo "   ⚠ $service غير مثبت"
        fi
    done
    
    echo ""
    
    # 2. فحص وإصلاح صلاحيات الملفات
    print_status "2. فحص وإصلاح صلاحيات الملفات..."
    
    if [ -d "/opt/banking-system" ]; then
        sudo chown -R banking:banking /opt/banking-system
        sudo chmod -R 755 /opt/banking-system
        sudo chmod +x /opt/banking-system/*.sh 2>/dev/null
        echo "   ✓ تم إصلاح صلاحيات الملفات"
    else
        echo "   ⚠ مجلد المشروع غير موجود"
    fi
    
    echo ""
    
    # 3. فحص وإنشاء المجلدات المطلوبة
    print_status "3. فحص المجلدات المطلوبة..."
    
    directories=("/opt/banking-system/logs" "/opt/banking-system/media" "/opt/banking-system/staticfiles")
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            sudo mkdir -p "$dir"
            sudo chown banking:banking "$dir"
            echo "   ✓ تم إنشاء المجلد: $dir"
        else
            echo "   ✓ المجلد موجود: $dir"
        fi
    done
    
    echo ""
    
    # 4. فحص إعدادات قاعدة البيانات
    print_status "4. فحص قاعدة البيانات..."
    
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw banking_system; then
        echo "   ✓ قاعدة البيانات banking_system موجودة"
        
        # فحص الاتصال
        if sudo -u postgres psql -d banking_system -c "SELECT 1;" > /dev/null 2>&1; then
            echo "   ✓ يمكن الاتصال بقاعدة البيانات"
        else
            echo "   ✗ مشكلة في الاتصال بقاعدة البيانات"
        fi
    else
        print_warning "   قاعدة البيانات banking_system غير موجودة"
        echo "   إنشاء قاعدة البيانات..."
        
        sudo -u postgres createdb banking_system
        sudo -u postgres psql -c "CREATE USER banking_user WITH PASSWORD 'secure_password_123';" 2>/dev/null
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user;"
        sudo -u postgres psql -c "ALTER USER banking_user CREATEDB;"
        
        echo "   ✓ تم إنشاء قاعدة البيانات"
    fi
    
    echo ""
    
    # 5. تطبيق الهجرات إذا لزم الأمر
    if [ -f "/opt/banking-system/manage.py" ]; then
        print_status "5. فحص الهجرات..."
        
        cd /opt/banking-system
        if sudo -u banking ./venv/bin/python manage.py showmigrations --plan | grep -q "\[ \]"; then
            echo "   تطبيق الهجرات المعلقة..."
            sudo -u banking ./venv/bin/python manage.py migrate
            echo "   ✓ تم تطبيق الهجرات"
        else
            echo "   ✓ جميع الهجرات مطبقة"
        fi
    fi
    
    echo ""
    
    # 6. جمع الملفات الثابتة
    if [ -f "/opt/banking-system/manage.py" ]; then
        print_status "6. جمع الملفات الثابتة..."
        
        cd /opt/banking-system
        sudo -u banking ./venv/bin/python manage.py collectstatic --noinput > /dev/null 2>&1
        echo "   ✓ تم جمع الملفات الثابتة"
    fi
    
    echo ""
    
    # 7. إعادة تحميل إعدادات systemd
    print_status "7. إعادة تحميل إعدادات النظام..."
    
    sudo systemctl daemon-reload
    echo "   ✓ تم إعادة تحميل إعدادات systemd"
    
    echo ""
    
    # 8. فحص نهائي
    print_status "8. فحص نهائي للحالة..."
    
    sleep 5  # انتظار قليل للخدمات للبدء
    
    all_good=true
    services_to_check=("gunicorn" "celery" "nginx" "postgresql" "redis-server")
    
    for service in "${services_to_check[@]}"; do
        if systemctl is-active --quiet $service 2>/dev/null; then
            echo "   ✓ $service يعمل"
        else
            echo "   ✗ $service لا يعمل"
            all_good=false
        fi
    done
    
    echo ""
    
    if $all_good; then
        print_status "🎉 تم الإصلاح بنجاح! جميع الخدمات تعمل الآن"
        echo ""
        echo "يمكنك الوصول للموقع عبر:"
        echo "http://$(hostname -I | awk '{print $1}')"
        echo "http://localhost"
    else
        print_warning "⚠️ لا تزال هناك مشاكل في بعض الخدمات"
        echo ""
        echo "للتشخيص المفصل، قم بتشغيل:"
        echo "./diagnose.sh"
        echo ""
        echo "لعرض السجلات:"
        echo "./ubuntu_maintenance.sh logs"
    fi
    
    echo ""
    echo "=============================================="
}

# إصلاح مشكلة محددة
fix_specific_service() {
    local service=$1
    
    echo "إصلاح مشكلة $service..."
    
    case $service in
        "gunicorn")
            echo "فحص إعدادات Gunicorn..."
            
            # التحقق من وجود ملف الخدمة
            if [ ! -f "/etc/systemd/system/gunicorn.service" ]; then
                print_error "ملف خدمة Gunicorn غير موجود"
                echo "قم بتشغيل: sudo ./setup_services.sh"
                return 1
            fi
            
            # التحقق من المجلد والملفات
            if [ ! -f "/opt/banking-system/manage.py" ]; then
                print_error "ملفات المشروع غير موجودة"
                return 1
            fi
            
            # إعادة تشغيل
            sudo systemctl stop gunicorn
            sleep 2
            sudo systemctl start gunicorn
            sudo systemctl enable gunicorn
            ;;
            
        "nginx")
            echo "فحص إعدادات Nginx..."
            
            # فحص إعدادات Nginx
            if sudo nginx -t; then
                sudo systemctl restart nginx
                sudo systemctl enable nginx
            else
                print_error "خطأ في إعدادات Nginx"
                echo "قم بتشغيل: sudo ./setup_nginx.sh"
                return 1
            fi
            ;;
            
        "postgresql")
            echo "فحص PostgreSQL..."
            
            sudo systemctl restart postgresql
            sudo systemctl enable postgresql
            
            # انتظار بدء الخدمة
            sleep 5
            
            # فحص الاتصال
            if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
                echo "✓ PostgreSQL يعمل الآن"
            else
                print_error "مشكلة في PostgreSQL"
                return 1
            fi
            ;;
            
        "redis-server"|"redis")
            echo "فحص Redis..."
            
            sudo systemctl restart redis-server
            sudo systemctl enable redis-server
            
            sleep 2
            
            if redis-cli ping > /dev/null 2>&1; then
                echo "✓ Redis يعمل الآن"
            else
                print_error "مشكلة في Redis"
                return 1
            fi
            ;;
            
        *)
            print_error "خدمة غير معروفة: $service"
            return 1
            ;;
    esac
    
    echo "✓ تم إصلاح $service"
}

# عرض القائمة
show_menu() {
    echo "=============================================="
    echo "             سكريبت الإصلاح السريع"
    echo "=============================================="
    echo "1. إصلاح سريع شامل"
    echo "2. إصلاح Gunicorn"
    echo "3. إصلاح Nginx"
    echo "4. إصلاح PostgreSQL"
    echo "5. إصلاح Redis"
    echo "6. تشخيص مفصل"
    echo "0. خروج"
    echo "=============================================="
    read -p "اختر الخيار: " choice
}

# تشغيل السكريبت
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        case $choice in
            1) quick_fix ;;
            2) fix_specific_service "gunicorn" ;;
            3) fix_specific_service "nginx" ;;
            4) fix_specific_service "postgresql" ;;
            5) fix_specific_service "redis" ;;
            6) 
                if [ -f "./diagnose.sh" ]; then
                    chmod +x ./diagnose.sh
                    ./diagnose.sh
                else
                    echo "ملف diagnose.sh غير موجود"
                fi
                ;;
            0) exit 0 ;;
            *) print_error "خيار غير صحيح" ;;
        esac
        echo ""
        read -p "اضغط Enter للمتابعة..."
        clear
    done
else
    case $1 in
        "all") quick_fix ;;
        "gunicorn"|"nginx"|"postgresql"|"redis") fix_specific_service "$1" ;;
        *) 
            echo "الاستخدام: $0 [all|gunicorn|nginx|postgresql|redis]"
            echo "أو قم بتشغيل السكريبت بدون معاملات للقائمة التفاعلية"
            ;;
    esac
fi