#!/bin/bash

# سكريبت نشر مشروع Django على Ubuntu بدون Docker
# Banking System Ubuntu Deployment Script

set -e  # إيقاف السكريبت عند حدوث خطأ

# المتغيرات
PROJECT_NAME="banking-system"
PROJECT_USER="banking"
PROJECT_DIR="/opt/$PROJECT_NAME"
PYTHON_VERSION="3.11"

echo "=== بدء نشر مشروع النظام المصرفي على Ubuntu ==="

# 1. تحديث النظام وتثبيت المتطلبات الأساسية
echo "1. تحديث النظام وتثبيت المتطلبات..."
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    supervisor \
    ufw \
    build-essential \
    libpq-dev

# 2. إنشاء مستخدم للمشروع
echo "2. إنشاء مستخدم المشروع..."
if ! id "$PROJECT_USER" &>/dev/null; then
    sudo adduser --system --group --home "$PROJECT_DIR" --shell /bin/bash "$PROJECT_USER"
    echo "تم إنشاء المستخدم: $PROJECT_USER"
else
    echo "المستخدم $PROJECT_USER موجود مسبقاً"
fi

# 3. إنشاء مجلد المشروع
echo "3. إعداد مجلد المشروع..."
sudo mkdir -p "$PROJECT_DIR"
sudo chown "$PROJECT_USER:$PROJECT_USER" "$PROJECT_DIR"

# 4. نقل ملفات المشروع (يفترض أن الملفات موجودة في المجلد الحالي)
echo "4. نقل ملفات المشروع..."
sudo cp -r . "$PROJECT_DIR/"
sudo chown -R "$PROJECT_USER:$PROJECT_USER" "$PROJECT_DIR"

# 5. إعداد قاعدة البيانات PostgreSQL
echo "5. إعداد قاعدة البيانات..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# إنشاء مستخدم وقاعدة بيانات
sudo -u postgres psql <<EOF
CREATE USER banking_user WITH PASSWORD 'secure_password_123';
CREATE DATABASE banking_system OWNER banking_user;
GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user;
ALTER USER banking_user CREATEDB;
\q
EOF

echo "تم إعداد قاعدة البيانات"

# 6. إعداد Redis
echo "6. إعداد Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 7. إعداد البيئة الافتراضية وتثبيت المتطلبات
echo "7. إعداد البيئة الافتراضية..."
sudo -u "$PROJECT_USER" python3 -m venv "$PROJECT_DIR/venv"
sudo -u "$PROJECT_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$PROJECT_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 8. إنشاء ملف متغيرات البيئة
echo "8. إنشاء ملف متغيرات البيئة..."
sudo -u "$PROJECT_USER" cat > "$PROJECT_DIR/.env" <<EOF
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=localhost,127.0.0.1,$(hostname -I | awk '{print $1}')

POSTGRES_DB=banking_system
POSTGRES_USER=banking_user
POSTGRES_PASSWORD=secure_password_123
DATABASE_URL=postgresql://banking_user:secure_password_123@localhost:5432/banking_system

REDIS_URL=redis://localhost:6379/0

SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False

PROJECT_ROOT=$PROJECT_DIR
STATIC_ROOT=$PROJECT_DIR/staticfiles
MEDIA_ROOT=$PROJECT_DIR/media
EOF

echo "تم إنشاء ملف متغيرات البيئة"

# 9. تطبيق الهجرات وجمع الملفات الثابتة
echo "9. تطبيق الهجرات وجمع الملفات الثابتة..."
cd "$PROJECT_DIR"

sudo -u "$PROJECT_USER" "$PROJECT_DIR/venv/bin/python" manage.py migrate
sudo -u "$PROJECT_USER" "$PROJECT_DIR/venv/bin/python" manage.py collectstatic --noinput

# إنشاء مستخدم إداري
echo "إنشاء مستخدم إداري..."
sudo -u "$PROJECT_USER" "$PROJECT_DIR/venv/bin/python" manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123456')
    print('تم إنشاء مستخدم إداري: admin/admin123456')
else:
    print('المستخدم الإداري موجود مسبقاً')
EOF

echo "=== تم النشر الأولي بنجاح ==="
echo ""
echo "الخطوات التالية:"
echo "1. تشغيل سكريبت إعداد الخدمات: sudo ./setup_services.sh"
echo "2. تشغيل سكريبت إعداد Nginx: sudo ./setup_nginx.sh"
echo "3. بدء الخدمات: sudo systemctl start gunicorn nginx"
echo ""
echo "معلومات الوصول:"
echo "- الموقع: http://$(hostname -I | awk '{print $1}')"
echo "- لوحة الإدارة: http://$(hostname -I | awk '{print $1}')/admin"
echo "- المستخدم الإداري: admin"
echo "- كلمة المرور: admin123456"