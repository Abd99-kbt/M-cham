"""
أدوات مساعدة لنظام المراسلة
"""
import bleach
from django.conf import settings


def clean_html_content(content):
    """
    تنظيف محتوى HTML للحماية من XSS والهجمات الأخرى
    
    Args:
        content (str): المحتوى HTML المراد تنظيفه
        
    Returns:
        str: المحتوى المنظف والآمن
    """
    # العناصر المسموح بها (تتضمن عناصر التنسيق الأساسية)
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 
        'th', 'td', 'div', 'span', 'code', 'pre', 'hr', 'sub', 'sup'
    ]
    
    # الخصائص المسموح بها لكل عنصر
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['class'],
        'th': ['colspan', 'rowspan'],
        'td': ['colspan', 'rowspan'],
        'div': ['class'],
        'span': ['class'],
        'p': ['class'],
        'h1': ['class'],
        'h2': ['class'],
        'h3': ['class'],
        'h4': ['class'],
        'h5': ['class'],
        'h6': ['class'],
        'ul': ['class'],
        'ol': ['class'],
        'li': ['class'],
        'blockquote': ['class'],
        'code': ['class'],
        'pre': ['class'],
    }
    
    # البروتوكولات المسموح بها للروابط
    allowed_protocols = ['http', 'https', 'mailto']
    
    # تنظيف المحتوى
    cleaned_content = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True  # إزالة العناصر غير المسموح بها بدلاً من escape
    )
    
    return cleaned_content


def sanitize_message_content(subject, body):
    """
    تنظيف محتوى الرسالة بالكامل
    
    Args:
        subject (str): موضوع الرسالة
        body (str): نص الرسالة
        
    Returns:
        tuple: (subject_cleaned, body_cleaned)
    """
    # تنظيف الموضوع (نص عادي فقط)
    subject_cleaned = bleach.clean(subject, tags=[], strip=True)
    
    # تنظيف نص الرسالة (مع السماح بـ HTML المحدود)
    body_cleaned = clean_html_content(body)
    
    return subject_cleaned, body_cleaned


def extract_text_from_html(html_content):
    """
    استخراج النص العادي من محتوى HTML
    
    Args:
        html_content (str): المحتوى HTML
        
    Returns:
        str: النص العادي فقط
    """
    return bleach.clean(html_content, tags=[], strip=True)


def validate_content_length(content, max_length=5000):
    """
    التحقق من طول المحتوى
    
    Args:
        content (str): المحتوى المراد فحصه
        max_length (int): الحد الأقصى للطول
        
    Returns:
        bool: True إذا كان الطول مناسب، False إذا كان طويل
    """
    # استخراج النص العادي للفحص
    text_content = extract_text_from_html(content)
    return len(text_content) <= max_length


def count_words_and_chars(html_content):
    """
    عد الكلمات والأحرف في محتوى HTML
    
    Args:
        html_content (str): المحتوى HTML
        
    Returns:
        dict: {'words': int, 'chars': int, 'chars_with_spaces': int}
    """
    # استخراج النص العادي
    text_content = extract_text_from_html(html_content)
    
    # عد الكلمات
    words = len(text_content.split()) if text_content.strip() else 0
    
    # عد الأحرف
    chars_no_spaces = len(text_content.replace(' ', ''))
    chars_with_spaces = len(text_content)
    
    return {
        'words': words,
        'chars': chars_no_spaces,
        'chars_with_spaces': chars_with_spaces
    }


def is_content_safe(content):
    """
    فحص ما إذا كان المحتوى آمن أم لا
    
    Args:
        content (str): المحتوى المراد فحصه
        
    Returns:
        tuple: (is_safe: bool, issues: list)
    """
    issues = []
    
    # فحص الطول
    if not validate_content_length(content):
        issues.append('المحتوى طويل جداً')
    
    # فحص وجود عناصر خطيرة
    dangerous_patterns = [
        '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=', 
        'onclick=', 'onmouseover=', 'onfocus=', 'onblur='
    ]
    
    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if pattern in content_lower:
            issues.append(f'وجود عنصر خطير: {pattern}')
    
    return len(issues) == 0, issues