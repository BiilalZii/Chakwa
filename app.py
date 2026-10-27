"""سجل الملاحظات والشكاوى الإلكتروني — النموذج التجريبي المحسّن.

نسخة تشغيلية من النموذج الموثق في README.MD، تتضمن:
- قفلًا مؤقتًا لمحاولات دخول الإدارة وتسجيلها (AuthEvent).
- طابور بريد (NotificationOutbox) مع إعادة محاولة وتراجع أسي.
- مصيدة روبوتات (Honeypot) في النموذج والـAPI.
- هرمزة رموز LIKE في البحث، ومعالجة أخطاء التزامن عند توليد المرجع.
- سياسة احتفاظ بالبيانات عبر أمر retention-cleanup.
- ترويسة HSTS في الإنتاج، وصفحات أخطاء موحّدة.
"""

import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
import time
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from io import BytesIO

import click
import qrcode
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, jsonify, redirect, render_template,
    request, send_file, session, url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError
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

# ----------------------------------------------------------------------
# إعدادات قابلة للضبط عبر متغيرات البيئة
# ----------------------------------------------------------------------
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "730"))
NOTIFICATION_MAX_ATTEMPTS = int(
    os.getenv("NOTIFICATION_MAX_ATTEMPTS", "5")
)
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
NOTIFICATION_BACKOFF_BASE = 60  # ثانية، تتضاعف مع كل محاولة

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
    """وقت موحد بصيغة UTC دون منطقة (يُخزَّن ساذجًا في SQLite أيضًا)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ----------------------------------------------------------------------
# النماذج
# ----------------------------------------------------------------------
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
    retention_until = db.Column(db.Date, nullable=True)
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


class NotificationOutbox(db.Model):
    """طابور بريد: يتيح إعادة المحاولة عند تعطل SMTP دون تعليق طلب المواطن."""

    __tablename__ = "notification_outbox"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False
    )
    complaint = db.relationship("Complaint", backref="outbox_items")
    recipient = db.Column(db.String(254), nullable=False)
    state = db.Column(
        db.String(20), nullable=False, default="pending",
        doc="pending | retry | sent | failed",
    )
    attempts = db.Column(db.Integer, nullable=False, default=0)
    next_attempt_at = db.Column(
        db.DateTime, nullable=False, default=utcnow
    )
    provider_id = db.Column(db.String(200), nullable=True)
    last_error_code = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)


class AuthEvent(db.Model):
    """سجل محاولات دخول لوحة الإدارة (دون تخزين كلمات المرور)."""

    __tablename__ = "auth_events"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class RetentionLog(db.Model):
    """أثر تدقيقي لعمليات الحذف الدورية دون أي بيانات شخصية."""

    __tablename__ = "retention_logs"

    id = db.Column(db.Integer, primary_key=True)
    deleted_count = db.Column(db.Integer, nullable=False, default=0)
    ran_at = db.Column(db.DateTime, nullable=False, default=utcnow)


# سجل مؤقت في الذاكرة لمحاولات الدخول الفاشلة لكل IP (القفل الأولي).
# في الإنتاج متعدد العمال يُنقل إلى Redis أو إلى جدول قاعدة البيانات.
_failed_logins: dict[str, list[float]] = {}


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
    if os.getenv("APP_ENV") == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if request.path.startswith("/admin") or request.path.startswith("/track/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404,
                           message="الصفحة أو المرفق غير موجود."), 404


@app.errorhandler(429)
def too_many_requests(_error):
    return render_template(
        "error.html", code=429,
        message="عدد الطلبات كبير جدًا. انتظر قليلًا ثم أعد المحاولة."
    ), 429


@app.errorhandler(500)
def internal_error(_error):
    db.session.rollback()
    return render_template(
        "error.html", code=500,
        message="حدث خطأ داخلي. لم تُفقد بيانات البلاغ إن كان قد أُنشئ، "
                "ويمكنك المتابعة برقمك المرجعي."
    ), 500


# ----------------------------------------------------------------------
# دوال مساعدة
# ----------------------------------------------------------------------
def get_branch_or_404(code):
    return Branch.query.filter_by(
        code=code, is_active=True
    ).first_or_404()


def public_query(branch):
    return Complaint.query.filter(
        Complaint.branch_id == branch.id,
        Complaint.public_text.isnot(None),
    )


def escape_like(value):
    """هرمزة رموز LIKE حتى لا تُفسد `%` و`_` الواردة من المستخدم البحث."""
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def is_honeypot_triggered(source):
    """حقل مخفي لا يملؤه إلا برنامج آلي. وجود قيمة فيه يعني طلبًا مشبوهًا."""
    return bool((source.get("website") or "").strip())


def _login_failures(ip):
    now = time.time()
    window = LOGIN_LOCKOUT_MINUTES * 60
    failures = [t for t in _failed_logins.get(ip, []) if now - t < window]
    _failed_logins[ip] = failures
    return failures


def _record_failed_login(ip):
    _failed_logins.setdefault(ip, []).append(time.time())


def _clear_failed_logins(ip):
    _failed_logins.pop(ip, None)


def create_complaint(branch, kind, category, body, consent_public):
    """إنشاء بلاغ مع إعادة محاولة عند تعارض مفتاح المرجع تحت التزامن."""
    token = secrets.token_urlsafe(32)
    now = utcnow()

    last_error = None
    for _attempt in range(5):
        try:
            complaint = Complaint(
                branch_id=branch.id,
                kind=kind,
                category=category,
                body_private=body,
                consent_public=consent_public,
                tracking_token_hash=hashlib.sha256(
                    token.encode("utf-8")
                ).hexdigest(),
                content_hash=hashlib.sha256(
                    body.encode("utf-8")
                ).hexdigest(),
                status="received",
                retention_until=now.date() + timedelta(days=RETENTION_DAYS),
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

            enqueue_notifications(complaint, now)
            db.session.commit()
            return complaint, token
        except IntegrityError as exc:
            db.session.rollback()
            last_error = exc

    raise RuntimeError(
        "تعذر إنشاء البلاغ بعد عدة محاولات بسبب تعارض في قاعدة البيانات"
    ) from last_error


def enqueue_notifications(complaint, now=None):
    """إضافة مستلمي البريد إلى طابور الإرسال بدل الإرسال المتزامن."""
    now = now or utcnow()
    recipients = []
    if complaint.branch.supervisor_email:
        recipients.append(complaint.branch.supervisor_email)
    archive_email = os.getenv("ARCHIVE_EMAIL")
    if archive_email:
        recipients.append(archive_email)
    recipients = list(dict.fromkeys(recipients))

    if not recipients:
        complaint.email_status = "not_configured"
        return

    for recipient in recipients:
        db.session.add(NotificationOutbox(
            complaint_id=complaint.id,
            recipient=recipient,
            state="pending",
            next_attempt_at=now,
        ))
    complaint.email_status = "queued"


def build_email_message(complaint):
    message = EmailMessage()
    message["Subject"] = f"شكوى جديدة — {complaint.ref_no}"
    message["From"] = os.getenv("SMTP_FROM", "no-reply@example.dz")
    message["To"] = (
        complaint.branch.supervisor_email
        or os.getenv("ARCHIVE_EMAIL", "")
    )
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
    return message


def send_one_notification(item):
    """محاولة إرسال رسالة واحدة عبر SMTP. ترفع استثناء عند الفشل."""
    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("SMTP_HOST غير مضبوط")

    message = build_email_message(item.complaint)
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        if username:
            server.login(username, password or "")
        # عنوان الأرشيف لا يظهر كـ BCC في ترويسة البريد.
        server.send_message(message, to_addrs=[item.recipient])


def process_outbox(limit=25):
    """معالجة رسائل الطابور المستحقة مع تراجع أسي وإعادة محاولة."""
    now = utcnow()
    pending = NotificationOutbox.query.filter(
        NotificationOutbox.state.in_(["pending", "retry"]),
        NotificationOutbox.next_attempt_at <= now,
    ).order_by(NotificationOutbox.id).limit(limit).all()

    for item in pending:
        try:
            send_one_notification(item)
            item.state = "sent"
            item.sent_at = utcnow()
            item.last_error_code = None
            item.complaint.email_status = "sent"
        except Exception as exc:  # noqa: BLE001 - نحفظ أي عطل لمراجعته
            item.attempts += 1
            item.last_error_code = str(exc)[:300]
            if item.attempts >= NOTIFICATION_MAX_ATTEMPTS:
                item.state = "failed"
                item.complaint.email_status = "error"
                app.logger.error(
                    "فشل نهائي لإشعار البريد الخاص بالمرجع %s",
                    item.complaint.ref_no,
                )
            else:
                item.state = "retry"
                backoff = min(
                    NOTIFICATION_BACKOFF_BASE * (2 ** (item.attempts - 1)),
                    3600,
                )
                item.next_attempt_at = utcnow() + timedelta(seconds=backoff)
        db.session.commit()

    return len(pending)


# ----------------------------------------------------------------------
# المسارات العامة
# ----------------------------------------------------------------------
@app.get("/")
def home():
    branch = (
        Branch.query.filter_by(is_active=True)
        .order_by(Branch.id)
        .first()
    )
    if not branch:
        return render_template("home.html")
    return redirect(url_for("branch_page", code=branch.code))


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

    click.echo("تم إنشاء قاعدة البيانات والمرفق التجريبي.")


@app.cli.command("send-notifications")
@click.option("--loop/--once", default=False,
              help="تشغيل مستمر بدل معالجة دفعة واحدة.")
@click.option("--interval", default=30, type=int,
              help="عدد الثواني بين الدفعات في الوضع المستمر.")
def send_notifications_command(loop, interval):
    """معالجة طابور البريد (يُشغَّل كخدمة دائمة في الإنتاج)."""
    while True:
        processed = process_outbox()
        click.echo(f"تمت معالجة {processed} رسالة مستحقة.")
        if not loop:
            break
        time.sleep(interval)


@app.cli.command("retention-cleanup")
def retention_cleanup_command():
    """حذف البلاغات التي تجاوزت مدة الاحتفاظ، مع أثر تدقيقي عددي فقط."""
    today = date.today()
    expired = Complaint.query.filter(
        Complaint.retention_until.isnot(None),
        Complaint.retention_until < today,
    ).all()

    count = 0
    for complaint in expired:
        NotificationOutbox.query.filter_by(
            complaint_id=complaint.id
        ).delete()
        AuditEvent.query.filter_by(
            complaint_id=complaint.id
        ).delete()
        db.session.delete(complaint)
        count += 1

    db.session.add(RetentionLog(deleted_count=count, ran_at=utcnow()))
    db.session.commit()
    click.echo(f"تم حذف {count} بلاغ منتهي مدة الاحتفاظ.")


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

    if is_honeypot_triggered(request.form):
        app.logger.warning(
            "رصد طلب مشبوه (مصيدة روبوتات) من %s",
            get_remote_address(),
        )
        abort(400)

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

    return redirect(url_for(
        "track_page", ref=complaint.ref_no, token=token
    ))


@app.get("/track/<ref>/<token>")
@limiter.limit("30 per hour")
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
        query = query.filter(
            Complaint.public_text.ilike(
                f"%{escape_like(search)}%", escape="\\"
            )
        )

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


# ----------------------------------------------------------------------
# واجهات API العامة
# ----------------------------------------------------------------------
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

    if is_honeypot_triggered(data):
        return jsonify({"error": "طلب مرفوض"}), 400

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
@limiter.limit("30 per hour")
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


# ----------------------------------------------------------------------
# لوحة الموظف
# ----------------------------------------------------------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def admin_login():
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    error = None
    client_ip = get_remote_address()

    if request.method == "POST":
        locked = len(_login_failures(client_ip)) >= LOGIN_MAX_FAILURES
        if locked:
            error = (
                f"أُقفل الدخول مؤقتًا لكثرة المحاولات. "
                f"أعد المحاولة بعد {LOGIN_LOCKOUT_MINUTES} دقيقة."
            )
        else:
            password = request.form.get("password", "")
            if not password_hash:
                error = "لم تُضبط كلمة مرور الإدارة في ملف الإعدادات."
            elif check_password_hash(password_hash, password):
                _clear_failed_logins(client_ip)
                db.session.add(AuthEvent(
                    ip_address=client_ip,
                    user_agent=(request.user_agent.string or "")[:200],
                    success=True,
                ))
                db.session.commit()
                session.clear()
                session["is_admin"] = True
                return redirect(url_for("admin_dashboard"))
            else:
                _record_failed_login(client_ip)
                db.session.add(AuthEvent(
                    ip_address=client_ip,
                    user_agent=(request.user_agent.string or "")[:200],
                    success=False,
                ))
                db.session.commit()
                remaining = LOGIN_MAX_FAILURES - len(
                    _login_failures(client_ip)
                )
                error = (
                    "بيانات الدخول غير صحيحة."
                    + (f" يتبقى لك {remaining} محاولات قبل القفل."
                       if remaining > 0 else "")
                )

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
