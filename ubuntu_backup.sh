#!/bin/bash

# سكريبت النسخ الاحتياطي للنشر التقليدي على Ubuntu
# Ubuntu Traditional Deployment Backup Script

PROJECT_NAME="banking-system"
PROJECT_USER="banking"
PROJECT_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# الألوان
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# إنشاء مجلد النسخ الاحتياطي
create_backup_dir() {
    print_status "إنشاء مجلد النسخ الاحتياطي..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown $USER:$USER "$BACKUP_DIR"
}

# نسخ احتياطي لقاعدة البيانات
backup_database() {
    print_status "إنشاء نسخة احتياطية لقاعدة البيانات..."
    
    # نسخ احتياطي مضغوطة
    sudo -u postgres pg_dump banking_system | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"
    
    if [ $? -eq 0 ]; then
        print_status "✓ تم إنشاء النسخة الاحتياطية لقاعدة البيانات"
        ls -lh "$BACKUP_DIR/database_$DATE.sql.gz"
    else
        print_error "✗ فشل في إنشاء النسخة الاحتياطية لقاعدة البيانات"
        return 1
    fi
    
    # إنشاء نسخة احتياطية منفصلة للبيانات الهامة فقط
    print_status "إنشاء نسخة احتياطية للبيانات الهامة..."
    sudo -u postgres pg_dump banking_system \\
        --data-only \\
        --table=accounts_user \\
        --table=accounts_department \\
        --table=messaging_message \\
        | gzip > "$BACKUP_DIR/critical_data_$DATE.sql.gz"
}

# نسخ احتياطي لملفات الوسائط
backup_media() {
    print_status "إنشاء نسخة احتياطية لملفات الوسائط..."
    
    if [ -d "$PROJECT_DIR/media" ] && [ "$(ls -A $PROJECT_DIR/media)" ]; then
        sudo tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C "$PROJECT_DIR" media/
        
        if [ $? -eq 0 ]; then
            print_status "✓ تم إنشاء النسخة الاحتياطية للوسائط"
            ls -lh "$BACKUP_DIR/media_$DATE.tar.gz"
        else
            print_error "✗ فشل في إنشاء النسخة الاحتياطية للوسائط"
        fi
    else
        print_warning "مجلد الوسائط فارغ أو غير موجود"
    fi
}

# نسخ احتياطي لإعدادات المشروع
backup_config() {
    print_status "إنشاء نسخة احتياطية لإعدادات المشروع..."
    
    sudo tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \\
        --exclude='venv' \\
        --exclude='__pycache__' \\
        --exclude='*.pyc' \\
        --exclude='staticfiles' \\
        --exclude='media' \\
        --exclude='.git' \\
        --exclude='logs' \\
        -C "$PROJECT_DIR" .
    
    if [ $? -eq 0 ]; then
        print_status "✓ تم إنشاء النسخة الاحتياطية للإعدادات"
        ls -lh "$BACKUP_DIR/config_$DATE.tar.gz"
    else
        print_error "✗ فشل في إنشاء النسخة الاحتياطية للإعدادات"
    fi
}

# نسخ احتياطي لإعدادات النظام
backup_system_config() {
    print_status "إنشاء نسخة احتياطية لإعدادات النظام..."
    
    # إنشاء مجلد مؤقت
    temp_dir=$(mktemp -d)
    
    # نسخ إعدادات systemd
    sudo cp /etc/systemd/system/gunicorn.service "$temp_dir/" 2>/dev/null
    sudo cp /etc/systemd/system/celery.service "$temp_dir/" 2>/dev/null
    sudo cp /etc/systemd/system/celerybeat.service "$temp_dir/" 2>/dev/null
    
    # نسخ إعدادات nginx
    sudo cp /etc/nginx/sites-available/$PROJECT_NAME "$temp_dir/" 2>/dev/null
    
    # نسخ إعدادات SSL (إن وجدت)
    if [ -d "/etc/letsencrypt/live" ]; then
        sudo cp -r /etc/letsencrypt/live "$temp_dir/" 2>/dev/null
        sudo cp -r /etc/letsencrypt/renewal "$temp_dir/" 2>/dev/null
    fi
    
    # إنشاء الأرشيف
    sudo tar -czf "$BACKUP_DIR/system_config_$DATE.tar.gz" -C "$temp_dir" .
    
    # حذف المجلد المؤقت
    sudo rm -rf "$temp_dir"
    
    if [ $? -eq 0 ]; then
        print_status "✓ تم إنشاء النسخة الاحتياطية لإعدادات النظام"
        ls -lh "$BACKUP_DIR/system_config_$DATE.tar.gz"
    else
        print_error "✗ فشل في إنشاء النسخة الاحتياطية لإعدادات النظام"
    fi
}

# نسخ احتياطي للسجلات
backup_logs() {
    print_status "إنشاء نسخة احتياطية للسجلات..."
    
    # إنشاء مجلد مؤقت
    temp_dir=$(mktemp -d)
    
    # نسخ سجلات Django
    if [ -d "$PROJECT_DIR/logs" ]; then
        sudo cp -r "$PROJECT_DIR/logs" "$temp_dir/"
    fi
    
    # نسخ سجلات Nginx
    sudo cp /var/log/nginx/${PROJECT_NAME}_*.log "$temp_dir/" 2>/dev/null
    
    # نسخ سجلات النظام (آخر أسبوع)
    sudo journalctl -u gunicorn --since "1 week ago" > "$temp_dir/gunicorn.log" 2>/dev/null
    sudo journalctl -u celery --since "1 week ago" > "$temp_dir/celery.log" 2>/dev/null
    
    # إنشاء الأرشيف
    sudo tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$temp_dir" .
    
    # حذف المجلد المؤقت
    sudo rm -rf "$temp_dir"
    
    if [ $? -eq 0 ]; then
        print_status "✓ تم إنشاء النسخة الاحتياطية للسجلات"
        ls -lh "$BACKUP_DIR/logs_$DATE.tar.gz"
    else
        print_error "✗ فشل في إنشاء النسخة الاحتياطية للسجلات"
    fi
}

# إنشاء نسخة احتياطية كاملة
full_backup() {
    print_status "=== إنشاء نسخة احتياطية كاملة ==="
    
    create_backup_dir
    backup_database
    backup_media
    backup_config
    backup_system_config
    backup_logs
    
    # إنشاء ملف معلومات النسخة الاحتياطية
    cat > "$BACKUP_DIR/backup_info_$DATE.txt" <<EOF
نسخة احتياطية لنظام الرسائل المصرفية
========================================

تاريخ النسخة الاحتياطية: $(date)
إصدار النظام: $(lsb_release -d | cut -f2)
مساحة القرص المستخدمة: $(df -h $PROJECT_DIR | awk 'NR==2{print $3 "/" $2 " (" $5 ")"}')

الملفات المشمولة:
- database_$DATE.sql.gz: قاعدة البيانات الكاملة
- critical_data_$DATE.sql.gz: البيانات الهامة فقط
- media_$DATE.tar.gz: ملفات الوسائط المرفوعة
- config_$DATE.tar.gz: إعدادات المشروع والكود المصدري
- system_config_$DATE.tar.gz: إعدادات النظام والخدمات
- logs_$DATE.tar.gz: ملفات السجلات

للاستعادة:
1. استعادة قاعدة البيانات: gunzip -c database_$DATE.sql.gz | sudo -u postgres psql banking_system
2. استعادة الملفات: tar -xzf config_$DATE.tar.gz -C $PROJECT_DIR
3. استعادة إعدادات النظام: tar -xzf system_config_$DATE.tar.gz -C /

ملاحظات:
- تأكد من إيقاف الخدمات قبل الاستعادة
- قم بتشغيل الهجرات بعد استعادة قاعدة البيانات
- تأكد من صلاحيات الملفات بعد الاستعادة
EOF

    print_status "✓ تم إنشاء ملف معلومات النسخة الاحتياطية"
}

# حذف النسخ الاحتياطية القديمة
cleanup_old_backups() {
    local days=${1:-7}
    
    print_status "حذف النسخ الاحتياطية الأقدم من $days أيام..."
    
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$days -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$days -delete
    find "$BACKUP_DIR" -name "*.txt" -mtime +$days -delete
    
    print_status "✓ تم تنظيف النسخ الاحتياطية القديمة"
}

# عرض ملخص النسخ الاحتياطية
show_backup_summary() {
    print_status "=== ملخص النسخ الاحتياطية ==="
    echo ""
    echo "مجلد النسخ الاحتياطية: $BACKUP_DIR"
    echo ""
    echo "النسخ الاحتياطية الحالية:"
    ls -lh "$BACKUP_DIR"/*"$DATE"* 2>/dev/null || echo "لا توجد نسخ احتياطية لهذا التاريخ"
    echo ""
    echo "المساحة المستخدمة:"
    du -sh "$BACKUP_DIR" 2>/dev/null || echo "غير متاح"
    echo ""
    echo "عدد النسخ الاحتياطية الإجمالي:"
    ls -1 "$BACKUP_DIR" | wc -l
}

# استعادة من نسخة احتياطية
restore_backup() {
    local backup_date=$1
    
    if [ -z "$backup_date" ]; then
        echo "النسخ الاحتياطية المتاحة:"
        ls -1 "$BACKUP_DIR" | grep -o '[0-9]\\{8\\}_[0-9]\\{6\\}' | sort -u
        read -p "أدخل تاريخ النسخة الاحتياطية (YYYYMMDD_HHMMSS): " backup_date
    fi
    
    if [ ! -f "$BACKUP_DIR/database_$backup_date.sql.gz" ]; then
        print_error "النسخة الاحتياطية غير موجودة: $backup_date"
        exit 1
    fi
    
    print_warning "تحذير: هذا سيقوم بحذف البيانات الحالية!"
    read -p "هل أنت متأكد؟ (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "تم الإلغاء"
        exit 0
    fi
    
    print_status "إيقاف الخدمات..."
    sudo systemctl stop gunicorn celery celerybeat
    
    print_status "استعادة قاعدة البيانات..."
    sudo -u postgres dropdb banking_system
    sudo -u postgres createdb banking_system -O banking_user
    gunzip -c "$BACKUP_DIR/database_$backup_date.sql.gz" | sudo -u postgres psql banking_system
    
    if [ -f "$BACKUP_DIR/config_$backup_date.tar.gz" ]; then
        print_status "استعادة إعدادات المشروع..."
        sudo tar -xzf "$BACKUP_DIR/config_$backup_date.tar.gz" -C "$PROJECT_DIR"
        sudo chown -R $PROJECT_USER:$PROJECT_USER "$PROJECT_DIR"
    fi
    
    if [ -f "$BACKUP_DIR/media_$backup_date.tar.gz" ]; then
        print_status "استعادة ملفات الوسائط..."
        sudo tar -xzf "$BACKUP_DIR/media_$backup_date.tar.gz" -C "$PROJECT_DIR"
    fi
    
    print_status "إعادة تشغيل الخدمات..."
    sudo systemctl start gunicorn celery celerybeat
    
    print_status "✓ تم استعادة النسخة الاحتياطية بنجاح"
}

# القائمة الرئيسية
show_menu() {
    echo "=================================================="
    echo "      سكريبت النسخ الاحتياطي - النشر التقليدي"
    echo "=================================================="
    echo "1. إنشاء نسخة احتياطية كاملة"
    echo "2. نسخ احتياطي لقاعدة البيانات فقط"
    echo "3. نسخ احتياطي للوسائط فقط"
    echo "4. عرض ملخص النسخ الاحتياطية"
    echo "5. استعادة من نسخة احتياطية"
    echo "6. تنظيف النسخ الاحتياطية القديمة"
    echo "0. خروج"
    echo "=================================================="
    read -p "اختر الخيار: " choice
}

# تشغيل السكريبت
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        case $choice in
            1) full_backup ;;
            2) create_backup_dir && backup_database ;;
            3) create_backup_dir && backup_media ;;
            4) show_backup_summary ;;
            5) restore_backup ;;
            6) 
                read -p "حذف النسخ الأقدم من كم يوم؟ (افتراضي 7): " days
                cleanup_old_backups "${days:-7}"
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
        full) full_backup ;;
        database) create_backup_dir && backup_database ;;
        media) create_backup_dir && backup_media ;;
        config) create_backup_dir && backup_config ;;
        system) create_backup_dir && backup_system_config ;;
        logs) create_backup_dir && backup_logs ;;
        cleanup) cleanup_old_backups "${2:-7}" ;;
        restore) restore_backup "$2" ;;
        summary) show_backup_summary ;;
        *) 
            echo "الاستخدام: $0 [full|database|media|config|system|logs|cleanup|restore|summary]"
            ;;
    esac
fi