"""
Django forms for accounts app
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re

from .models import Department, Position

User = get_user_model()


class DepartmentForm(forms.ModelForm):
    """نموذج إضافة وتعديل الأقسام"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم القسم'
        }),
        label="اسم القسم"
    )
    
    code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز القسم',
            'dir': 'ltr'
        }),
        label="رمز القسم"
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'وصف القسم',
            'rows': 5
        }),
        label="الوصف"
    )
    
    parent_department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="القسم الأعلى",
        empty_label="- لا يوجد -"
    )
    
    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="مدير القسم",
        empty_label="- لا يوجد -"
    )
    
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'parent_department', 'manager']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد المديرين المحتملين (المستخدمين النشطين مع مستوى صلاحيات مناسب)
        self.fields['manager'].queryset = User.objects.filter(
            is_active=True,
            position__level__gte=3  # مستوى مشرف فما فوق
        ).order_by('arabic_name')
        
        # إضافة help text
        self.fields['code'].help_text = "رمز فريد للقسم (حروف وأرقام فقط)"
        self.fields['parent_department'].help_text = "اختر القسم الأعلى إذا كان هذا القسم فرعياً"
        self.fields['manager'].help_text = "اختر مدير القسم (مستوى مشرف فما فوق)"
        
        # التحقق من وجود مديرين محتملين
        if not self.fields['manager'].queryset.exists():
            self.fields['manager'].help_text += " - لا يوجد مديرين محتملين حالياً"
    
    def clean_code(self):
        """التحقق من رمز القسم"""
        code = self.cleaned_data.get('code')
        
        if code:
            # التحقق من أن الرمز يحتوي على أحرف وأرقام فقط
            if not re.match(r'^[a-zA-Z0-9]+$', code):
                raise ValidationError('رمز القسم يجب أن يحتوي على أحرف إنجليزية وأرقام فقط.')
            
            # التحقق من عدم وجود الرمز مسبقاً (إلا في حالة التعديل)
            if self.instance.pk:
                # في حالة التعديل - استثناء القسم الحالي
                if Department.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('رمز القسم موجود بالفعل.')
            else:
                # في حالة الإضافة الجديدة
                if Department.objects.filter(code=code).exists():
                    raise ValidationError('رمز القسم موجود بالفعل.')
        
        return code
    
    def clean_parent_department(self):
        """التحقق من القسم الأعلى"""
        parent_department = self.cleaned_data.get('parent_department')
        
        # التأكد من عدم اختيار القسم نفسه كقسم أعلى (في حالة التعديل)
        if self.instance.pk and parent_department and parent_department.pk == self.instance.pk:
            raise ValidationError('لا يمكن اختيار القسم نفسه كقسم أعلى.')
        
        return parent_department


class UserRegistrationForm(UserCreationForm):
    """نموذج تسجيل مستخدم جديد"""
    
    # الحقول الأساسية
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم',
            'dir': 'ltr'
        }),
        label="اسم المستخدم"
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@bank.com',
            'dir': 'ltr'
        }),
        label="البريد الإلكتروني"
    )
    
    arabic_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الاسم الكامل بالعربية'
        }),
        label="الاسم بالعربية"
    )
    
    employee_id = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{1,10}$', 'رقم الموظف يجب أن يكون أرقام فقط')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345',
            'dir': 'ltr'
        }),
        label="رقم الموظف"
    )
    
    phone = forms.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{3,15}$', 'رقم الهاتف يجب أن يكون أرقام فقط (3-15 رقم)')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456789',
            'dir': 'ltr',
            'maxlength': '15'
        }),
        label="رقم الهاتف"
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="القسم"
    )
    
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="المنصب"
    )
    
    direct_manager = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="المدير المباشر (اختياري)"
    )
    
    # كلمة المرور مع التحقق المخصص
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور',
            'dir': 'ltr'
        }),
        label="كلمة المرور"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور',
            'dir': 'ltr'
        }),
        label="تأكيد كلمة المرور"
    )
    
    # موافقة على الشروط
    terms_accepted = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="أوافق على شروط الاستخدام وسياسة الخصوصية"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'arabic_name', 'employee_id', 'phone', 
                 'department', 'position', 'direct_manager', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديث queryset للمناصب بناءً على القسم المختار
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['position'].queryset = Position.objects.filter(department_id=department_id)
            except (ValueError, TypeError):
                pass
        
        # إضافة خصائص إضافية للحقول
        self.fields['username'].help_text = "اسم مستخدم فريد (أحرف إنجليزية وأرقام فقط)"
        self.fields['password1'].help_text = "كلمة المرور يجب أن تحتوي على 8 خانات على الأقل، أحرف وأرقام"

    def clean_password1(self):
        """التحقق من كلمة المرور - 8 خانات، أحرف وأرقام"""
        password = self.cleaned_data.get('password1')
        
        if password:
            # التحقق من الطول (8 خانات على الأقل)
            if len(password) < 8:
                raise ValidationError('كلمة المرور يجب أن تحتوي على 8 خانات على الأقل.')
            
            # التحقق من وجود أحرف
            if not re.search(r'[a-zA-Z]', password):
                raise ValidationError('كلمة المرور يجب أن تحتوي على أحرف إنجليزية.')
            
            # التحقق من وجود أرقام
            if not re.search(r'\d', password):
                raise ValidationError('كلمة المرور يجب أن تحتوي على أرقام.')
            
            # التحقق من عدم احتواء مسافات
            if ' ' in password:
                raise ValidationError('كلمة المرور لا يجب أن تحتوي على مسافات.')
        
        return password

    def clean_username(self):
        """التحقق من اسم المستخدم"""
        username = self.cleaned_data.get('username')
        
        if username:
            # التحقق من أن اسم المستخدم يحتوي على أحرف إنجليزية وأرقام فقط
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                raise ValidationError('اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام فقط.')
            
            # التحقق من عدم وجود اسم المستخدم مسبقاً
            if User.objects.filter(username=username).exists():
                raise ValidationError('اسم المستخدم موجود بالفعل.')
        
        return username

    def clean_employee_id(self):
        """التحقق من رقم الموظف"""
        employee_id = self.cleaned_data.get('employee_id')
        
        if employee_id:
            # التحقق من عدم وجود رقم الموظف مسبقاً
            if User.objects.filter(employee_id=employee_id).exists():
                raise ValidationError('رقم الموظف موجود بالفعل.')
        
        return employee_id

    def clean_email(self):
        """التحقق من البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        
        if email:
            # التحقق من عدم وجود البريد الإلكتروني مسبقاً
            if User.objects.filter(email=email).exists():
                raise ValidationError('البريد الإلكتروني موجود بالفعل.')
        
        return email

    def clean_arabic_name(self):
        """التحقق من الاسم العربي"""
        arabic_name = self.cleaned_data.get('arabic_name')
        
        if arabic_name:
            # التحقق من أن الاسم يحتوي على أحرف عربية
            if not re.search(r'[\u0600-\u06FF]', arabic_name):
                raise ValidationError('الاسم يجب أن يحتوي على أحرف عربية.')
        
        return arabic_name

    def clean_terms_accepted(self):
        """التحقق من موافقة المستخدم على الشروط"""
        terms_accepted = self.cleaned_data.get('terms_accepted')
        
        if not terms_accepted:
            raise ValidationError('يجب الموافقة على شروط الاستخدام وسياسة الخصوصية.')
        
        return terms_accepted

    def save(self, commit=True):
        """حفظ المستخدم الجديد"""
        user = super().save(commit=False)
        
        # تعيين البيانات الإضافية
        user.arabic_name = self.cleaned_data['arabic_name']
        user.employee_id = self.cleaned_data['employee_id']
        user.phone = self.cleaned_data['phone']
        user.department = self.cleaned_data['department']
        user.position = self.cleaned_data['position']
        user.direct_manager = self.cleaned_data.get('direct_manager')
        user.email = self.cleaned_data['email']
        
        # تعيين إعدادات افتراضية
        user.is_active = True  # يمكن تغييرها إلى False إذا كان يتطلب موافقة المدير
        user.require_password_change = False  # لأن المستخدم أنشأ كلمة مرور جديدة
        
        if commit:
            user.save()
        
        return user


class PositionsByDepartmentForm(forms.Form):
    """نموذج للحصول على المناصب حسب القسم (AJAX)"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True)
    )