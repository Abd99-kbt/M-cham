# البدء السريع - نشر نظام الرسائل المصرفية على Ubuntu

## خطوات النشر السريع (5 دقائق)

### 1. تحضير الملفات

```bash
# على جهازك المحلي
tar -czf banking-system.tar.gz .

# نقل للسيرفر
scp banking-system.tar.gz user@server-ip:/tmp/

# على السيرفر
cd /tmp
tar -xzf banking-system.tar.gz
cd banking-system
```

### 2. النشر التلقائي

```bash
# جعل السكريبتات قابلة للتنفيذ
chmod +x *.sh

# النشر الكامل (سيستغرق 5-10 دقائق)
sudo ./ubuntu_deploy.sh
sudo ./setup_services.sh
sudo ./setup_nginx.sh
```

### 3. التحقق من النجاح

```bash
# فحص سريع
./ubuntu_maintenance.sh health

# الوصول للموقع
curl http://localhost
```

## معلومات الوصول

- **الموقع**: `http://YOUR_SERVER_IP`
- **الإدارة**: `http://YOUR_SERVER_IP/admin`
- **المستخدم**: `admin`
- **كلمة المرور**: `admin123456` (غيّرها فوراً!)

## الأوامر الأساسية

```bash
# مراقبة الحالة
./ubuntu_maintenance.sh status

# عرض السجلات
./ubuntu_maintenance.sh logs

# إنشاء نسخة احتياطية
./ubuntu_backup.sh full

# إعادة تشغيل التطبيق
sudo systemctl restart gunicorn
```

## إعداد HTTPS (اختياري)

```bash
# للمواقع بنطاق مسجل
./setup_ssl.sh
```

## في حالة المشاكل

```bash
# إعادة تشغيل جميع الخدمات
sudo systemctl restart gunicorn celery nginx

# فحص مفصل
./ubuntu_maintenance.sh health

# عرض آخر أخطاء
sudo journalctl -u gunicorn -n 20
```

## المجلدات المهمة

- المشروع: `/opt/banking-system`
- النسخ الاحتياطية: `/opt/backups`
- السجلات: `/opt/banking-system/logs`
- إعدادات Nginx: `/etc/nginx/sites-available/banking-system`

---

**تهانينا! 🎉 تم نشر نظام الرسائل المصرفية بنجاح**

للدليل الكامل، راجع: `UBUNTU_DEPLOYMENT_GUIDE.md`