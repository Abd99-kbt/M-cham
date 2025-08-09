from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class AuditLog(models.Model):
    """سجل تدقيق العمليات"""
    ACTION_TYPES = [
        ('LOGIN', 'تسجيل دخول'),
        ('LOGOUT', 'تسجيل خروج'),
        ('ADMIN_LOGIN', 'تسجيل دخول المدير'),
        ('ADMIN_LOGOUT', 'تسجيل خروج المدير'),
        ('UNAUTHORIZED_ACCESS', 'محاولة وصول غير مصرح'),
        ('MESSAGE_SEND', 'إرسال رسالة'),
        ('MESSAGE_READ', 'قراءة رسالة'),
        ('MESSAGE_DELETE', 'حذف رسالة'),
        ('FILE_UPLOAD', 'رفع ملف'),
        ('FILE_DOWNLOAD', 'تحميل ملف'),
        ('ADMIN_ACTION', 'إجراء إداري'),
        ('SECURITY_VIOLATION', 'مخالفة أمنية'),
        ('FAILED_LOGIN', 'فشل تسجيل دخول'),
    ]
    
    operation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    user_ip = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['user_ip', '-timestamp']),
            models.Index(fields=['is_successful', '-timestamp']),
            models.Index(fields=['-timestamp']),  # للترتيب العام
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.user}"

class UserSession(models.Model):
    """جلسات المستخدمين النشطة"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active', '-last_activity']),
            models.Index(fields=['ip_address', '-login_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"

class LoginAttempt(models.Model):
    """محاولات تسجيل الدخول"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    is_successful = models.BooleanField()
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField()
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['is_successful', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        status = "نجح" if self.is_successful else "فشل"
        return f"{self.username} - {status}"
