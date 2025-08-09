"""
أدوات الأمان والحماية
"""
import hashlib
import hmac
import secrets
import qrcode
import pyotp
from io import BytesIO
import base64
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from cryptography.fernet import Fernet
from .models import AuditLog, LoginAttempt

class SecurityUtils:
    """فئة أدوات الأمان"""
    
    @staticmethod
    def generate_secret_key():
        """إنشاء مفتاح سري للمصادقة الثنائية"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """إنشاء رمز QR للمصادقة الثنائية"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="نظام الرسائل المصرفية"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp(secret, token):
        """التحقق من رمز المصادقة الثنائية"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def encrypt_data(data, key=None):
        """تشفير البيانات"""
        if key is None:
            key = settings.SECRET_KEY[:32].encode()
        
        fernet = Fernet(base64.urlsafe_b64encode(key))
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data.decode()
    
    @staticmethod
    def decrypt_data(encrypted_data, key=None):
        """فك تشفير البيانات"""
        if key is None:
            key = settings.SECRET_KEY[:32].encode()
        
        try:
            fernet = Fernet(base64.urlsafe_b64encode(key))
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception:
            return None
    
    @staticmethod
    def generate_hash(data):
        """إنشاء hash للبيانات"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_hash(data, expected_hash):
        """التحقق من hash البيانات"""
        return hmac.compare_digest(
            SecurityUtils.generate_hash(data),
            expected_hash
        )
    
    @staticmethod
    def is_ip_blocked(ip_address):
        """فحص ما إذا كان IP محظور"""
        # فحص محاولات الدخول الفاشلة
        recent_attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            is_successful=False,
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        return recent_attempts >= 5
    
    @staticmethod
    def block_ip(ip_address, duration_hours=24):
        """حظر IP لفترة محددة"""
        cache_key = f"blocked_ip_{ip_address}"
        cache.set(cache_key, True, duration_hours * 3600)
    
    @staticmethod
    def log_security_event(event_type, description, user=None, ip_address=None):
        """تسجيل حدث أمني"""
        AuditLog.objects.create(
            action_type=event_type,
            description=description,
            user=user,
            user_ip=ip_address,
            is_successful=False
        )
    
    @staticmethod
    def check_password_strength(password):
        """فحص قوة كلمة المرور"""
        errors = []
        
        if len(password) < 12:
            errors.append("كلمة المرور يجب أن تكون 12 حرف على الأقل")
        
        if not any(c.isupper() for c in password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف كبير")
        
        if not any(c.islower() for c in password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف صغير")
        
        if not any(c.isdigit() for c in password):
            errors.append("كلمة المرور يجب أن تحتوي على رقم")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("كلمة المرور يجب أن تحتوي على رمز خاص")
        
        return errors
    
    @staticmethod
    def generate_secure_token():
        """إنشاء رمز آمن"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_file_type(file):
        """التحقق من نوع الملف"""
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'text/plain'
        ]
        
        return file.content_type in allowed_types
    
    @staticmethod
    def scan_file_for_malware(file):
        """فحص الملف للبرامج الضارة (مبسط)"""
        # هذا مثال بسيط - في الواقع تحتاج لمكتبة متخصصة
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        
        file_name = file.name.lower()
        for ext in dangerous_extensions:
            if file_name.endswith(ext):
                return False
        
        return True
    
    @staticmethod
    def get_client_ip(request):
        """الحصول على IP العميل الحقيقي"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def is_suspicious_activity(user, action):
        """فحص النشاط المشبوه"""
        # فحص تكرار العمليات
        recent_actions = AuditLog.objects.filter(
            user=user,
            action_type=action,
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_actions > 10:  # أكثر من 10 عمليات في 5 دقائق
            return True
        
        # فحص التوقيت غير المعتاد
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 22:  # خارج ساعات العمل
            if action in ['MESSAGE_SEND', 'FILE_UPLOAD']:
                return True
        
        return False