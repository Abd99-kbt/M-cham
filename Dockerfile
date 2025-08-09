# نظام الرسائل المصرفية - Dockerfile
FROM python:3.13-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE myproject.settings

# تثبيت متطلبات النظام
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gettext \
        build-essential \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم غير جذر
RUN adduser --disabled-password --gecos '' appuser

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود المصدري
COPY . /app/

# إنشاء المجلدات المطلوبة
RUN mkdir -p /app/media /app/staticfiles /app/logs

# تغيير ملكية الملفات
RUN chown -R appuser:appuser /app

# تبديل للمستخدم غير الجذر
USER appuser

# تجميع الملفات الثابتة
RUN python manage.py collectstatic --noinput

# تعريض المنفذ
EXPOSE 8000

# الأمر الافتراضي
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]