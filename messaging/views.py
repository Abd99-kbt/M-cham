"""
Views for messaging app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Prefetch, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Message, MessageRecipient, MessageCategory, MessageAttachment, DigitalSignature
from .utils import sanitize_message_content, validate_content_length, is_content_safe
from .signature_utils import create_digital_signature, verify_signature
from security.models import AuditLog

@login_required
def inbox(request):
    """صندوق الوارد"""
    message_recipients = MessageRecipient.objects.filter(
        recipient=request.user,
        is_deleted=False
    ).select_related('message__sender', 'message__category').order_by('-message__created_at')
    
    # تحسين عدد العناصر للأداء
    items_per_page = int(request.GET.get('per_page', 15))  # تقليل العدد الافتراضي
    if items_per_page > 50:  # حد أقصى للأمان
        items_per_page = 50
        
    paginator = Paginator(message_recipients, items_per_page)
    page_number = request.GET.get('page')
    message_recipients = paginator.get_page(page_number)
    
    return render(request, 'messaging/inbox.html', {
        'message_recipients': message_recipients
    })

@login_required
def sent_messages(request):
    """الرسائل المرسلة"""
    messages_sent = Message.objects.filter(
        sender=request.user
    ).select_related('category').order_by('-created_at')
    
    # تحسين عدد العناصر للأداء
    items_per_page = int(request.GET.get('per_page', 15))
    if items_per_page > 50:
        items_per_page = 50
        
    paginator = Paginator(messages_sent, items_per_page)
    page_number = request.GET.get('page')
    messages_sent = paginator.get_page(page_number)
    
    return render(request, 'messaging/sent.html', {
        'messages': messages_sent
    })

@login_required
def drafts(request):
    """المسودات"""
    draft_messages = Message.objects.filter(
        sender=request.user,
        status='DRAFT'
    ).select_related('category').order_by('-created_at')
    
    # إضافة التصفح للأداء
    paginator = Paginator(draft_messages, 20)
    page_number = request.GET.get('page')
    draft_messages = paginator.get_page(page_number)
    
    return render(request, 'messaging/drafts.html', {
        'messages': draft_messages
    })

@login_required
def archive(request):
    """الأرشيف"""
    # البحث في الرسائل المؤرشفة
    search_query = request.GET.get('search', '')
    period = request.GET.get('period', '')
    message_type = request.GET.get('type', '')
    
    # الرسائل المؤرشفة للمستخدم
    archived_messages = Message.objects.filter(
        Q(sender=request.user) | Q(messagerecipient__recipient=request.user),
        archived_at__isnull=False
    ).select_related('sender', 'category').prefetch_related('messagerecipient_set__recipient').distinct()
    
    # تطبيق الفلاتر
    if search_query:
        archived_messages = archived_messages.filter(
            Q(subject__icontains=search_query) | 
            Q(body__icontains=search_query) |
            Q(sender__arabic_name__icontains=search_query)
        )
    
    if period:
        from datetime import datetime, timedelta
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        archived_messages = archived_messages.filter(archived_at__gte=start_date)
    
    if message_type == 'sent':
        archived_messages = archived_messages.filter(sender=request.user)
    elif message_type == 'received':
        archived_messages = archived_messages.filter(messagerecipient__recipient=request.user)
    
    # ترتيب حسب تاريخ الأرشفة ثم تاريخ الإرسال
    archived_messages = archived_messages.order_by('-archived_at', '-sent_at', '-created_at')
    
    # إحصائيات الأرشيف
    total_archived = archived_messages.count()
    archived_this_month = archived_messages.filter(
        archived_at__month=timezone.now().month,
        archived_at__year=timezone.now().year
    ).count()
    sent_archived = archived_messages.filter(sender=request.user).count()
    received_archived = archived_messages.exclude(sender=request.user).count()
    
    # التصفح للأداء
    items_per_page = int(request.GET.get('per_page', 15))
    if items_per_page > 50:
        items_per_page = 50
        
    paginator = Paginator(archived_messages, items_per_page)
    page_number = request.GET.get('page')
    archived_messages = paginator.get_page(page_number)
    
    return render(request, 'messaging/archive.html', {
        'message_recipients': archived_messages,
        'search_query': search_query,
        'period': period,
        'message_type': message_type,
        'stats': {
            'total': total_archived,
            'this_month': archived_this_month,
            'sent': sent_archived,
            'received': received_archived,
        }
    })

@login_required
def compose_message(request):
    """إنشاء رسالة جديدة"""
    if request.method == 'POST':
        try:
            # استخراج البيانات من النموذج
            subject_raw = request.POST.get('subject', '').strip()
            body_raw = request.POST.get('body', '').strip()
            category_id = request.POST.get('category')
            priority = request.POST.get('priority', 'NORMAL')
            confidentiality = request.POST.get('confidentiality', 'INTERNAL')
            recipients_ids = request.POST.getlist('recipients')
            
            # التحقق من البيانات المطلوبة
            if not subject_raw or not body_raw or not recipients_ids:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
                return redirect('messaging:compose')
            
            # فحص أمان المحتوى
            is_safe, safety_issues = is_content_safe(body_raw)
            if not is_safe:
                messages.error(request, f'المحتوى غير آمن: {", ".join(safety_issues)}')
                return redirect('messaging:compose')
            
            # تنظيف المحتوى من ناحية الأمان
            subject, body = sanitize_message_content(subject_raw, body_raw)
            
            # التحقق من طول المحتوى بعد التنظيف
            if not validate_content_length(body):
                messages.error(request, 'نص الرسالة طويل جداً. الحد الأقصى 5000 حرف.')
                return redirect('messaging:compose')
            
            # الحصول على التصنيف
            try:
                category = MessageCategory.objects.get(id=category_id)
            except MessageCategory.DoesNotExist:
                category = MessageCategory.objects.first()
            
            # إنشاء الرسالة
            message = Message.objects.create(
                subject=subject,
                body=body,
                sender=request.user,
                category=category,
                priority=priority,
                confidentiality=confidentiality,
                status='SENT',
                sent_at=timezone.now()
            )
            
            # إضافة المستقبلين
            from accounts.models import User
            for recipient_id in recipients_ids:
                try:
                    recipient_user = User.objects.get(id=recipient_id)
                    MessageRecipient.objects.create(
                        message=message,
                        recipient=recipient_user,
                        recipient_type='TO'
                    )
                except User.DoesNotExist:
                    continue
            
            # معالجة المرفقات إذا وجدت
            attachments = request.FILES.getlist('attachments')
            for attachment_file in attachments:
                if attachment_file:
                    MessageAttachment.objects.create(
                        message=message,
                        file=attachment_file,
                        original_filename=attachment_file.name,
                        file_size=attachment_file.size,
                        mime_type=attachment_file.content_type or 'application/octet-stream'
                    )
            
            # تسجيل العملية في سجل الأمان
            from security.models import AuditLog
            AuditLog.objects.create(
                action_type='MESSAGE_SEND',
                description=f'إرسال رسالة: {subject}',
                user=request.user,
                user_ip=request.META.get('REMOTE_ADDR'),
                is_successful=True
            )
            
            messages.success(request, f'تم إرسال الرسالة "{subject}" بنجاح إلى {len(recipients_ids)} مستقبل.')
            return redirect('messaging:sent')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إرسال الرسالة: {str(e)}')
            return redirect('messaging:compose')
    
    # عرض نموذج الإنشاء مع تحسين الأداء
    # استخدام التخزين المؤقت للفئات والمستخدمين
    categories = cache.get('message_categories')
    if categories is None:
        categories = list(MessageCategory.objects.all())
        cache.set('message_categories', categories, 300)  # 5 دقائق
    
    from accounts.models import User
    users_cache_key = f'active_users_exclude_{request.user.id}'
    users = cache.get(users_cache_key)
    if users is None:
        users = User.objects.filter(is_active=True).exclude(id=request.user.id).select_related('department', 'position')
        cache.set(users_cache_key, users, 180)  # 3 دقائق
    
    return render(request, 'messaging/compose.html', {
        'categories': categories,
        'users': users
    })

@login_required
def message_detail(request, message_id):
    """تفاصيل الرسالة"""
    # تحسين الاستعلام مع select_related و prefetch_related
    message = get_object_or_404(
        Message.objects.select_related('sender', 'category')
        .prefetch_related(
            Prefetch('messagerecipient_set', 
                    queryset=MessageRecipient.objects.select_related('recipient'))
        ),
        message_id=message_id
    )
    
    # Check if user has access to this message (استعلام محسن)
    user_recipient = None
    has_access = message.sender == request.user
    
    if not has_access:
        for recipient in message.messagerecipient_set.all():
            if recipient.recipient == request.user:
                has_access = True
                user_recipient = recipient
                break
    
    if not has_access:
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الرسالة.')
        return redirect('messaging:inbox')
    
    # Mark as read if recipient (تحسين الأداء)
    if user_recipient and not user_recipient.read_at:
        user_recipient.mark_as_read()
    
    return render(request, 'messaging/message_detail.html', {
        'message': message
    })

@login_required
def reply_message(request, message_id):
    """الرد على رسالة"""
    original_message = get_object_or_404(Message, message_id=message_id)
    
    if request.method == 'POST':
        try:
            # استخراج البيانات
            subject_raw = request.POST.get('subject', '').strip()
            body_raw = request.POST.get('body', '').strip()
            
            if not subject_raw or not body_raw:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
                return redirect('messaging:reply', message_id=message_id)
            
            # فحص أمان المحتوى وتنظيفه
            is_safe, safety_issues = is_content_safe(body_raw)
            if not is_safe:
                messages.error(request, f'المحتوى غير آمن: {", ".join(safety_issues)}')
                return redirect('messaging:reply', message_id=message_id)
            
            subject, body = sanitize_message_content(subject_raw, body_raw)
            
            if not validate_content_length(body):
                messages.error(request, 'نص الرسالة طويل جداً. الحد الأقصى 5000 حرف.')
                return redirect('messaging:reply', message_id=message_id)
            
            # إنشاء الرد
            reply = Message.objects.create(
                subject=f"رد: {subject}",
                body=body,
                sender=request.user,
                category=original_message.category,
                priority=original_message.priority,
                confidentiality=original_message.confidentiality,
                status='SENT',
                sent_at=timezone.now(),
                reply_to=original_message
            )
            
            # إضافة المرسل الأصلي كمستقبل
            MessageRecipient.objects.create(
                message=reply,
                recipient=original_message.sender,
                recipient_type='TO'
            )
            
            # إنشاء التوقيع الرقمي للرد
            try:
                digital_signature = create_digital_signature(
                    message=reply,
                    signer=request.user,
                    signature_type='REPLY',
                    reason=f'رد على الرسالة {original_message.sequence_number}',
                    request=request
                )
                
                # إضافة التوقيع إلى نص الرسالة
                reply.digital_signature = str(digital_signature.signature_id)
                reply.save()
                
                messages.success(request, 'تم إرسال الرد مع التوقيع الرقمي بنجاح.')
            except Exception as e:
                messages.warning(request, f'تم إرسال الرد ولكن حدث خطأ في التوقيع الرقمي: {str(e)}')
            
            # تحديث حالة الرسالة الأصلية
            original_message.status = 'REPLIED'
            original_message.save()
            
            return redirect('messaging:message_detail', message_id=message_id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إرسال الرد: {str(e)}')
            return redirect('messaging:reply', message_id=message_id)
    
    categories = MessageCategory.objects.all()
    return render(request, 'messaging/reply.html', {
        'original_message': original_message,
        'categories': categories
    })

@login_required
def forward_message(request, message_id):
    """تحويل رسالة"""
    original_message = get_object_or_404(Message, message_id=message_id)
    
    if original_message.prevent_forwarding:
        messages.error(request, 'لا يمكن تحويل هذه الرسالة.')
        return redirect('messaging:message_detail', message_id=message_id)
    
    if request.method == 'POST':
        try:
            # استخراج البيانات
            recipients_ids = request.POST.getlist('recipients')
            additional_notes_raw = request.POST.get('additional_notes', '').strip()
            
            if not recipients_ids:
                messages.error(request, 'يرجى اختيار مستقبل واحد على الأقل.')
                return redirect('messaging:forward', message_id=message_id)
            
            # تنظيف الملاحظات الإضافية
            additional_notes = ''
            if additional_notes_raw:
                _, additional_notes = sanitize_message_content('', additional_notes_raw)
            
            # إنشاء الرسالة المحولة
            forward_body = f"--- رسالة محولة ---\n"
            if additional_notes:
                forward_body += f"ملاحظات: {additional_notes}\n\n"
            forward_body += f"من: {original_message.sender.arabic_name}\n"
            forward_body += f"التاريخ: {original_message.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            forward_body += f"الموضوع: {original_message.subject}\n\n"
            forward_body += original_message.body
            
            # تنظيف المحتوى الكامل
            _, forward_body = sanitize_message_content('', forward_body)
            
            forwarded_message = Message.objects.create(
                subject=f"محول: {original_message.subject}",
                body=forward_body,
                sender=request.user,
                category=original_message.category,
                priority=original_message.priority,
                confidentiality=original_message.confidentiality,
                status='SENT',
                sent_at=timezone.now(),
                forwarded_from=original_message
            )
            
            # إضافة المستقبلين
            from accounts.models import User
            for recipient_id in recipients_ids:
                try:
                    recipient_user = User.objects.get(id=recipient_id)
                    MessageRecipient.objects.create(
                        message=forwarded_message,
                        recipient=recipient_user,
                        recipient_type='TO'
                    )
                except User.DoesNotExist:
                    continue
            
            # تحديث حالة الرسالة الأصلية
            original_message.status = 'FORWARDED'
            original_message.save()
            
            messages.success(request, f'تم تحويل الرسالة بنجاح إلى {len(recipients_ids)} مستقبل.')
            return redirect('messaging:message_detail', message_id=message_id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تحويل الرسالة: {str(e)}')
            return redirect('messaging:forward', message_id=message_id)
    
    from accounts.models import User
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    return render(request, 'messaging/forward.html', {
        'original_message': original_message,
        'users': users
    })

@login_required
def delete_message(request, message_id):
    """حذف رسالة"""
    message = get_object_or_404(Message, message_id=message_id)
    
    if request.method == 'POST':
        if message.sender == request.user:
            # Sender deleting their message
            message.status = 'DELETED'
            message.save()
        else:
            # Recipient deleting from their inbox
            MessageRecipient.objects.filter(
                message=message,
                recipient=request.user
            ).update(is_deleted=True)
        
        messages.success(request, 'تم حذف الرسالة بنجاح.')
        return redirect('messaging:inbox')
    
    return render(request, 'messaging/delete_confirm.html', {
        'message': message
    })

@login_required
def archive_message(request, message_id):
    """أرشفة رسالة"""
    message = get_object_or_404(Message, message_id=message_id)
    
    # التأكد من صلاحية المستخدم
    if not (message.sender == request.user or 
            message.messagerecipient_set.filter(recipient=request.user).exists()):
        messages.error(request, 'ليس لديك صلاحية لأرشفة هذه الرسالة.')
        return redirect('messaging:inbox')
    
    if request.method == 'POST':
        message.archived_at = timezone.now()
        message.status = 'ARCHIVED'
        message.save()
        
        # تسجيل في سجل التاريخ
        from .models import MessageHistory
        MessageHistory.objects.create(
            message=message,
            action='ARCHIVED',
            performed_by=request.user,
            details=f'تم أرشفة الرسالة {message.sequence_number}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        messages.success(request, 'تم أرشفة الرسالة بنجاح.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': 'تم أرشفة الرسالة بنجاح.',
                'redirect_url': '/messaging/inbox/'
            })
        
        return redirect('messaging:inbox')
    
    # GET request - عرض صفحة تأكيد الأرشفة
    return render(request, 'messaging/archive_confirm.html', {
        'message': message
    })

@login_required
def unarchive_message(request, message_id):
    """استعادة رسالة من الأرشيف"""
    message = get_object_or_404(Message, message_id=message_id, archived_at__isnull=False)
    
    # التأكد من صلاحية المستخدم
    if not (message.sender == request.user or 
            message.messagerecipient_set.filter(recipient=request.user).exists()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لاستعادة هذه الرسالة.'})
        messages.error(request, 'ليس لديك صلاحية لاستعادة هذه الرسالة.')
        return redirect('messaging:archive')
    
    if request.method == 'POST':
        message.archived_at = None
        message.status = 'SENT' if message.sent_at else 'DRAFT'
        message.save()
        
        # تسجيل في سجل التاريخ
        from .models import MessageHistory
        MessageHistory.objects.create(
            message=message,
            action='RESTORED',
            performed_by=request.user,
            details=f'تم استعادة الرسالة {message.sequence_number} من الأرشيف',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        messages.success(request, 'تم استعادة الرسالة من الأرشيف بنجاح.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': 'تم استعادة الرسالة من الأرشيف بنجاح.',
                'redirect_url': '/messaging/inbox/'
            })
        
        return redirect('messaging:inbox')
    
    # GET request - عرض صفحة تأكيد الاستعادة
    return render(request, 'messaging/unarchive_confirm.html', {
        'message': message
    })

@login_required
@require_http_methods(["GET"])
@csrf_exempt
def unread_count(request):
    """عدد الرسائل غير المقروءة"""
    try:
        # التحقق من أن الطلب AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid request'}, status=400)
            
        count = MessageRecipient.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
            is_deleted=False
        ).count()
        
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def mark_as_read(request, message_id):
    """تعليم الرسالة كمقروءة"""
    if request.method == 'POST':
        try:
            recipient = MessageRecipient.objects.get(
                message__message_id=message_id,
                recipient=request.user
            )
            recipient.mark_as_read()
            return JsonResponse({'success': True})
        except MessageRecipient.DoesNotExist:
            return JsonResponse({'success': False})
    
    return JsonResponse({'success': False})

@login_required
def save_draft(request):
    """حفظ مسودة"""
    if request.method == 'POST':
        # Handle draft saving
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def search_messages(request):
    """البحث في الرسائل"""
    query = request.GET.get('q', '')
    target = request.GET.get('target', 'all')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Basic search implementation
    messages_list = Message.objects.filter(
        Q(subject__icontains=query) | Q(body__icontains=query),
        Q(sender=request.user) | Q(messagerecipient__recipient=request.user)
    ).distinct()[:10]
    
    results = []
    for msg in messages_list:
        results.append({
            'title': msg.subject,
            'description': msg.body[:100] + '...' if len(msg.body) > 100 else msg.body,
            'url': f'/messaging/message/{msg.message_id}/'
        })
    
    return JsonResponse({'results': results})

@login_required
def category_list(request):
    """قائمة تصنيفات الرسائل"""
    categories = MessageCategory.objects.all()
    return render(request, 'messaging/category_list.html', {
        'categories': categories
    })

@login_required
def add_category(request):
    """إضافة تصنيف جديد"""
    return render(request, 'messaging/add_category.html')

@login_required
def edit_category(request, cat_id):
    """تعديل تصنيف"""
    category = get_object_or_404(MessageCategory, id=cat_id)
    return render(request, 'messaging/edit_category.html', {
        'category': category
    })

@login_required
def message_reports(request):
    """تقارير الرسائل"""
    return render(request, 'messaging/reports.html')

@login_required
def export_messages(request):
    """تصدير الرسائل"""
    # Handle export
    return HttpResponse('تصدير الرسائل')

@login_required
def download_attachment(request, attachment_id):
    """تحميل مرفق"""
    attachment = get_object_or_404(MessageAttachment, id=attachment_id)
    
    # Check access permissions
    has_access = (
        attachment.message.sender == request.user or
        MessageRecipient.objects.filter(
            message=attachment.message,
            recipient=request.user
        ).exists()
    )
    
    if not has_access:
        messages.error(request, 'ليس لديك صلاحية لتحميل هذا الملف.')
        return redirect('messaging:inbox')
    
    # Log download
    AuditLog.objects.create(
        action_type='FILE_DOWNLOAD',
        description=f'تحميل ملف: {attachment.original_filename}',
        user=request.user,
        user_ip=request.META.get('REMOTE_ADDR'),
        is_successful=True
    )
    
    # Return file
    response = HttpResponse(attachment.file, content_type=attachment.mime_type)
    response['Content-Disposition'] = f'attachment; filename="{attachment.original_filename}"'
    return response

@login_required
def view_attachment(request, attachment_id):
    """عرض مرفق"""
    attachment = get_object_or_404(MessageAttachment, id=attachment_id)
    
    # Similar access check as download
    has_access = (
        attachment.message.sender == request.user or
        MessageRecipient.objects.filter(
            message=attachment.message,
            recipient=request.user
        ).exists()
    )
    
    if not has_access:
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الملف.')
        return redirect('messaging:inbox')
    
    response = HttpResponse(attachment.file, content_type=attachment.mime_type)
    response['Content-Disposition'] = f'inline; filename="{attachment.original_filename}"'
    return response

@login_required
def test_editor(request):
    """صفحة اختبار محرر النصوص الغني"""
    return render(request, 'messaging/test_editor.html')

def debug_tinymce(request):
    """صفحة تشخيص TinyMCE - متاحة بدون تسجيل دخول للتشخيص السريع"""
    return render(request, 'messaging/debug_tinymce.html')

def simple_test(request):
    """صفحة اختبار TinyMCE البسيطة - متاحة بدون تسجيل دخول"""
    return render(request, 'messaging/simple_test.html')


def verify_signature_view(request, signature_id):
    """عرض تفاصيل التوقيع الرقمي للتحقق"""
    verification_result = verify_signature(signature_id)
    
    if not verification_result['is_valid']:
        return render(request, 'messaging/signature_verification.html', {
            'verification_result': verification_result,
            'error': verification_result.get('error', 'التوقيع غير صالح')
        })
    
    signature = verification_result['signature']
    verification_details = verification_result['verification_details']
    
    # تسجيل عملية التحقق في السجلات الأمنية
    try:
        from .signature_utils import get_client_ip
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='SIGNATURE_VERIFICATION',
            resource_type='DigitalSignature',
            resource_id=str(signature.id),
            details=f'تم التحقق من التوقيع {signature_id}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except:
        pass  # تجاهل أخطاء التسجيل
    
    return render(request, 'messaging/signature_verification.html', {
        'verification_result': verification_result,
        'signature': signature,
        'verification_details': verification_details,
    })


@login_required
def signature_qr_image(request, signature_id):
    """عرض صورة QR للتوقيع الرقمي"""
    try:
        signature = get_object_or_404(DigitalSignature, signature_id=signature_id)
        
        # التحقق من الصلاحية
        user_has_access = (
            signature.signer == request.user or 
            signature.message.sender == request.user or
            signature.message.messagerecipient_set.filter(recipient=request.user).exists()
        )
        
        if not user_has_access and not request.user.is_staff:
            return HttpResponse('ليس لديك صلاحية لعرض هذا التوقيع', status=403)
        
        if signature.qr_code:
            response = HttpResponse(signature.qr_code.read(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="signature_{signature_id}.png"'
            return response
        else:
            return HttpResponse('صورة QR غير متوفرة', status=404)
            
    except DigitalSignature.DoesNotExist:
        return HttpResponse('التوقيع غير موجود', status=404)
    except Exception as e:
        return HttpResponse(f'خطأ في عرض الصورة: {str(e)}', status=500)


@login_required
def signature_certificate(request, signature_id):
    """تنزيل شهادة التوقيع الرقمي"""
    try:
        signature = get_object_or_404(DigitalSignature, signature_id=signature_id)
        
        # التحقق من الصلاحية
        user_has_access = (
            signature.signer == request.user or 
            signature.message.sender == request.user or
            signature.message.messagerecipient_set.filter(recipient=request.user).exists()
        )
        
        if not user_has_access and not request.user.is_staff:
            return HttpResponse('ليس لديك صلاحية لتنزيل هذه الشهادة', status=403)
        
        # إنشاء محتوى الشهادة
        certificate_data = {
            'certificate_info': {
                'serial_number': signature.certificate_serial,
                'signature_id': str(signature.signature_id),
                'issued_date': signature.signed_at.isoformat(),
                'expiry_date': signature.expires_at.isoformat(),
                'status': signature.verification_status,
            },
            'signer_info': signature.signature_data.get('signer_info', {}),
            'message_info': signature.signature_data.get('message_info', {}),
            'verification_details': {
                'hash': signature.hash_value,
                'verification_url': signature.get_verification_url(),
                'qr_data': signature.qr_data,
            }
        }
        
        # إنشاء ملف JSON للشهادة
        import json
        certificate_json = json.dumps(certificate_data, ensure_ascii=False, indent=2)
        
        response = HttpResponse(certificate_json, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="certificate_{signature_id}.json"'
        
        return response
        
    except DigitalSignature.DoesNotExist:
        return HttpResponse('التوقيع غير موجود', status=404)
    except Exception as e:
        return HttpResponse(f'خطأ في إنشاء الشهادة: {str(e)}', status=500)
