"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # locations
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_input", sa.String(512), nullable=False),
        sa.Column("city", sa.String(256)),
        sa.Column("region", sa.String(256)),
        sa.Column("country", sa.String(128)),
        sa.Column("country_code", sa.String(8)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("population", sa.Integer()),
        sa.Column("timezone", sa.String(64)),
        sa.Column("normalized", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # proxies
    op.create_table(
        "proxies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("provider", sa.String(128)),
        sa.Column("proxy_type", sa.String(32), server_default="datacenter"),
        sa.Column("country", sa.String(8)),
        sa.Column("city", sa.String(128)),
        sa.Column("sticky_capable", sa.Boolean(), server_default="false"),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("health_score", sa.Float(), server_default="1.0"),
        sa.Column("avg_latency_ms", sa.Integer()),
        sa.Column("recent_failures", sa.Integer(), server_default="0"),
        sa.Column("cooldown_until", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    # search_jobs
    op.create_table(
        "search_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("source_types", postgresql.JSON()),
        sa.Column("keywords", postgresql.JSON()),
        sa.Column("proxy_mode", sa.String(32), server_default="rotating_residential"),
        sa.Column("pages_discovered", sa.Integer(), server_default="0"),
        sa.Column("pages_scraped", sa.Integer(), server_default="0"),
        sa.Column("emails_found", sa.Integer(), server_default="0"),
        sa.Column("emails_verified", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # proxy_assignments
    op.create_table(
        "proxy_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proxy_id", postgresql.UUID(as_uuid=True)),
        sa.Column("session_id", sa.String(128)),
        sa.Column("mode", sa.String(32), server_default="rotating"),
        sa.Column("country_requested", sa.String(8)),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("success", sa.Boolean()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("blocked", sa.Boolean(), server_default="false"),
        sa.ForeignKeyConstraint(["proxy_id"], ["proxies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # proxy_events
    op.create_table(
        "proxy_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proxy_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(64)),
        sa.Column("domain", sa.String(256)),
        sa.Column("status_code", sa.Integer()),
        sa.Column("message", sa.Text()),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["proxy_id"], ["proxies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # pages
    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True)),
        sa.Column("proxy_assignment_id", postgresql.UUID(as_uuid=True)),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(256)),
        sa.Column("status_code", sa.Integer()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("emails_found", sa.Integer(), server_default="0"),
        sa.Column("rendered", sa.Boolean(), server_default="false"),
        sa.Column("blocked", sa.Boolean(), server_default="false"),
        sa.Column("error", sa.Text()),
        sa.Column("scraped_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["job_id"], ["search_jobs.id"]),
        sa.ForeignKeyConstraint(["proxy_assignment_id"], ["proxy_assignments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pages_url_hash", "pages", ["content_hash"])

    # email_leads
    op.create_table(
        "email_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_page_id", postgresql.UUID(as_uuid=True)),
        sa.Column("email", sa.String(512), nullable=False),
        sa.Column("name", sa.String(256)),
        sa.Column("phone", sa.String(64)),
        sa.Column("website", sa.Text()),
        sa.Column("snippet", sa.Text()),
        sa.Column("location_raw", sa.String(512)),
        sa.Column("city", sa.String(256)),
        sa.Column("region", sa.String(256)),
        sa.Column("country", sa.String(128)),
        sa.Column("country_code", sa.String(8)),
        sa.Column("location_confidence", sa.Float(), server_default="0.0"),
        sa.Column("lead_score", sa.Float(), server_default="0.0"),
        sa.Column("is_suppressed", sa.Boolean(), server_default="false"),
        sa.Column("suppressed_at", sa.DateTime(timezone=True)),
        sa.Column("suppressed_reason", sa.String(256)),
        sa.Column("source_url", sa.Text()),
        sa.Column("scraped_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["source_page_id"], ["pages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_leads_email", "email_leads", ["email"])
    op.create_index("ix_email_leads_country_code", "email_leads", ["country_code"])
    op.create_index("ix_email_leads_city", "email_leads", ["city"])

    # verifications
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("syntax_valid", sa.Boolean()),
        sa.Column("dns_valid", sa.Boolean()),
        sa.Column("mx_valid", sa.Boolean()),
        sa.Column("smtp_valid", sa.Boolean()),
        sa.Column("is_disposable", sa.Boolean()),
        sa.Column("is_role_account", sa.Boolean()),
        sa.Column("is_catch_all", sa.Boolean()),
        sa.Column("is_free_provider", sa.Boolean()),
        sa.Column("verdict", sa.String(32)),
        sa.Column("confidence", sa.Float()),
        sa.Column("raw_response", sa.Text()),
        sa.Column("verifier_version", sa.String(64)),
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["email_leads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_id"),
    )


def downgrade() -> None:
    op.drop_table("verifications")
    op.drop_index("ix_email_leads_city", table_name="email_leads")
    op.drop_index("ix_email_leads_country_code", table_name="email_leads")
    op.drop_index("ix_email_leads_email", table_name="email_leads")
    op.drop_table("email_leads")
    op.drop_index("ix_pages_url_hash", table_name="pages")
    op.drop_table("pages")
    op.drop_table("proxy_events")
    op.drop_table("proxy_assignments")
    op.drop_table("search_jobs")
    op.drop_table("proxies")
    op.drop_table("locations")
