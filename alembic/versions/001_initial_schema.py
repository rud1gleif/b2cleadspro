"""Initial schema — matches all current SQLAlchemy models.

Revision ID: 001
Revises:
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── locations ────────────────────────────────────────────────────────────
    op.create_table(
        'locations',
        sa.Column('id',           UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_input',    sa.String(512),  nullable=False),
        sa.Column('city',         sa.String(256),  nullable=True),
        sa.Column('region',       sa.String(256),  nullable=True),
        sa.Column('country',      sa.String(128),  nullable=True),
        sa.Column('country_code', sa.String(8),    nullable=True),
        sa.Column('latitude',     sa.Float(),      nullable=True),
        sa.Column('longitude',    sa.Float(),      nullable=True),
        sa.Column('population',   sa.Integer(),    nullable=True),
        sa.Column('timezone',     sa.String(64),   nullable=True),
        sa.Column('normalized',   sa.Boolean(),    server_default='false'),
        sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_locations_country_code', 'locations', ['country_code'])
    op.create_index('ix_locations_city',         'locations', ['city'])

    # ── proxies ───────────────────────────────────────────────────────────────
    op.create_table(
        'proxies',
        sa.Column('id',              UUID(as_uuid=True), primary_key=True),
        sa.Column('url',             sa.String(512),  nullable=False, unique=True),
        sa.Column('provider',        sa.String(128),  nullable=True),
        sa.Column('proxy_type',      sa.String(32),   server_default='datacenter'),
        sa.Column('country',         sa.String(8),    nullable=True),
        sa.Column('city',            sa.String(128),  nullable=True),
        sa.Column('sticky_capable',  sa.Boolean(),    server_default='false'),
        sa.Column('active',          sa.Boolean(),    server_default='true'),
        sa.Column('health_score',    sa.Float(),      server_default='1.0'),
        sa.Column('avg_latency_ms',  sa.Integer(),    nullable=True),
        sa.Column('recent_failures', sa.Integer(),    server_default='0'),
        sa.Column('cooldown_until',  sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── proxy_assignments ─────────────────────────────────────────────────────
    op.create_table(
        'proxy_assignments',
        sa.Column('id',                UUID(as_uuid=True), primary_key=True),
        sa.Column('proxy_id',          UUID(as_uuid=True), sa.ForeignKey('proxies.id'), nullable=False),
        sa.Column('session_id',        sa.String(128),  nullable=True),
        sa.Column('mode',              sa.String(32),   server_default='rotating'),
        sa.Column('country_requested', sa.String(8),    nullable=True),
        sa.Column('assigned_at',       sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('released_at',       sa.DateTime(timezone=True), nullable=True),
        sa.Column('success',           sa.Boolean(),    nullable=True),
        sa.Column('latency_ms',        sa.Integer(),    nullable=True),
        sa.Column('blocked',           sa.Boolean(),    server_default='false'),
    )
    op.create_index('ix_proxy_assignments_proxy_id', 'proxy_assignments', ['proxy_id'])

    # ── proxy_events ──────────────────────────────────────────────────────────
    op.create_table(
        'proxy_events',
        sa.Column('id',          UUID(as_uuid=True), primary_key=True),
        sa.Column('proxy_id',    UUID(as_uuid=True), sa.ForeignKey('proxies.id'), nullable=False),
        sa.Column('event_type',  sa.String(64),  nullable=False),
        sa.Column('domain',      sa.String(256), nullable=True),
        sa.Column('status_code', sa.Integer(),   nullable=True),
        sa.Column('message',     sa.Text(),      nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_proxy_events_proxy_id', 'proxy_events', ['proxy_id'])

    # ── search_jobs ───────────────────────────────────────────────────────────
    op.create_table(
        'search_jobs',
        sa.Column('id',               UUID(as_uuid=True), primary_key=True),
        sa.Column('location_id',      UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('status',           sa.String(32),   server_default='pending'),
        sa.Column('source_types',     sa.JSON(),       nullable=True),
        sa.Column('keywords',         sa.JSON(),       nullable=True),
        sa.Column('proxy_mode',       sa.String(32),   server_default='rotating_residential'),
        sa.Column('pages_discovered', sa.Integer(),    server_default='0'),
        sa.Column('pages_scraped',    sa.Integer(),    server_default='0'),
        sa.Column('emails_found',     sa.Integer(),    server_default='0'),
        sa.Column('emails_verified',  sa.Integer(),    server_default='0'),
        sa.Column('error_message',    sa.Text(),       nullable=True),
        sa.Column('started_at',       sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at',      sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',       sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at',       sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_search_jobs_status',      'search_jobs', ['status'])
    op.create_index('ix_search_jobs_location_id', 'search_jobs', ['location_id'])

    # ── pages ─────────────────────────────────────────────────────────────────
    op.create_table(
        'pages',
        sa.Column('id',                  UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id',              UUID(as_uuid=True), sa.ForeignKey('search_jobs.id'), nullable=True),
        sa.Column('proxy_assignment_id', UUID(as_uuid=True), sa.ForeignKey('proxy_assignments.id'), nullable=True),
        sa.Column('url',                 sa.Text(),      nullable=False),
        sa.Column('domain',              sa.String(256), nullable=True),
        sa.Column('status_code',         sa.Integer(),   nullable=True),
        sa.Column('content_hash',        sa.String(64),  nullable=True),
        sa.Column('emails_found',        sa.Integer(),   server_default='0'),
        sa.Column('rendered',            sa.Boolean(),   server_default='false'),
        sa.Column('blocked',             sa.Boolean(),   server_default='false'),
        sa.Column('error',               sa.Text(),      nullable=True),
        sa.Column('scraped_at',          sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',          sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_pages_job_id', 'pages', ['job_id'])
    op.create_index('ix_pages_domain',  'pages', ['domain'])

    # ── email_leads ───────────────────────────────────────────────────────────
    op.create_table(
        'email_leads',
        sa.Column('id',                  UUID(as_uuid=True), primary_key=True),
        sa.Column('source_page_id',      UUID(as_uuid=True), sa.ForeignKey('pages.id'), nullable=True),
        sa.Column('email',               sa.String(512),  nullable=False, index=True),
        sa.Column('name',                sa.String(256),  nullable=True),
        sa.Column('phone',               sa.String(64),   nullable=True),
        sa.Column('website',             sa.Text(),       nullable=True),
        sa.Column('snippet',             sa.Text(),       nullable=True),
        sa.Column('location_raw',        sa.String(512),  nullable=True),
        sa.Column('city',                sa.String(256),  nullable=True),
        sa.Column('region',              sa.String(256),  nullable=True),
        sa.Column('country',             sa.String(128),  nullable=True),
        sa.Column('country_code',        sa.String(8),    nullable=True),
        sa.Column('location_confidence', sa.Float(),      server_default='0.0'),
        sa.Column('lead_score',          sa.Float(),      server_default='0.0'),
        sa.Column('is_suppressed',       sa.Boolean(),    server_default='false'),
        sa.Column('suppressed_at',       sa.DateTime(timezone=True), nullable=True),
        sa.Column('suppressed_reason',   sa.String(256),  nullable=True),
        sa.Column('source_url',          sa.Text(),       nullable=True),
        sa.Column('scraped_at',          sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',          sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at',          sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_email_leads_country_code', 'email_leads', ['country_code'])
    op.create_index('ix_email_leads_lead_score',   'email_leads', ['lead_score'])
    op.create_index('ix_email_leads_is_suppressed','email_leads', ['is_suppressed'])

    # ── verifications ─────────────────────────────────────────────────────────
    op.create_table(
        'verifications',
        sa.Column('id',               UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id',          UUID(as_uuid=True), sa.ForeignKey('email_leads.id'), nullable=False, unique=True),
        sa.Column('syntax_valid',     sa.Boolean(),  nullable=True),
        sa.Column('dns_valid',        sa.Boolean(),  nullable=True),
        sa.Column('mx_valid',         sa.Boolean(),  nullable=True),
        sa.Column('smtp_valid',       sa.Boolean(),  nullable=True),
        sa.Column('is_disposable',    sa.Boolean(),  nullable=True),
        sa.Column('is_role_account',  sa.Boolean(),  nullable=True),
        sa.Column('is_catch_all',     sa.Boolean(),  nullable=True),
        sa.Column('is_free_provider', sa.Boolean(),  nullable=True),
        sa.Column('verdict',          sa.String(32), nullable=True),
        sa.Column('confidence',       sa.Float(),    nullable=True),
        sa.Column('raw_response',     sa.Text(),     nullable=True),
        sa.Column('verifier_version', sa.String(64), nullable=True),
        sa.Column('last_checked_at',  sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at',       sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_verifications_lead_id', 'verifications', ['lead_id'])


def downgrade() -> None:
    op.drop_table('verifications')
    op.drop_table('email_leads')
    op.drop_table('pages')
    op.drop_table('search_jobs')
    op.drop_table('proxy_events')
    op.drop_table('proxy_assignments')
    op.drop_table('proxies')
    op.drop_table('locations')
