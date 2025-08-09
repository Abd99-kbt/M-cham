"""
دوال مساعدة للتوقيع الرقمي و QR Code
"""
import qrcode
import json
import hashlib
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import DigitalSignature


def generate_qr_code(data, size=(300, 300), border=4):
    """
    إنشاء QR code من البيانات المعطاة
    
    Args:
        data: البيانات المراد تشفيرها في QR
        size: حجم الصورة (width, height)
        border: حجم الحدود
    
    Returns:
        ContentFile: ملف الصورة
    """
    # إنشاء QR code
    qr = qrcode.QRCode(
        version=1,  # يتحكم في حجم QR code
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # مستوى عالي من تصحيح الأخطاء
        box_size=10,
        border=border,
    )
    
    # إضافة البيانات
    if isinstance(data, dict):
        qr_data = json.dumps(data, ensure_ascii=False)
    else:
        qr_data = str(data)
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # إنشاء الصورة
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # تغيير حجم الصورة إذا لزم الأمر
    if qr_img.size != size:
        qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
    
    # حفظ الصورة في الذاكرة
    img_io = io.BytesIO()
    qr_img.save(img_io, format='PNG', quality=95)
    img_io.seek(0)
    
    return ContentFile(img_io.getvalue(), name='qr_code.png')


def generate_signature_qr_with_logo(signature_data, logo_path=None, size=(400, 400)):
    """
    إنشاء QR code مخصص للتوقيع مع شعار البنك
    
    Args:
        signature_data: بيانات التوقيع
        logo_path: مسار شعار البنك
        size: حجم الصورة النهائية
    
    Returns:
        ContentFile: ملف الصورة المخصص
    """
    # إنشاء QR code أساسي
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=3,
    )
    
    qr_data = json.dumps(signature_data, ensure_ascii=False, indent=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # إنشاء صورة QR
    qr_img = qr.make_image(fill_color="#1e4a6b", back_color="white")
    
    # إضافة شعار البنك في المنتصف (إذا كان متوفراً)
    if logo_path:
        try:
            logo = Image.open(logo_path)
            # تغيير حجم الشعار
            logo_size = min(qr_img.size[0] // 5, qr_img.size[1] // 5)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # إضافة خلفية بيضاء للشعار
            logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
            logo_bg.paste(logo, (10, 10))
            
            # وضع الشعار في منتصف QR code
            logo_pos = ((qr_img.size[0] - logo_bg.size[0]) // 2,
                       (qr_img.size[1] - logo_bg.size[1]) // 2)
            qr_img.paste(logo_bg, logo_pos)
        except Exception as e:
            print(f"خطأ في إضافة الشعار: {e}")
    
    # إنشاء صورة نهائية مع معلومات إضافية
    final_img = Image.new('RGB', size, 'white')
    
    # حساب موقع QR code
    qr_size = min(size[0] - 100, size[1] - 150)  # ترك مساحة للنص
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    qr_pos = ((size[0] - qr_size) // 2, 50)
    final_img.paste(qr_img, qr_pos)
    
    # إضافة نص معلوماتي
    draw = ImageDraw.Draw(final_img)
    
    try:
        # استخدام خط عربي إذا كان متوفراً
        title_font = ImageFont.truetype("arial.ttf", 16)
        text_font = ImageFont.truetype("arial.ttf", 12)
    except:
        # استخدام الخط الافتراضي
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # عنوان التوقيع
    title = "التوقيع الرقمي - بنك الشام"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_pos = ((size[0] - title_bbox[2]) // 2, 10)
    draw.text(title_pos, title, fill='#1e4a6b', font=title_font)
    
    # معلومات الموقع
    signer_name = signature_data.get('signer', 'غير محدد')
    position = signature_data.get('position', 'غير محدد')
    signed_date = signature_data.get('signed_at', 'غير محدد')
    
    info_text = f"الموقع: {signer_name}\nالمنصب: {position}\nالتاريخ: {signed_date}"
    info_lines = info_text.split('\n')
    
    start_y = qr_pos[1] + qr_size + 20
    for i, line in enumerate(info_lines):
        line_bbox = draw.textbbox((0, 0), line, font=text_font)
        line_pos = ((size[0] - line_bbox[2]) // 2, start_y + i * 25)
        draw.text(line_pos, line, fill='#333333', font=text_font)
    
    # حفظ الصورة
    img_io = io.BytesIO()
    final_img.save(img_io, format='PNG', quality=95)
    img_io.seek(0)
    
    return ContentFile(img_io.getvalue(), name='signature_qr.png')


def create_digital_signature(message, signer, signature_type='REPLY', reason='', request=None):
    """
    إنشاء توقيع رقمي جديد مع QR code
    
    Args:
        message: كائن الرسالة
        signer: المستخدم الموقع
        signature_type: نوع التوقيع
        reason: سبب التوقيع
        request: كائن HTTP request للحصول على معلومات الشبكة
    
    Returns:
        DigitalSignature: كائن التوقيع الرقمي
    """
    # إنشاء كائن التوقيع
    signature = DigitalSignature(
        message=message,
        signer=signer,
        signature_type=signature_type,
        reason=reason,
    )
    
    # إضافة معلومات الشبكة إذا كان request متوفراً
    if request:
        signature.ip_address = get_client_ip(request)
        signature.user_agent = request.META.get('HTTP_USER_AGENT', '')
        signature.location_info = get_location_info(request)
    else:
        signature.ip_address = '127.0.0.1'
        signature.user_agent = 'Unknown'
    
    # إنشاء بيانات التوقيع
    signature_data = signature.generate_signature_data()
    signature.signature_data = signature_data
    
    # إنشاء بيانات QR المختصرة
    qr_display_data = signature.get_qr_display_data()
    signature.qr_data = json.dumps(qr_display_data, ensure_ascii=False)
    
    # حفظ التوقيع أولاً لإنشاء ID
    signature.save()
    
    # إنشاء QR code
    logo_path = None
    try:
        logo_path = settings.STATIC_ROOT + '/images/logo-cham.jpg'
    except:
        pass
    
    qr_file = generate_signature_qr_with_logo(qr_display_data, logo_path)
    signature.qr_code.save(f'signature_{signature.signature_id}.png', qr_file)
    
    return signature


def verify_signature(signature_id):
    """
    التحقق من صحة التوقيع الرقمي
    
    Args:
        signature_id: معرف التوقيع
    
    Returns:
        dict: نتيجة التحقق
    """
    try:
        signature = DigitalSignature.objects.get(signature_id=signature_id)
        
        verification_result = {
            'is_valid': signature.is_valid(),
            'signature': signature,
            'verification_details': {
                'status': signature.verification_status,
                'signed_at': signature.signed_at,
                'expires_at': signature.expires_at,
                'hash_valid': signature.verify_hash(),
                'signer_info': signature.signature_data.get('signer_info', {}),
                'message_info': signature.signature_data.get('message_info', {}),
            }
        }
        
        return verification_result
        
    except DigitalSignature.DoesNotExist:
        return {
            'is_valid': False,
            'error': 'التوقيع غير موجود',
            'verification_details': None
        }
    except Exception as e:
        return {
            'is_valid': False,
            'error': f'خطأ في التحقق: {str(e)}',
            'verification_details': None
        }


def get_client_ip(request):
    """الحصول على عنوان IP الحقيقي للعميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_info(request):
    """الحصول على معلومات الموقع (يمكن تطويرها لاحقاً)"""
    return {
        'timezone': str(timezone.get_current_timezone()),
        'timestamp': timezone.now().isoformat(),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
    }


def generate_signature_certificate(signature):
    """
    إنشاء شهادة رقمية للتوقيع (يمكن تطويرها لاحقاً)
    
    Args:
        signature: كائن التوقيع الرقمي
    
    Returns:
        str: رقم الشهادة
    """
    cert_data = f"{signature.signature_id}{signature.signer.employee_id}{signature.signed_at}"
    cert_hash = hashlib.md5(cert_data.encode()).hexdigest()
    return f"CHAM-{cert_hash[:12].upper()}"


def batch_verify_signatures(signature_ids):
    """
    التحقق من عدة توقيعات دفعة واحدة
    
    Args:
        signature_ids: قائمة معرفات التوقيع
    
    Returns:
        dict: نتائج التحقق لكل توقيع
    """
    results = {}
    signatures = DigitalSignature.objects.filter(signature_id__in=signature_ids)
    
    for signature in signatures:
        results[str(signature.signature_id)] = {
            'is_valid': signature.is_valid(),
            'status': signature.verification_status,
            'signer': signature.signer.arabic_name,
            'signed_at': signature.signed_at,
        }
    
    # إضافة التوقيعات غير الموجودة
    found_ids = [str(sig.signature_id) for sig in signatures]
    for sig_id in signature_ids:
        if sig_id not in found_ids:
            results[sig_id] = {
                'is_valid': False,
                'error': 'التوقيع غير موجود'
            }
    
    return results