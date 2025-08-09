#!/bin/bash

# سكريبت إصلاح الخدمات - حل مشاكل محددة
# Fix Services Script - Solve Specific Issues

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

PROJECT_DIR="/opt/banking-system"
PROJECT_USER="banking"

echo "=============================================="
echo "        إصلاح مشاكل الخدمات المحددة"
echo "=============================================="
echo ""

# إيقاف الخدمات المتعطلة
print_info "إيقاف الخدمات المتعطلة..."
sudo systemctl stop gunicorn celery celerybeat 2>/dev/null
sudo systemctl reset-failed gunicorn celery celerybeat 2>/dev/null

# 1. فحص وإنشاء ملف .env
print_status "1. فحص ملف .env..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_warning "ملف .env غير موجود، إنشاؤه الآن..."
    
    sudo -u $PROJECT_USER tee "$PROJECT_DIR/.env" > /dev/null <<EOF
# إعدادات الإنتاج
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=localhost,127.0.0.1,$(hostname -I | awk '{print $1}')

# إعدادات قاعدة البيانات
POSTGRES_DB=banking_system
POSTGRES_USER=banking_user
POSTGRES_PASSWORD=secure_password_123
DATABASE_URL=postgresql://banking_user:secure_password_123@localhost:5432/banking_system

# إعدادات Redis
REDIS_URL=redis://localhost:6379/0

# إعدادات الأمان
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0

# مسارات النظام
PROJECT_ROOT=$PROJECT_DIR
STATIC_ROOT=$PROJECT_DIR/staticfiles
MEDIA_ROOT=$PROJECT_DIR/media

# إعدادات Gunicorn
GUNICORN_WORKERS=3
GUNICORN_BIND=127.0.0.1:8000
EOF
    
    sudo chown $PROJECT_USER:$PROJECT_USER "$PROJECT_DIR/.env"
    print_status "تم إنشاء ملف .env"
else
    print_status "ملف .env موجود"
fi

# 2. فحص البيئة الافتراضية
print_status "2. فحص البيئة الافتراضية..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    print_warning "البيئة الافتراضية غير موجودة، إنشاؤها الآن..."
    
    sudo -u $PROJECT_USER python3 -m venv "$PROJECT_DIR/venv"
    sudo -u $PROJECT_USER "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
    
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        print_info "تثبيت المتطلبات..."
        sudo -u $PROJECT_USER "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    fi
    
    print_status "تم إنشاء البيئة الافتراضية"
else
    print_status "البيئة الافتراضية موجودة"
fi

# 3. فحص وإنشاء المجلدات المطلوبة
print_status "3. فحص المجلدات المطلوبة..."

directories=("$PROJECT_DIR/logs" "$PROJECT_DIR/media" "$PROJECT_DIR/staticfiles")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        sudo mkdir -p "$dir"
        sudo chown $PROJECT_USER:$PROJECT_USER "$dir"
        print_status "تم إنشاء: $dir"
    fi
done

# 4. فحص ملف manage.py
print_status "4. فحص ملف Django..."

if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    print_error "ملف manage.py غير موجود!"
    print_info "تحقق من أن المشروع منسوخ بشكل صحيح في $PROJECT_DIR"
    exit 1
else
    print_status "ملف manage.py موجود"
fi

# 5. تطبيق الهجرات
print_status "5. تطبيق الهجرات..."

cd "$PROJECT_DIR"
if sudo -u $PROJECT_USER "$PROJECT_DIR/venv/bin/python" manage.py migrate --check > /dev/null 2>&1; then
    print_status "الهجرات مطبقة"
else
    print_info "تطبيق الهجرات..."
    sudo -u $PROJECT_USER "$PROJECT_DIR/venv/bin/python" manage.py migrate
fi

# 6. جمع الملفات الثابتة
print_status "6. جمع الملفات الثابتة..."
sudo -u $PROJECT_USER "$PROJECT_DIR/venv/bin/python" manage.py collectstatic --noinput > /dev/null 2>&1

# 7. فحص وتصحيح ملفات الخدمة
print_status "7. فحص ملفات الخدمة..."

# فحص ملف gunicorn.service
if [ -f "/etc/systemd/system/gunicorn.service" ]; then
    # التحقق من المسارات في ملف الخدمة
    if grep -q "EnvironmentFile=$PROJECT_DIR/.env" /etc/systemd/system/gunicorn.service; then
        print_status "ملف خدمة Gunicorn صحيح"
    else
        print_warning "تصحيح ملف خدمة Gunicorn..."
        
        sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve Banking System
After=network.target

[Service]
User=$PROJECT_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 myproject.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        print_status "تم تصحيح ملف خدمة Gunicorn"
    fi
fi

# 8. إعادة تحميل وتشغيل الخدمات
print_status "8. إعادة تحميل إعدادات النظام..."

sudo systemctl daemon-reload

print_status "9. تشغيل الخدمات..."

# تشغيل Gunicorn أولاً
print_info "تشغيل Gunicorn..."
if sudo systemctl start gunicorn; then
    print_status "Gunicorn تم تشغيله بنجاح"
    sudo systemctl enable gunicorn
else
    print_error "فشل في تشغيل Gunicorn"
    print_info "فحص الأخطاء:"
    sudo journalctl -u gunicorn --no-pager -n 5
fi

sleep 3

# تشغيل Celery
print_info "تشغيل Celery..."
if sudo systemctl start celery; then
    print_status "Celery تم تشغيله بنجاح"
    sudo systemctl enable celery
else
    print_warning "مشكلة في تشغيل Celery (قد يعمل لاحقاً)"
fi

# تشغيل Celery Beat
print_info "تشغيل Celery Beat..."
if sudo systemctl start celerybeat; then
    print_status "Celery Beat تم تشغيله بنجاح"
    sudo systemctl enable celerybeat
else
    print_warning "مشكلة في تشغيل Celery Beat (قد يعمل لاحقاً)"
fi

# 10. فحص نهائي
print_status "10. فحص نهائي..."

sleep 5

echo ""
echo "حالة الخدمات:"
services=("gunicorn" "celery" "celerybeat")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        print_status "$service يعمل ✓"
    else
        print_warning "$service لا يعمل ⚠"
    fi
done

echo ""

# فحص الاتصال
print_info "فحص الاتصال بالتطبيق..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null | grep -q "200\|301\|302\|403"; then
    print_status "التطبيق يستجيب على المنفذ 8000 ✓"
else
    print_warning "التطبيق لا يستجيب على المنفذ 8000"
    print_info "قد يحتاج بعض الوقت للبدء..."
fi

echo ""
echo "=============================================="
print_status "تم انتهاء الإصلاح!"
echo ""
echo "للفحص المفصل:"
echo "sudo systemctl status gunicorn"
echo "sudo journalctl -u gunicorn -f"
echo ""
echo "للوصول للتطبيق:"
echo "http://$(hostname -I | awk '{print $1}'):8000"
echo "=============================================="