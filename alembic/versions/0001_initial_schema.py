"""Initial schema — all tables.

Revision ID: 0001
Revises: 
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('city', sa.String(128), nullable=True),
        sa.Column('region', sa.String(128), nullable=True),
        sa.Column('country', sa.String(128), nullable=False),
        sa.Column('country_code', sa.String(4), nullable=False),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'proxies',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('host', sa.String(256), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('protocol', sa.String(16), default='http'),
        sa.Column('username', sa.String(128), nullable=True),
        sa.Column('password', sa.String(256), nullable=True),
        sa.Column('country_code', sa.String(4), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('fail_count', sa.Integer, default=0),
        sa.Column('success_count', sa.Integer, default=0),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('status', sa.String(32), default='pending'),
        sa.Column('location_ids', sa.Text, nullable=False),
        sa.Column('niches', sa.Text, nullable=True),
        sa.Column('max_pages', sa.Integer, default=50),
        sa.Column('concurrency', sa.Integer, default=5),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('leads_found', sa.Integer, default=0),
        sa.Column('pages_crawled', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'pages',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('url', sa.Text, nullable=False),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=True),
        sa.Column('status_code', sa.Integer, nullable=True),
        sa.Column('emails_found', sa.Integer, default=0),
        sa.Column('crawled_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'email_leads',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email', sa.String(320), nullable=False, unique=True),
        sa.Column('first_name', sa.String(128), nullable=True),
        sa.Column('last_name', sa.String(128), nullable=True),
        sa.Column('full_name', sa.String(256), nullable=True),
        sa.Column('city', sa.String(128), nullable=True),
        sa.Column('region', sa.String(128), nullable=True),
        sa.Column('country', sa.String(128), nullable=True),
        sa.Column('country_code', sa.String(4), nullable=True),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('source_domain', sa.String(256), nullable=True),
        sa.Column('niche', sa.String(128), nullable=True),
        sa.Column('score', sa.Integer, default=0),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_disposable', sa.Boolean, default=False),
        sa.Column('mx_valid', sa.Boolean, default=False),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'verifications',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email_lead_id', sa.Integer, sa.ForeignKey('email_leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('syntax_ok', sa.Boolean, default=False),
        sa.Column('mx_ok', sa.Boolean, default=False),
        sa.Column('smtp_ok', sa.Boolean, nullable=True),
        sa.Column('is_disposable', sa.Boolean, default=False),
        sa.Column('is_role_account', sa.Boolean, default=False),
        sa.Column('score', sa.Integer, default=0),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for fast filtering
    op.create_index('ix_leads_country_code', 'email_leads', ['country_code'])
    op.create_index('ix_leads_city', 'email_leads', ['city'])
    op.create_index('ix_leads_score', 'email_leads', ['score'])
    op.create_index('ix_leads_job_id', 'email_leads', ['job_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])


def downgrade() -> None:
    op.drop_table('verifications')
    op.drop_table('email_leads')
    op.drop_table('pages')
    op.drop_table('jobs')
    op.drop_table('proxies')
    op.drop_table('locations')
