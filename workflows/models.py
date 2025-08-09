from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class ApprovalWorkflow(models.Model):
    """نموذج سير عمل الموافقات"""
    WORKFLOW_TYPES = [
        ('MESSAGE_APPROVAL', 'موافقة رسالة'),
        ('DOCUMENT_APPROVAL', 'موافقة وثيقة'),
        ('TRANSACTION_APPROVAL', 'موافقة معاملة'),
        ('ACCESS_REQUEST', 'طلب صلاحية'),
        ('BUDGET_APPROVAL', 'موافقة ميزانية'),
        ('POLICY_CHANGE', 'تغيير سياسة'),
    ]
    
    workflow_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_type = models.CharField(max_length=30, choices=WORKFLOW_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # إعدادات الموافقة
    requires_sequential_approval = models.BooleanField(default=True, verbose_name="يتطلب موافقة متسلسلة")
    minimum_approvers = models.IntegerField(default=1, verbose_name="الحد الأدنى للموافقين")
    auto_approve_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # الأقسام المعنية
    applicable_departments = models.ManyToManyField('accounts.Department', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "سير عمل الموافقة"
        verbose_name_plural = "سير عمل الموافقات"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_workflow_type_display()}"

class ApprovalRequest(models.Model):
    """طلب موافقة"""
    STATUS_CHOICES = [
        ('PENDING', 'في الانتظار'),
        ('IN_PROGRESS', 'قيد المراجعة'),
        ('APPROVED', 'موافق عليه'),
        ('REJECTED', 'مرفوض'),
        ('CANCELLED', 'ملغى'),
        ('EXPIRED', 'منتهي الصلاحية'),
    ]
    
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.PROTECT)
    
    # طالب الموافقة
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approval_requests')
    
    # الكائن المطلوب الموافقة عليه
    content_type = models.CharField(max_length=50)  # message, document, etc.
    object_id = models.CharField(max_length=50)
    
    # تفاصيل الطلب
    title = models.CharField(max_length=200)
    description = models.TextField()
    justification = models.TextField(blank=True, verbose_name="المبرر")
    
    # المبلغ (إن وجد)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='SAR', blank=True)
    
    # الحالة والأوقات
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # إعدادات الأولوية
    is_urgent = models.BooleanField(default=False)
    priority_level = models.IntegerField(default=3)  # 1-5 scale
    
    class Meta:
        verbose_name = "طلب موافقة"
        verbose_name_plural = "طلبات الموافقة"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class ApprovalStep(models.Model):
    """خطوة موافقة"""
    ACTION_CHOICES = [
        ('APPROVE', 'موافقة'),
        ('REJECT', 'رفض'),
        ('REQUEST_INFO', 'طلب معلومات'),
        ('DELEGATE', 'تفويض'),
        ('SKIP', 'تخطي'),
    ]
    
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='approval_steps')
    step_order = models.IntegerField()
    
    # الموافق
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approval_steps')
    delegated_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_approvals')
    
    # الإجراء
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, null=True, blank=True)
    comments = models.TextField(blank=True)
    
    # الأوقات
    assigned_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    # الحالة
    is_completed = models.BooleanField(default=False)
    is_current_step = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['request', 'step_order']
        ordering = ['step_order']
    
    def __str__(self):
        return f"{self.request.title} - Step {self.step_order} - {self.approver}"

class WorkflowTemplate(models.Model):
    """قوالب سير العمل"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=30, choices=ApprovalWorkflow.WORKFLOW_TYPES)
    
    # الخطوات المحددة مسبقاً
    template_steps = models.JSONField(default=dict)  # يحتوي على تسلسل الموافقات
    
    # الشروط
    conditions = models.JSONField(default=dict)  # شروط تطبيق القالب
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "قالب سير العمل"
        verbose_name_plural = "قوالب سير العمل"
        ordering = ['name']
    
    def __str__(self):
        return self.name
