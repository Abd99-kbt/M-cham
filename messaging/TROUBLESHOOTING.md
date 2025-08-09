# حل مشاكل محرر النصوص الغني

## 🚨 المشكلة: شريط الأدوات لا يظهر

### الأسباب المحتملة والحلول:

#### 1. **مشكلة الاتصال بالإنترنت**
- **السبب**: عدم القدرة على تحميل TinyMCE من CDN
- **الحل**: 
  ```bash
  # تحقق من الاتصال
  ping cdn.tiny.cloud
  ```
- **بديل**: استخدم نسخة محلية من TinyMCE

#### 2. **حجب JavaScript أو CDN**
- **السبب**: إعدادات الأمان أو حماية الشركة
- **الحل**: 
  - تفعيل JavaScript في المتصفح
  - إضافة `cdn.tiny.cloud` إلى قائمة المواقع المسموحة
  - تحقق من إعدادات Firewall

#### 3. **خطأ في التكوين**
- **السبب**: خطأ في كود JavaScript
- **الحل**: فحص Console للأخطاء

#### 4. **تضارب مع مكتبات أخرى**
- **السبب**: تضارب مع jQuery أو Bootstrap
- **الحل**: تحديث ترتيب تحميل الملفات

---

## 🔧 خطوات التشخيص

### الخطوة 1: فحص أساسي
```javascript
// في Developer Console (F12)
console.log(typeof tinymce); // يجب أن يعطي "object"
```

### الخطوة 2: فحص العنصر
```javascript
// فحص وجود العنصر
console.log(document.getElementById('id_body'));
```

### الخطوة 3: فحص التهيئة
```javascript
// فحص حالة المحرر
console.log(tinymce.get('id_body'));
```

### الخطوة 4: استخدام أدوات التشخيص
1. اذهب إلى: `/messaging/test-editor/`
2. افتح Developer Console (F12)
3. اكتب: `tinymceDebug.report()`

---

## 🛠️ الحلول السريعة

### الحل الأول: إعادة تحميل الصفحة
```javascript
location.reload();
```

### الحل الثاني: إعادة تهيئة المحرر
```javascript
// في Console
if (tinymce.get('id_body')) {
    tinymce.get('id_body').remove();
}
initTinyMCE(); // إذا كانت الدالة متاحة
```

### الحل الثالث: استخدام نسخة محلية
1. حمل TinyMCE محلياً
2. ضعه في مجلد `static/js/`
3. غير مسار التحميل في `base.html`

---

## 🔍 رسائل الخطأ الشائعة

### "tinymce is not defined"
- **المعنى**: لم يتم تحميل مكتبة TinyMCE
- **الحل**: تحقق من الاتصال بالإنترنت والـ CDN

### "Cannot read property 'init' of undefined"
- **المعنى**: محاولة تشغيل TinyMCE قبل تحميله
- **الحل**: انتظار تحميل المكتبة كاملة

### "Refused to load the script"
- **المعنى**: المتصفح يرفض تحميل السكريبت
- **الحل**: تحقق من إعدادات الأمان

---

## 📱 مشاكل متعلقة بالمتصفح

### Internet Explorer (غير مدعوم)
- **المشكلة**: IE لا يدعم TinyMCE 6
- **الحل**: استخدم متصفح حديث

### Safari
- **المشكلة**: قيود أمان صارمة
- **الحل**: تفعيل "Allow cross-origin requests"

### Chrome مع إعدادات أمان عالية
- **المشكلة**: حجب CDN
- **الحل**: إضافة الموقع للمواقع الموثوقة

---

## 🚀 تحسين الأداء

### 1. تحميل مسبق
```html
<link rel="preconnect" href="https://cdn.tiny.cloud">
<link rel="dns-prefetch" href="https://cdn.tiny.cloud">
```

### 2. تحميل محلي للبيئة الإنتاجية
```bash
# تحميل TinyMCE محلياً
npm install tinymce
```

### 3. ضغط وتحسين
- استخدم نسخة مضغوطة (minified)
- تحميل plugins فقط عند الحاجة

---

## 📞 طرق الدعم

### 1. أدوات التشخيص المدمجة
```javascript
// في Console
tinymceDebug.check();     // فحص سريع
tinymceDebug.report();    // تقرير شامل
tinymceDebug.fix();       // محاولة إصلاح
```

### 2. صفحة الاختبار
- اذهب إلى: `/messaging/test-editor/`
- اختبر جميع الميزات
- احصل على تقرير شامل

### 3. معلومات النظام
```javascript
// معلومات مفيدة للدعم
console.log({
    userAgent: navigator.userAgent,
    url: window.location.href,
    tinymceVersion: typeof tinymce !== 'undefined' ? tinymce.majorVersion : 'not loaded',
    timestamp: new Date().toISOString()
});
```

---

## ✅ اختبارات التحقق

### قائمة فحص سريعة:
- [ ] الاتصال بالإنترنت يعمل
- [ ] JavaScript مفعل في المتصفح
- [ ] لا توجد أخطاء في Console
- [ ] العنصر `#id_body` موجود في الصفحة
- [ ] `tinymce` متاح في `window`
- [ ] لا يوجد تضارب مع مكتبات أخرى

### اختبار شامل:
1. افتح `/messaging/test-editor/`
2. تحقق من رسائل النجاح/الخطأ
3. جرب كتابة نص في المحرر
4. اختبر أدوات التنسيق
5. احفظ تقرير التشخيص

---

## 🔄 إعادة التثبيت

إذا فشلت جميع الحلول:

1. **مسح Cache المتصفح**
2. **إعادة تشغيل الخادم**
3. **تحقق من ملفات requirements.txt**
4. **فحص أذونات الملفات**
5. **مراجعة إعدادات Django**

---

> 💡 **نصيحة**: استخدم صفحة الاختبار `/messaging/test-editor/` للتشخيص السريع والدقيق.