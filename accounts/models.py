from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator

class Department(models.Model):
    """نموذج للأقسام في البنك"""
    name = models.CharField(max_length=100, verbose_name="اسم القسم")
    code = models.CharField(max_length=10, unique=True, verbose_name="رمز القسم")
    description = models.TextField(blank=True, verbose_name="الوصف")
    parent_department = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="القسم الأعلى")
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments', verbose_name="مدير القسم")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "القسم"
        verbose_name_plural = "الأقسام"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Position(models.Model):
    """نموذج للمناصب الوظيفية"""
    LEVEL_CHOICES = [
        (1, 'موظف'),
        (2, 'مشرف'),
        (3, 'رئيس قسم'),
        (4, 'مدير'),
        (5, 'مدير عام'),
        (6, 'نائب المدير العام'),
        (7, 'المدير العام'),
    ]
    
    title = models.CharField(max_length=100, verbose_name="المسمى الوظيفي")
    level = models.IntegerField(choices=LEVEL_CHOICES, verbose_name="المستوى الوظيفي")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="القسم")
    permissions_level = models.IntegerField(default=1, verbose_name="مستوى الصلاحيات")
    can_approve_messages = models.BooleanField(default=False, verbose_name="يمكن الموافقة على الرسائل")
    max_approval_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="أقصى مبلغ للموافقة")
    
    class Meta:
        verbose_name = "المنصب"
        verbose_name_plural = "المناصب"
        ordering = ['-level', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.department.name}"

class User(AbstractUser):
    """نموذج مخصص للمستخدمين"""
    employee_id = models.CharField(
        max_length=10, 
        unique=True, 
        validators=[RegexValidator(r'^\d{1,10}$', 'رقم الموظف يجب أن يكون أرقام فقط')],
        verbose_name="رقم الموظف"
    )
    arabic_name = models.CharField(max_length=100, verbose_name="الاسم بالعربية")
    phone = models.CharField(
        max_length=3, 
        validators=[RegexValidator(r'^\d{3}$', 'رقم الهاتف يجب أن يتألف من 3 أرقام فقط')],
        verbose_name="رقم الهاتف"
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name="القسم")
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name="المنصب")
    direct_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المدير المباشر")
    
    # إعدادات الأمان
    is_active_session = models.BooleanField(default=False, verbose_name="جلسة نشطة")
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name="آخر نشاط")
    failed_login_attempts = models.IntegerField(default=0, verbose_name="محاولات الدخول الفاشلة")
    account_locked_until = models.DateTimeField(null=True, blank=True, verbose_name="مقفل حتى")
    require_password_change = models.BooleanField(default=True, verbose_name="يتطلب تغيير كلمة المرور")
    two_factor_enabled = models.BooleanField(default=False, verbose_name="المصادقة الثنائية مفعلة")
    two_factor_secret = models.CharField(max_length=32, blank=True, verbose_name="مفتاح المصادقة الثنائية")
    
    # إعدادات الصلاحيات
    can_send_confidential = models.BooleanField(default=False, verbose_name="يمكن إرسال رسائل سرية")
    can_send_urgent = models.BooleanField(default=False, verbose_name="يمكن إرسال رسائل عاجلة")
    delegate_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_from', verbose_name="مفوض إلى")
    delegation_start_date = models.DateTimeField(null=True, blank=True, verbose_name="بداية التفويض")
    delegation_end_date = models.DateTimeField(null=True, blank=True, verbose_name="نهاية التفويض")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "المستخدم"
        verbose_name_plural = "المستخدمون"
        ordering = ['department', 'position__level', 'arabic_name']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department', 'position']),
            models.Index(fields=['is_active', 'is_staff']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['username', 'is_active']),
            models.Index(fields=['delegation_start_date', 'delegation_end_date']),
        ]
    
    def __str__(self):
        return f"{self.arabic_name} ({self.employee_id})"
    
    def is_account_locked(self):
        """فحص ما إذا كان الحساب مقفل"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def has_delegation_active(self):
        """فحص ما إذا كان التفويض نشط"""
        if self.delegation_start_date and self.delegation_end_date:
            now = timezone.now()
            return self.delegation_start_date <= now <= self.delegation_end_date
        return False
    
    def get_effective_permissions(self):
        """الحصول على الصلاحيات الفعالة (مع التفويض)"""
        if self.has_delegation_active() and self.delegate_to:
            return self.delegate_to.position.permissions_level
        return self.position.permissions_level
    
    def get_unread_messages_count(self):
        """الحصول على عدد الرسائل غير المقروءة"""
        try:
            from messaging.models import MessageRecipient
            return MessageRecipient.objects.filter(
                recipient=self,
                read_at__isnull=True,
                is_deleted=False
            ).count()
        except:
            return 0

class UserGroup(models.Model):
    """نموذج لمجموعات المستخدمين"""
    name = models.CharField(max_length=100, verbose_name="اسم المجموعة")
    description = models.TextField(blank=True, verbose_name="الوصف")
    members = models.ManyToManyField(User, related_name='user_groups', verbose_name="الأعضاء")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups', verbose_name="منشئ المجموعة")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "مجموعة المستخدمين"
        verbose_name_plural = "مجموعات المستخدمين"
        ordering = ['name']
    
    def __str__(self):
        return self.name
