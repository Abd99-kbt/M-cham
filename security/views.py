"""
Views for security app
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import AuditLog, UserSession, LoginAttempt

@login_required
@user_passes_test(lambda u: u.is_staff)
def audit_logs(request):
    """سجل التدقيق"""
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:100]
    return render(request, 'security/audit_logs.html', {'logs': logs})

@login_required
@user_passes_test(lambda u: u.is_staff)
def audit_log_detail(request, log_id):
    """تفاصيل سجل التدقيق"""
    log = get_object_or_404(AuditLog, operation_id=log_id)
    return render(request, 'security/audit_log_detail.html', {'log': log})

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_audit_logs(request):
    """تصدير سجل التدقيق"""
    return HttpResponse('تصدير سجل التدقيق')

@login_required
@user_passes_test(lambda u: u.is_staff)
def active_sessions(request):
    """الجلسات النشطة"""
    sessions = UserSession.objects.filter(
        is_active=True
    ).select_related('user').order_by('-login_time')
    return render(request, 'security/active_sessions.html', {'sessions': sessions})

@login_required
def my_sessions(request):
    """جلساتي"""
    sessions = UserSession.objects.filter(
        user=request.user
    ).order_by('-login_time')
    return render(request, 'security/my_sessions.html', {'sessions': sessions})

@login_required
@user_passes_test(lambda u: u.is_staff)
def terminate_session(request, session_id):
    """إنهاء جلسة"""
    session = get_object_or_404(UserSession, id=session_id)
    session.is_active = False
    session.logout_time = timezone.now()
    session.forced_logout = True
    session.save()
    return JsonResponse({'success': True})

@login_required
@user_passes_test(lambda u: u.is_staff)
def login_attempts(request):
    """محاولات تسجيل الدخول"""
    attempts = LoginAttempt.objects.order_by('-timestamp')[:100]
    return render(request, 'security/login_attempts.html', {'attempts': attempts})

@login_required
@user_passes_test(lambda u: u.is_staff)
def failed_login_attempts(request):
    """محاولات الدخول الفاشلة"""
    failed_attempts = LoginAttempt.objects.filter(
        is_successful=False
    ).order_by('-timestamp')[:100]
    return render(request, 'security/failed_attempts.html', {'attempts': failed_attempts})

@login_required
@user_passes_test(lambda u: u.is_staff)
def security_reports(request):
    """تقارير الأمان"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # إحصائيات
    stats = {
        'total_logins_today': LoginAttempt.objects.filter(
            timestamp__date=today, is_successful=True
        ).count(),
        'failed_logins_today': LoginAttempt.objects.filter(
            timestamp__date=today, is_successful=False
        ).count(),
        'active_sessions': UserSession.objects.filter(is_active=True).count(),
        'audit_logs_week': AuditLog.objects.filter(
            timestamp__date__gte=week_ago
        ).count(),
    }
    
    return render(request, 'security/reports.html', {'stats': stats})

@login_required
@user_passes_test(lambda u: u.is_staff)
def daily_security_report(request):
    """التقرير الأمني اليومي"""
    return render(request, 'security/daily_report.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def weekly_security_report(request):
    """التقرير الأمني الأسبوعي"""
    return render(request, 'security/weekly_report.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def monthly_security_report(request):
    """التقرير الأمني الشهري"""
    return render(request, 'security/monthly_report.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def security_settings(request):
    """إعدادات الأمان"""
    return render(request, 'security/settings.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def password_policy(request):
    """سياسة كلمات المرور"""
    return render(request, 'security/password_policy.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def session_config(request):
    """إعدادات الجلسات"""
    return render(request, 'security/session_config.html')

@login_required
def setup_2fa(request):
    """إعداد المصادقة الثنائية"""
    return render(request, 'security/setup_2fa.html')

@login_required
def verify_2fa(request):
    """التحقق من المصادقة الثنائية"""
    return render(request, 'security/verify_2fa.html')

@login_required
def disable_2fa(request):
    """إلغاء المصادقة الثنائية"""
    return render(request, 'security/disable_2fa.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def security_incidents(request):
    """الحوادث الأمنية"""
    return render(request, 'security/incidents.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_incident(request):
    """إضافة حادث أمني"""
    return render(request, 'security/add_incident.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def incident_detail(request, incident_id):
    """تفاصيل الحادث الأمني"""
    return render(request, 'security/incident_detail.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def update_incident(request, incident_id):
    """تحديث الحادث الأمني"""
    return render(request, 'security/update_incident.html')
