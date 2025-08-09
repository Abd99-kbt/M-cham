#!/bin/bash

# سكريبت إعداد SSL/HTTPS للموقع
# SSL/HTTPS Setup Script

PROJECT_NAME="banking-system"
DOMAIN_NAME=""

# الألوان
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
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

# طلب النطاق من المستخدم
get_domain() {
    echo "=== إعداد شهادة SSL ==="
    echo ""
    read -p "أدخل اسم النطاق (مثال: banking.example.com): " DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        print_error "يجب إدخال اسم النطاق!"
        exit 1
    fi
    
    echo "سيتم إعداد SSL لـ: $DOMAIN_NAME و www.$DOMAIN_NAME"
    read -p "هل تريد المتابعة؟ (y/n): " confirm
    
    if [ "$confirm" != "y" ]; then
        echo "تم الإلغاء"
        exit 0
    fi
}

# تثبيت Certbot
install_certbot() {
    print_status "تثبيت Certbot..."
    
    # تحديث النظام
    sudo apt update
    
    # تثبيت snapd إذا لم يكن مثبتاً
    if ! command -v snap &> /dev/null; then
        sudo apt install snapd -y
    fi
    
    # تثبيت certbot عبر snap
    sudo snap install core; sudo snap refresh core
    sudo snap install --classic certbot
    
    # إنشاء رابط symbolic
    sudo ln -sf /snap/bin/certbot /usr/bin/certbot
    
    print_status "تم تثبيت Certbot"
}

# الحصول على شهادة SSL
obtain_certificate() {
    print_status "الحصول على شهادة SSL..."
    
    # إيقاف nginx مؤقتاً
    sudo systemctl stop nginx
    
    # الحصول على الشهادة
    sudo certbot certonly --standalone \\
        --preferred-challenges http \\
        -d $DOMAIN_NAME \\
        -d www.$DOMAIN_NAME \\
        --email admin@$DOMAIN_NAME \\
        --agree-tos \\
        --non-interactive
    
    if [ $? -eq 0 ]; then
        print_status "تم الحصول على شهادة SSL بنجاح"
    else
        print_error "فشل في الحصول على شهادة SSL"
        sudo systemctl start nginx
        exit 1
    fi
}

# تحديث إعدادات Nginx للـ HTTPS
update_nginx_config() {
    print_status "تحديث إعدادات Nginx..."
    
    # إنشاء نسخة احتياطية من الإعدادات الحالية
    sudo cp /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-available/${PROJECT_NAME}.backup
    
    # إنشاء إعدادات جديدة مع HTTPS
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null <<EOF
# إعدادات Nginx مع SSL لنظام الرسائل المصرفية

# إعدادات التخزين المؤقت
proxy_cache_path /var/cache/nginx/banking levels=1:2 keys_zone=banking_cache:10m max_size=100m;

# مجموعة خوادم التطبيق
upstream banking_app {
    server 127.0.0.1:8000;
}

# إعادة توجيه HTTP إلى HTTPS
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    return 301 https://\\$server_name\\$request_uri;
}

# الخادم الرئيسي مع HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # شهادات SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
    
    # إعدادات SSL الآمنة
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN_NAME/chain.pem;
    
    # إعدادات الأمان
    server_tokens off;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # إعدادات رفع الملفات
    client_max_body_size 20M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # مجلد الجذر
    root /opt/$PROJECT_NAME;
    
    # ملفات السجلات
    access_log /var/log/nginx/${PROJECT_NAME}_access.log;
    error_log /var/log/nginx/${PROJECT_NAME}_error.log;
    
    # الملفات الثابتة
    location /static/ {
        alias /opt/$PROJECT_NAME/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # ضغط الملفات
        gzip on;
        gzip_vary on;
        gzip_types
            text/css
            text/javascript
            text/xml
            text/plain
            application/javascript
            application/xml+rss
            application/json;
    }
    
    # ملفات الوسائط
    location /media/ {
        alias /opt/$PROJECT_NAME/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # التطبيق الرئيسي
    location / {
        proxy_pass http://banking_app;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        
        # إعدادات المهلة الزمنية
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # إعدادات التخزين المؤقت
        proxy_cache banking_cache;
        proxy_cache_valid 200 302 10m;
        proxy_cache_valid 404 1m;
        proxy_cache_bypass \\$cookie_sessionid;
        proxy_no_cache \\$cookie_sessionid;
        
        # إضافة headers للتخزين المؤقت
        add_header X-Cache-Status \\$upstream_cache_status;
    }
    
    # حماية من الطلبات الضارة
    location ~ /\\\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # ملفات النظام
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
    
    location = /robots.txt {
        log_not_found off;
        access_log off;
    }
    
    # حماية ملفات Python
    location ~* \\\\.(py|pyc|pyo)\\$ {
        deny all;
    }
    
    # حماية ملفات الإعدادات
    location ~* \\\\.(env|conf|config)\\$ {
        deny all;
    }
}
EOF

    # فحص الإعدادات
    if sudo nginx -t; then
        print_status "إعدادات Nginx صحيحة"
    else
        print_error "خطأ في إعدادات Nginx!"
        # استعادة النسخة الاحتياطية
        sudo mv /etc/nginx/sites-available/${PROJECT_NAME}.backup /etc/nginx/sites-available/$PROJECT_NAME
        exit 1
    fi
}

# تحديث إعدادات Django للـ HTTPS
update_django_settings() {
    print_status "تحديث إعدادات Django..."
    
    # تحديث ملف .env
    sudo -u banking sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' /opt/$PROJECT_NAME/.env
    sudo -u banking sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' /opt/$PROJECT_NAME/.env
    sudo -u banking sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' /opt/$PROJECT_NAME/.env
    sudo -u banking sed -i 's/SECURE_HSTS_SECONDS=0/SECURE_HSTS_SECONDS=31536000/' /opt/$PROJECT_NAME/.env
    
    # إضافة النطاق لـ ALLOWED_HOSTS إذا لم يكن موجوداً
    current_hosts=$(sudo -u banking grep "ALLOWED_HOSTS" /opt/$PROJECT_NAME/.env | cut -d'=' -f2)
    if [[ "$current_hosts" != *"$DOMAIN_NAME"* ]]; then
        new_hosts="$current_hosts,$DOMAIN_NAME,www.$DOMAIN_NAME"
        sudo -u banking sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$new_hosts/" /opt/$PROJECT_NAME/.env
    fi
    
    print_status "تم تحديث إعدادات Django"
}

# إعداد التجديد التلقائي
setup_auto_renewal() {
    print_status "إعداد التجديد التلقائي..."
    
    # إنشاء سكريبت hook لإعادة تحميل nginx
    sudo tee /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh > /dev/null <<EOF
#!/bin/bash
systemctl reload nginx
EOF
    
    sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh
    
    # إضافة مهمة cron للتجديد التلقائي
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    
    print_status "تم إعداد التجديد التلقائي"
}

# إعادة تشغيل الخدمات
restart_services() {
    print_status "إعادة تشغيل الخدمات..."
    
    sudo systemctl restart gunicorn
    sudo systemctl start nginx
    
    # فحص حالة الخدمات
    if systemctl is-active --quiet nginx && systemctl is-active --quiet gunicorn; then
        print_status "جميع الخدمات تعمل بنجاح"
    else
        print_error "مشكلة في إحدى الخدمات"
        exit 1
    fi
}

# فحص SSL
test_ssl() {
    print_status "فحص شهادة SSL..."
    
    echo "فحص الاتصال بـ HTTPS..."
    if curl -I https://$DOMAIN_NAME > /dev/null 2>&1; then
        print_status "✓ HTTPS يعمل بشكل صحيح"
        
        # فحص تقييم SSL
        echo ""
        echo "لفحص تقييم SSL الكامل، قم بزيارة:"
        echo "https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN_NAME"
    else
        print_warning "قد تحتاج بعض الوقت حتى تعمل الشهادة بشكل كامل"
    fi
}

# الدالة الرئيسية
main() {
    echo "=== سكريبت إعداد SSL لنظام الرسائل المصرفية ==="
    echo ""
    
    # التحقق من الصلاحيات
    if [ "$EUID" -eq 0 ]; then
        print_error "لا تشغل هذا السكريبت كـ root"
        exit 1
    fi
    
    get_domain
    install_certbot
    obtain_certificate
    update_nginx_config
    update_django_settings
    setup_auto_renewal
    restart_services
    test_ssl
    
    echo ""
    print_status "=== تم إعداد SSL بنجاح ==="
    echo ""
    echo "يمكنك الآن الوصول للموقع عبر:"
    echo "- https://$DOMAIN_NAME"
    echo "- https://www.$DOMAIN_NAME"
    echo ""
    echo "سيتم تجديد الشهادة تلقائياً كل 12 ساعة ظهراً"
    echo ""
    echo "للتحقق من التجديد يدوياً:"
    echo "sudo certbot renew --dry-run"
}

# تشغيل السكريبت
main