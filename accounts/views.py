"""
Views for accounts app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import Department, Position, UserGroup
from .forms import UserRegistrationForm, DepartmentForm
from security.models import AuditLog, UserSession, LoginAttempt
from django.http import JsonResponse
from django.db import transaction

User = get_user_model()

def get_client_ip(request):
    """الحصول على عنوان IP للعميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def register_view(request):
    """تسجيل مستخدم جديد"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # حفظ المستخدم الجديد
                    user = form.save()
                    
                    # تسجيل العملية في سجل الأمان
                    AuditLog.objects.create(
                        action_type='USER_REGISTRATION',
                        description=f'تسجيل مستخدم جديد: {user.username} ({user.arabic_name})',
                        user=user,
                        user_ip=get_client_ip(request),
                        is_successful=True
                    )
                    
                    messages.success(
                        request, 
                        f'تم تسجيلك بنجاح! مرحباً {user.arabic_name}. يمكنك الآن تسجيل الدخول.'
                    )
                    
                    # توجيه إلى صفحة تسجيل الدخول
                    return redirect('accounts:login')
                    
            except Exception as e:
                # تسجيل الخطأ
                AuditLog.objects.create(
                    action_type='USER_REGISTRATION_FAILED',
                    description=f'فشل في تسجيل مستخدم جديد: {form.cleaned_data.get("username", "غير معروف")} - {str(e)}',
                    user_ip=get_client_ip(request),
                    is_successful=False
                )
                
                messages.error(request, 'حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.')
        else:
            # في حالة وجود أخطاء في النموذج
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields.get(field, {}).label or field
                    messages.error(request, f'{field_label}: {error}')
    else:
        form = UserRegistrationForm()
    
    # الحصول على الأقسام والمناصب للنموذج
    departments = Department.objects.filter(is_active=True).order_by('name')
    positions = Position.objects.all().order_by('department', 'level')
    managers = User.objects.filter(is_active=True, position__level__gte=3).order_by('arabic_name')
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'departments': departments,
        'positions': positions,
        'managers': managers
    })


def get_positions_by_department(request):
    """الحصول على المناصب حسب القسم (AJAX)"""
    department_id = request.GET.get('department_id')
    
    if department_id:
        positions = Position.objects.filter(department_id=department_id).order_by('level')
        position_data = [
            {'id': pos.id, 'title': pos.title, 'level': pos.get_level_display()}
            for pos in positions
        ]
        return JsonResponse({'positions': position_data})
    
    return JsonResponse({'positions': []})


def login_view(request):
    """تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            
            # Ensure session is created and saved before accessing session_key
            if not request.session.session_key:
                request.session.create()
            request.session.save()
            
            # Create user session
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Log successful login
            AuditLog.objects.create(
                action_type='LOGIN',
                description=f'تسجيل دخول ناجح للمستخدم {user.username}',
                user=user,
                user_ip=get_client_ip(request),
                is_successful=True
            )
            
            messages.success(request, f'مرحباً {user.arabic_name or user.username}!')
            
            # التوجيه حسب نوع المستخدم
            # المدير العام أو مدراء الإدارات يذهبون لصفحة المدير
            if user.is_superuser or (user.position and user.position.level >= 5):
                return redirect('accounts:admin_dashboard')
            # الموظفين العاديين يذهبون للوحة التحكم العادية
            return redirect('dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    """تسجيل الخروج"""
    user = request.user
    is_admin = user.is_staff
    
    # Log logout
    AuditLog.objects.create(
        action_type='ADMIN_LOGOUT' if is_admin else 'LOGOUT',
        description=f'تسجيل خروج للمستخدم {user.username}',
        user=user,
        user_ip=get_client_ip(request),
        is_successful=True
    )
    
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح.')
    
    # توجيه المديرين إلى صفحة تسجيل دخول المدير
    if is_admin:
        return redirect('accounts:admin_login')
    else:
        return redirect('accounts:login')

@login_required
def profile_view(request):
    """عرض الملف الشخصي"""
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    """تعديل الملف الشخصي"""
    return render(request, 'accounts/edit_profile.html')

@login_required
def user_settings(request):
    """إعدادات المستخدم"""
    return render(request, 'accounts/settings.html')

@login_required
def change_password(request):
    """تغيير كلمة المرور"""
    return render(request, 'accounts/change_password.html')

# Admin Views
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_list(request):
    """قائمة المستخدمين"""
    users = User.objects.select_related('department', 'position').all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_detail(request, user_id):
    """تفاصيل المستخدم"""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/user_detail.html', {'profile_user': user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_user(request):
    """إضافة مستخدم جديد"""
    departments = Department.objects.all()
    positions = Position.objects.all()
    return render(request, 'accounts/add_user.html', {
        'departments': departments,
        'positions': positions
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_user(request, user_id):
    """تعديل مستخدم"""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/edit_user.html', {'profile_user': user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_user(request, user_id):
    """حذف مستخدم"""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/delete_user.html', {'profile_user': user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_permissions(request, user_id):
    """صلاحيات المستخدم"""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/user_permissions.html', {'profile_user': user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def department_list(request):
    """قائمة الأقسام"""
    departments = Department.objects.all()
    return render(request, 'accounts/department_list.html', {'departments': departments})

@login_required
@user_passes_test(lambda u: u.is_staff)
def department_detail(request, dept_id):
    """تفاصيل القسم"""
    department = get_object_or_404(Department, id=dept_id)
    return render(request, 'accounts/department_detail.html', {'department': department})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_department(request):
    """إضافة قسم جديد"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # حفظ القسم الجديد
                    department = form.save()
                    
                    # تسجيل العملية في سجل الأمان
                    AuditLog.objects.create(
                        action_type='DEPARTMENT_ADDED',
                        description=f'تم إضافة قسم جديد: {department.name} ({department.code})',
                        user=request.user,
                        user_ip=get_client_ip(request),
                        is_successful=True
                    )
                    
                    messages.success(
                        request, 
                        f'تم إضافة القسم "{department.name}" بنجاح!'
                    )
                    
                    return redirect('accounts:departments')
                    
            except Exception as e:
                # تسجيل الخطأ
                AuditLog.objects.create(
                    action_type='DEPARTMENT_ADD_FAILED',
                    description=f'فشل في إضافة قسم جديد: {form.cleaned_data.get("name", "غير معروف")} - {str(e)}',
                    user=request.user,
                    user_ip=get_client_ip(request),
                    is_successful=False
                )
                
                messages.error(request, 'حدث خطأ أثناء إضافة القسم. يرجى المحاولة مرة أخرى.')
                
        else:
            # في حالة وجود أخطاء في النموذج
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = DepartmentForm()
    
    # إعداد البيانات المطلوبة للقالب
    departments = Department.objects.filter(is_active=True).order_by('name')
    # المديرين المحتملين - مستوى مشرف فما فوق
    users = User.objects.filter(
        is_active=True, 
        position__level__gte=3
    ).select_related('position', 'department').order_by('arabic_name')
    

    return render(request, 'accounts/add_department.html', {
        'form': form,
        'departments': departments,
        'users': users
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def debug_department_form(request):
    """صفحة تشخيص نموذج القسم"""
    from django.http import HttpResponse
    
    form = DepartmentForm()
    
    html = f"""
    <html dir="rtl">
    <head><title>تشخيص نموذج القسم</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>تشخيص نموذج إضافة القسم</h1>
        
        <h2>إحصائيات:</h2>
        <ul>
            <li>عدد المديرين في النموذج: {form.fields['manager'].queryset.count()}</li>
            <li>عدد الأقسام في النموذج: {form.fields['parent_department'].queryset.count()}</li>
        </ul>
        
        <h2>المديرين المتاحين:</h2>
        <ul>
        """
    
    for manager in form.fields['manager'].queryset:
        html += f"<li>{manager.arabic_name} ({manager.username}) - مستوى: {manager.position.level}</li>"
    
    html += """
        </ul>
        
        <h2>الأقسام المتاحة:</h2>
        <ul>
    """
    
    for dept in form.fields['parent_department'].queryset:
        html += f"<li>{dept.name} ({dept.code})</li>"
    
    html += """
        </ul>
        
        <h2>النموذج الفعلي:</h2>
        <form method="post">
            <div style="margin: 10px 0;">
                <label>مدير القسم:</label><br>
                """ + str(form['manager']) + """
            </div>
            
            <div style="margin: 10px 0;">
                <label>القسم الأعلى:</label><br>
                """ + str(form['parent_department']) + """
            </div>
        </form>
        
        <p><a href="/accounts/departments/add/">العودة إلى الصفحة الأصلية</a></p>
    </body>
    </html>
    """
    
    return HttpResponse(html)

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_department(request, dept_id):
    """تعديل قسم"""
    department = get_object_or_404(Department, id=dept_id)
    return render(request, 'accounts/edit_department.html', {'department': department})

@login_required
@user_passes_test(lambda u: u.is_staff)
def position_list(request):
    """قائمة المناصب"""
    positions = Position.objects.select_related('department').all()
    return render(request, 'accounts/position_list.html', {'positions': positions})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_position(request):
    """إضافة منصب جديد"""
    departments = Department.objects.all()
    return render(request, 'accounts/add_position.html', {'departments': departments})

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_position(request, pos_id):
    """تعديل منصب"""
    position = get_object_or_404(Position, id=pos_id)
    return render(request, 'accounts/edit_position.html', {'position': position})

@login_required
@user_passes_test(lambda u: u.is_staff)
def group_list(request):
    """قائمة المجموعات"""
    groups = UserGroup.objects.all()
    return render(request, 'accounts/group_list.html', {'groups': groups})

@login_required
@user_passes_test(lambda u: u.is_staff)
def group_detail(request, group_id):
    """تفاصيل المجموعة"""
    group = get_object_or_404(UserGroup, id=group_id)
    return render(request, 'accounts/group_detail.html', {'group': group})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_group(request):
    """إضافة مجموعة جديدة"""
    users = User.objects.filter(is_active=True)
    return render(request, 'accounts/add_group.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_group(request, group_id):
    """تعديل مجموعة"""
    group = get_object_or_404(UserGroup, id=group_id)
    return render(request, 'accounts/edit_group.html', {'group': group})

@login_required
def delegation_view(request):
    """عرض التفويضات"""
    return render(request, 'accounts/delegation.html')

@login_required
def create_delegation(request):
    """إنشاء تفويض"""
    return render(request, 'accounts/create_delegation.html')

@login_required
def end_delegation(request, delegation_id):
    """إنهاء تفويض"""
    messages.success(request, 'تم إنهاء التفويض بنجاح.')
    return redirect('accounts:delegation')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    users_count = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    return render(request, 'accounts/admin_dashboard.html', {
        'users_count': users_count,
        'active_users': active_users,
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_users(request):
    users = User.objects.all().select_related('department', 'position')
    return render(request, 'accounts/admin_users.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_add_user(request):
    # منطق إضافة مستخدم جديد (نموذج بسيط)
    return render(request, 'accounts/admin_add_user.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'تم حذف المستخدم بنجاح.')
    return redirect('accounts:admin_users')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'تم {"تفعيل" if user.is_active else "تعطيل"} الحساب.')
    return redirect('accounts:admin_users')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.set_password('bank123456')
    user.require_password_change = True
    user.save()
    messages.success(request, 'تم إعادة تعيين كلمة المرور للمستخدم (bank123456).')
    return redirect('accounts:admin_users')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_activity(request, user_id):
    user = get_object_or_404(User, id=user_id)
    logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:50]
    last_login = UserSession.objects.filter(user=user, is_active=False).order_by('-login_time').first()
    last_logout = UserSession.objects.filter(user=user, is_active=False).order_by('-last_activity').first()
    return render(request, 'accounts/admin_user_activity.html', {
        'profile_user': user,
        'logs': logs,
        'last_login': last_login,
        'last_logout': last_logout,
    })

def admin_login_view(request):
    """تسجيل دخول مدير النظام"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('accounts:admin_dashboard')
        else:
            return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Log admin login attempt
        LoginAttempt.objects.create(
            username=username,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_successful=False,
            failure_reason='Admin login attempt'
        )
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            # التحقق من أن المستخدم مدير
            if not user.is_staff:
                messages.error(request, 'ليس لديك صلاحية الوصول إلى لوحة تحكم المدير.')
                
                # Log unauthorized admin access attempt
                AuditLog.objects.create(
                    action_type='UNAUTHORIZED_ACCESS',
                    description=f'محاولة دخول غير مصرحة للوحة المدير من المستخدم {user.username}',
                    user=user,
                    user_ip=get_client_ip(request),
                    is_successful=False
                )
                return render(request, 'accounts/admin_login.html')
            
            login(request, user)
            
            # Ensure session is created and saved before accessing session_key
            if not request.session.session_key:
                request.session.create()
            request.session.save()
            
            # Create user session
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Update login attempt to successful
            attempt = LoginAttempt.objects.filter(
                username=username,
                ip_address=get_client_ip(request)
            ).last()
            if attempt:
                attempt.is_successful = True
                attempt.save()
            
            # Log successful admin login
            AuditLog.objects.create(
                action_type='ADMIN_LOGIN',
                description=f'تسجيل دخول ناجح للمدير {user.username}',
                user=user,
                user_ip=get_client_ip(request),
                is_successful=True
            )
            
            messages.success(request, f'مرحباً أيها المدير {user.arabic_name or user.username}!')
            return redirect('accounts:admin_dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    
    return render(request, 'accounts/admin_login.html')