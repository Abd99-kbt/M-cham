# Generated migration to update phone field to 3 digits
from django.db import migrations, models
import django.core.validators

def clean_phone_data(apps, schema_editor):
    """تنظيف بيانات الهاتف الموجودة لتتوافق مع النظام الجديد (3 أرقام)"""
    User = apps.get_model('accounts', 'User')
    
    for user in User.objects.all():
        if user.phone:
            # استخراج الأرقام فقط من رقم الهاتف
            phone_digits = ''.join(filter(str.isdigit, user.phone))
            
            if len(phone_digits) >= 3:
                # أخذ آخر 3 أرقام
                user.phone = phone_digits[-3:]
            elif len(phone_digits) > 0:
                # إذا كان أقل من 3 أرقام، اجعله 3 أرقام بإضافة أصفار
                user.phone = phone_digits.zfill(3)
            else:
                # إذا لم يكن هناك أرقام، اجعله 000
                user.phone = '000'
            
            user.save()

def reverse_clean_phone_data(apps, schema_editor):
    """لا يمكن عكس هذه العملية"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_department_accounts_de_is_acti_0ea50a_idx'),
    ]

    operations = [
        # تنظيف البيانات أولاً
        migrations.RunPython(clean_phone_data, reverse_clean_phone_data),
        
        # تعديل هيكل الحقل بعد تنظيف البيانات
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(
                max_length=3, 
                validators=[django.core.validators.RegexValidator(
                    regex='^\\d{3}$', 
                    message='رقم الهاتف يجب أن يتألف من 3 أرقام فقط'
                )], 
                verbose_name='رقم الهاتف'
            ),
        ),
    ]