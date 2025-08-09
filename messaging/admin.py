from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    MessageCategory, Message, MessageRecipient, 
    MessageAttachment, MessageHistory, DigitalSignature
)


@admin.register(MessageCategory)
class MessageCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'requires_approval', 'default_priority']
    list_filter = ['requires_approval', 'default_priority']
    search_fields = ['name', 'description']
    ordering = ['name']


class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient
    extra = 0
    fields = ['recipient', 'recipient_type', 'read_at', 'is_deleted']
    readonly_fields = ['read_at']


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    fields = ['original_filename', 'file_size', 'mime_type', 'is_encrypted']
    readonly_fields = ['file_size', 'mime_type', 'checksum']


class DigitalSignatureInline(admin.TabularInline):
    model = DigitalSignature
    extra = 0
    fields = ['signer', 'signature_type', 'verification_status', 'signed_at']
    readonly_fields = ['signer', 'signature_type', 'signed_at', 'verification_status']
    
    def has_add_permission(self, request, obj):
        return False  # منع إضافة توقيعات جديدة من لوحة الإدارة


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'sequence_number', 'subject', 'sender', 'category', 
        'priority', 'status', 'created_at', 'digital_signature_count'
    ]
    list_filter = [
        'category', 'priority', 'confidentiality', 'status', 
        'created_at', 'is_encrypted'
    ]
    search_fields = [
        'sequence_number', 'subject', 'body', 'sender__arabic_name',
        'sender__employee_id', 'reference_number', 'account_number'
    ]
    readonly_fields = [
        'message_id', 'sequence_number', 'created_at', 'sent_at',
        'hash_value', 'digital_signature_count'
    ]
    inlines = [MessageRecipientInline, MessageAttachmentInline, DigitalSignatureInline]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('message_id', 'sequence_number', 'subject', 'body')
        }),
        ('الإرسال والاستقبال', {
            'fields': ('sender', 'category', 'priority', 'confidentiality', 'status')
        }),
        ('التوقيت', {
            'fields': ('created_at', 'sent_at', 'expires_at', 'auto_delete_at')
        }),
        ('المرجع والربط', {
            'fields': ('reference_number', 'account_number', 'transaction_reference', 
                      'reply_to', 'forwarded_from')
        }),
        ('الأمان والتشفير', {
            'fields': ('is_encrypted', 'digital_signature', 'hash_value')
        }),
        ('إعدادات التحكم', {
            'fields': ('prevent_forwarding', 'require_read_receipt')
        }),
    )
    
    def digital_signature_count(self, obj):
        count = obj.digital_signatures.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} توقيع</span>',
                count
            )
        return "لا يوجد"
    digital_signature_count.short_description = "التوقيعات الرقمية"


@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = ['message', 'recipient', 'recipient_type', 'read_at', 'is_deleted']
    list_filter = ['recipient_type', 'is_deleted', 'read_at']
    search_fields = [
        'message__sequence_number', 'message__subject', 
        'recipient__arabic_name', 'recipient__employee_id'
    ]
    readonly_fields = ['read_at', 'acknowledged_at']
    ordering = ['-message__created_at']


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'message', 'file_size_formatted', 
        'mime_type', 'is_encrypted', 'uploaded_at'
    ]
    list_filter = ['mime_type', 'is_encrypted', 'uploaded_at']
    search_fields = ['original_filename', 'message__sequence_number']
    readonly_fields = ['file_size', 'mime_type', 'checksum', 'uploaded_at']
    ordering = ['-uploaded_at']
    
    def file_size_formatted(self, obj):
        from django.template.defaultfilters import filesizeformat
        return filesizeformat(obj.file_size)
    file_size_formatted.short_description = "حجم الملف"


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = [
        'signature_id_short', 'signer', 'message_subject', 'signature_type',
        'verification_status', 'signed_at', 'qr_code_preview'
    ]
    list_filter = [
        'signature_type', 'verification_status', 'signed_at', 
        'signer__department'
    ]
    search_fields = [
        'signature_id', 'signer__arabic_name', 'signer__employee_id',
        'message__sequence_number', 'message__subject'
    ]
    readonly_fields = [
        'signature_id', 'hash_value', 'signed_at', 'expires_at',
        'qr_data', 'ip_address', 'user_agent', 'qr_code_preview',
        'verification_link'
    ]
    ordering = ['-signed_at']
    date_hierarchy = 'signed_at'
    
    fieldsets = (
        ('معلومات التوقيع', {
            'fields': ('signature_id', 'message', 'signer', 'signature_type', 'reason')
        }),
        ('حالة التحقق', {
            'fields': ('verification_status', 'signed_at', 'expires_at')
        }),
        ('البيانات التقنية', {
            'fields': ('hash_value', 'qr_data', 'signature_data'),
            'classes': ['collapse']
        }),
        ('معلومات الشبكة', {
            'fields': ('ip_address', 'user_agent', 'location_info'),
            'classes': ['collapse']
        }),
        ('QR Code والتحقق', {
            'fields': ('qr_code_preview', 'verification_link', 'certificate_serial')
        }),
    )
    
    def signature_id_short(self, obj):
        return str(obj.signature_id)[:8] + "..."
    signature_id_short.short_description = "معرف التوقيع"
    
    def message_subject(self, obj):
        return obj.message.subject[:50] + "..." if len(obj.message.subject) > 50 else obj.message.subject
    message_subject.short_description = "موضوع الرسالة"
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.qr_code.url
            )
        return "لا يوجد"
    qr_code_preview.short_description = "معاينة QR"
    
    def verification_link(self, obj):
        if obj.id:
            url = reverse('messaging:verify_signature', args=[obj.signature_id])
            return format_html(
                '<a href="{}" target="_blank">التحقق من التوقيع</a>',
                url
            )
        return "غير متاح"
    verification_link.short_description = "رابط التحقق"
    
    def has_add_permission(self, request):
        return False  # منع إضافة توقيعات جديدة من لوحة الإدارة


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'message', 'action', 'performed_by', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'performed_by__department']
    search_fields = [
        'message__sequence_number', 'performed_by__arabic_name',
        'details', 'ip_address'
    ]
    readonly_fields = ['timestamp', 'ip_address', 'user_agent']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # منع إضافة سجلات تاريخ جديدة
    
    def has_change_permission(self, request, obj=None):
        return False  # منع تعديل السجلات
