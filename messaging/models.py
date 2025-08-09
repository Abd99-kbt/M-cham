from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.urls import reverse
import uuid
import os
import json
import hashlib
from datetime import datetime

class MessageCategory(models.Model):
    """تصنيف الرسائل"""
    CATEGORY_CHOICES = [
        ('CREDIT', 'ائتمان'),
        ('TREASURY', 'خزينة'),
        ('OPERATIONS', 'عمليات'),
        ('ADMIN', 'إدارية'),
        ('HR', 'موارد بشرية'),
        ('IT', 'تقنية المعلومات'),
        ('COMPLIANCE', 'امتثال'),
        ('AUDIT', 'مراجعة'),
        ('CUSTOMER', 'خدمة العملاء'),
        ('OTHER', 'أخرى'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, verbose_name="الوصف")
    requires_approval = models.BooleanField(default=False, verbose_name="يتطلب موافقة")
    default_priority = models.CharField(max_length=20, default='NORMAL', verbose_name="الأولوية الافتراضية")
    
    class Meta:
        verbose_name = "تصنيف الرسالة"
        verbose_name_plural = "تصنيفات الرسائل"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()

class Message(models.Model):
    """نموذج الرسائل الأساسي"""
    PRIORITY_CHOICES = [
        ('LOW', 'عادية'),
        ('NORMAL', 'متوسطة'),
        ('HIGH', 'مهمة'),
        ('URGENT', 'عاجلة'),
        ('CRITICAL', 'حرجة'),
    ]
    
    CONFIDENTIALITY_CHOICES = [
        ('PUBLIC', 'عامة'),
        ('INTERNAL', 'داخلية'),
        ('CONFIDENTIAL', 'سرية'),
        ('TOP_SECRET', 'سرية للغاية'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('SENT', 'مرسلة'),
        ('RECEIVED', 'مستلمة'),
        ('READ', 'مقروءة'),
        ('REPLIED', 'مجاب عليها'),
        ('FORWARDED', 'محولة'),
        ('ARCHIVED', 'مؤرشفة'),
        ('DELETED', 'محذوفة'),
    ]
    
    # معرف فريد للرسالة
    message_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="معرف الرسالة")
    
    # الترقيم التسلسلي
    sequence_number = models.CharField(max_length=20, unique=True, verbose_name="الرقم التسلسلي")
    
    # الأساسيات
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    body = models.TextField(verbose_name="نص الرسالة")
    
    # المرسل والمستقبل
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sent_messages', verbose_name="المرسل")
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, through='MessageRecipient', related_name='received_messages', verbose_name="المستقبلون")
    
    # التصنيف والأولوية
    category = models.ForeignKey(MessageCategory, on_delete=models.PROTECT, verbose_name="التصنيف")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL', verbose_name="الأولوية")
    confidentiality = models.CharField(max_length=20, choices=CONFIDENTIALITY_CHOICES, default='INTERNAL', verbose_name="مستوى السرية")
    
    # الحالة والتوقيت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإرسال")
    
    # المرجع والربط
    reference_number = models.CharField(max_length=50, blank=True, verbose_name="رقم المرجع")
    account_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الحساب")
    transaction_reference = models.CharField(max_length=50, blank=True, verbose_name="مرجع المعاملة")
    
    # الرد والتحويل
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name="رد على")
    forwarded_from = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='forwards', verbose_name="محول من")
    
    # الأمان والتشفير
    is_encrypted = models.BooleanField(default=True, verbose_name="مشفرة")
    digital_signature = models.TextField(blank=True, verbose_name="التوقيع الرقمي")
    hash_value = models.CharField(max_length=64, blank=True, verbose_name="قيمة التشفير")
    
    # انتهاء الصلاحية والأرشفة
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهاء الصلاحية")
    auto_delete_at = models.DateTimeField(null=True, blank=True, verbose_name="الحذف التلقائي")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الأرشفة")
    
    # إعدادات التحكم
    prevent_forwarding = models.BooleanField(default=False, verbose_name="منع التحويل")
    require_read_receipt = models.BooleanField(default=False, verbose_name="يتطلب إيصال قراءة")
    
    class Meta:
        verbose_name = "الرسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['account_number']),
        ]
    
    def __str__(self):
        return f"{self.sequence_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.sequence_number:
            # إنشاء رقم تسلسلي
            year = timezone.now().year
            category_code = self.category.name[:3] if self.category else 'GEN'
            count = Message.objects.filter(created_at__year=year).count() + 1
            self.sequence_number = f"{year}-{category_code}-{count:05d}"
        super().save(*args, **kwargs)

class MessageRecipient(models.Model):
    """نموذج وسطي لربط الرسائل بالمستقبلين"""
    RECIPIENT_TYPE_CHOICES = [
        ('TO', 'إلى'),
        ('CC', 'نسخة'),
        ('BCC', 'نسخة مخفية'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="الرسالة")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="المستقبل")
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_TYPE_CHOICES, default='TO', verbose_name="نوع المستقبل")
    
    # حالة القراءة
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ القراءة")
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإقرار")
    
    # الإعدادات الخاصة
    is_deleted = models.BooleanField(default=False, verbose_name="محذوفة")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    
    class Meta:
        unique_together = ['message', 'recipient']
        verbose_name = "مستقبل الرسالة"
        verbose_name_plural = "مستقبلو الرسائل"
    
    def mark_as_read(self):
        """تعليم الرسالة كمقروءة"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save()

def message_attachment_path(instance, filename):
    """مسار حفظ المرفقات"""
    return f'messages/{instance.message.message_id}/attachments/{filename}'

class MessageAttachment(models.Model):
    """مرفقات الرسائل"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', verbose_name="الرسالة")
    file = models.FileField(
        upload_to=message_attachment_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png'])],
        verbose_name="الملف"
    )
    original_filename = models.CharField(max_length=255, verbose_name="اسم الملف الأصلي")
    file_size = models.BigIntegerField(verbose_name="حجم الملف")
    mime_type = models.CharField(max_length=100, verbose_name="نوع الملف")
    
    # الأمان
    is_encrypted = models.BooleanField(default=True, verbose_name="مشفر")
    checksum = models.CharField(max_length=64, verbose_name="المجموع التحققي")
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    
    class Meta:
        verbose_name = "مرفق الرسالة"
        verbose_name_plural = "مرفقات الرسائل"
    
    def __str__(self):
        return self.original_filename
    
    def delete(self, *args, **kwargs):
        # حذف الملف من النظام
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

class MessageHistory(models.Model):
    """تاريخ وسجل الرسائل"""
    ACTION_CHOICES = [
        ('CREATED', 'إنشاء'),
        ('SENT', 'إرسال'),
        ('READ', 'قراءة'),
        ('REPLIED', 'رد'),
        ('FORWARDED', 'تحويل'),
        ('ARCHIVED', 'أرشفة'),
        ('DELETED', 'حذف'),
        ('MODIFIED', 'تعديل'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='history', verbose_name="الرسالة")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="الإجراء")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="نُفذ بواسطة")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")
    details = models.TextField(blank=True, verbose_name="التفاصيل")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, verbose_name="معلومات المتصفح")
    
    class Meta:
        verbose_name = "تاريخ الرسالة"
        verbose_name_plural = "تاريخ الرسائل"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.message.sequence_number} - {self.get_action_display()} - {self.performed_by}"


def signature_qr_path(instance, filename):
    """مسار حفظ صور QR للتوقيع الرقمي"""
    return f'signatures/{instance.signature_id}/qr/{filename}'


class DigitalSignature(models.Model):
    """نموذج التوقيع الرقمي مع QR Code"""
    
    SIGNATURE_TYPE_CHOICES = [
        ('APPROVAL', 'موافقة'),
        ('REPLY', 'رد'),
        ('FORWARD', 'تحويل'),
        ('ACKNOWLEDGEMENT', 'إقرار'),
        ('REJECTION', 'رفض'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('VALID', 'صالح'),
        ('EXPIRED', 'منتهي الصلاحية'),
        ('REVOKED', 'ملغي'),
        ('INVALID', 'غير صالح'),
    ]
    
    # معرف فريد للتوقيع
    signature_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="معرف التوقيع")
    
    # ربط التوقيع بالرسالة والمستخدم
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='digital_signatures', verbose_name="الرسالة")
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="الموقع")
    
    # نوع التوقيع والسبب
    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPE_CHOICES, verbose_name="نوع التوقيع")
    reason = models.TextField(blank=True, verbose_name="سبب التوقيع")
    
    # معلومات التوقيع
    signature_data = models.JSONField(verbose_name="بيانات التوقيع")  # يحتوي على تفاصيل المستخدم عند التوقيع
    hash_value = models.CharField(max_length=64, verbose_name="قيمة التشفير")  # SHA-256 hash
    
    # QR Code
    qr_code = models.ImageField(upload_to=signature_qr_path, verbose_name="رمز QR")
    qr_data = models.TextField(verbose_name="بيانات QR")  # البيانات المشفرة في QR
    
    # معلومات الشبكة والأمان
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    user_agent = models.TextField(verbose_name="معلومات المتصفح")
    location_info = models.JSONField(blank=True, null=True, verbose_name="معلومات الموقع")
    
    # التوقيت والصلاحية
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت التوقيع")
    expires_at = models.DateTimeField(verbose_name="انتهاء الصلاحية")
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='VALID', verbose_name="حالة التحقق")
    
    # معلومات إضافية للتحقق
    certificate_serial = models.CharField(max_length=50, blank=True, verbose_name="رقم الشهادة")
    verification_url = models.URLField(blank=True, verbose_name="رابط التحقق")
    
    class Meta:
        verbose_name = "التوقيع الرقمي"
        verbose_name_plural = "التوقيعات الرقمية"
        ordering = ['-signed_at']
        indexes = [
            models.Index(fields=['signature_id']),
            models.Index(fields=['message', 'signer']),
            models.Index(fields=['verification_status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"توقيع {self.signer.arabic_name} - {self.get_signature_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.hash_value:
            self.hash_value = self.generate_signature_hash()
        if not self.expires_at:
            # تعيين انتهاء الصلاحية بعد سنة واحدة
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=365)
        super().save(*args, **kwargs)
    
    def generate_signature_hash(self):
        """إنشاء hash للتوقيع"""
        signature_string = f"{self.signature_id}{self.message.message_id}{self.signer.employee_id}{timezone.now().isoformat()}"
        return hashlib.sha256(signature_string.encode()).hexdigest()
    
    def generate_signature_data(self):
        """إنشاء بيانات التوقيع الكاملة"""
        return {
            'signature_id': str(self.signature_id),
            'signer_info': {
                'employee_id': self.signer.employee_id,
                'arabic_name': self.signer.arabic_name,
                'english_name': f"{self.signer.first_name} {self.signer.last_name}",
                'position': self.signer.position.title,
                'department': self.signer.department.name,
                'phone': self.signer.phone,
                'email': self.signer.email,
            },
            'message_info': {
                'message_id': str(self.message.message_id),
                'sequence_number': self.message.sequence_number,
                'subject': self.message.subject,
                'category': self.message.category.get_name_display(),
            },
            'signature_details': {
                'type': self.get_signature_type_display(),
                'reason': self.reason,
                'signed_at': self.signed_at.isoformat() if self.signed_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'hash': self.hash_value,
            },
            'verification': {
                'status': self.get_verification_status_display(),
                'url': self.get_verification_url(),
                'certificate_serial': self.certificate_serial,
            }
        }
    
    def get_verification_url(self):
        """الحصول على رابط التحقق من التوقيع"""
        if hasattr(self, 'id') and self.id:
            return f"{settings.SITE_URL}/messaging/verify-signature/{self.signature_id}/"
        return ""
    
    def is_valid(self):
        """فحص صحة التوقيع"""
        if self.verification_status != 'VALID':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.verification_status = 'EXPIRED'
            self.save()
            return False
        return True
    
    def verify_hash(self):
        """التحقق من صحة الـ hash"""
        expected_hash = self.generate_signature_hash()
        return self.hash_value == expected_hash
    
    def get_qr_display_data(self):
        """الحصول على البيانات المختصرة لعرضها في QR"""
        return {
            'sig_id': str(self.signature_id)[:8],  # أول 8 أحرف من معرف التوقيع
            'signer': self.signer.arabic_name,
            'employee_id': self.signer.employee_id,
            'position': self.signer.position.title,
            'department': self.signer.department.name,
            'signed_at': self.signed_at.strftime('%Y-%m-%d %H:%M') if self.signed_at else '',
            'verify_url': self.get_verification_url(),
        }
