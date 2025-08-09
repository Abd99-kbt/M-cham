"""
Views for main project
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from messaging.models import Message, MessageRecipient
from workflows.models import ApprovalRequest
from security.models import AuditLog, UserSession

User = get_user_model()

@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية"""
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # إحصائيات الرسائل
    unread_messages = MessageRecipient.objects.filter(
        recipient=user,
        read_at__isnull=True,
        is_deleted=False
    ).count()
    
    total_messages = MessageRecipient.objects.filter(
        recipient=user,
        is_deleted=False
    ).count()
    
    sent_messages = Message.objects.filter(
        sender=user,
        status__in=['SENT', 'READ', 'REPLIED']
    ).count()
    
    # إحصائيات الموافقات
    pending_approvals = ApprovalRequest.objects.filter(
        approval_steps__approver=user,
        approval_steps__is_current_step=True,
        approval_steps__is_completed=False
    ).count()
    
    my_requests = ApprovalRequest.objects.filter(
        requester=user,
        status__in=['PENDING', 'IN_PROGRESS']
    ).count()
    
    # الرسائل الحديثة
    recent_messages = Message.objects.filter(
        messagerecipient__recipient=user,
        messagerecipient__is_deleted=False
    ).select_related('sender', 'category').order_by('-created_at')[:5]
    
    # الموافقات المعلقة
    recent_approvals = ApprovalRequest.objects.filter(
        approval_steps__approver=user,
        approval_steps__is_current_step=True,
        approval_steps__is_completed=False
    ).select_related('requester', 'workflow')[:5]
    
    # إحصائيات النشاط الأسبوعي
    weekly_activity = AuditLog.objects.filter(
        user=user,
        timestamp__date__gte=week_ago
    ).values('timestamp__date').annotate(
        count=Count('id')
    ).order_by('timestamp__date')
    
    # المستخدمون النشطون
    active_users = UserSession.objects.filter(
        is_active=True,
        last_activity__gte=timezone.now() - timedelta(minutes=30)
    ).count()
    
    context = {
        'user': user,
        'stats': {
            'unread_messages': unread_messages,
            'total_messages': total_messages,
            'sent_messages': sent_messages,
            'pending_approvals': pending_approvals,
            'my_requests': my_requests,
            'active_users': active_users,
        },
        'recent_messages': recent_messages,
        'recent_approvals': recent_approvals,
        'weekly_activity': weekly_activity,
    }
    
    return render(request, 'dashboard.html', context)

def home(request):
    """الصفحة الرئيسية"""
    if request.user.is_authenticated:
        # التوجيه حسب نوع المستخدم
        if request.user.is_superuser or (request.user.position and request.user.position.level >= 5):
            return redirect('accounts:admin_dashboard')
        return redirect('dashboard')
    return redirect('accounts:login')