"""Initial schema — all tables.

Revision ID: 0001
Revises: 
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── locations ────────────────────────────────────────────────────────────
    op.create_table(
        'locations',
        sa.Column('id',           sa.Integer(),     nullable=False, primary_key=True),
        sa.Column('city',         sa.String(120),   nullable=True),
        sa.Column('region',       sa.String(120),   nullable=True),
        sa.Column('country',      sa.String(120),   nullable=False),
        sa.Column('country_code', sa.String(4),     nullable=True),
        sa.Column('latitude',     sa.Float(),       nullable=True),
        sa.Column('longitude',    sa.Float(),       nullable=True),
        sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_locations_country_code', 'locations', ['country_code'])
    op.create_index('ix_locations_city',         'locations', ['city'])

    # ── proxies ───────────────────────────────────────────────────────────────
    op.create_table(
        'proxies',
        sa.Column('id',           sa.Integer(),  nullable=False, primary_key=True),
        sa.Column('url',          sa.String(255), nullable=False, unique=True),
        sa.Column('country_code', sa.String(4),  nullable=True),
        sa.Column('is_active',    sa.Boolean(),  server_default='true'),
        sa.Column('latency_ms',   sa.Integer(),  nullable=True),
        sa.Column('fail_count',   sa.Integer(),  server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── jobs ──────────────────────────────────────────────────────────────────
    op.create_table(
        'jobs',
        sa.Column('id',            sa.Integer(),    nullable=False, primary_key=True),
        sa.Column('status',        sa.String(20),   server_default='pending'),
        sa.Column('location_ids',  sa.Text(),       nullable=True),   # JSON array
        sa.Column('niches',        sa.Text(),       nullable=True),   # JSON array
        sa.Column('max_pages',     sa.Integer(),    server_default='50'),
        sa.Column('concurrency',   sa.Integer(),    server_default='5'),
        sa.Column('progress',      sa.Integer(),    server_default='0'),
        sa.Column('leads_found',   sa.Integer(),    server_default='0'),
        sa.Column('pages_crawled', sa.Integer(),    server_default='0'),
        sa.Column('error_message', sa.Text(),       nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at',    sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at',   sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_jobs_status', 'jobs', ['status'])

    # ── pages ─────────────────────────────────────────────────────────────────
    op.create_table(
        'pages',
        sa.Column('id',           sa.Integer(),   nullable=False, primary_key=True),
        sa.Column('url',          sa.Text(),      nullable=False),
        sa.Column('job_id',       sa.Integer(),   sa.ForeignKey('jobs.id', ondelete='CASCADE')),
        sa.Column('status_code',  sa.Integer(),   nullable=True),
        sa.Column('emails_found', sa.Integer(),   server_default='0'),
        sa.Column('crawled_at',   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_pages_job_id', 'pages', ['job_id'])

    # ── email_leads ───────────────────────────────────────────────────────────
    op.create_table(
        'email_leads',
        sa.Column('id',             sa.Integer(),   nullable=False, primary_key=True),
        sa.Column('email',          sa.String(255), nullable=False, unique=True),
        sa.Column('city',           sa.String(120), nullable=True),
        sa.Column('region',         sa.String(120), nullable=True),
        sa.Column('country',        sa.String(120), nullable=True),
        sa.Column('country_code',   sa.String(4),   nullable=True),
        sa.Column('niche',          sa.String(120), nullable=True),
        sa.Column('source_url',     sa.Text(),      nullable=True),
        sa.Column('source_domain',  sa.String(255), nullable=True),
        sa.Column('is_verified',    sa.Boolean(),   server_default='false'),
        sa.Column('is_disposable',  sa.Boolean(),   server_default='false'),
        sa.Column('mx_valid',       sa.Boolean(),   server_default='false'),
        sa.Column('syntax_ok',      sa.Boolean(),   server_default='false'),
        sa.Column('is_reachable',   sa.String(20),  nullable=True),
        sa.Column('score',          sa.Integer(),   server_default='0'),
        sa.Column('job_id',         sa.Integer(),   sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at',    sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',     sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_email_leads_country_code', 'email_leads', ['country_code'])
    op.create_index('ix_email_leads_niche',        'email_leads', ['niche'])
    op.create_index('ix_email_leads_score',        'email_leads', ['score'])
    op.create_index('ix_email_leads_job_id',       'email_leads', ['job_id'])
    op.create_index('ix_email_leads_is_verified',  'email_leads', ['is_verified'])


def downgrade() -> None:
    op.drop_table('email_leads')
    op.drop_table('pages')
    op.drop_table('jobs')
    op.drop_table('proxies')
    op.drop_table('locations')
