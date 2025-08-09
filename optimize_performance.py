#!/usr/bin/env python
"""
سكريبت تحسين الأداء الشامل لنظام الرسائل المصرفية
يقوم بتنفيذ جميع تحسينات الأداء المطلوبة
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """إعداد Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    django.setup()

def create_migrations():
    """إنشاء migrations للفهارس الجديدة"""
    print("🔄 إنشاء migrations للفهارس الجديدة...")
    
    apps_to_migrate = ['accounts', 'security', 'messaging']
    
    for app in apps_to_migrate:
        print(f"📋 إنشاء migration لـ {app}...")
        execute_from_command_line(['manage.py', 'makemigrations', app])
    
    print("✅ تم إنشاء migrations بنجاح")

def apply_migrations():
    """تطبيق migrations"""
    print("🔄 تطبيق migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    print("✅ تم تطبيق migrations بنجاح")

def collect_static():
    """جمع الملفات الثابتة"""
    print("🔄 جمع الملفات الثابتة...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("✅ تم جمع الملفات الثابتة بنجاح")

def clear_cache():
    """مسح الذاكرة المؤقتة"""
    print("🔄 مسح الذاكرة المؤقتة...")
    try:
        from django.core.cache import cache
        cache.clear()
        print("✅ تم مسح الذاكرة المؤقتة بنجاح")
    except Exception as e:
        print(f"⚠️ تعذر مسح الذاكرة المؤقتة: {e}")

def optimize_database():
    """تحسين قاعدة البيانات"""
    print("🔄 تحسين قاعدة البيانات...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # تحسين PostgreSQL
            cursor.execute("VACUUM ANALYZE;")
            print("✅ تم تحسين قاعدة البيانات")
    except Exception as e:
        print(f"⚠️ تعذر تحسين قاعدة البيانات: {e}")

def show_performance_tips():
    """عرض نصائح الأداء"""
    print("\n" + "="*60)
    print("🚀 نصائح إضافية لتحسين الأداء:")
    print("="*60)
    
    tips = [
        "✅ تم تحسين إعدادات Django للأداء",
        "✅ تم تحسين استعلامات قاعدة البيانات",
        "✅ تم إضافة فهارس للحقول المهمة",
        "✅ تم تحسين تحميل الملفات الثابتة",
        "✅ تم تحسين JavaScript والواجهة الأمامية",
        "✅ تم تحسين نظام التصفح",
        "",
        "💡 نصائح إضافية:",
        "   • فعّل Redis كخادم تخزين مؤقت",
        "   • استخدم CDN للملفات الثابتة",
        "   • قم بضغط الصور قبل الرفع",
        "   • راقب استخدام الذاكرة والمعالج",
        "   • قم بعمل backup دوري لقاعدة البيانات",
        "",
        "🔧 للإنتاج:",
        "   • غيّر DEBUG = False",
        "   • استخدم Gunicorn + Nginx",
        "   • فعّل SSL/HTTPS",
        "   • استخدم قاعدة بيانات منفصلة للقراءة",
    ]
    
    for tip in tips:
        print(tip)
    
    print("="*60)

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء تحسين الأداء الشامل لنظام الرسائل المصرفية")
    print("="*60)
    
    try:
        setup_django()
        
        # تنفيذ التحسينات
        create_migrations()
        apply_migrations()
        collect_static()
        clear_cache()
        optimize_database()
        
        print("\n🎉 تم تحسين الأداء بنجاح!")
        show_performance_tips()
        
    except KeyboardInterrupt:
        print("\n❌ تم إيقاف العملية بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()