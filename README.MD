# حزمة أولية لمشروع سجل الشكاوى الإلكتروني — ولاية الأغواط

أضع لك أدناه نموذجًا أوليًا قابلًا للتشغيل، مع تصميم الواجهات، ومخطط قاعدة بيانات إنتاجي مقترح، وواجهة API، ومسودة قرار ولائي ومذكرة عرض، وتقدير تكلفة وتصميم لوحة QR.

> ## تحديث: المشروع أصبح قابلًا للتشغيل فعليًا
>
> تم استخراج الكود المضمَّن في هذه الوثيقة إلى ملفات حقيقية في جذر المستودع، مع تطبيق التحسينات الأمنية والهندسية الموثقة في **[تقرير التحليل](docs/ANALYSIS.md)** — ومنها: قفل مؤقت لمحاولات دخول الإدارة، طابور بريد مع إعادة محاولة، مصيدة روبوتات، هرمزة رموز البحث، معالجة أخطاء التزامن، آلية احتفاظ/حذف، ومجموعة اختبارات آلية.
>
> - نقطة البداية التقنية: [`app.py`](app.py) و[`requirements.txt`](requirements.txt) و[`.env.example`](.env.example)
> - مواصفة API: [`openapi.yaml`](openapi.yaml) — مخطط الإنتاج: [`schema.sql`](schema.sql)
> - الاختبارات: مجلد [`tests/`](tests)
>
> تبقى هذه الوثيقة المرجع التصميمي والتنظيمي الكامل؛ الكود المستخرج هو النسخة التشغيلية المحسّنة منها.

## فهرس المحتويات

1. [النموذج البرمجي الأولي](#1-النموذج-البرمجي-الأولي)
2. [تصميم الواجهات — Wireframes](#2-تصميم-الواجهات--wireframes-لخمس-شاشات)
3. [مخطط قاعدة البيانات المقترح للإنتاج](#3-مخطط-قاعدة-البيانات-المقترح-للإنتاج)
4. [توثيق API بصيغة OpenAPI](#4-توثيق-api-بصيغة-openapi)
5. [مسودة قرار ولائي لتنظيم التجربة](#5-مسودة-قرار-ولائي-لتنظيم-التجربة)
6. [مذكرة عرض المشروع على والي الولاية](#6-مذكرة-عرض-المشروع-على-والي-ولاية-الأغواط)
7. [تقدير أولي لتكلفة المشروع](#7-تقدير-أولي-لتكلفة-المشروع)
8. [نص اللوحة المطبوعة](#8-نص-اللوحة-المطبوعة)
9. [ملاحظات إلزامية قبل الإطلاق الرسمي](#9-ملاحظات-إلزامية-قبل-الإطلاق-الرسمي)

## قرارات مهمة قبل البدء

1. **رمز QR يعرّف المرفق فقط**؛ لا يثبت أن الماسح موجود داخل المرفق، ولا يمنحه صلاحيات خاصة. أي شخص يستطيع فتح الرابط.
2. **لا تُنشر الشكوى الأصلية تلقائيًا.** تُعرض للعموم نسخة راجعها موظف مخوّل ونقّح منها البيانات الشخصية، وبموافقة صاحب الشكوى على النشر. تظل الشكوى المرسلة إلى الجهة المختصة متاحة لها وفق الصلاحيات.
3. النظام **مكمّل** للقنوات القانونية والإدارية القائمة، ولا ينشئ وحده أجلًا قانونيًا للرد. يمكن اعتماد هدف داخلي تجريبي، مثل 15 يوم عمل، بعد مراجعة المصالح القانونية.
4. النموذج التالي للتجربة التقنية، وليس للاستخدام الرسمي المباشر. قبل الإطلاق يجب اعتماد الجهة المسؤولة عن المعالجة، وسياسة الاحتفاظ، والمراسلات الرسمية، ومتطلبات حماية المعطيات.

---

# 1. النموذج البرمجي الأولي

## ماذا يفعل هذا النموذج؟

- يعرض صفحة خاصة بكل مرفق عبر QR.
- يسمح بإيداع شكوى أو اقتراح أو ملاحظة دون إنشاء حساب أو إدخال رقم بطاقة الهوية.
- يرسل الشكوى إلى بريد الجهة المحدد وبريد الأرشيف عند ضبط إعدادات البريد.
- يحفظ الشكوى في قاعدة بيانات على الخادم.
- يعطي صاحب الشكوى رقمًا مرجعيًا ورابط متابعة سريًا.
- يسمح للموظف بمراجعة الشكوى، وتحديث حالتها، ونشر **ملخص منقح** فقط إذا وافق صاحبها.
- لا يتضمن النموذج الأولي رفع صور أو SMS أو حسابات متعددة أو مصادقة متعددة العوامل.

### هيكل المشروع

```text
laghouat-complaints/
├── app.py
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html
│   ├── branch.html
│   ├── new_complaint.html
│   ├── track.html
│   ├── public.html
│   ├── admin_login.html
│   ├── admin.html
│   └── admin_detail.html
└── static/
    └── style.css
```

## `requirements.txt`

```text
Flask>=3.0,<4
Flask-SQLAlchemy>=3.1,<4
Flask-WTF>=1.2,<2
Flask-Limiter>=3.8,<5
python-dotenv>=1.0,<2
qrcode[pil]>=7.4,<9
psycopg[binary]>=3.2,<4
gunicorn>=22,<24
```

## `.env.example`

انسخ الملف إلى `.env`، وغيّر القيم قبل التشغيل.

```env
APP_ENV=development
SECRET_KEY=غيّر-هذه-القيمة-إلى-مفتاح-طويل-وعشوائي
DATABASE_URL=sqlite:///complaints.db

# بريد تجريبي فقط، ويجب استبداله ببريد رسمي معتمد
PILOT_SUPERVISOR_EMAIL=
ARCHIVE_EMAIL=

SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=no-reply@example.dz

# العنوان الذي سيحوّله QR إليه
PUBLIC_BASE_URL=http://127.0.0.1:5000

# أنشئ كلمة المرور المشفرة بالأمر الموضح بعد الكود
ADMIN_PASSWORD_HASH=

# في الإنتاج يُفضّل استخدام Redis بدل الذاكرة المحلية
RATELIMIT_STORAGE_URI=memory://
```

## `app.py`

```python
import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import wraps
from io import BytesIO

import qrcode
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, jsonify, redirect, render_template,
    request, send_file, session, url_for
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("يجب ضبط SECRET_KEY في ملف .env")

os.makedirs("instance", exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secret_key,
    SQLALCHEMY_DATABASE_URI=os.getenv(
        "DATABASE_URL", "sqlite:///complaints.db"
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=1_000_000,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(os.getenv("APP_ENV") == "production"),
)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    default_limits=["1000 per day"],
)

KIND_LABELS = {
    "complaint": "شكوى",
    "suggestion": "اقتراح",
    "praise": "إشادة",
    "observation": "ملاحظة",
}

CATEGORY_LABELS = {
    "waiting": "الانتظار وطول الطابور",
    "reception": "الاستقبال والتعامل",
    "procedure": "الإجراءات والوثائق",
    "service": "رفض أو تعطل خدمة",
    "accessibility": "الولوجية والمرافق",
    "other": "أخرى",
}

STATUS_LABELS = {
    "received": "تم الاستلام",
    "in_review": "قيد المعالجة",
    "answered": "تم الرد",
    "closed": "مغلقة",
}


def utcnow():
    # نخزن وقتًا موحدًا بصيغة UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    name_ar = db.Column(db.String(200), nullable=False)
    description_ar = db.Column(db.String(500), nullable=True)
    supervisor_email = db.Column(db.String(254), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    ref_no = db.Column(db.String(40), unique=True, nullable=True)
    branch_id = db.Column(
        db.Integer, db.ForeignKey("branches.id"), nullable=False
    )
    branch = db.relationship("Branch", backref="complaints")

    kind = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    body_private = db.Column(db.Text, nullable=False)

    # نص منفصل لا يظهر إلا بعد المراجعة والموافقة
    public_text = db.Column(db.Text, nullable=True)
    consent_public = db.Column(db.Boolean, nullable=False, default=False)

    status = db.Column(db.String(30), nullable=False, default="received")
    response_public = db.Column(db.Text, nullable=True)

    # لا نخزن رمز المتابعة نفسه، بل بصمته
    tracking_token_hash = db.Column(db.String(64), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)

    email_status = db.Column(
        db.String(30), nullable=False, default="not_configured"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False
    )
    actor = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


@app.context_processor
def inject_labels():
    return {
        "kind_labels": KIND_LABELS,
        "category_labels": CATEGORY_LABELS,
        "status_labels": STATUS_LABELS,
    }


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    if request.path.startswith("/admin") or request.path.startswith("/track/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def get_branch_or_404(code):
    return Branch.query.filter_by(
        code=code, is_active=True
    ).first_or_404()


def public_query(branch):
    return Complaint.query.filter(
        Complaint.branch_id == branch.id,
        Complaint.public_text.isnot(None),
    )


def create_complaint(branch, kind, category, body, consent_public):
    token = secrets.token_urlsafe(32)
    now = utcnow()

    complaint = Complaint(
        branch_id=branch.id,
        kind=kind,
        category=category,
        body_private=body,
        consent_public=consent_public,
        tracking_token_hash=hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest(),
        content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        status="received",
        created_at=now,
        updated_at=now,
    )

    db.session.add(complaint)
    db.session.flush()

    complaint.ref_no = f"LGH-{now.year}-{complaint.id:06d}"

    db.session.add(AuditEvent(
        complaint_id=complaint.id,
        actor="citizen",
        action="submitted",
        details={"channel": "web_qr"},
        created_at=now,
    ))

    db.session.commit()
    return complaint, token


def send_notification(complaint):
    """
    نموذج تجريبي: يرسل محتوى الشكوى إلى بريد الجهة المحدد وبريد الأرشيف.
    في الإنتاج يُفضّل استخدام خادم بريد رسمي، وقائمة مستلمين معتمدة،
    وطابور إرسال يعيد المحاولة عند التعطل.
    """
    host = os.getenv("SMTP_HOST")
    recipients = []

    if complaint.branch.supervisor_email:
        recipients.append(complaint.branch.supervisor_email)

    archive_email = os.getenv("ARCHIVE_EMAIL")
    if archive_email:
        recipients.append(archive_email)

    recipients = list(dict.fromkeys(recipients))

    if not host or not recipients:
        complaint.email_status = "not_configured"
        db.session.commit()
        return

    message = EmailMessage()
    message["Subject"] = f"شكوى جديدة — {complaint.ref_no}"
    message["From"] = os.getenv("SMTP_FROM", "no-reply@example.dz")
    message["To"] = complaint.branch.supervisor_email or recipients[0]

    message.set_content(
        f"""رقم المرجع: {complaint.ref_no}
المرفق: {complaint.branch.name_ar}
النوع: {KIND_LABELS.get(complaint.kind, complaint.kind)}
الفئة: {CATEGORY_LABELS.get(complaint.category, complaint.category)}
تاريخ الإيداع: {complaint.created_at.isoformat()} UTC

نص البلاغ:
{complaint.body_private}

هذه رسالة آلية من النموذج التجريبي. يرجى التعامل معها عبر القنوات
والإجراءات المعتمدة لدى الجهة.
"""
    )

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            username = os.getenv("SMTP_USERNAME")
            password = os.getenv("SMTP_PASSWORD")
            if username:
                server.login(username, password or "")
            # عنوان الأرشيف لا يظهر كـ BCC في ترويسة البريد.
            server.send_message(message, to_addrs=recipients)

        complaint.email_status = "sent"
    except Exception:
        complaint.email_status = "error"
        app.logger.exception(
            "تعذر إرسال إشعار البريد للمرجع %s", complaint.ref_no
        )

    db.session.commit()


@app.get("/")
def home():
    return redirect(url_for("branch_page", code="LGH-PILOT-001"))


@app.cli.command("init-db")
def init_db():
    """إنشاء الجداول وإضافة مرفق تجريبي."""
    db.create_all()

    branch = Branch.query.filter_by(code="LGH-PILOT-001").first()
    if not branch:
        branch = Branch(
            code="LGH-PILOT-001",
            name_ar="مرفق تجريبي — يحدد لاحقًا بالتنسيق مع الولاية",
            description_ar="نموذج تقني أولي غير رسمي.",
            supervisor_email=os.getenv("PILOT_SUPERVISOR_EMAIL") or None,
            is_active=True,
        )
        db.session.add(branch)
        db.session.commit()

    print("تم إنشاء قاعدة البيانات والمرفق التجريبي.")


@app.get("/q/<code>")
def branch_page(code):
    branch = get_branch_or_404(code)
    recent = public_query(branch).order_by(
        Complaint.created_at.desc()
    ).limit(5).all()

    return render_template(
        "branch.html",
        branch=branch,
        recent=recent,
        public_count=public_query(branch).count(),
    )


@app.get("/q/<code>/new")
def new_complaint(code):
    branch = get_branch_or_404(code)
    return render_template("new_complaint.html", branch=branch)


@app.post("/q/<code>/submit")
@limiter.limit("10 per hour")
def submit_complaint(code):
    branch = get_branch_or_404(code)

    kind = request.form.get("kind", "")
    category = request.form.get("category", "")
    body = request.form.get("body", "").strip()
    consent_public = request.form.get("consent_public") == "yes"

    if kind not in KIND_LABELS:
        flash("يرجى اختيار نوع صحيح للبلاغ.", "error")
        return redirect(url_for("new_complaint", code=code))

    if category not in CATEGORY_LABELS:
        flash("يرجى اختيار فئة صحيحة.", "error")
        return redirect(url_for("new_complaint", code=code))

    if len(body) < 20 or len(body) > 3000:
        flash("يجب أن يكون نص البلاغ بين 20 و3000 حرف.", "error")
        return redirect(url_for("new_complaint", code=code))

    complaint, token = create_complaint(
        branch, kind, category, body, consent_public
    )
    send_notification(complaint)

    return redirect(url_for(
        "track_page", ref=complaint.ref_no, token=token
    ))


@app.get("/track/<ref>/<token>")
def track_page(ref, token):
    complaint = Complaint.query.filter_by(ref_no=ref).first_or_404()
    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    if not hmac.compare_digest(
        complaint.tracking_token_hash, supplied_hash
    ):
        abort(404)

    tracking_url = url_for(
        "track_page", ref=ref, token=token, _external=True
    )
    return render_template(
        "track.html",
        complaint=complaint,
        tracking_url=tracking_url,
    )


@app.get("/q/<code>/public")
def public_archive(code):
    branch = get_branch_or_404(code)
    search = request.args.get("q", "").strip()[:100]

    query = public_query(branch)
    if search:
        query = query.filter(Complaint.public_text.ilike(f"%{search}%"))

    complaints = query.order_by(
        Complaint.created_at.desc()
    ).limit(100).all()

    return render_template(
        "public.html",
        branch=branch,
        complaints=complaints,
        search=search,
    )


@app.get("/qr/<code>.png")
def qr_png(code):
    branch = get_branch_or_404(code)
    base = os.getenv(
        "PUBLIC_BASE_URL", "http://127.0.0.1:5000"
    ).rstrip("/")
    target_url = f"{base}/q/{branch.code}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png", max_age=0)


# ---------- واجهات API العامة ----------

@app.get("/api/v1/branches/<code>")
def api_branch(code):
    branch = get_branch_or_404(code)
    return jsonify({
        "code": branch.code,
        "name_ar": branch.name_ar,
        "public_url": url_for(
            "branch_page", code=branch.code, _external=True
        ),
        "published_count": public_query(branch).count(),
    })


@app.get("/api/v1/branches/<code>/complaints")
def api_public_complaints(code):
    branch = get_branch_or_404(code)

    try:
        limit = min(max(int(request.args.get("limit", "20")), 1), 100)
        offset = max(int(request.args.get("offset", "0")), 0)
    except ValueError:
        return jsonify({"error": "limit/offset غير صالح"}), 400

    complaints = public_query(branch).order_by(
        Complaint.created_at.desc()
    ).offset(offset).limit(limit).all()

    return jsonify({
        "data": [{
            "reference": c.ref_no,
            "type": c.kind,
            "type_ar": KIND_LABELS.get(c.kind, c.kind),
            "category": c.category,
            "category_ar": CATEGORY_LABELS.get(c.category, c.category),
            "public_text": c.public_text,
            "status": c.status,
            "status_ar": STATUS_LABELS.get(c.status, c.status),
            "submitted_at": c.created_at.isoformat() + "Z",
        } for c in complaints],
        "limit": limit,
        "offset": offset,
    })


@app.post("/api/v1/complaints")
@limiter.limit("10 per hour")
@csrf.exempt
def api_create_complaint():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "يجب إرسال JSON"}), 400

    branch = Branch.query.filter_by(
        code=data.get("branch_code"),
        is_active=True,
    ).first()

    if not branch:
        return jsonify({"error": "المرفق غير موجود أو غير نشط"}), 404

    kind = data.get("type")
    category = data.get("category")
    body = data.get("body")

    if kind not in KIND_LABELS:
        return jsonify({"error": "نوع البلاغ غير صالح"}), 400
    if category not in CATEGORY_LABELS:
        return jsonify({"error": "الفئة غير صالحة"}), 400
    if not isinstance(body, str):
        return jsonify({"error": "body يجب أن يكون نصًا"}), 400

    body = body.strip()
    if len(body) < 20 or len(body) > 3000:
        return jsonify({"error": "طول النص يجب أن يكون بين 20 و3000 حرف"}), 400

    consent_public = data.get("consent_public") is True
    complaint, token = create_complaint(
        branch, kind, category, body, consent_public
    )
    send_notification(complaint)

    return jsonify({
        "reference": complaint.ref_no,
        "tracking_token": token,
        "tracking_url": url_for(
            "track_page",
            ref=complaint.ref_no,
            token=token,
            _external=True,
        ),
        "status": complaint.status,
    }), 201


@app.get("/api/v1/complaints/<ref>/track")
def api_track_complaint(ref):
    complaint = Complaint.query.filter_by(ref_no=ref).first_or_404()
    token = request.headers.get("X-Tracking-Token", "")

    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not token or not hmac.compare_digest(
        complaint.tracking_token_hash, supplied_hash
    ):
        abort(404)

    return jsonify({
        "reference": complaint.ref_no,
        "status": complaint.status,
        "status_ar": STATUS_LABELS.get(
            complaint.status, complaint.status
        ),
        "submitted_at": complaint.created_at.isoformat() + "Z",
        "response": complaint.response_public,
    })


# ---------- لوحة الموظف التجريبية ----------

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    error = None

    if request.method == "POST":
        password = request.form.get("password", "")
        if not password_hash:
            error = "لم تُضبط كلمة مرور الإدارة في ملف الإعدادات."
        elif check_password_hash(password_hash, password):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "بيانات الدخول غير صحيحة."

    return render_template("admin_login.html", error=error)


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(200).all()

    counts = {
        "received": Complaint.query.filter_by(status="received").count(),
        "in_review": Complaint.query.filter_by(status="in_review").count(),
        "answered": Complaint.query.filter_by(status="answered").count(),
        "closed": Complaint.query.filter_by(status="closed").count(),
    }

    return render_template(
        "admin.html", complaints=complaints, counts=counts
    )


@app.route("/admin/c/<ref>", methods=["GET", "POST"])
@admin_required
def admin_detail(ref):
    complaint = Complaint.query.filter_by(ref_no=ref).first_or_404()

    if request.method == "POST":
        status = request.form.get("status", "")
        public_text = request.form.get("public_text", "").strip()
        response_public = request.form.get(
            "response_public", ""
        ).strip()

        if status not in STATUS_LABELS:
            flash("حالة غير صحيحة.", "error")
            return redirect(url_for("admin_detail", ref=ref))

        if public_text and not complaint.consent_public:
            flash(
                "لا يمكن نشر نص لهذا البلاغ لأن صاحبه لم يوافق على النشر.",
                "error",
            )
            return redirect(url_for("admin_detail", ref=ref))

        old_status = complaint.status
        complaint.status = status
        complaint.public_text = public_text or None
        complaint.response_public = response_public or None
        complaint.updated_at = utcnow()

        db.session.add(AuditEvent(
            complaint_id=complaint.id,
            actor="admin",
            action="updated",
            details={
                "old_status": old_status,
                "new_status": status,
                "published": bool(public_text),
            },
        ))
        db.session.commit()

        flash("تم حفظ التعديلات.", "success")
        return redirect(url_for("admin_detail", ref=ref))

    return render_template("admin_detail.html", complaint=complaint)


if __name__ == "__main__":
    # للاختبار المحلي فقط، لا تستخدم خادم Flask التطويري في الإنتاج.
    app.run(host="127.0.0.1", port=5000, debug=False)
```

## قوالب الواجهة

### `templates/base.html`

```html
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}سجل الملاحظات والشكاوى{% endblock %}</title>
  <link rel="stylesheet"
        href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{{ url_for('home') }}">
    سجل الملاحظات والشكاوى
  </a>
  <span class="pilot-badge">نموذج تجريبي — ولاية الأغواط</span>
</header>

<main class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="alert {{ category }}">{{ message }}</div>
    {% endfor %}
  {% endwith %}

  {% block content %}{% endblock %}
</main>

<footer class="site-footer">
  <p>
    لا تكتب أرقام الهوية أو المعلومات الصحية أو بيانات أشخاص آخرين.
    هذا النموذج تجريبي ولا يحل محل القنوات القانونية المعتمدة.
  </p>
  <a href="{{ url_for('admin_login') }}">دخول الموظف</a>
</footer>
</body>
</html>
```

### `templates/branch.html`

```html
{% extends "base.html" %}
{% block title %}{{ branch.name_ar }} — سجل الشكاوى{% endblock %}
{% block content %}
<section class="hero">
  <p class="eyebrow">المرفق المحدد بواسطة رمز QR</p>
  <h1>{{ branch.name_ar }}</h1>
  <p>{{ branch.description_ar or "يمكنك تقديم شكوى أو اقتراح أو ملاحظة." }}</p>

  <div class="actions">
    <a class="button primary"
       href="{{ url_for('new_complaint', code=branch.code) }}">
      أرسل بلاغًا
    </a>
    <a class="button secondary"
       href="{{ url_for('public_archive', code=branch.code) }}">
      اطّلع على البلاغات المنشورة
    </a>
  </div>
</section>

<section class="panel">
  <h2>الشفافية</h2>
  <p>
    عدد البلاغات التي نُشرت بعد المراجعة:
    <strong>{{ public_count }}</strong>
  </p>
  <p class="muted">
    لا تظهر الشكوى للعامة تلقائيًا. النشر يقتصر على نسخة راجعها الموظف
    المخوّل بعد إزالة البيانات الشخصية، وبموافقة صاحب البلاغ.
  </p>
</section>

<section class="panel">
  <div class="section-heading">
    <h2>أحدث البلاغات المنشورة</h2>
    <a href="{{ url_for('public_archive', code=branch.code) }}">عرض الكل</a>
  </div>

  {% if recent %}
    {% for c in recent %}
      <article class="complaint-card">
        <div class="card-meta">
          <span>{{ c.ref_no }}</span>
          <span>{{ category_labels.get(c.category, c.category) }}</span>
          <span>{{ status_labels.get(c.status, c.status) }}</span>
        </div>
        <p>{{ c.public_text|truncate(220) }}</p>
      </article>
    {% endfor %}
  {% else %}
    <p class="muted">لا توجد بلاغات منشورة حاليًا.</p>
  {% endif %}
</section>
{% endblock %}
```

### `templates/new_complaint.html`

```html
{% extends "base.html" %}
{% block title %}إرسال بلاغ{% endblock %}
{% block content %}
<section class="panel narrow">
  <a href="{{ url_for('branch_page', code=branch.code) }}">← رجوع</a>
  <h1>إرسال بلاغ إلى</h1>
  <p><strong>{{ branch.name_ar }}</strong></p>

  <form method="post"
        action="{{ url_for('submit_complaint', code=branch.code) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

    <label for="kind">نوع البلاغ</label>
    <select id="kind" name="kind" required>
      {% for value, label in kind_labels.items() %}
        <option value="{{ value }}">{{ label }}</option>
      {% endfor %}
    </select>

    <label for="category">الفئة</label>
    <select id="category" name="category" required>
      {% for value, label in category_labels.items() %}
        <option value="{{ value }}">{{ label }}</option>
      {% endfor %}
    </select>

    <label for="body">نص البلاغ</label>
    <textarea id="body" name="body" minlength="20" maxlength="3000"
              rows="8" required
              placeholder="اشرح ما حدث، ومتى، وما الخدمة التي كنت تطلبها."></textarea>
    <small>من 20 إلى 3000 حرف. لا تذكر أرقام الهوية أو معلومات صحية أو أسماء أشخاص.</small>

    <label class="checkbox">
      <input type="checkbox" name="consent_public" value="yes">
      أوافق على أن تُراجع نسخة منقحة من بلاغي، وقد تُنشر للعموم بعد
      إزالة البيانات الشخصية. عدم الموافقة لا يمنع إرسال البلاغ.
    </label>

    <div class="notice">
      سيظهر لك رقم مرجعي ورابط متابعة سري. احتفظ بالرابط ولا تشاركه مع الآخرين.
    </div>

    <button class="button primary" type="submit">إرسال البلاغ</button>
  </form>
</section>
{% endblock %}
```

### `templates/track.html`

```html
{% extends "base.html" %}
{% block title %}متابعة البلاغ {{ complaint.ref_no }}{% endblock %}
{% block content %}
<section class="panel narrow">
  <p class="eyebrow">تم حفظ البلاغ</p>
  <h1>رقم المتابعة</h1>
  <div class="reference">{{ complaint.ref_no }}</div>

  <p>
    الحالة الحالية:
    <strong>{{ status_labels.get(complaint.status, complaint.status) }}</strong>
  </p>
  <p class="muted">تاريخ الإيداع: {{ complaint.created_at.strftime("%Y-%m-%d %H:%M") }} UTC</p>

  <details>
    <summary>عرض نص البلاغ الذي أرسلته</summary>
    <p class="private-text">{{ complaint.body_private }}</p>
  </details>

  {% if complaint.response_public %}
    <section class="response">
      <h2>الرد</h2>
      <p>{{ complaint.response_public }}</p>
    </section>
  {% else %}
    <p class="muted">لم يُسجل رد بعد.</p>
  {% endif %}

  <label for="tracking-link">رابط المتابعة السري — احتفظ به</label>
  <input id="tracking-link" type="text" readonly value="{{ tracking_url }}">

  <div class="notice warning">
    الرابط السري يتيح لمن يملكه متابعة البلاغ. لا ترسله إلى أشخاص غير موثوقين.
  </div>
</section>
{% endblock %}
```

### `templates/public.html`

```html
{% extends "base.html" %}
{% block title %}البلاغات المنشورة — {{ branch.name_ar }}{% endblock %}
{% block content %}
<section class="panel">
  <a href="{{ url_for('branch_page', code=branch.code) }}">← صفحة المرفق</a>
  <h1>البلاغات المنشورة</h1>
  <p>{{ branch.name_ar }}</p>

  <form method="get" class="search-form">
    <label for="q">بحث في النصوص المنشورة</label>
    <input id="q" name="q" value="{{ search }}" maxlength="100">
    <button class="button secondary" type="submit">بحث</button>
  </form>

  {% for c in complaints %}
    <article class="complaint-card">
      <div class="card-meta">
        <span>{{ c.ref_no }}</span>
        <span>{{ category_labels.get(c.category, c.category) }}</span>
        <span>{{ status_labels.get(c.status, c.status) }}</span>
        <span>{{ c.created_at.strftime("%Y-%m-%d") }}</span>
      </div>
      <p>{{ c.public_text }}</p>
      {% if c.response_public %}
        <div class="response">
          <strong>رد الجهة:</strong>
          <p>{{ c.response_public }}</p>
        </div>
      {% endif %}
    </article>
  {% else %}
    <p class="muted">لا توجد نتائج منشورة.</p>
  {% endfor %}
</section>
{% endblock %}
```

### `templates/admin_login.html`

```html
{% extends "base.html" %}
{% block title %}دخول الموظف{% endblock %}
{% block content %}
<section class="panel narrow">
  <h1>دخول الموظف</h1>
  {% if error %}<div class="alert error">{{ error }}</div>{% endif %}
  <form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label for="password">كلمة المرور</label>
    <input id="password" name="password" type="password" required>
    <button class="button primary" type="submit">دخول</button>
  </form>
  <p class="muted">
    هذه مصادقة تجريبية بكلمة مرور واحدة. لا تصلح وحدها لنظام حكومي إنتاجي.
  </p>
</section>
{% endblock %}
```

### `templates/admin.html`

```html
{% extends "base.html" %}
{% block title %}لوحة الموظف{% endblock %}
{% block content %}
<section class="panel">
  <div class="section-heading">
    <h1>لوحة معالجة البلاغات</h1>
    <form method="post" action="{{ url_for('admin_logout') }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <button class="button secondary" type="submit">خروج</button>
    </form>
  </div>

  <div class="stats">
    <div>جديد: <strong>{{ counts.received }}</strong></div>
    <div>قيد المعالجة: <strong>{{ counts.in_review }}</strong></div>
    <div>تم الرد: <strong>{{ counts.answered }}</strong></div>
    <div>مغلق: <strong>{{ counts.closed }}</strong></div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>المرجع</th>
          <th>المرفق</th>
          <th>النوع</th>
          <th>الفئة</th>
          <th>الحالة</th>
          <th>البريد</th>
          <th>التاريخ</th>
        </tr>
      </thead>
      <tbody>
      {% for c in complaints %}
        <tr>
          <td><a href="{{ url_for('admin_detail', ref=c.ref_no) }}">{{ c.ref_no }}</a></td>
          <td>{{ c.branch.name_ar }}</td>
          <td>{{ kind_labels.get(c.kind, c.kind) }}</td>
          <td>{{ category_labels.get(c.category, c.category) }}</td>
          <td>{{ status_labels.get(c.status, c.status) }}</td>
          <td>{{ c.email_status }}</td>
          <td>{{ c.created_at.strftime("%Y-%m-%d %H:%M") }}</td>
        </tr>
      {% else %}
        <tr><td colspan="7">لا توجد بلاغات.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</section>
{% endblock %}
```

### `templates/admin_detail.html`

```html
{% extends "base.html" %}
{% block title %}معالجة {{ complaint.ref_no }}{% endblock %}
{% block content %}
<section class="panel">
  <a href="{{ url_for('admin_dashboard') }}">← لوحة الموظف</a>
  <h1>{{ complaint.ref_no }}</h1>

  <div class="stats">
    <div>النوع: {{ kind_labels.get(complaint.kind, complaint.kind) }}</div>
    <div>الفئة: {{ category_labels.get(complaint.category, complaint.category) }}</div>
    <div>حالة البريد: {{ complaint.email_status }}</div>
    <div>
      موافقة النشر:
      {{ "نعم" if complaint.consent_public else "لا" }}
    </div>
  </div>

  <h2>النص الأصلي — للاستخدام الداخلي المخوّل فقط</h2>
  <div class="private-text">{{ complaint.body_private }}</div>

  <form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

    <label for="status">الحالة</label>
    <select id="status" name="status">
      {% for value, label in status_labels.items() %}
        <option value="{{ value }}"
          {% if complaint.status == value %}selected{% endif %}>
          {{ label }}
        </option>
      {% endfor %}
    </select>

    <label for="public_text">النسخة المنقحة للنشر — لا تضع أسماء أو بيانات شخصية</label>
    <textarea id="public_text" name="public_text" rows="5">{{
      complaint.public_text or ""
    }}</textarea>
    {% if not complaint.consent_public %}
      <small class="warning-text">
        لم يوافق صاحب البلاغ على النشر. يمنع نشر نسخة منه في هذه الحالة.
      </small>
    {% endif %}

    <label for="response_public">رد الجهة الذي يمكن عرضه لصاحب البلاغ/للعموم</label>
    <textarea id="response_public" name="response_public" rows="5">{{
      complaint.response_public or ""
    }}</textarea>

    <button class="button primary" type="submit">حفظ التعديلات</button>
  </form>
</section>
{% endblock %}
```

### `static/style.css`

```css
:root {
  --navy: #16324f;
  --blue: #146c94;
  --light: #f3f6f8;
  --border: #d9e1e7;
  --text: #17212b;
  --muted: #596875;
  --green: #26734d;
  --red: #9b3030;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--light);
  color: var(--text);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 17px;
  line-height: 1.7;
}

.site-header {
  background: var(--navy);
  color: white;
  padding: 14px max(18px, calc((100% - 1050px) / 2));
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.brand {
  color: white;
  text-decoration: none;
  font-weight: bold;
  font-size: 20px;
}

.pilot-badge {
  font-size: 14px;
  opacity: .9;
}

.container {
  width: min(1050px, calc(100% - 28px));
  margin: 24px auto;
}

.hero, .panel {
  background: white;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 24px;
  margin-bottom: 18px;
}

.hero {
  border-top: 5px solid var(--blue);
}

.narrow { max-width: 720px; margin-inline: auto; }

h1, h2 { line-height: 1.35; }
h1 { font-size: clamp(25px, 4vw, 36px); }
h2 { font-size: 22px; }

.eyebrow, .muted, small { color: var(--muted); }
.eyebrow { font-weight: bold; }

.actions, .section-heading, .card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.button {
  border: 0;
  border-radius: 8px;
  padding: 11px 18px;
  display: inline-block;
  text-decoration: none;
  font: inherit;
  cursor: pointer;
}

.primary { background: var(--blue); color: white; }
.secondary { background: #e9eff3; color: var(--navy); }

form { display: grid; gap: 10px; margin-top: 16px; }
label { font-weight: bold; }
input, textarea, select {
  width: 100%;
  border: 1px solid #aebbc5;
  border-radius: 7px;
  padding: 11px;
  background: white;
  color: var(--text);
  font: inherit;
}
textarea { resize: vertical; }
.checkbox {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-weight: normal;
  margin: 10px 0;
}
.checkbox input { width: auto; margin-top: 8px; }

.notice {
  background: #eef6f9;
  border-right: 4px solid var(--blue);
  padding: 12px;
  margin: 12px 0;
}
.warning { background: #fff5e8; border-color: #aa6a00; }

.complaint-card {
  border-top: 1px solid var(--border);
  padding: 15px 0;
}
.card-meta { color: var(--muted); font-size: 14px; }

.reference {
  padding: 12px;
  background: #eef6f9;
  border-radius: 8px;
  font-size: 24px;
  font-weight: bold;
  direction: ltr;
  text-align: center;
}

.private-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #f7f8f9;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.response {
  border-right: 4px solid var(--green);
  background: #f1f8f3;
  padding: 12px;
  margin-top: 12px;
}

.alert { padding: 12px; margin: 10px 0; border-radius: 8px; }
.alert.error { color: var(--red); background: #fff0f0; }
.alert.success { color: var(--green); background: #eef8f0; }
.warning-text { color: var(--red); }

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  margin: 16px 0;
}
.stats > div {
  background: #f5f7f8;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
}

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 720px; }
th, td { padding: 10px; border-bottom: 1px solid var(--border); text-align: right; }
th { background: #f1f4f6; }

.site-footer {
  padding: 20px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}

@media (max-width: 600px) {
  body { font-size: 16px; }
  .hero, .panel { padding: 17px; }
  .site-header { align-items: flex-start; }
}
```

## تشغيل النموذج محليًا

```bash
python -m venv .venv
source .venv/bin/activate       # في Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

أنشئ بصمة كلمة مرور لوحة الموظف:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('غيّرني-إلى-كلمة-مرور-قوية'))"
```

انسخ الناتج إلى `ADMIN_PASSWORD_HASH` في `.env`، ثم:

```bash
flask --app app init-db
flask --app app run --host 127.0.0.1 --port 5000
```

- صفحة المرفق التجريبي: `http://127.0.0.1:5000/q/LGH-PILOT-001`
- لوحة الموظف: `http://127.0.0.1:5000/admin/login`
- صورة QR للطباعة: `http://127.0.0.1:5000/qr/LGH-PILOT-001.png`

هذا النموذج يحفظ البيانات في SQLite للتجربة. **لا تستخدم خادم Flask التطويري أو SQLite في الإطلاق الرسمي.** الانتقال للإنتاج يحتاج PostgreSQL، HTTPS، نسخًا احتياطيًا مشفرًا، صلاحيات موظفين متعددة، مصادقة قوية، وطابور بريد يعيد المحاولة عند الفشل.

---

# 2. تصميم الواجهات — Wireframes لخمس شاشات

## الشاشة 1: صفحة المرفق

```text
┌───────────────────────────────────────┐
│ سجل الملاحظات والشكاوى | نموذج تجريبي │
├───────────────────────────────────────┤
│ المرفق: [اسم الإدارة أو الفرع]         │
│                                       │
│ [ أرسل شكوى/اقتراح/ملاحظة ]           │
│ [ اطّلع على البلاغات المنشورة ]        │
│                                       │
│ البلاغات المنشورة بعد المراجعة: 12    │
│                                       │
│ أحدث المنشورات:                       │
│ • انتظار طويل — قيد المعالجة           │
│ • اقتراح لتحسين الاستقبال — تم الرد    │
└───────────────────────────────────────┘
```

## الشاشة 2: نموذج الإيداع

```text
┌───────────────────────────────────────┐
│ إرسال بلاغ إلى [اسم المرفق]           │
├───────────────────────────────────────┤
│ النوع:   [شكوى ▼]                      │
│ الفئة:   [الانتظار وطول الطابور ▼]     │
│ النص:                                    │
│ [ اشرح ما حدث، ومتى، وما الخدمة المطلوبة ]│
│                                       │
│ ☐ أوافق على نشر نسخة منقحة بعد مراجعتها │
│                                       │
│ لا تكتب رقم الهوية أو بيانات صحية.      │
│ [ إرسال البلاغ ]                        │
└───────────────────────────────────────┘
```

## الشاشة 3: إيصال الإيداع والمتابعة

```text
┌───────────────────────────────────────┐
│ تم حفظ البلاغ                           │
│ رقم المرجع: LGH-2026-000001            │
│ الحالة: تم الاستلام                    │
│                                       │
│ رابط متابعة سري:                       │
│ [ https://.../track/... ]               │
│                                       │
│ احتفظ بالرابط ولا تشاركه.               │
│ الرد: لم يُسجل رد بعد                   │
└───────────────────────────────────────┘
```

## الشاشة 4: الأرشيف العمومي للمرفق

```text
┌───────────────────────────────────────┐
│ البلاغات المنشورة — [اسم المرفق]       │
│ بحث: [________________] [بحث]           │
├───────────────────────────────────────┤
│ المرجع | الفئة | التاريخ | الحالة       │
│ نص منقح لا يحتوي على أسماء أو بيانات    │
│ رد الإدارة إن وجد                       │
├───────────────────────────────────────┤
│ المرجع | الفئة | التاريخ | الحالة       │
│ نص منقح ...                             │
└───────────────────────────────────────┘
```

## الشاشة 5: لوحة الموظف والمراجعة

```text
┌────────────────────────────────────────┐
│ لوحة معالجة البلاغات                   │
│ جديد: 8 | قيد المعالجة: 4 | تم الرد: 9  │
├────────────────────────────────────────┤
│ المرجع | الفئة | الحالة | وقت الإيداع   │
│ اضغط على مرجع لفتح ملف البلاغ            │
├────────────────────────────────────────┤
│ النص الأصلي — للاستخدام الداخلي فقط     │
│ الحالة: [قيد المعالجة ▼]                 │
│ النص المنقح للنشر: [__________________]  │
│ رد الجهة: [__________________________]   │
│ [حفظ]                                   │
└────────────────────────────────────────┘
```

**قاعدة تصميم:** النص الأصلي والنسخة العمومية حقلان منفصلان. الموظف يكتب النسخة العمومية بعد إزالة أسماء الأشخاص، أرقام الملفات، بيانات الاتصال، والمعلومات الحساسة.

---

# 3. مخطط قاعدة البيانات المقترح للإنتاج

الكود السابق يستخدم قاعدة مبسطة. للإنتاج أوصي بنقل البيانات إلى PostgreSQL مع فصل معلومات الاتصال عن نص الشكوى.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,
    name_ar     TEXT NOT NULL,
    name_fr     TEXT,
    parent_id   UUID REFERENCES organizations(id),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    code            TEXT UNIQUE NOT NULL,
    plate_serial    TEXT UNIQUE NOT NULL,
    name_ar         TEXT NOT NULL,
    address_ar      TEXT,
    supervisor_email TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE complaints (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference           TEXT UNIQUE NOT NULL,
    branch_id           UUID NOT NULL REFERENCES branches(id),
    kind                TEXT NOT NULL
                        CHECK (kind IN
                        ('complaint','suggestion','praise','observation')),
    category_code       TEXT NOT NULL,
    original_text       TEXT NOT NULL,
    public_text         TEXT,
    consent_public      BOOLEAN NOT NULL DEFAULT FALSE,
    consent_public_at   TIMESTAMPTZ,
    publication_status  TEXT NOT NULL DEFAULT 'private'
                        CHECK (publication_status IN
                        ('private','pending','published','rejected')),
    status              TEXT NOT NULL DEFAULT 'received'
                        CHECK (status IN
                        ('received','in_review','answered','closed')),
    tracking_token_hash BYTEA NOT NULL,
    content_sha256      CHAR(64) NOT NULL,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    retention_until     DATE
);

-- معلومات الاتصال اختيارية، مشفرة، ومنفصلة عن نص الشكوى.
-- النموذج الأولي أعلاه لا يجمع البريد أو الهاتف.
CREATE TABLE complaint_private_contact (
    complaint_id UUID PRIMARY KEY REFERENCES complaints(id),
    email_ciphertext BYTEA,
    phone_ciphertext BYTEA,
    encryption_key_id TEXT,
    delete_after TIMESTAMPTZ
);

CREATE TABLE complaint_responses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id    UUID NOT NULL REFERENCES complaints(id),
    author_org_id   UUID REFERENCES organizations(id),
    response_text   TEXT NOT NULL,
    public_response BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- سجل التدقيق: صلاحيات التطبيق تمنع تعديل أو حذف السجلات السابقة.
CREATE TABLE complaint_events (
    id              BIGSERIAL PRIMARY KEY,
    complaint_id    UUID NOT NULL REFERENCES complaints(id),
    actor_type      TEXT NOT NULL,
    actor_id        TEXT,
    action          TEXT NOT NULL,
    old_status      TEXT,
    new_status      TEXT,
    details         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- طابور بريد لإعادة المحاولة عند انقطاع SMTP.
CREATE TABLE notification_outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id    UUID NOT NULL REFERENCES complaints(id),
    recipient       TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'pending'
                    CHECK (state IN
                    ('pending','sent','retry','failed')),
    attempts        INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ,
    provider_id     TEXT,
    last_error_code TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at         TIMESTAMPTZ
);

CREATE INDEX idx_complaints_branch_date
    ON complaints(branch_id, submitted_at DESC);

CREATE INDEX idx_complaints_status_date
    ON complaints(status, submitted_at);

CREATE INDEX idx_complaints_publication
    ON complaints(publication_status, submitted_at DESC);

CREATE INDEX idx_events_complaint_date
    ON complaint_events(complaint_id, created_at);
```

في الإنتاج، لا يكفي إنشاء جدول تدقيق وتسميته “غير قابل للتعديل”. يجب ضبط صلاحيات قاعدة البيانات، ونسخ احتياطية مشفرة، واختبار الاسترجاع، وربط سجلات التدقيق بأرشيف مستقل عند الحاجة.

---

# 4. توثيق API بصيغة OpenAPI

الواجهة التالية للقراءة العامة والإيداع والمتابعة. لا تتضمن API لوحة الموظف، التي تكون محمية بتسجيل دخول إداري.

احفظها في `openapi.yaml`:

```yaml
openapi: 3.1.0
info:
  title: واجهة سجل الشكاوى — النموذج التجريبي
  version: 0.1.0
  description: >
    واجهة عامة لتحديد المرفق، قراءة البلاغات المنشورة بعد مراجعتها،
    وإيداع بلاغ جديد. لا تعرض هذه الواجهة الشكوى الأصلية للعامة.

servers:
  - url: http://127.0.0.1:5000

paths:
  /api/v1/branches/{code}:
    get:
      summary: معلومات المرفق
      parameters:
        - name: code
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: بيانات المرفق
          content:
            application/json:
              schema:
                type: object
                properties:
                  code: { type: string }
                  name_ar: { type: string }
                  public_url: { type: string }
                  published_count: { type: integer }
        "404":
          description: المرفق غير موجود أو غير نشط

  /api/v1/branches/{code}/complaints:
    get:
      summary: قراءة البلاغات المنشورة فقط
      parameters:
        - name: code
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        "200":
          description: قائمة البلاغات المنشورة
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/PublicComplaint"
                  limit: { type: integer }
                  offset: { type: integer }

  /api/v1/complaints:
    post:
      summary: إيداع بلاغ جديد
      description: >
        لا يتطلب حسابًا. يجب تطبيق حماية إضافية من الإغراق قبل إطلاق الخدمة.
        موافقة النشر اختيارية ولا تمنع الإيداع عند رفضها.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - branch_code
                - type
                - category
                - body
              properties:
                branch_code:
                  type: string
                  example: LGH-PILOT-001
                type:
                  type: string
                  enum: [complaint, suggestion, praise, observation]
                category:
                  type: string
                  enum:
                    - waiting
                    - reception
                    - procedure
                    - service
                    - accessibility
                    - other
                body:
                  type: string
                  minLength: 20
                  maxLength: 3000
                consent_public:
                  type: boolean
                  default: false
      responses:
        "201":
          description: تم إنشاء البلاغ
          content:
            application/json:
              schema:
                type: object
                properties:
                  reference: { type: string }
                  tracking_token: { type: string }
                  tracking_url: { type: string }
                  status: { type: string }
        "400":
          description: بيانات غير صالحة
        "404":
          description: المرفق غير موجود

  /api/v1/complaints/{reference}/track:
    get:
      summary: متابعة بلاغ باستخدام رمز المتابعة السري
      parameters:
        - name: reference
          in: path
          required: true
          schema:
            type: string
      security:
        - TrackingToken: []
      responses:
        "200":
          description: حالة البلاغ والرد
          content:
            application/json:
              schema:
                type: object
                properties:
                  reference: { type: string }
                  status: { type: string }
                  status_ar: { type: string }
                  submitted_at: { type: string, format: date-time }
                  response: { type: [string, "null"] }
        "404":
          description: المرجع أو رمز المتابعة غير صحيح

components:
  securitySchemes:
    TrackingToken:
      type: apiKey
      in: header
      name: X-Tracking-Token

  schemas:
    PublicComplaint:
      type: object
      properties:
        reference: { type: string }
        type: { type: string }
        type_ar: { type: string }
        category: { type: string }
        category_ar: { type: string }
        public_text: { type: string }
        status: { type: string }
        status_ar: { type: string }
        submitted_at: { type: string, format: date-time }
```

---

# 5. مسودة قرار ولائي لتنظيم التجربة

> **تنبيه:** هذه مسودة تنظيمية للعرض والمراجعة، وليست نصًا نافذًا أو استشارة قانونية. يجب أن يراجعها مكتب الشؤون القانونية في الولاية، خصوصًا في ما يتعلق بالاختصاص، وحماية المعطيات، وآجال الرد، وطرق الأرشفة.

## مشروع قرار ولائي

**الجمهورية الجزائرية الديمقراطية الشعبية**  
**ولاية الأغواط**

**مشروع قرار ولائي رقم: …… مؤرخ في: ……**  
**يتضمن إطلاق تجربة سجل إلكتروني للملاحظات والشكاوى والاقتراحات عبر رمز الاستجابة السريعة QR**

إن والي ولاية الأغواط،

- بناءً على القانون رقم **12-07** المتعلق بالولاية؛
- وبناءً على القانون رقم **11-10** المتعلق بالبلدية، في حدود المرافق والجهات المعنية؛
- وبناءً على المرسوم التنفيذي رقم **88-131** المتعلق بتنظيم العلاقات بين الإدارة والمواطن؛
- وبناءً على القانون رقم **18-07** المتعلق بحماية الأشخاص الطبيعيين في مجال معالجة المعطيات ذات الطابع الشخصي، وما قد يطرأ عليه من تعديل أو تتميم؛
- وبعد استكمال رأي المصالح القانونية والتقنية المختصة؛

**يقرر ما يأتي:**

### المادة 1
يهدف هذا القرار إلى إطلاق تجربة محدودة لسجل إلكتروني للملاحظات والشكاوى والاقتراحات، يستعمل رمز QR لتعريف المرفق وتمكين المواطن من إيداع بلاغ إلكتروني ومتابعته.

### المادة 2
تطبق التجربة على المصالح والمرافق المحددة في **ملحق هذا القرار**، التابعة للولاية أو المشاركة بموجب موافقة أو اتفاق مكتوب. ولا يمتد نطاق القرار إلى جهة مستقلة أو مرفق غير مشارك إلا بعد استكمال الإجراء القانوني المناسب.

### المادة 3
لا يحل السجل الإلكتروني محل القنوات الإدارية والقانونية المعمول بها، ولا يمس بحق المواطن في استعمال طرق التظلم أو الطعن أو التبليغ المنصوص عليها في التشريعات السارية.

### المادة 4
يُمنح كل مرفق مشارك رمزًا ورقم لوحة مرجعيين. ويحدد الرمز المرفق المقصود تقنيًا، ولا يعد إثباتًا لمكان وجود المستخدم أو هويته.

### المادة 5
يُمنح صاحب البلاغ رقمًا مرجعيًا، ويُوجّه البلاغ إلى المصلحة المختصة وفق دليل توجيه معتمد. وتلتزم الجهة المشاركة بتحديد موظف مسؤول عن الاستلام والمتابعة، مع تسجيل مراحل المعالجة.

### المادة 6
تحدد كل جهة مشاركة، بالتنسيق مع منسق المشروع، هدفًا داخليًا لمعالجة البلاغات. ولا يفسر الهدف التجريبي على أنه تعديل لأي أجل قانوني مقرر في نص أعلى أو خاص.

> يمكن اقتراح هدف داخلي أولي قدره **15 يوم عمل** لأغراض قياس الأداء، بشرط موافقة المصالح القانونية والجهات المشاركة. لا يُطبع هذا الأجل على اللوحة قبل اعتماده رسميًا.

### المادة 7
لا ينشر نص البلاغ الأصلي تلقائيًا. ويجوز نشر نسخة منقحة بعد:
1. موافقة منفصلة وواضحة من صاحب البلاغ على النشر؛
2. مراجعة بشرية من موظف مخوّل؛
3. إزالة الأسماء، وأرقام الهوية والملفات، وبيانات الاتصال، والمعلومات الصحية، وكل ما قد يؤدي إلى تحديد الأشخاص.

### المادة 8
لا تُنشر البلاغات التي تتضمن اتهامات شخصية أو معلومات حساسة أو ما قد يشكل مساسًا بحقوق الغير. وتحال هذه البلاغات، بحسب طبيعتها، عبر مسار داخلي سري إلى الجهة المختصة، وفق التشريعات السارية.

### المادة 9
تجمع المنصة الحد الأدنى من البيانات اللازمة لاستلام البلاغ ومتابعته. ولا يطلب رقم بطاقة الهوية الوطنية في النموذج التجريبي. وتحدد الجهة المسؤولة عن المعالجة، وأساس المعالجة، ومدة الاحتفاظ، وحقوق أصحاب البيانات بعد استكمال مراجعة متطلبات القانون رقم 18-07 والإجراءات التي تطلبها السلطة المختصة بحماية المعطيات.

### المادة 10
تتخذ التدابير التقنية والتنظيمية اللازمة لحماية النظام، ومنها ضبط صلاحيات المستخدمين، وتسجيل العمليات الإدارية، والنسخ الاحتياطي، وإدارة الحوادث الأمنية، ومنع الدخول غير المصرح به.

### المادة 11
يكلف منسق ولائي للمشروع بإعداد تقرير دوري يتضمن، على الأقل، عدد البلاغات حسب الفئة والمرفق، ونسب الرد، ومتوسط مدة المعالجة، والبلاغات المتأخرة، ونتائج رضا المستخدمين، دون نشر بيانات شخصية.

### المادة 12
تستمر التجربة مدة **ستة أشهر** من تاريخ التشغيل الفعلي، وتُقيّم نتائجها قبل أي تعميم أو تمديد.

### المادة 13
يكلف كل فيما يخصه، الأمين العام للولاية، ومسؤولو المصالح المشاركة، والمصالح التقنية والقانونية المختصة، بتنفيذ هذا القرار.

### المادة 14
ينشر هذا القرار ويبلغ إلى الجهات المعنية.

حرر بالأغواط في: ……  
والي ولاية الأغواط  
الإمضاء والختم

**ملاحظة قانونية:** يجب على مكتب الولاية التحقق من الصياغة النهائية، ومن النصوص النافذة وتعديلاتها، ومن مدى الحاجة إلى تصريح أو ترخيص أو إجراء لدى السلطة الوطنية المختصة بحماية المعطيات الشخصية، قبل التشغيل.

---

# 6. مذكرة عرض المشروع على والي ولاية الأغواط

**إلى السيد والي ولاية الأغواط**  
**الموضوع: طلب الموافقة المبدئية على إطلاق تجربة سجل إلكتروني للشكاوى والملاحظات عبر QR**

يشرفني أن أرفع إلى سيادتكم مقترح إطلاق تجربة محدودة لنظام إلكتروني يستقبل شكاوى وملاحظات واقتراحات المواطنين في بعض المصالح والمرافق بولاية الأغواط، من خلال رمز QR يوضع في مكان واضح داخل كل مرفق مشارك.

## أ. هدف المشروع

- تسهيل إيداع الملاحظات والشكاوى دون تحميل تطبيق.
- توجيه البلاغ مباشرة إلى المصلحة المعنية والجهة الوصية المحددة.
- منح المشتكي رقمًا مرجعيًا ورابط متابعة.
- تمكين المواطن من الاطلاع على **نسخ منقحة ومعتمدة للنشر**، مع إظهار حالة المعالجة والرد الرسمي.
- توفير إحصاءات تساعد الولاية على تحديد المشكلات المتكررة وتحسين الخدمة.

## ب. نطاق التجربة المقترح

- مدة التجربة: **ستة أشهر** بعد انتهاء الإعداد والاختبار.
- النطاق المقترح: **خمسة مرافق أو مصالح مختارة، ونحو عشرة مواضع QR**.
- تحديد المرافق وأسماء الموظفين المسؤولين عن المتابعة يتم بملحق لاحق.
- لا تتضمن النسخة الأولى جمع رقم الهوية الوطنية أو استقبال المرفقات، تجنبًا لزيادة المخاطر القانونية والتقنية.

## ج. طريقة العمل

1. يمسح المواطن رمز QR الخاص بالمرفق.
2. يختار نوع البلاغ وفئته ويكتب نصه.
3. يحصل على رقم مرجعي ورابط متابعة سري.
4. يُرسل البلاغ إلى البريد الرسمي المعتمد ويُحفظ في قاعدة بيانات الخادم.
5. يراجع الموظف المختص البلاغ، ويحدث حالته، ويدخل الرد.
6. لا يظهر للعموم إلا نص منقح، وبعد موافقة صاحب البلاغ ومراجعته.

## د. ما لا يقوم به النظام

- لا يستبدل التظلمات أو المسارات القانونية الرسمية.
- لا يثبت QR وجود المواطن في المرفق.
- لا ينشر النص الخام آليًا.
- لا ينشئ أجلًا قانونيًا للرد من دون سند أو اعتماد رسمي.
- لا يستقبل بلاغات الطوارئ التي تتطلب تدخلًا فوريًا.

## هـ. متطلبات القرار والتسيير

يرجى، عند الموافقة المبدئية:

1. تعيين مصلحة راعية للمشروع ومنسق ولائي.
2. تكليف المصالح القانونية والتقنية بمراجعة المشروع والنص المقترح.
3. اختيار المرافق المشاركة وتحديد بريد رسمي مسؤول لكل مرفق.
4. تحديد موقع الخادم وآلية النسخ الاحتياطي والصلاحيات.
5. اعتماد سياسة واضحة للنشر والخصوصية والاحتفاظ بالبيانات.
6. اعتماد مؤشر زمني داخلي للمعالجة، دون المساس بأي أجل قانوني آخر.
7. الموافقة على إطلاق مرحلة تجريبية قبل أي تعميم.

## و. مؤشرات تقييم مقترحة

- نسبة البلاغات التي تم استلامها وتوجيهها بنجاح.
- نسبة الردود ضمن الهدف الداخلي المعتمد.
- متوسط مدة معالجة البلاغ.
- أكثر الفئات تكرارًا.
- نسبة البلاغات التي أعيد فتحها بسبب عدم رضا المشتكي.
- رضا المستخدمين وسهولة استخدام المنصة.
- عدد الحوادث المتعلقة بالخصوصية أو الأمن؛ والهدف أن يكون صفرًا.

## ز. المرفقات المقترحة

1. عرض أولي للواجهات.
2. نموذج رمز QR واللوحة.
3. مسودة قرار ولائي.
4. تقدير تكلفة أولي.
5. خطة حماية البيانات والأمن.
6. قائمة المرافق المقترحة، بعد اختيارها من الولاية.

وتفضلوا بقبول فائق الاحترام والتقدير.

الاسم: ……  
الصفة/الجهة: ……  
التاريخ: ……  
التوقيع: ……

---

# 7. تقدير أولي لتكلفة المشروع

هذا **تقدير تخطيطي** وليس عرض سعر أو اعتمادًا ماليًا. افترضت: 10 نقاط QR، خمسة مرافق، ستة أشهر للتجربة، واجهة عربية متوافقة مع الهاتف، بريد رسمي موجود، وعدم إدخال SMS أو USSD أو رفع الصور في المرحلة الأولى.

## تكلفة الإعداد مرة واحدة

| البند | تقدير تقريبي بالدينار الجزائري |
|---|---:|
| دراسة الإجراءات والمراجعة القانونية الأولية | 350,000 – 600,000 |
| تصميم الواجهات وإعداد المحتوى العربي/الفرنسي | 300,000 – 550,000 |
| تطوير النظام ولوحة الإدارة وواجهات API والاختبار | 3,600,000 – 5,800,000 |
| مراجعة أمنية واختبار اختراق ومراجعة الخصوصية | 500,000 – 1,000,000 |
| النشر والتدريب وإعداد دليل الاستعمال | 300,000 – 550,000 |
| تصنيع 10 لوحات QR وتركيبها | 100,000 – 250,000 |
| خادم ونسخ احتياطي إذا لم تتوفر بنية حكومية مناسبة | 1,200,000 – 2,400,000 |
| احتياط تقريبي للتغييرات والتكاليف غير المتوقعة | 635,000 – 1,115,000 |
| **المجموع التقريبي للإعداد** | **نحو 7,000,000 – 12,300,000** |

## تكلفة التشغيل السنوية

| البند | تقدير تقريبي سنوي |
|---|---:|
| صيانة ودعم فني | 700,000 – 1,200,000 |
| استضافة ونسخ احتياطي ومراقبة | 250,000 – 600,000 |
| تنسيق ومراجعة المحتوى والبلاغات | 600,000 – 1,200,000 |
| بريد ونطاق ومراقبة أمنية أساسية | 50,000 – 200,000 |
| **المجموع السنوي التقريبي** | **1,600,000 – 3,200,000** |

### تقدير السنة الأولى

- مع شراء خادم جديد: **نحو 8,600,000 – 15,500,000 دج**.
- إذا كان لدى الولاية خادم وبنية نسخ احتياطي مناسبين، يمكن تخفيض بند الإعداد بما يقارب **1,200,000 – 2,400,000 دج**.
- لا يشمل التقدير رسائل SMS أو USSD، أو تكاملًا مع أنظمة وطنية، أو ضرائب ورسومًا قد يحددها مسار الصفقة، أو تكاليف موظفين إضافيين إذا احتاج التشغيل إلى توظيف جديد.

قبل اعتماد الميزانية، ينبغي طلب عروض فعلية من مزودين أو فرق تقنية مؤهلة، وتحديد ما إذا كان العمل سينجز داخليًا أو بصفقة خدمات.

---

# 8. نص اللوحة المطبوعة

## النص العربي المقترح

```text
ولاية الأغواط
[اسم الإدارة أو المرفق]

سجل الملاحظات والشكاوى الإلكتروني

امسح الرمز لتقديم شكوى أو اقتراح أو ملاحظة
أو للاطلاع على البلاغات المنشورة الخاصة بهذا المرفق.

• الخدمة مجانية ولا تحتاج إلى تحميل تطبيق.
• سيظهر لك رقم مرجعي لمتابعة البلاغ.
• لا تكتب رقم بطاقة الهوية أو معلومات صحية أو بيانات أشخاص آخرين.
• لا تُنشر البلاغات تلقائيًا؛ لا تظهر للعموم إلا نسخة منقحة
  بعد المراجعة وبموافقة صاحب البلاغ.
• هذا السجل مكمّل للقنوات الإدارية والقانونية المعتمدة.

[رمز QR]

رابط بديل: [رابط قصير رسمي]
رقم اللوحة: [LGH-…]
```

## النص الفرنسي المقترح

```text
Wilaya de Laghouat
[Nom de l’administration ou de l’établissement]

Registre numérique des observations et réclamations

Scannez le code pour déposer une réclamation,
une suggestion ou une observation, ou consulter
les publications concernant cet établissement.

Service gratuit, sans application à installer.
Un numéro de référence vous sera fourni.
Ne saisissez pas votre numéro d’identité, des données
de santé ni les informations personnelles d’autrui.
Les publications ne sont pas automatiques : seul un texte
vérifié et anonymisé peut être publié, avec l’accord
de son auteur.
Ce registre complète les voies administratives et légales existantes.

Code QR
Lien alternatif : [lien officiel]
N° de plaque : [LGH-…]
```

## مواصفات اللوحة

- حجم A4 أو A3، ويفضل مادة مقاومة للرطوبة والعبث.
- رمز QR أسود على خلفية بيضاء، لا يقل عن 5×5 سم.
- طباعة رابط بديل ورقم اللوحة لمن لا يستطيع المسح.
- عدم وضع شعار رسمي أو ختم قبل الحصول على موافقة الجهة المختصة.
- تثبيت اللوحة في مكان ظاهر وسهل الوصول، مع اختبار الرمز على عدة هواتف.
- استخدام رابط ديناميكي رسمي يمكن تغييره دون إعادة طباعة اللوحات.
- فحص دوري للوحة لمنع لصق رمز QR مزيف فوق الرمز المعتمد.

---

# 9. ملاحظات إلزامية قبل الإطلاق الرسمي

1. مراجعة المشروع من مصلحة الشؤون القانونية في الولاية، والتحقق من النصوص القانونية النافذة وتعديلاتها.
2. تحديد الجهة التي تتحمل مسؤولية معالجة البيانات، والجهات المخولة بالاطلاع.
3. التحقق من الإجراءات المطلوبة لدى السلطة الوطنية المختصة بحماية المعطيات ذات الطابع الشخصي.
4. استخدام بريد رسمي وخادم معتمدين من الجهة، وعدم استخدام بريد شخصي أو خادم تجريبي.
5. تحديد مدة الاحتفاظ بالشكاوى وسجلات المتابعة قبل جمع بيانات فعلية.
6. إضافة حسابات متعددة وصلاحيات مختلفة ومصادقة قوية للموظفين.
7. إضافة طابور بريد وإعادة المحاولة وسجل تدقيق موثوق؛ فالنموذج البرمجي أعلاه لا يعيد الإرسال تلقائيًا عند تعطل البريد.
8. تجربة النظام داخل مرفق أو اثنين أولًا، ثم توسيعه بعد تقييم النتائج.

**التوصية العملية:** ابدأ بموافقة مبدئية من والي ولاية الأغواط على مرحلة إعداد وتجربة تقنية محدودة، ثم اعتمد قائمة المرافق، والبريد الرسمي، والخادم، والنص التنظيمي قبل توزيع اللوحات أو فتح النظام للجمهور.