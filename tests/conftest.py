"""تهيئة بيئة الاختبار قبل استيراد التطبيق.

مهم: يجب ضبط DATABASE_URL على قاعدة مؤقتة قبل أي استيراد لـ app، حتى
يُنشأ محرك SQLAlchemy مرة واحدة على القاعدة المؤقتة ولا تمس الاختبارات
قاعدة بيانات المعاينة في instance/.
"""
import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

_TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "chakwa_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
os.environ.setdefault(
    "ADMIN_PASSWORD_HASH", generate_password_hash("Admin-12345")
)

from app import (  # noqa: E402
    _failed_logins, app as flask_app, db, Branch, limiter,
)

ADMIN_PASSWORD = "Admin-12345"
BRANCH_CODE = "LGH-PILOT-001"
VALID_BODY = "نص تجريبي طويل بما يكفي ليتجاوز عشرين حرفًا كاملة."


@pytest.fixture()
def app():
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    # نعطّل محدد المعدل في الاختبارات؛ القفل المؤقت له آلية مستقلة نختبرها.
    limiter.enabled = False
    _failed_logins.clear()

    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(Branch(
            code=BRANCH_CODE,
            name_ar="مرفق تجريبي",
            description_ar="وصف تجريبي",
            supervisor_email="sup@example.dz",
            is_active=True,
        ))
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    _failed_logins.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def submit_complaint(client, **overrides):
    data = {
        "kind": "complaint",
        "category": "waiting",
        "body": VALID_BODY,
        "consent_public": "",
    }
    data.update(overrides)
    return client.post(
        f"/q/{BRANCH_CODE}/submit", data=data,
        follow_redirects=False,
    )


def login_admin(client, password=ADMIN_PASSWORD):
    return client.post(
        "/admin/login",
        data={"password": password},
        follow_redirects=False,
    )
