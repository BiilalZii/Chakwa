# صورة نشر تجريبي لسجل الشكاوى — تعمل على Render / Railway / Fly / أي منصة حاويات
FROM python:3.11-slim

# تجنّب كتابة ملفات .pyc وضمان السجلات اللحظية
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# تثبيت الاعتماديات أولًا للاستفادة من تخزين الطبقات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود التطبيق
COPY . .

# سكربت الإقلاع: تهيئة الجداول + بذر البيانات التجريبية (عاطل) ثم gunicorn
RUN chmod +x ./docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
