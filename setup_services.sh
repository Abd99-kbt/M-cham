#!/bin/bash

# سكريبت إعداد خدمات systemd
# Setup SystemD Services Script

PROJECT_NAME="banking-system"
PROJECT_USER="banking"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "=== إعداد خدمات SystemD ==="

# 1. إنشاء خدمة Gunicorn
echo "1. إنشاء خدمة Gunicorn..."
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

# 2. إنشاء خدمة Celery Worker
echo "2. إنشاء خدمة Celery Worker..."
sudo tee /etc/systemd/system/celery.service > /dev/null <<EOF
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/celery -A myproject worker --loglevel=info --detach
ExecStop=$PROJECT_DIR/venv/bin/celery -A myproject control shutdown
ExecReload=$PROJECT_DIR/venv/bin/celery -A myproject control reload
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 3. إنشاء خدمة Celery Beat (للمهام المجدولة)
echo "3. إنشاء خدمة Celery Beat..."
sudo tee /etc/systemd/system/celerybeat.service > /dev/null <<EOF
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/celery -A myproject beat --loglevel=info
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. إعادة تحميل وتفعيل الخدمات
echo "4. تفعيل الخدمات..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.service
sudo systemctl enable celery.service
sudo systemctl enable celerybeat.service

# 5. بدء الخدمات
echo "5. بدء الخدمات..."
sudo systemctl start gunicorn
sudo systemctl start celery
sudo systemctl start celerybeat

# 6. فحص حالة الخدمات
echo "6. فحص حالة الخدمات..."
echo "حالة Gunicorn:"
sudo systemctl status gunicorn --no-pager -l

echo ""
echo "حالة Celery:"
sudo systemctl status celery --no-pager -l

echo ""
echo "حالة Celery Beat:"
sudo systemctl status celerybeat --no-pager -l

echo ""
echo "=== تم إعداد جميع الخدمات بنجاح ==="
echo ""
echo "أوامر مفيدة:"
echo "- إعادة تشغيل Gunicorn: sudo systemctl restart gunicorn"
echo "- إعادة تشغيل Celery: sudo systemctl restart celery"
echo "- مراقبة السجلات: sudo journalctl -u gunicorn -f"
echo "- فحص حالة جميع الخدمات: sudo systemctl status gunicorn celery celerybeat"