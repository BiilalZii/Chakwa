#!/bin/sh
# إقلاع النشر التجريبي:
# 1) إنشاء الجداول إن لم تكن موجودة.
# 2) بذر المرفق والبلاغات التجريبية (الأمر عاطل لا يكرر البيانات).
# 3) تشغيل gunicorn على المنفذ الذي تمنحه المنصة (PORT) أو 5000 محليًا.
set -e

flask --app app init-db
flask --app app seed-demo

exec gunicorn \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    app:app
