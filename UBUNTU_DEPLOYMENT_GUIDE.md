# دليل النشر على Ubuntu Server (بدون Docker)

دليل شامل لنشر نظام الرسائل المصرفية على Ubuntu Server باستخدام الطريقة التقليدية بدون Docker.

## المتطلبات الأساسية

### متطلبات السيرفر
- Ubuntu 20.04 LTS أو أحدث
- ذاكرة وصول عشوائي: 2GB على الأقل (4GB مفضل)
- مساحة القرص: 20GB على الأقل
- معالج: 2 نواة على الأقل
- اتصال إنترنت مستقر

### البرامج المطلوبة
سيتم تثبيتها تلقائياً:
- Python 3.11+
- PostgreSQL 15+
- Redis
- Nginx
- Git
- Supervisor (للإدارة المتقدمة)

## خطوات النشر

### 1. تحضير السيرفر والملفات

```bash
# على جهازك المحلي، ضغط المشروع
cd /path/to/your/project
tar -czf banking-system.tar.gz .

# نقل الملفات للسيرفر
scp banking-system.tar.gz user@your-server-ip:/tmp/

# على السيرفر
cd /tmp
tar -xzf banking-system.tar.gz
```

### 2. تشغيل سكريبت النشر الرئيسي

```bash
# جعل السكريبت قابل للتنفيذ
chmod +x ubuntu_deploy.sh

# تشغيل النشر
sudo ./ubuntu_deploy.sh
```

هذا السكريبت سيقوم بـ:
- تحديث النظام وتثبيت جميع المتطلبات
- إنشاء مستخدم نظام للمشروع
- إعداد قاعدة البيانات PostgreSQL
- إعداد Redis
- إنشاء البيئة الافتراضية وتثبيت المتطلبات
- تطبيق الهجرات
- إنشاء مستخدم إداري

### 3. إعداد الخدمات

```bash
# إعداد خدمات systemd
chmod +x setup_services.sh
sudo ./setup_services.sh
```

يتم إنشاء الخدمات التالية:
- `gunicorn.service`: خادم تطبيق Django
- `celery.service`: معالج المهام الخلفية
- `celerybeat.service`: جدولة المهام

### 4. إعداد Nginx

```bash
# إعداد خادم الويب
chmod +x setup_nginx.sh
sudo ./setup_nginx.sh
```

### 5. التحقق من النشر

```bash
# فحص حالة الخدمات
sudo systemctl status gunicorn celery nginx

# فحص صحة النظام
chmod +x ubuntu_maintenance.sh
./ubuntu_maintenance.sh health
```

## الوصول للنظام

بعد النشر الناجح:

- **الموقع الرئيسي**: `http://your-server-ip`
- **لوحة الإدارة**: `http://your-server-ip/admin`
- **بيانات المستخدم الإداري**:
  - اسم المستخدم: `admin`
  - كلمة المرور: `admin123456`

> ⚠️ **تحذير**: قم بتغيير كلمة المرور فور تسجيل الدخول الأول!

## إعداد HTTPS (اختياري ولكن مهم)

### للحصول على شهادة SSL مجانية:

```bash
# إعداد SSL مع Let's Encrypt
chmod +x setup_ssl.sh
./setup_ssl.sh
```

سيطلب منك:
- اسم النطاق (مثال: banking.example.com)
- عنوان بريد إلكتروني للتجديد

بعد النجاح:
- سيتم تفعيل HTTPS تلقائياً
- إعادة توجيه HTTP إلى HTTPS
- تجديد تلقائي للشهادة

## الصيانة والمراقبة

### سكريبت الصيانة الشامل

```bash
# تشغيل قائمة الصيانة التفاعلية
./ubuntu_maintenance.sh

# أو استخدام الأوامر مباشرة:
./ubuntu_maintenance.sh status      # عرض حالة النظام
./ubuntu_maintenance.sh logs        # عرض السجلات
./ubuntu_maintenance.sh health      # فحص صحة النظام
./ubuntu_maintenance.sh restart     # إعادة تشغيل الخدمات
./ubuntu_maintenance.sh cleanup     # تنظيف النظام
./ubuntu_maintenance.sh update      # تحديث التطبيق
```

### النسخ الاحتياطية

```bash
# إنشاء نسخة احتياطية كاملة
./ubuntu_backup.sh full

# أو استخدام القائمة التفاعلية
./ubuntu_backup.sh

# نسخة احتياطية تلقائية يومية
sudo crontab -e
# أضف: 0 2 * * * /opt/banking-system/ubuntu_backup.sh full
```

## الأوامر المفيدة

### إدارة الخدمات

```bash
# إعادة تشغيل التطبيق
sudo systemctl restart gunicorn

# إعادة تشغيل معالج المهام
sudo systemctl restart celery

# إعادة تحميل Nginx
sudo systemctl reload nginx

# مراقبة السجلات المباشرة
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/banking-system_error.log
```

### إدارة قاعدة البيانات

```bash
# الاتصال بقاعدة البيانات
sudo -u postgres psql banking_system

# نسخ احتياطي سريع
sudo -u postgres pg_dump banking_system > backup.sql

# استعادة من نسخة احتياطية
sudo -u postgres psql banking_system < backup.sql
```

### إدارة Python

```bash
# تفعيل البيئة الافتراضية
source /opt/banking-system/venv/bin/activate

# تشغيل أوامر Django
cd /opt/banking-system
./venv/bin/python manage.py migrate
./venv/bin/python manage.py collectstatic
./venv/bin/python manage.py createsuperuser
```

## حل المشاكل الشائعة

### 1. خطأ 502 Bad Gateway

```bash
# فحص حالة Gunicorn
sudo systemctl status gunicorn

# فحص السجلات
sudo journalctl -u gunicorn -n 50

# إعادة تشغيل إذا لزم الأمر
sudo systemctl restart gunicorn
```

### 2. مشكلة في قاعدة البيانات

```bash
# فحص حالة PostgreSQL
sudo systemctl status postgresql

# فحص الاتصال
sudo -u postgres psql -c "SELECT 1;"

# إعادة تشغيل إذا لزم الأمر
sudo systemctl restart postgresql
```

### 3. مشكلة في الملفات الثابتة

```bash
# إعادة جمع الملفات الثابتة
cd /opt/banking-system
sudo -u banking ./venv/bin/python manage.py collectstatic --noinput

# التحقق من الصلاحيات
sudo chown -R banking:www-data /opt/banking-system/staticfiles
```

### 4. مشكلة في Redis

```bash
# فحص حالة Redis
sudo systemctl status redis-server

# فحص الاتصال
redis-cli ping

# إعادة تشغيل إذا لزم الأمر
sudo systemctl restart redis-server
```

## الأمان

### إعدادات جدار الحماية

```bash
# تفعيل UFW
sudo ufw enable

# السماح بـ SSH
sudo ufw allow ssh

# السماح بـ HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# فحص القواعد
sudo ufw status
```

### تحديثات الأمان

```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تحديث المشروع
cd /opt/banking-system
git pull origin main
./ubuntu_maintenance.sh update
```

### مراقبة الأمان

```bash
# مراقبة محاولات تسجيل الدخول الفاشلة
sudo grep "Failed password" /var/log/auth.log

# مراقبة سجلات الأمان في Django
tail -f /opt/banking-system/logs/security.log
```

## التحسينات المتقدمة

### 1. زيادة عدد Workers

```bash
# تحرير خدمة Gunicorn
sudo systemctl edit gunicorn.service

# إضافة:
[Service]
ExecStart=
ExecStart=/opt/banking-system/venv/bin/gunicorn --workers 5 --bind 127.0.0.1:8000 myproject.wsgi:application

sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

### 2. تحسين PostgreSQL

```bash
# تحرير إعدادات PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf

# تحسينات مقترحة:
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

sudo systemctl restart postgresql
```

### 3. إعداد مراقبة متقدمة

```bash
# تثبيت htop للمراقبة
sudo apt install htop

# إعداد مراقبة تلقائية
echo "*/5 * * * * /opt/banking-system/ubuntu_maintenance.sh health >> /var/log/health_check.log" | sudo crontab -
```

## المساعدة والدعم

### ملفات السجلات المهمة

- **Django**: `/opt/banking-system/logs/django.log`
- **Nginx Access**: `/var/log/nginx/banking-system_access.log`
- **Nginx Error**: `/var/log/nginx/banking-system_error.log`
- **Gunicorn**: `sudo journalctl -u gunicorn`
- **Celery**: `sudo journalctl -u celery`

### التحقق من الأداء

```bash
# استخدام الموارد
htop

# مساحة القرص
df -h

# استخدام الذاكرة
free -h

# الاتصالات النشطة
netstat -an | grep :80 | wc -l
```

### إعادة النشر الكاملة

```bash
# في حالة الحاجة لإعادة النشر من الصفر
sudo systemctl stop gunicorn celery celerybeat nginx
sudo rm -rf /opt/banking-system
# ثم إعادة تشغيل ubuntu_deploy.sh
```

---

## ملاحظات مهمة

1. **النسخ الاحتياطية**: قم بإنشاء نسخ احتياطية منتظمة قبل أي تحديث
2. **المراقبة**: استخدم سكريبت الصيانة لمراقبة النظام بانتظام
3. **الأمان**: غيّر كلمات المرور الافتراضية فوراً
4. **التحديثات**: احرص على تحديث النظام والتطبيق بانتظام
5. **الدعم**: احتفظ بنسخة من هذا الدليل للرجوع إليه

للمزيد من المساعدة، راجع الملفات:
- `ubuntu_maintenance.sh` للصيانة
- `ubuntu_backup.sh` للنسخ الاحتياطية
- `setup_ssl.sh` لإعداد HTTPS