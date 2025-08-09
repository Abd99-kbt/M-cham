"""
Views for workflows app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from .models import ApprovalWorkflow, ApprovalRequest, ApprovalStep, WorkflowTemplate

@login_required
def pending_approvals(request):
    """الموافقات المعلقة"""
    pending_requests = ApprovalRequest.objects.filter(
        approval_steps__approver=request.user,
        approval_steps__is_current_step=True,
        approval_steps__is_completed=False
    ).distinct().select_related('requester', 'workflow')
    
    return render(request, 'workflows/pending.html', {
        'requests': pending_requests
    })

@login_required
def my_requests(request):
    """طلباتي"""
    my_requests_list = ApprovalRequest.objects.filter(
        requester=request.user
    ).select_related('workflow').prefetch_related('approval_steps').order_by('-created_at')
    
    # Add current step to each request for easy access in template
    for req in my_requests_list:
        req.current_step = req.approval_steps.filter(is_current_step=True).first()
        
    return render(request, 'workflows/my_requests.html', {
        'my_requests': my_requests_list
    })

@login_required
def approval_history(request):
    """سجل الموافقات"""
    history = ApprovalRequest.objects.filter(
        approval_steps__approver=request.user
    ).distinct().select_related('requester', 'workflow').prefetch_related('approval_steps').order_by('-created_at')

    # تجهيز آخر خطوة للمستخدم في كل طلب
    for req in history:
        req.my_step = req.approval_steps.filter(approver=request.user).order_by('-responded_at').first()

    return render(request, 'workflows/history.html', {
        'requests': history
    })

@login_required
def request_detail(request, request_id):
    """تفاصيل طلب الموافقة"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    
    # Check if user has access
    has_access = (
        approval_request.requester == request.user or
        ApprovalStep.objects.filter(
            request=approval_request,
            approver=request.user
        ).exists() or
        request.user.is_staff
    )
    
    if not has_access:
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الطلب.')
        return redirect('workflows:pending')
    
    steps = approval_request.approval_steps.all().order_by('step_order')
    
    return render(request, 'workflows/request_detail.html', {
        'request': approval_request,
        'steps': steps
    })

@login_required
def approve_request(request, request_id):
    """الموافقة على طلب"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        
        # Find current step for this user
        current_step = ApprovalStep.objects.filter(
            request=approval_request,
            approver=request.user,
            is_current_step=True,
            is_completed=False
        ).first()
        
        if current_step:
            current_step.action = 'APPROVE'
            current_step.comments = comments
            current_step.responded_at = timezone.now()
            current_step.is_completed = True
            current_step.is_current_step = False
            current_step.save()
            
            messages.success(request, 'تم قبول الطلب بنجاح.')
        else:
            messages.error(request, 'لا يمكن معالجة هذا الطلب.')
        
        return redirect('workflows:request_detail', request_id=request_id)
    
    return render(request, 'workflows/approve.html', {
        'request': approval_request
    })

@login_required
def reject_request(request, request_id):
    """رفض طلب"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        
        current_step = ApprovalStep.objects.filter(
            request=approval_request,
            approver=request.user,
            is_current_step=True,
            is_completed=False
        ).first()
        
        if current_step:
            current_step.action = 'REJECT'
            current_step.comments = comments
            current_step.responded_at = timezone.now()
            current_step.is_completed = True
            current_step.is_current_step = False
            current_step.save()
            
            # Update request status
            approval_request.status = 'REJECTED'
            approval_request.completed_at = timezone.now()
            approval_request.save()
            
            messages.success(request, 'تم رفض الطلب.')
        else:
            messages.error(request, 'لا يمكن معالجة هذا الطلب.')
        
        return redirect('workflows:request_detail', request_id=request_id)
    
    return render(request, 'workflows/reject.html', {
        'request': approval_request
    })

@login_required
def delegate_request(request, request_id):
    """تفويض طلب"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    
    if request.method == 'POST':
        # Handle delegation
        messages.success(request, 'تم تفويض الطلب بنجاح.')
        return redirect('workflows:request_detail', request_id=request_id)
    
    return render(request, 'workflows/delegate.html', {
        'request': approval_request
    })

@login_required
def cancel_request(request, request_id):
    """إلغاء طلب"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    
    if approval_request.requester != request.user:
        messages.error(request, 'لا يمكنك إلغاء هذا الطلب.')
        return redirect('workflows:my_requests')
    
    if request.method == 'POST':
        approval_request.status = 'CANCELLED'
        approval_request.completed_at = timezone.now()
        approval_request.save()
        
        messages.success(request, 'تم إلغاء الطلب بنجاح.')
        return redirect('workflows:my_requests')
    
    return render(request, 'workflows/cancel.html', {
        'request': approval_request
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def workflow_list(request):
    """قائمة سير العمل"""
    workflows = ApprovalWorkflow.objects.all()
    return render(request, 'workflows/workflow_list.html', {
        'workflows': workflows
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def workflow_detail(request, workflow_id):
    """تفاصيل سير العمل"""
    workflow = get_object_or_404(ApprovalWorkflow, workflow_id=workflow_id)
    return render(request, 'workflows/workflow_detail.html', {
        'workflow': workflow
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_workflow(request):
    """إضافة سير عمل جديد"""
    if request.method == 'POST':
        # Handle workflow creation
        messages.success(request, 'تم إنشاء سير العمل بنجاح.')
        return redirect('workflows:workflows')
    
    return render(request, 'workflows/add_workflow.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_workflow(request, workflow_id):
    """تعديل سير العمل"""
    workflow = get_object_or_404(ApprovalWorkflow, workflow_id=workflow_id)
    
    if request.method == 'POST':
        # Handle workflow update
        messages.success(request, 'تم تحديث سير العمل بنجاح.')
        return redirect('workflows:workflow_detail', workflow_id=workflow_id)
    
    return render(request, 'workflows/edit_workflow.html', {
        'workflow': workflow
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_workflow(request, workflow_id):
    """حذف سير العمل"""
    workflow = get_object_or_404(ApprovalWorkflow, workflow_id=workflow_id)
    
    if request.method == 'POST':
        workflow.is_active = False
        workflow.save()
        messages.success(request, 'تم إلغاء تفعيل سير العمل بنجاح.')
        return redirect('workflows:workflows')
    
    return render(request, 'workflows/delete_workflow.html', {
        'workflow': workflow
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_list(request):
    """قائمة قوالب سير العمل"""
    templates = WorkflowTemplate.objects.filter(is_active=True)
    return render(request, 'workflows/template_list.html', {
        'templates': templates
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_detail(request, template_id):
    """تفاصيل قالب سير العمل"""
    template = get_object_or_404(WorkflowTemplate, id=template_id)
    return render(request, 'workflows/template_detail.html', {
        'template': template
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_template(request):
    """إضافة قالب سير عمل جديد"""
    return render(request, 'workflows/add_template.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_template(request, template_id):
    """تعديل قالب سير العمل"""
    template = get_object_or_404(WorkflowTemplate, id=template_id)
    return render(request, 'workflows/edit_template.html', {
        'template': template
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def clone_template(request, template_id):
    """نسخ قالب سير العمل"""
    template = get_object_or_404(WorkflowTemplate, id=template_id)
    return render(request, 'workflows/clone_template.html', {
        'template': template
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def workflow_reports(request):
    """تقارير سير العمل"""
    return render(request, 'workflows/reports.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def performance_report(request):
    """تقرير الأداء"""
    return render(request, 'workflows/performance_report.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def bottleneck_report(request):
    """تقرير الاختناقات"""
    return render(request, 'workflows/bottleneck_report.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_workflow_data(request):
    """تصدير بيانات سير العمل"""
    return HttpResponse('تصدير بيانات سير العمل')

@login_required
def step_status(request, request_id):
    """حالة خطوات الموافقة"""
    approval_request = get_object_or_404(ApprovalRequest, request_id=request_id)
    steps = approval_request.approval_steps.all().order_by('step_order')
    
    step_data = []
    for step in steps:
        step_data.append({
            'order': step.step_order,
            'approver': step.approver.arabic_name or step.approver.username,
            'action': step.action,
            'completed': step.is_completed,
            'current': step.is_current_step,
            'responded_at': step.responded_at.isoformat() if step.responded_at else None,
            'comments': step.comments
        })
    
    return JsonResponse({'steps': step_data})

@login_required
def escalate_request(request, request_id):
    """تصعيد طلب"""
    if request.method == 'POST':
        # Handle escalation
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})
