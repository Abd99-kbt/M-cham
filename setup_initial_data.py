#!/usr/bin/env python
"""
ملف إعداد البيانات الأولية لنظام الرسائل المصرفية
"""
import os
import django
from django.core.management import execute_from_command_line

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import Department, Position, User
from messaging.models import MessageCategory
from workflows.models import ApprovalWorkflow
from django.contrib.auth.hashers import make_password

def create_departments():
    """إنشاء الأقسام الأساسية"""
    departments = [
        {'name': 'الإدارة العامة', 'code': 'GM'},
        {'name': 'إدارة الائتمان', 'code': 'CR'},
        {'name': 'إدارة الخزينة', 'code': 'TR'},
        {'name': 'إدارة العمليات', 'code': 'OP'},
        {'name': 'إدارة الموارد البشرية', 'code': 'HR'},
        {'name': 'إدارة تقنية المعلومات', 'code': 'IT'},
        {'name': 'إدارة الامتثال', 'code': 'CP'},
        {'name': 'إدارة المراجعة الداخلية', 'code': 'IA'},
        {'name': 'إدارة خدمة العملاء', 'code': 'CS'},
    ]
    
    created_departments = {}
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults={'name': dept_data['name']}
        )
        created_departments[dept_data['code']] = dept
        if created:
            print(f"تم إنشاء قسم: {dept.name}")
    
    return created_departments

def create_positions(departments):
    """إنشاء المناصب الوظيفية"""
    positions_data = [
        {'title': 'المدير العام', 'level': 7, 'can_approve': True, 'max_amount': None},
        {'title': 'نائب المدير العام', 'level': 6, 'can_approve': True, 'max_amount': None},
        {'title': 'مدير إدارة', 'level': 5, 'can_approve': True, 'max_amount': None},
        {'title': 'رئيس قسم', 'level': 4, 'can_approve': True, 'max_amount': None},
        {'title': 'نائب رئيس قسم', 'level': 3, 'can_approve': True, 'max_amount': None},
        {'title': 'مشرف', 'level': 2, 'can_approve': False, 'max_amount': None},
        {'title': 'موظف', 'level': 1, 'can_approve': False, 'max_amount': None},
    ]
    
    created_positions = {}
    for dept_code, dept in departments.items():
        for pos_data in positions_data:
            pos, created = Position.objects.get_or_create(
                title=pos_data['title'],
                department=dept,
                defaults={
                    'level': pos_data['level'],
                    'can_approve_messages': pos_data['can_approve'],
                    'max_approval_amount': pos_data['max_amount'],
                    'permissions_level': pos_data['level']
                }
            )
            created_positions[f"{dept_code}_{pos_data['level']}"] = pos
            if created:
                print(f"تم إنشاء منصب: {pos.title} في {dept.name}")
    
    return created_positions

def create_message_categories():
    """إنشاء تصنيفات الرسائل"""
    categories_data = [
        {'name': 'CREDIT', 'requires_approval': True},
        {'name': 'TREASURY', 'requires_approval': True},
        {'name': 'OPERATIONS', 'requires_approval': False},
        {'name': 'ADMIN', 'requires_approval': False},
        {'name': 'HR', 'requires_approval': False},
        {'name': 'IT', 'requires_approval': False},
        {'name': 'COMPLIANCE', 'requires_approval': True},
        {'name': 'AUDIT', 'requires_approval': True},
        {'name': 'CUSTOMER', 'requires_approval': False},
        {'name': 'OTHER', 'requires_approval': False},
    ]
    
    for cat_data in categories_data:
        cat, created = MessageCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'requires_approval': cat_data['requires_approval'],
                'default_priority': 'NORMAL'
            }
        )
        if created:
            print(f"تم إنشاء تصنيف: {cat.get_name_display()}")

def create_sample_users(departments, positions):
    """إنشاء مستخدمين تجريبيين"""
    
    usernames_to_delete = ['admin', 'manager_credit', 'manager_treasury', 'officer1', 'officer2']
    
    # حذف السجلات والرسائل المرتبطة بالمستخدمين التجريبيين
    from messaging.models import Message
    from security.models import AuditLog
    
    users_to_delete = User.objects.filter(username__in=usernames_to_delete)
    
    Message.objects.filter(sender__in=users_to_delete).delete()
    AuditLog.objects.filter(user__in=users_to_delete).delete()
    
    # الآن حذف المستخدمين
    users_to_delete.delete()
    print("🗑️ تم حذف المستخدمين التجريبيين القدامى والبيانات المرتبطة بهم.")

    users_data = [
        {
            'username': 'admin',
            'employee_id': '1001',
            'arabic_name': 'المدير العام',
            'email': 'admin@bank.com',
            'department': 'GM',
            'level': 7,
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'manager_credit',
            'employee_id': '1002',
            'arabic_name': 'مدير الائتمان',
            'email': 'credit@bank.com',
            'department': 'CR',
            'level': 5,
            'is_staff': True,
            'is_superuser': False
        },
        {
            'username': 'manager_treasury',
            'employee_id': '1003',
            'arabic_name': 'مدير الخزينة',
            'email': 'treasury@bank.com',
            'department': 'TR',
            'level': 5,
            'is_staff': True,
            'is_superuser': False
        },
        {
            'username': 'officer1',
            'employee_id': '2001',
            'arabic_name': 'موظف ائتمان',
            'email': 'officer1@bank.com',
            'department': 'CR',
            'level': 1,
            'is_staff': False,
            'is_superuser': False
        },
        {
            'username': 'officer2',
            'employee_id': '2002',
            'arabic_name': 'موظف خزينة',
            'email': 'officer2@bank.com',
            'department': 'TR',
            'level': 1,
            'is_staff': False,
            'is_superuser': False
        }
    ]

    for user_data in users_data:
        department = departments[user_data['department']]
        position = positions[f"{user_data['department']}_{user_data['level']}"]
        
        try:
            if user_data['is_superuser']:
                user = User.objects.create_superuser(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='bank123456',  # Set password directly
                    employee_id=user_data['employee_id'],
                    arabic_name=user_data['arabic_name'],
                    department=department,
                    position=position,
                    phone='123'
                )
            else:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='bank123456',  # Set password directly
                    employee_id=user_data['employee_id'],
                    arabic_name=user_data['arabic_name'],
                    department=department,
                    position=position,
                    phone='123'
                )
            
            # Update additional fields
            user.is_staff = user_data['is_staff']
            user.is_active = True
            user.require_password_change = True
            user.can_send_confidential = user_data['level'] >= 4
            user.can_send_urgent = user_data['level'] >= 3
            user.save()
            
            print(f"✅ تم إنشاء مستخدم: {user.arabic_name} ({user.username})")

        except Exception as e:
            print(f"❌ خطأ في إنشاء المستخدم {user_data['username']}: {e}")

def create_workflows():
    """إنشاء سير عمل الموافقات"""
    workflows_data = [
        {
            'name': 'موافقة رسائل الائتمان',
            'workflow_type': 'MESSAGE_APPROVAL',
            'description': 'سير عمل موافقة الرسائل المتعلقة بالائتمان',
            'minimum_approvers': 1,
            'sequential': True
        },
        {
            'name': 'موافقة معاملات الخزينة',
            'workflow_type': 'TRANSACTION_APPROVAL',
            'description': 'سير عمل موافقة معاملات الخزينة',
            'minimum_approvers': 2,
            'sequential': True
        }
    ]
    
    for workflow_data in workflows_data:
        workflow, created = ApprovalWorkflow.objects.get_or_create(
            name=workflow_data['name'],
            defaults={
                'workflow_type': workflow_data['workflow_type'],
                'description': workflow_data['description'],
                'minimum_approvers': workflow_data['minimum_approvers'],
                'requires_sequential_approval': workflow_data['sequential']
            }
        )
        if created:
            print(f"تم إنشاء سير عمل: {workflow.name}")

def main():
    """تشغيل إعداد البيانات الأولية"""
    print("بدء إعداد البيانات الأولية...")
    
    # إنشاء الأقسام
    print("\n1. إنشاء الأقسام...")
    departments = create_departments()
    
    # إنشاء المناصب
    print("\n2. إنشاء المناصب...")
    positions = create_positions(departments)
    
    # إنشاء تصنيفات الرسائل
    print("\n3. إنشاء تصنيفات الرسائل...")
    create_message_categories()
    
    # إنشاء المستخدمين التجريبيين
    print("\n4. إنشاء المستخدمين...")
    create_sample_users(departments, positions)
    
    # إنشاء سير العمل
    print("\n5. إنشاء سير العمل...")
    create_workflows()
    
    print("\n✅ تم إعداد البيانات الأولية بنجاح!")
    print("\nبيانات الدخول التجريبية:")
    print("- المدير العام: admin / bank123456")
    print("- مدير الائتمان: manager_credit / bank123456")
    print("- مدير الخزينة: manager_treasury / bank123456")
    print("- موظف ائتمان: officer1 / bank123456")
    print("- موظف خزينة: officer2 / bank123456")

if __name__ == '__main__':
    main()