#!/bin/bash

# سكريبت إعداد Nginx للنشر التقليدي
# Setup Nginx for Traditional Deployment

PROJECT_NAME="banking-system"
PROJECT_DIR="/opt/$PROJECT_NAME"
DOMAIN_NAME="your-domain.com"  # غير هذا إلى النطاق الخاص بك

echo "=== إعداد Nginx ==="

# 1. إنشاء ملف إعدادات Nginx للموقع
echo "1. إنشاء ملف إعدادات Nginx..."
sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null <<EOF
# إعدادات Nginx لنظام الرسائل المصرفية

# إعدادات التخزين المؤقت
proxy_cache_path /var/cache/nginx/banking levels=1:2 keys_zone=banking_cache:10m max_size=100m;

# مجموعة خوادم التطبيق
upstream banking_app {
    server 127.0.0.1:8000;
}

# إعادة توجيه HTTP إلى HTTPS (يتم تفعيله لاحقاً)
# server {
#     listen 80;
#     server_name $DOMAIN_NAME www.$DOMAIN_NAME;
#     return 301 https://\$server_name\$request_uri;
# }

# الخادم الرئيسي
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME _;
    
    # إعدادات الأمان
    server_tokens off;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # إعدادات رفع الملفات
    client_max_body_size 20M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # مجلد الجذر
    root $PROJECT_DIR;
    
    # ملفات السجلات
    access_log /var/log/nginx/${PROJECT_NAME}_access.log;
    error_log /var/log/nginx/${PROJECT_NAME}_error.log;
    
    # الملفات الثابتة
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
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
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # التطبيق الرئيسي
    location / {
        proxy_pass http://banking_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # إعدادات المهلة الزمنية
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # إعدادات التخزين المؤقت
        proxy_cache banking_cache;
        proxy_cache_valid 200 302 10m;
        proxy_cache_valid 404 1m;
        proxy_cache_bypass \$cookie_sessionid;
        proxy_no_cache \$cookie_sessionid;
        
        # إضافة headers للتخزين المؤقت
        add_header X-Cache-Status \$upstream_cache_status;
    }
    
    # حماية من الطلبات الضارة
    location ~ /\\. {
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
    location ~* \\.(py|pyc|pyo)\$ {
        deny all;
    }
    
    # حماية ملفات الإعدادات
    location ~* \\.(env|conf|config)\$ {
        deny all;
    }
}

# إعداد HTTPS (للتفعيل لاحقاً بعد الحصول على شهادة SSL)
# server {
#     listen 443 ssl http2;
#     server_name $DOMAIN_NAME www.$DOMAIN_NAME;
#     
#     # شهادات SSL
#     ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
#     
#     # إعدادات SSL الآمنة
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
#     ssl_prefer_server_ciphers off;
#     ssl_session_cache shared:SSL:10m;
#     ssl_session_timeout 10m;
#     
#     # HSTS
#     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
#     
#     # باقي الإعدادات نفس HTTP server
# }
EOF

# 2. تفعيل الموقع
echo "2. تفعيل الموقع..."
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/

# 3. إزالة الموقع الافتراضي
echo "3. إزالة الموقع الافتراضي..."
sudo rm -f /etc/nginx/sites-enabled/default

# 4. إنشاء مجلد التخزين المؤقت
echo "4. إعداد التخزين المؤقت..."
sudo mkdir -p /var/cache/nginx/banking
sudo chown www-data:www-data /var/cache/nginx/banking

# 5. فحص إعدادات Nginx
echo "5. فحص إعدادات Nginx..."
sudo nginx -t

if [ \$? -eq 0 ]; then
    echo "إعدادات Nginx صحيحة"
    
    # 6. إعادة تحميل Nginx
    echo "6. إعادة تحميل Nginx..."
    sudo systemctl reload nginx
    sudo systemctl enable nginx
    
    echo ""
    echo "=== تم إعداد Nginx بنجاح ==="
    echo ""
    echo "يمكنك الوصول للموقع عبر:"
    echo "- http://\$(hostname -I | awk '{print \$1}')"
    echo "- http://localhost (إذا كنت على نفس السيرفر)"
    echo ""
    echo "لمراقبة سجلات Nginx:"
    echo "- tail -f /var/log/nginx/${PROJECT_NAME}_access.log"
    echo "- tail -f /var/log/nginx/${PROJECT_NAME}_error.log"
    
else
    echo "خطأ في إعدادات Nginx! يرجى مراجعة الأخطاء أعلاه"
    exit 1
fi