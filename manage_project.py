#!/usr/bin/env python
"""
أداة إدارة المشروع - Banking Messaging System
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Department, Position
from messaging.models import MessageCategory, Message
from security.models import AuditLog
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ProjectManager:
    """فئة إدارة المشروع"""
    
    def __init__(self):
        self.commands = {
            'setup': self.setup_project,
            'reset': self.reset_database,
            'backup': self.backup_database,
            'restore': self.restore_database,
            'stats': self.show_statistics,
            'cleanup': self.cleanup_old_data,
            'health': self.health_check,
            'users': self.manage_users,
            'help': self.show_help
        }
    
    def run(self, command=None, *args):
        """تشغيل الأمر المحدد"""
        if not command or command not in self.commands:
            self.show_help()
            return
        
        try:
            self.commands[command](*args)
        except Exception as e:
            print(f"❌ خطأ في تنفيذ الأمر: {e}")
    
    def setup_project(self):
        """إعداد المشروع الكامل"""
        print("🚀 بدء إعداد المشروع...")
        
        # تطبيق المايجريشن
        print("📦 تطبيق المايجريشن...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # إعداد البيانات الأولية
        print("📊 إعداد البيانات الأولية...")
        os.system('python setup_initial_data.py')
        
        # تجميع الملفات الثابتة
        print("📁 تجميع الملفات الثابتة...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        
        print("✅ تم إعداد المشروع بنجاح!")
        print("\n📋 معلومات الدخول:")
        print("- الإدارة: http://127.0.0.1:8000/admin/")
        print("- النظام: http://127.0.0.1:8000/")
        print("- المستخدم: admin")
        print("- كلمة المرور: bank123456")
    
    def reset_database(self):
        """إعادة تعيين قاعدة البيانات"""
        confirm = input("⚠️  هل أنت متأكد من إعادة تعيين قاعدة البيانات؟ (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ تم إلغاء العملية")
            return
        
        print("🗄️ إعادة تعيين قاعدة البيانات...")
        
        # حذف الملفات
        import glob
        migration_files = glob.glob('*/migrations/0*.py')
        for file in migration_files:
            if '__pycache__' not in file:
                os.remove(file)
                print(f"🗑️ تم حذف: {file}")
        
        # إعادة إنشاء المايجريشن
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        
        # إعادة إعداد البيانات
        os.system('python setup_initial_data.py')
        
        print("✅ تم إعادة تعيين قاعدة البيانات بنجاح!")
    
    def backup_database(self, filename=None):
        """نسخ احتياطي لقاعدة البيانات"""
        if not filename:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}.json"
        
        print(f"💾 إنشاء نسخة احتياطية: {filename}")
        execute_from_command_line(['manage.py', 'dumpdata', '--output', filename])
        print("✅ تم إنشاء النسخة الاحتياطية بنجاح!")
    
    def restore_database(self, filename):
        """استعادة قاعدة البيانات"""
        if not os.path.exists(filename):
            print(f"❌ الملف غير موجود: {filename}")
            return
        
        print(f"📥 استعادة البيانات من: {filename}")
        execute_from_command_line(['manage.py', 'loaddata', filename])
        print("✅ تم استعادة البيانات بنجاح!")
    
    def show_statistics(self):
        """عرض إحصائيات المشروع"""
        print("📊 إحصائيات النظام")
        print("=" * 50)
        
        # المستخدمين
        users_count = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        print(f"👥 المستخدمون: {users_count} (نشط: {active_users})")
        
        # الأقسام
        departments_count = Department.objects.count()
        print(f"🏢 الأقسام: {departments_count}")
        
        # الرسائل
        messages_count = Message.objects.count()
        sent_messages = Message.objects.filter(status='SENT').count()
        draft_messages = Message.objects.filter(status='DRAFT').count()
        print(f"📧 الرسائل: {messages_count} (مرسلة: {sent_messages}, مسودات: {draft_messages})")
        
        # الأمان
        today = timezone.now().date()
        today_logs = AuditLog.objects.filter(timestamp__date=today).count()
        print(f"🔒 سجلات اليوم: {today_logs}")
        
        # الرسائل حسب الأولوية
        print("\n📈 الرسائل حسب الأولوية:")
        priorities = Message.objects.values('priority').distinct()
        for priority in priorities:
            count = Message.objects.filter(priority=priority['priority']).count()
            print(f"  - {priority['priority']}: {count}")
    
    def cleanup_old_data(self, days=90):
        """تنظيف البيانات القديمة"""
        cutoff_date = timezone.now() - timedelta(days=int(days))
        
        print(f"🧹 تنظيف البيانات الأقدم من {days} يوم...")
        
        # حذف السجلات القديمة
        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        logs_count = old_logs.count()
        old_logs.delete()
        print(f"🗑️ تم حذف {logs_count} سجل أمان قديم")
        
        # حذف الرسائل المحذوفة نهائياً
        deleted_messages = Message.objects.filter(
            status='DELETED',
            updated_at__lt=cutoff_date
        )
        messages_count = deleted_messages.count()
        deleted_messages.delete()
        print(f"🗑️ تم حذف {messages_count} رسالة محذوفة نهائياً")
        
        print("✅ تم تنظيف البيانات بنجاح!")
    
    def health_check(self):
        """فحص صحة النظام"""
        print("🏥 فحص صحة النظام")
        print("=" * 50)
        
        issues = []
        
        # فحص قاعدة البيانات
        try:
            User.objects.first()
            print("✅ قاعدة البيانات: متصلة")
        except Exception as e:
            issues.append("قاعدة البيانات غير متاحة")
            print(f"❌ قاعدة البيانات: {e}")
        
        # فحص المساحة التخزينية
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        print(f"💾 المساحة الحرة: {free_gb} GB")
        
        if free_gb < 1:
            issues.append("مساحة التخزين منخفضة")
        
        # فحص الملفات المهمة
        required_files = [
            'manage.py',
            'requirements.txt',
            'myproject/settings.py'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f"✅ {file}: موجود")
            else:
                issues.append(f"ملف مفقود: {file}")
                print(f"❌ {file}: مفقود")
        
        # تقرير النتائج
        if issues:
            print(f"\n⚠️ تم العثور على {len(issues)} مشكلة:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ النظام يعمل بشكل طبيعي!")
    
    def manage_users(self, action=None, username=None):
        """إدارة المستخدمين"""
        if not action:
            print("📝 أوامر إدارة المستخدمين:")
            print("  list - عرض جميع المستخدمين")
            print("  create - إنشاء مستخدم جديد")
            print("  activate <username> - تفعيل مستخدم")
            print("  deactivate <username> - إلغاء تفعيل مستخدم")
            return
        
        if action == 'list':
            print("👥 قائمة المستخدمين:")
            users = User.objects.all()
            for user in users:
                status = "نشط" if user.is_active else "غير نشط"
                print(f"  - {user.username} ({user.arabic_name}) - {status}")
        
        elif action == 'create':
            username = input("اسم المستخدم: ")
            email = input("البريد الإلكتروني: ")
            arabic_name = input("الاسم بالعربية: ")
            employee_id = input("رقم الموظف: ")
            
            # اختيار القسم
            departments = Department.objects.all()
            print("الأقسام المتاحة:")
            for i, dept in enumerate(departments):
                print(f"  {i+1}. {dept.name}")
            
            dept_choice = int(input("اختر رقم القسم: ")) - 1
            department = departments[dept_choice]
            
            # اختيار المنصب
            positions = Position.objects.filter(department=department)
            print("المناصب المتاحة:")
            for i, pos in enumerate(positions):
                print(f"  {i+1}. {pos.title}")
            
            pos_choice = int(input("اختر رقم المنصب: ")) - 1
            position = positions[pos_choice]
            
            # إنشاء المستخدم
            user = User.objects.create_user(
                username=username,
                email=email,
                arabic_name=arabic_name,
                employee_id=employee_id,
                department=department,
                position=position,
                phone='+966501234567'
            )
            user.set_password('temp123456')
            user.require_password_change = True
            user.save()
            
            print(f"✅ تم إنشاء المستخدم: {username}")
        
        elif action in ['activate', 'deactivate'] and username:
            try:
                user = User.objects.get(username=username)
                user.is_active = (action == 'activate')
                user.save()
                status = "تفعيل" if action == 'activate' else "إلغاء تفعيل"
                print(f"✅ تم {status} المستخدم: {username}")
            except User.DoesNotExist:
                print(f"❌ المستخدم غير موجود: {username}")
    
    def show_help(self):
        """عرض المساعدة"""
        print("🛠️ أداة إدارة نظام الرسائل المصرفية")
        print("=" * 50)
        print("الأوامر المتاحة:")
        print("  setup    - إعداد المشروع الكامل")
        print("  reset    - إعادة تعيين قاعدة البيانات")
        print("  backup   - نسخ احتياطي لقاعدة البيانات")
        print("  restore  - استعادة قاعدة البيانات")
        print("  stats    - عرض إحصائيات النظام")
        print("  cleanup  - تنظيف البيانات القديمة")
        print("  health   - فحص صحة النظام")
        print("  users    - إدارة المستخدمين")
        print("  help     - عرض هذه المساعدة")
        print("\nمثال: python manage_project.py setup")

if __name__ == '__main__':
    manager = ProjectManager()
    if len(sys.argv) > 1:
        manager.run(*sys.argv[1:])
    else:
        manager.show_help()