"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('locations', sa.Text, nullable=False),
        sa.Column('niches', sa.Text, nullable=True),
        sa.Column('sources', sa.Text, nullable=False, server_default='gmaps,yelp,yellowpages,angi'),
        sa.Column('max_pages', sa.Integer, nullable=False, server_default='5'),
        sa.Column('concurrency', sa.Integer, nullable=False, server_default='3'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('leads_found', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'leads',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('name', sa.Text, nullable=True),
        sa.Column('phone', sa.Text, nullable=True),
        sa.Column('email', sa.Text, nullable=True),
        sa.Column('website', sa.Text, nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('rating', sa.Float, nullable=True),
        sa.Column('category', sa.Text, nullable=True),
        sa.Column('location', sa.Text, nullable=True),
        sa.Column('niche', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_leads_job_id', 'leads', ['job_id'])
    op.create_index('ix_leads_source', 'leads', ['source'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])


def downgrade() -> None:
    op.drop_table('leads')
    op.drop_table('jobs')
