#!/bin/bash

# سكريبت الصيانة والمراقبة
# Banking System Maintenance Script

PROJECT_DIR="/opt/banking-system"

# الانتقال لمجلد المشروع
cd "$PROJECT_DIR" || exit 1

show_status() {
    echo "=== حالة الخدمات ==="
    docker-compose ps
    echo ""
    
    echo "=== استخدام الموارد ==="
    docker stats --no-stream
    echo ""
}

show_logs() {
    echo "=== السجلات الأخيرة ==="
    docker-compose logs --tail=100 "$1"
}

cleanup_system() {
    echo "=== تنظيف النظام ==="
    
    # حذف الصور غير المستخدمة
    echo "حذف صور Docker غير المستخدمة..."
    docker image prune -f
    
    # حذف الشبكات غير المستخدمة
    echo "حذف شبكات Docker غير المستخدمة..."
    docker network prune -f
    
    # حذف الأحجام غير المستخدمة
    echo "حذف أحجام Docker غير المستخدمة..."
    docker volume prune -f
    
    echo "تم تنظيف النظام"
}

restart_service() {
    if [ -z "$1" ]; then
        echo "إعادة تشغيل جميع الخدمات..."
        docker-compose restart
    else
        echo "إعادة تشغيل خدمة: $1"
        docker-compose restart "$1"
    fi
}

update_system() {
    echo "=== تحديث النظام ==="
    
    # إيقاف الخدمات
    echo "إيقاف الخدمات..."
    docker-compose down
    
    # سحب آخر التحديثات
    echo "سحب آخر التحديثات..."
    git pull origin main
    
    # بناء الصور مرة أخرى
    echo "بناء الصور..."
    docker-compose build --no-cache
    
    # تطبيق الهجرات
    echo "تطبيق الهجرات..."
    docker-compose run --rm web python manage.py migrate
    
    # جمع الملفات الثابتة
    echo "جمع الملفات الثابتة..."
    docker-compose run --rm web python manage.py collectstatic --noinput
    
    # إعادة تشغيل الخدمات
    echo "إعادة تشغيل الخدمات..."
    docker-compose up -d
    
    echo "تم تحديث النظام"
}

check_health() {
    echo "=== فحص صحة النظام ==="
    
    # فحص PostgreSQL
    echo "فحص قاعدة البيانات..."
    if docker-compose exec db pg_isready -U postgres > /dev/null 2>&1; then
        echo "✓ قاعدة البيانات تعمل بشكل صحيح"
    else
        echo "✗ مشكلة في قاعدة البيانات"
    fi
    
    # فحص Redis
    echo "فحص Redis..."
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis يعمل بشكل صحيح"
    else
        echo "✗ مشكلة في Redis"
    fi
    
    # فحص تطبيق الويب
    echo "فحص تطبيق الويب..."
    if curl -f http://localhost:8000 > /dev/null 2>&1; then
        echo "✓ تطبيق الويب يعمل بشكل صحيح"
    else
        echo "✗ مشكلة في تطبيق الويب"
    fi
    
    # فحص Nginx
    echo "فحص Nginx..."
    if curl -f http://localhost > /dev/null 2>&1; then
        echo "✓ Nginx يعمل بشكل صحيح"
    else
        echo "✗ مشكلة في Nginx"
    fi
}

# عرض القائمة الرئيسية
show_menu() {
    echo "=== سكريبت صيانة نظام الرسائل المصرفية ==="
    echo "1. عرض حالة الخدمات"
    echo "2. عرض السجلات"
    echo "3. إعادة تشغيل الخدمات"
    echo "4. فحص صحة النظام"
    echo "5. تنظيف النظام"
    echo "6. تحديث النظام"
    echo "7. إنشاء نسخة احتياطية"
    echo "0. خروج"
    echo ""
    read -p "اختر الخيار: " choice
}

# تشغيل القائمة الرئيسية
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        case $choice in
            1) show_status ;;
            2) 
                echo "أدخل اسم الخدمة (أو اتركه فارغاً لجميع الخدمات):"
                read service
                show_logs "$service"
                ;;
            3) 
                echo "أدخل اسم الخدمة (أو اتركه فارغاً لجميع الخدمات):"
                read service
                restart_service "$service"
                ;;
            4) check_health ;;
            5) cleanup_system ;;
            6) update_system ;;
            7) ./backup.sh ;;
            0) exit 0 ;;
            *) echo "خيار غير صحيح" ;;
        esac
        echo ""
        read -p "اضغط Enter للمتابعة..."
        clear
    done
else
    # تشغيل الأوامر مباشرة
    case $1 in
        status) show_status ;;
        logs) show_logs "$2" ;;
        restart) restart_service "$2" ;;
        health) check_health ;;
        cleanup) cleanup_system ;;
        update) update_system ;;
        backup) ./backup.sh ;;
        *) echo "استخدام: $0 [status|logs|restart|health|cleanup|update|backup]" ;;
    esac
fi