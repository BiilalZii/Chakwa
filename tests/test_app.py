"""اختبارات التدفقات الحرجة لسجل الشكاوى."""
from datetime import date, timedelta

from app import (
    AuditEvent, Complaint, NotificationOutbox, RetentionLog, db,
)

from conftest import ADMIN_PASSWORD, BRANCH_CODE, VALID_BODY, login_admin, submit_complaint


def test_home_redirects_to_first_active_branch(client):
    response = client.get("/")
    assert response.status_code == 302
    assert f"/q/{BRANCH_CODE}" in response.headers["Location"]


def test_branch_page_ok_and_unknown_branch_404(client):
    assert client.get(f"/q/{BRANCH_CODE}").status_code == 200
    response = client.get("/q/UNKNOWN")
    assert response.status_code == 404


def test_submit_valid_complaint_returns_tracking_redirect(client):
    response = submit_complaint(client)
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/track/LGH-" in location


def test_submit_short_body_rejected(client, app):
    response = submit_complaint(client, body="قصير")
    assert response.status_code == 302
    with app.app_context():
        assert Complaint.query.count() == 0


def test_honeypot_blocks_suspicious_submission(client):
    response = submit_complaint(client, website="http://robot.example")
    assert response.status_code == 400


def test_complaint_enqueues_email_without_synchronous_sending(client, app):
    submit_complaint(client)
    with app.app_context():
        complaint = Complaint.query.one()
        assert complaint.email_status == "queued"
        assert NotificationOutbox.query.filter_by(
            complaint_id=complaint.id
        ).count() == 1


def test_tracking_with_wrong_token_returns_404(client):
    response = submit_complaint(client)
    ref = response.headers["Location"].split("/track/")[1].split("/")[0]
    bad = client.get(f"/track/{ref}/bad-token")
    assert bad.status_code == 404


def test_tracking_with_valid_token_ok(client):
    response = submit_complaint(client)
    assert client.get(response.headers["Location"]).status_code == 200


def test_publication_blocked_without_consent_even_by_admin(client, app):
    submit_complaint(client)
    login_admin(client)

    with app.app_context():
        complaint = Complaint.query.one()
        ref = complaint.ref_no

    response = client.post(
        f"/admin/c/{ref}",
        data={"status": "in_review", "public_text": "نص للنشر"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        refreshed = Complaint.query.filter_by(ref_no=ref).one()
        assert refreshed.public_text is None


def test_admin_can_publish_revised_text_with_consent(client, app):
    submit_complaint(client, consent_public="yes")
    login_admin(client)

    with app.app_context():
        ref = Complaint.query.one().ref_no

    response = client.post(
        f"/admin/c/{ref}",
        data={
            "status": "answered",
            "public_text": "نسخة منقحة خالية من البيانات الشخصية.",
            "response_public": "تمت معالجة الملاحظة.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        refreshed = Complaint.query.filter_by(ref_no=ref).one()
        assert refreshed.public_text is not None
        assert refreshed.status == "answered"
        assert AuditEvent.query.filter_by(action="updated").count() == 1


def test_admin_lockout_after_five_failures(client):
    for _ in range(5):
        response = login_admin(client, password="wrong-password")
        assert response.status_code == 200  # يعيد نموذج الدخول مع خطأ

    # المحاولة السادسة بكلمة المرور الصحيحة تُرفض بسبب القفل
    response = login_admin(client)
    assert response.status_code == 200
    assert "أُقفل الدخول مؤقتًا".encode() in response.data


def test_api_create_and_track_flow(client):
    response = client.post(
        "/api/v1/complaints",
        json={
            "branch_code": BRANCH_CODE,
            "type": "suggestion",
            "category": "reception",
            "body": VALID_BODY,
            "consent_public": False,
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["reference"].startswith("LGH-")
    assert payload["tracking_token"]

    tracked = client.get(
        f"/api/v1/complaints/{payload['reference']}/track",
        headers={"X-Tracking-Token": payload["tracking_token"]},
    )
    assert tracked.status_code == 200
    assert tracked.get_json()["status"] == "received"

    bad = client.get(
        f"/api/v1/complaints/{payload['reference']}/track",
        headers={"X-Tracking-Token": "wrong"},
    )
    assert bad.status_code == 404


def test_api_rejects_honeypot(client):
    response = client.post(
        "/api/v1/complaints",
        json={
            "branch_code": BRANCH_CODE,
            "type": "complaint",
            "category": "other",
            "body": VALID_BODY,
            "website": "spam",
        },
    )
    assert response.status_code == 400


def test_search_escapes_like_wildcards(client, app):
    submit_complaint(client, consent_public="yes")
    login_admin(client)

    with app.app_context():
        ref = Complaint.query.one().ref_no

    client.post(
        f"/admin/c/{ref}",
        data={
            "status": "closed",
            "public_text": "خصم بنسبة 100% على الخدمة المقدمة.",
        },
    )

    found = client.get(f"/q/{BRANCH_CODE}/public?q=100%25")
    # البحث بحرف النسبة المئوية حرفي لا يسبب خطأ ولا يطابق كل شيء
    assert found.status_code == 200
    assert ref.encode() in found.data

    no_match = client.get(f"/q/{BRANCH_CODE}/public?q=100_999")
    assert no_match.status_code == 200
    assert ref.encode() not in no_match.data


def test_qr_png_endpoint(client):
    response = client.get(f"/qr/{BRANCH_CODE}.png")
    assert response.status_code == 200
    assert response.mimetype == "image/png"


def test_notification_worker_sends_queued_mail(client, app, runner, monkeypatch):
    submit_complaint(client)
    monkeypatch.setenv("SMTP_HOST", "mail.example.dz")

    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=15):
            self.host = host

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def ehlo(self):
            pass

        def starttls(self, context=None):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message, to_addrs=None):
            sent_messages.append((message, to_addrs))

    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)

    result = runner.invoke(args=["send-notifications"])
    assert result.exit_code == 0
    assert len(sent_messages) == 1

    with app.app_context():
        item = NotificationOutbox.query.one()
        assert item.state == "sent"
        assert item.sent_at is not None
        assert Complaint.query.one().email_status == "sent"


def test_retention_cleanup_deletes_expired_and_logs_count(client, app, runner):
    submit_complaint(client)
    with app.app_context():
        complaint = Complaint.query.one()
        complaint.retention_until = date.today() - timedelta(days=1)
        db.session.commit()
        complaint_id = complaint.id

    result = runner.invoke(args=["retention-cleanup"])
    assert result.exit_code == 0

    with app.app_context():
        assert db.session.get(Complaint, complaint_id) is None
        assert AuditEvent.query.count() == 0
        log = RetentionLog.query.one()
        assert log.deleted_count == 1
