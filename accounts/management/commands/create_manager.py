"""
أمر Django لإنشاء مدير قسم جديد
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.models import Department, Position

User = get_user_model()


class Command(BaseCommand):
    help = 'إنشاء مستخدم جديد بصلاحيات مديرية'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='اسم المستخدم')
        parser.add_argument('email', type=str, help='البريد الإلكتروني')
        parser.add_argument('arabic_name', type=str, help='الاسم بالعربية')
        parser.add_argument('employee_id', type=str, help='رقم الموظف')
        parser.add_argument('department_code', type=str, help='رمز القسم')
        parser.add_argument('phone', type=str, help='رقم الهاتف (3 أرقام)')
        parser.add_argument(
            '--level',
            type=int,
            default=5,
            help='المستوى الوظيفي (افتراضي: 5 - مدير إدارة)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='bank123456',
            help='كلمة المرور (افتراضي: bank123456)'
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='منح صلاحيات الإدارة'
        )

    def handle(self, *args, **options):
        try:
            # التحقق من وجود القسم
            try:
                department = Department.objects.get(code=options['department_code'])
            except Department.DoesNotExist:
                raise CommandError(f'القسم برمز "{options["department_code"]}" غير موجود')

            # التحقق من وجود المنصب
            try:
                position = Position.objects.get(
                    department=department, 
                    level=options['level']
                )
            except Position.DoesNotExist:
                raise CommandError(
                    f'المنصب بمستوى {options["level"]} في قسم {department.name} غير موجود'
                )

            # التحقق من عدم وجود المستخدم مسبقاً
            if User.objects.filter(username=options['username']).exists():
                raise CommandError(f'المستخدم "{options["username"]}" موجود بالفعل')

            if User.objects.filter(employee_id=options['employee_id']).exists():
                raise CommandError(f'رقم الموظف "{options["employee_id"]}" موجود بالفعل')

            if User.objects.filter(email=options['email']).exists():
                raise CommandError(f'البريد الإلكتروني "{options["email"]}" موجود بالفعل')

            # إنشاء المستخدم
            user = User.objects.create_user(
                username=options['username'],
                email=options['email'],
                password=options['password'],
                employee_id=options['employee_id'],
                arabic_name=options['arabic_name'],
                department=department,
                position=position,
                phone=options['phone']
            )

            # تعيين الصلاحيات
            user.is_staff = options['staff']
            user.is_active = True
            user.require_password_change = True
            user.can_send_confidential = options['level'] >= 4
            user.can_send_urgent = options['level'] >= 3
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'تم إنشاء المستخدم "{user.arabic_name}" ({user.username}) بنجاح'
                )
            )
            self.stdout.write(f'القسم: {department.name}')
            self.stdout.write(f'المنصب: {position.title}')
            self.stdout.write(f'كلمة المرور: {options["password"]}')

        except Exception as e:
            raise CommandError(f'خطأ في إنشاء المستخدم: {str(e)}')