#!/bin/bash

# سكريبت نشر المشروع على Ubuntu Server
# Banking System Deployment Script

echo "=== بدء عملية النشر ==="

# التحقق من وجود ملف .env.production
if [ ! -f ".env.production" ]; then
    echo "خطأ: ملف .env.production غير موجود!"
    echo "يرجى إنشاء ملف .env.production أولاً"
    exit 1
fi

# إيقاف الخدمات الموجودة (إن وجدت)
echo "إيقاف الخدمات الموجودة..."
docker-compose down

# بناء الصور الجديدة
echo "بناء صور Docker..."
docker-compose build --no-cache

# تشغيل المهام المطلوبة
echo "تشغيل المهام الأولية..."

# تطبيق ملفات الهجرة
echo "تطبيق ملفات الهجرة..."
docker-compose run --rm web python manage.py migrate

# جمع الملفات الثابتة
echo "جمع الملفات الثابتة..."
docker-compose run --rm web python manage.py collectstatic --noinput

# إنشاء مستخدم إداري (إن لم يكن موجوداً)
echo "إنشاء مستخدم إداري..."
docker-compose run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123456')
    print('تم إنشاء مستخدم إداري: admin/admin123456')
else:
    print('المستخدم الإداري موجود مسبقاً')
"

# تشغيل جميع الخدمات
echo "تشغيل جميع الخدمات..."
docker-compose up -d

# التحقق من حالة الخدمات
echo "التحقق من حالة الخدمات..."
sleep 10
docker-compose ps

# عرض السجلات
echo "عرض آخر السجلات..."
docker-compose logs --tail=50

echo "=== تم النشر بنجاح ==="
echo "يمكنك الوصول للموقع عبر: http://$(hostname -I | awk '{print $1}')"
echo "يمكنك الوصول لوحة الإدارة عبر: http://$(hostname -I | awk '{print $1}')/admin"
echo "المستخدم الإداري: admin"
echo "كلمة المرور: admin123456"
echo ""
echo "لمراقبة السجلات المباشرة: docker-compose logs -f"
echo "لإيقاف الخدمات: docker-compose down"
echo "لإعادة التشغيل: docker-compose restart"