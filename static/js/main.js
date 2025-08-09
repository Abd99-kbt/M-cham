// نظام الرسائل المصرفية - JavaScript الرئيسي - محسن للأداء مع تأثيرات تفاعلية

// متغيرات عامة لتحسين الأداء
let unreadCountInterval;
let requestController = new AbortController();
let animationObserver;

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة محسنة للتوولتيبس
    initializeTooltips();
    
    // تهيئة التأثيرات التفاعلية
    initializeInteractiveEffects();
    
    // تهيئة أنيميشن التحميل التدريجي
    initializeAnimationObserver();

    // تأكيد الحذف مع تحسين الأداء
    document.addEventListener('click', function(e) {
        if (e.target.matches('.btn-delete, .btn-delete *')) {
            const deleteBtn = e.target.closest('.btn-delete');
            if (deleteBtn && !confirm('هل أنت متأكد من الحذف؟')) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });

    // تحديث عدد الرسائل غير المقروءة مع تحسين الأداء (فقط إذا كان المستخدم مسجل دخول)
    const currentPath = window.location.pathname;
    if (!currentPath.includes('/accounts/') && !currentPath.includes('/login/') && !currentPath.includes('/register/')) {
        updateUnreadCount();
        unreadCountInterval = setInterval(updateUnreadCount, 30000);
    }

    // التحقق من رفع الملفات
    const fileInput = document.getElementById('attachments');
    if (fileInput) {
        fileInput.addEventListener('change', validateFiles);
    }

    // تحسين أداء النماذج
    optimizeForms();
    enhancedOptimizeForms();
    
    // تحسين التنقل
    optimizeNavigation();
    
    // تهيئة ميزات إضافية
    initializeRippleEffect();
    initializeParallaxEffect();
    initializeSmoothAnimations();
});

// تهيئة التوولتيبس مع تأثيرات محسنة
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl, {
                trigger: 'hover focus',
                animation: true,
                delay: { show: 500, hide: 100 },
                customClass: 'modern-tooltip'
            });
        });
    }
}

// تهيئة التأثيرات التفاعلية
function initializeInteractiveEffects() {
    // تأثيرات hover للبطاقات
    const cards = document.querySelectorAll('.modern-card, .card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
            this.style.boxShadow = 'var(--cham-shadow-hover)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'var(--cham-shadow-sm)';
        });
    });
    
    // تأثيرات الأزرار
    const buttons = document.querySelectorAll('.modern-btn, .btn');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.2s ease';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// تهيئة مراقب الأنيميشن
function initializeAnimationObserver() {
    if ('IntersectionObserver' in window) {
        animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    // إضافة أنيميشن عشوائي للعناصر
                    const animations = [
                        'animate-fade-in-up',
                        'animate-slide-in-right',
                        'animate-scale-in',
                        'animate-bounce-in'
                    ];
                    
                    const randomAnimation = animations[Math.floor(Math.random() * animations.length)];
                    element.classList.add(randomAnimation);
                    
                    // إزالة العنصر من المراقبة بعد تطبيق الأنيميشن
                    animationObserver.unobserve(element);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });
        
        // مراقبة العناصر التي تحتاج أنيميشن
        const animateElements = document.querySelectorAll('.animate-on-scroll, .modern-stat-card:not([class*="animate-"]), .modern-card:not([class*="animate-"])');
        animateElements.forEach(el => {
            animationObserver.observe(el);
        });
    }
}

// تهيئة تأثير الموجة
function initializeRippleEffect() {
    const rippleElements = document.querySelectorAll('.modern-btn');
    
    rippleElements.forEach(element => {
        element.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            const ripple = document.createElement('span');
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// تهيئة تأثير البارالاكس
function initializeParallaxEffect() {
    const parallaxElements = document.querySelectorAll('.parallax-element');
    
    if (parallaxElements.length > 0) {
        window.addEventListener('scroll', throttle(() => {
            const scrolled = window.pageYOffset;
            
            parallaxElements.forEach(element => {
                const rate = scrolled * -0.5;
                element.style.transform = `translateY(${rate}px)`;
            });
        }, 16));
    }
}

// تهيئة الأنيميشن السلس
function initializeSmoothAnimations() {
    // أنيميشن العد التصاعدي للأرقام
    const counters = document.querySelectorAll('.modern-stat-number');
    
    const animateCounters = () => {
        counters.forEach(counter => {
            const target = parseInt(counter.textContent) || 0;
            const duration = 2000;
            const stepTime = Math.abs(Math.floor(duration / target));
            let current = 0;
            
            const timer = setInterval(() => {
                current += Math.ceil(target / 100);
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = current;
            }, stepTime);
        });
    };
    
    // تشغيل العد عند رؤية العناصر
    if ('IntersectionObserver' in window) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    counterObserver.disconnect();
                }
            });
        });
        
        if (counters.length > 0) {
            counterObserver.observe(counters[0]);
        }
    }
}

// دالة throttle لتحسين الأداء
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// الحصول على CSRF token
function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    
    // البحث في cookies إذا لم يوجد في النموذج
    const cookieValue = document.cookie.match(/csrftoken=([^;]+)/);
    return cookieValue ? cookieValue[1] : '';
}

// إظهار إشعار مخصص
function showCustomNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `modern-alert modern-alert-${type} notification-enter`;
    notification.innerHTML = `
        <i class="ph ph-${getIconForType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close ms-auto" onclick="this.parentElement.remove()"></button>
    `;
    
    // إضافة الإشعار إلى الصفحة
    const container = document.querySelector('.notification-container') || createNotificationContainer();
    container.appendChild(notification);
    
    // إزالة الإشعار تلقائياً
    setTimeout(() => {
        notification.classList.add('notification-exit');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

// إنشاء حاوي الإشعارات
function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'notification-container';
    container.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 350px;
    `;
    document.body.appendChild(container);
    return container;
}

// الحصول على أيقونة حسب نوع الإشعار
function getIconForType(type) {
    const icons = {
        success: 'check-circle',
        danger: 'x-circle',
        warning: 'warning-circle',
        info: 'info'
    };
    return icons[type] || 'info';
}

// تحسين النماذج مع إضافات جديدة
function enhancedOptimizeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // تحسين حقول الإدخال
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // تأثيرات focus و blur
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
                this.style.transform = 'scale(1.02)';
                this.style.transition = 'transform 0.2s ease';
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
                this.style.transform = 'scale(1)';
            });
            
            // التحقق من صحة البيانات في الوقت الفعلي
            input.addEventListener('input', function() {
                validateInputRealtime(this);
            });
        });
        
        // تحسين إرسال النماذج
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                // إضافة حالة التحميل
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // إضافة spinner
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>' + originalText;
                
                // إزالة حالة التحميل بعد فترة
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }, 3000);
            }
        });
    });
}

// التحقق من صحة الحقول في الوقت الفعلي
function validateInputRealtime(input) {
    const value = input.value.trim();
    const type = input.type;
    
    // إزالة الفئات السابقة
    input.classList.remove('is-valid', 'is-invalid');
    
    // التحقق حسب نوع الحقل
    let isValid = true;
    
    if (input.hasAttribute('required') && !value) {
        isValid = false;
    } else if (type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
    } else if (type === 'tel' && value && !isValidPhone(value)) {
        isValid = false;
    }
    
    // إضافة الفئة المناسبة
    input.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // إضافة تأثير بصري
    if (!isValid) {
        input.classList.add('animate-shake');
        setTimeout(() => {
            input.classList.remove('animate-shake');
        }, 600);
    }
}

// فحص صحة البريد الإلكتروني
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// فحص صحة رقم الهاتف
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

// تحديث عدد الرسائل غير المقروءة مع تحسين الأداء
function updateUnreadCount() {
    // التحقق من وجود عنصر عدد الرسائل أولاً
    const badge = document.getElementById('unread-count');
    if (!badge) {
        // إذا لم يوجد العنصر، توقف عن المحاولة
        if (unreadCountInterval) {
            clearInterval(unreadCountInterval);
        }
        return;
    }
    
    // إلغاء الطلب السابق إذا كان لا يزال قيد التنفيذ
    if (requestController) {
        requestController.abort();
    }
    requestController = new AbortController();
    
    fetch('/messaging/api/unread-count/', {
        headers: { 
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache',
            'X-CSRFToken': getCsrfToken()
        },
        signal: requestController.signal
    })
    .then(response => {
        if (!response.ok) {
            // إذا كان 401 أو 403، فالمستخدم غير مسجل دخول
            if (response.status === 401 || response.status === 403) {
                if (unreadCountInterval) {
                    clearInterval(unreadCountInterval);
                }
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // التحقق من أن الاستجابة JSON صحيحة
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Expected JSON response');
        }
        
        return response.json();
    })
    .then(data => {
        if (data && badge) {
            const newCount = data.count || 0;
            if (badge.textContent !== newCount.toString()) {
                badge.textContent = newCount;
                badge.style.display = newCount > 0 ? 'inline' : 'none';
                
                // تأثير بصري عند تغيير العدد
                if (newCount > 0) {
                    badge.classList.add('pulse-animation');
                    setTimeout(() => badge.classList.remove('pulse-animation'), 1000);
                }
            }
        }
    })
    .catch(error => {
        if (error.name !== 'AbortError') {
            // عدم عرض الأخطاء في صفحات التسجيل/تسجيل الدخول
            const currentPath = window.location.pathname;
            if (!currentPath.includes('/accounts/') && !currentPath.includes('/login/') && !currentPath.includes('/register/')) {
                console.error('خطأ في تحديث العدد:', error);
            }
            
            // إذا كان الخطأ يتعلق بعدم تسجيل الدخول، توقف عن المحاولة
            if (error.message.includes('401') || error.message.includes('403') || 
                error.message.includes('Expected JSON response')) {
                if (unreadCountInterval) {
                    clearInterval(unreadCountInterval);
                }
            }
        }
    });
}

// التحقق من الملفات
function validateFiles() {
    const maxSize = 10 * 1024 * 1024; // 10 MB
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf', 
                         'application/msword'];
    
    for (let file of this.files) {
        if (file.size > maxSize) {
            alert('الملف كبير جداً. الحد الأقصى 10 ميجابايت.');
            this.value = '';
            return;
        }
        
        if (!allowedTypes.includes(file.type)) {
            alert('نوع الملف غير مدعوم.');
            this.value = '';
            return;
        }
    }
}

// عرض إشعار
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed`;
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// طباعة الرسالة
function printMessage() {
    window.print();
}

// تحسين أداء النماذج
function optimizeForms() {
    // تحسين النماذج الطويلة بالتحميل التدريجي
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // منع الإرسال المتعدد
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && submitBtn.disabled) {
                e.preventDefault();
                return false;
            }
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'جاري المعالجة...';
                
                // إعادة تمكين الزر بعد 10 ثوانٍ كإجراء احتياطي
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.dataset.originalText || 'إرسال';
                }, 10000);
            }
        });
        
        // حفظ النصوص الأصلية للأزرار
        const submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitBtns.forEach(btn => {
            btn.dataset.originalText = btn.textContent || btn.value;
        });
    });
}

// تحسين التنقل
function optimizeNavigation() {
    // تحسين روابط التنقل بـ Prefetch
    const navLinks = document.querySelectorAll('a[href^="/"]');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            // تحميل مسبق للصفحة عند hover
            if (!link.dataset.prefetched) {
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = link.href;
                document.head.appendChild(prefetchLink);
                link.dataset.prefetched = 'true';
            }
        });
    });
}

// تحسين تحميل المحتوى بشكل تدريجي
function lazyLoadContent() {
    const lazyElements = document.querySelectorAll('[data-lazy]');
    const lazyObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const src = element.dataset.lazy;
                
                if (element.tagName === 'IMG') {
                    element.src = src;
                } else {
                    fetch(src)
                        .then(response => response.text())
                        .then(html => {
                            element.innerHTML = html;
                        });
                }
                
                element.removeAttribute('data-lazy');
                lazyObserver.unobserve(element);
            }
        });
    });
    
    lazyElements.forEach(element => lazyObserver.observe(element));
}

// تحسين ذاكرة التخزين المحلي
function optimizeLocalStorage() {
    // تنظيف البيانات القديمة
    const now = Date.now();
    const maxAge = 24 * 60 * 60 * 1000; // 24 ساعة
    
    for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cache_')) {
            try {
                const data = JSON.parse(localStorage.getItem(key));
                if (data.timestamp && (now - data.timestamp) > maxAge) {
                    localStorage.removeItem(key);
                }
            } catch (e) {
                localStorage.removeItem(key);
            }
        }
    }
}

// دالة لحفظ البيانات في التخزين المحلي مع انتهاء صلاحية
function cacheData(key, data, ttl = 300000) { // 5 دقائق افتراضياً
    const cacheObject = {
        data: data,
        timestamp: Date.now(),
        ttl: ttl
    };
    localStorage.setItem(`cache_${key}`, JSON.stringify(cacheObject));
}

// دالة لاسترداد البيانات من التخزين المحلي
function getCachedData(key) {
    try {
        const cached = localStorage.getItem(`cache_${key}`);
        if (!cached) return null;
        
        const cacheObject = JSON.parse(cached);
        const now = Date.now();
        
        if (now - cacheObject.timestamp > cacheObject.ttl) {
            localStorage.removeItem(`cache_${key}`);
            return null;
        }
        
        return cacheObject.data;
    } catch (e) {
        return null;
    }
}

// تهيئة تحسينات الأداء عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    lazyLoadContent();
    optimizeLocalStorage();
});

// تنظيف الذاكرة عند إغلاق الصفحة
window.addEventListener('beforeunload', function() {
    if (unreadCountInterval) {
        clearInterval(unreadCountInterval);
    }
    if (requestController) {
        requestController.abort();
    }
    if (animationObserver) {
        animationObserver.disconnect();
    }
});

// إضافة الأنماط للتأثيرات الجديدة
const dynamicStyles = document.createElement('style');
dynamicStyles.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .modern-tooltip {
        --bs-tooltip-bg: var(--cham-primary);
        --bs-tooltip-opacity: 0.95;
        font-family: var(--cham-font-family);
        font-size: 0.875rem;
        animation: fadeIn 0.3s ease;
    }
    
    .focused {
        transform: scale(1.02);
        transition: transform 0.2s ease;
    }
    
    .notification-container .modern-alert {
        margin-bottom: 0.5rem;
        animation-duration: 0.3s;
    }
    
    .parallax-element {
        will-change: transform;
    }
    
    /* تحسينات للعناصر التفاعلية */
    .modern-btn:hover {
        animation: none;
    }
    
    .modern-btn.loading {
        position: relative;
        color: transparent;
    }
    
    .modern-btn.loading .loading-spinner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 16px;
        height: 16px;
        border-width: 2px;
    }
`;
document.head.appendChild(dynamicStyles);