/**
 * ملف تشخيص وإصلاح مشاكل TinyMCE
 */

// فحص توفر TinyMCE
function checkTinyMCE() {
    console.log('🔍 فحص حالة TinyMCE...');
    
    // فحص تحميل المكتبة
    if (typeof tinymce === 'undefined') {
        console.error('❌ TinyMCE غير محمل');
        return false;
    }
    
    console.log('✅ TinyMCE محمل بنجاح');
    console.log('📦 إصدار TinyMCE:', tinymce.majorVersion + '.' + tinymce.minorVersion);
    
    return true;
}

// فحص الاتصال بالإنترنت
function checkInternetConnection() {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
        img.src = 'https://cdn.tiny.cloud/1/favicon.ico?' + Date.now();
    });
}

// إنشاء تقرير تشخيصي
async function generateDiagnosticReport() {
    console.log('📋 إنشاء تقرير التشخيص...');
    
    const report = {
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        tinymceAvailable: typeof tinymce !== 'undefined',
        internetConnection: await checkInternetConnection(),
        domReady: document.readyState,
        errors: []
    };
    
    // فحص TinyMCE
    if (report.tinymceAvailable) {
        report.tinymceVersion = tinymce.majorVersion + '.' + tinymce.minorVersion;
        report.tinymceInstanceExists = !!tinymce.get('id_body');
    } else {
        report.errors.push('TinyMCE library not loaded');
    }
    
    // فحص العناصر المطلوبة
    const requiredElements = ['#id_body', '.rich-text-editor-container'];
    requiredElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (!element) {
            report.errors.push(`Required element not found: ${selector}`);
        }
    });
    
    console.table(report);
    return report;
}

// محاولة إصلاح تلقائي
function attemptAutoFix() {
    console.log('🔧 محاولة الإصلاح التلقائي...');
    
    // إزالة أي instance موجود
    if (typeof tinymce !== 'undefined' && tinymce.get('id_body')) {
        tinymce.get('id_body').remove();
        console.log('🗑️ تم إزالة instance قديم');
    }
    
    // إعادة محاولة التهيئة
    setTimeout(() => {
        if (typeof initTinyMCE === 'function') {
            console.log('🔄 إعادة محاولة التهيئة...');
            initTinyMCE();
        }
    }, 1000);
}

// إضافة أدوات تشخيص إلى window
window.tinymceDebug = {
    check: checkTinyMCE,
    report: generateDiagnosticReport,
    fix: attemptAutoFix,
    checkConnection: checkInternetConnection
};

// تشغيل فحص تلقائي عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        generateDiagnosticReport();
    }, 3000);
});

console.log('🛠️ أدوات تشخيص TinyMCE جاهزة. اكتب tinymceDebug في الكونسول للمساعدة');