-- مخطط قاعدة البيانات الإنتاجي المقترح (PostgreSQL).
-- النموذج التشغيلي app.py يستخدم SQLite للتجربة؛ هذا المخطط مرجع الإنتاج.
-- راجع القسم 3 من README.MD للشروح التنظيمية والأمنية.

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
-- النموذج الأولي لا يجمع البريد أو الهاتف.
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

-- سجل محاولات دخول الموظفين دون تخزين كلمات المرور.
CREATE TABLE admin_auth_events (
    id          BIGSERIAL PRIMARY KEY,
    ip_address  INET NOT NULL,
    user_agent  TEXT,
    success     BOOLEAN NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_complaints_branch_date
    ON complaints(branch_id, submitted_at DESC);

CREATE INDEX idx_complaints_status_date
    ON complaints(status, submitted_at);

CREATE INDEX idx_complaints_publication
    ON complaints(publication_status, submitted_at DESC);

CREATE INDEX idx_events_complaint_date
    ON complaint_events(complaint_id, created_at);

CREATE INDEX idx_outbox_due
    ON notification_outbox(state, next_attempt_at)
    WHERE state IN ('pending', 'retry');
