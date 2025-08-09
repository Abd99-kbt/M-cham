#!/bin/bash

# سكريبت النسخ الاحتياطي للمشروع
# Banking System Backup Script

# إعداد المتغيرات
BACKUP_DIR="/opt/banking-system-backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/banking-system"

echo "=== بدء عملية النسخ الاحتياطي ==="

# إنشاء مجلد النسخ الاحتياطي
mkdir -p "$BACKUP_DIR"

# الانتقال لمجلد المشروع
cd "$PROJECT_DIR" || exit 1

# نسخ احتياطي لقاعدة البيانات
echo "إنشاء نسخة احتياطية لقاعدة البيانات..."
docker-compose exec -T db pg_dump -U postgres ms > "$BACKUP_DIR/database_backup_$DATE.sql"

if [ $? -eq 0 ]; then
    echo "تم إنشاء النسخة الاحتياطية لقاعدة البيانات: database_backup_$DATE.sql"
else
    echo "خطأ في إنشاء النسخة الاحتياطية لقاعدة البيانات"
fi

# نسخ احتياطي لملفات الوسائط
echo "إنشاء نسخة احتياطية لملفات الوسائط..."
if [ -d "media" ]; then
    tar -czf "$BACKUP_DIR/media_backup_$DATE.tar.gz" media/
    echo "تم إنشاء النسخة الاحتياطية للوسائط: media_backup_$DATE.tar.gz"
fi

# نسخ احتياطي لإعدادات المشروع
echo "إنشاء نسخة احتياطية لإعدادات المشروع..."
tar -czf "$BACKUP_DIR/project_config_$DATE.tar.gz" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='media' \
    --exclude='staticfiles' \
    --exclude='.git' \
    .

echo "تم إنشاء النسخة الاحتياطية للمشروع: project_config_$DATE.tar.gz"

# ضغط النسخة الاحتياطية لقاعدة البيانات
echo "ضغط النسخة الاحتياطية لقاعدة البيانات..."
gzip "$BACKUP_DIR/database_backup_$DATE.sql"

# عرض ملخص النسخ الاحتياطية
echo ""
echo "=== ملخص النسخ الاحتياطية ==="
ls -lh "$BACKUP_DIR"/*"$DATE"*

# حذف النسخ الاحتياطية القديمة (أكثر من 7 أيام)
echo ""
echo "حذف النسخ الاحتياطية القديمة (أكثر من 7 أيام)..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "=== تم إنهاء عملية النسخ الاحتياطي ==="