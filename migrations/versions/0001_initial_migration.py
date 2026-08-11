"""Initial migration for Aiva AI models (UUID primary keys).

Revision ID: 0001
Revises:
Create Date: 2024-07-13 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

booking_status = postgresql.ENUM(
    "pending",
    "confirmed",
    "completed",
    "cancelled",
    "no_show",
    name="bookingstatus",
    create_type=False,
)
subscription_status = postgresql.ENUM(
    "active",
    "expired",
    "cancelled",
    name="subscriptionstatus",
    create_type=False,
)
interaction_direction = postgresql.ENUM(
    "inbound",
    "outbound",
    name="interactiondirection",
    create_type=False,
)


def upgrade() -> None:
    booking_status.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)
    interaction_direction.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "masters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("work_start_hour", sa.Integer(), nullable=True),
        sa.Column("work_end_hour", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_masters_telegram_id", "masters", ["telegram_id"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("phone_encrypted", sa.String(), nullable=True),
        sa.Column("name_encrypted", sa.String(), nullable=True),
        sa.Column("preferences", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("reliability_score", sa.Integer(), nullable=False, server_default="50"),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clients_master_id", "clients", ["master_id"], unique=False)

    op.create_table(
        "services",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.String(length=36), nullable=False),
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            booking_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("tariff_name", sa.String(), nullable=False),
        sa.Column(
            "status",
            subscription_status,
            nullable=False,
            server_default="active",
        ),
        sa.Column("monthly_bookings_limit", sa.Integer(), nullable=False),
        sa.Column("additional_skills", sa.String(), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_trial", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("master_id"),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("client_hash", sa.String(), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=True),
        sa.Column("direction", interaction_direction, nullable=False),
        sa.Column("service_type", sa.String(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("location_district", sa.String(), nullable=True),
        sa.Column("event_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("client_hash IS NOT NULL", name="ck_interactions_client_hash_not_null"),
        sa.CheckConstraint("master_id IS NOT NULL", name="ck_interactions_master_id_not_null"),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interactions_master_created",
        "interactions",
        ["master_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interactions_event_created",
        "interactions",
        ["event_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interactions_service_created",
        "interactions",
        ["service_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interactions_district_created",
        "interactions",
        ["location_district", "created_at"],
        unique=False,
    )

    op.create_table(
        "master_analytics",
        sa.Column("master_id", sa.String(length=36), nullable=False),
        sa.Column("total_bookings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cancellations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_no_shows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("top_service_type", sa.String(), nullable=True),
        sa.Column("peak_hours", sa.String(), nullable=True),
        sa.Column("client_retention_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.PrimaryKeyConstraint("master_id"),
    )

    op.create_table(
        "district_analytics",
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("total_masters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bookings_30d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_price_by_service", sa.String(), nullable=True),
        sa.Column("demand_trend", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("top_services", sa.String(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("district"),
    )

    op.create_table(
        "data_api_clients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("contact_email", sa.String(), nullable=False),
        sa.Column("api_tier", sa.String(), nullable=False),
        sa.Column("monthly_quota", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("data_api_client_id", sa.String(length=36), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("permissions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("rate_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["data_api_client_id"], ["data_api_clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=False)

    op.create_table(
        "api_request_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("api_key_id", sa.String(length=36), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("api_request_logs")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_table("data_api_clients")
    op.drop_table("district_analytics")
    op.drop_table("master_analytics")

    op.drop_index("ix_interactions_district_created", table_name="interactions")
    op.drop_index("ix_interactions_service_created", table_name="interactions")
    op.drop_index("ix_interactions_event_created", table_name="interactions")
    op.drop_index("ix_interactions_master_created", table_name="interactions")
    op.drop_table("interactions")

    op.drop_table("subscriptions")
    op.drop_table("bookings")
    op.drop_table("services")
    op.drop_index("ix_clients_master_id", table_name="clients")
    op.drop_table("clients")
    op.drop_index("ix_masters_telegram_id", table_name="masters")
    op.drop_table("masters")

    interaction_direction.drop(op.get_bind(), checkfirst=True)
    subscription_status.drop(op.get_bind(), checkfirst=True)
    booking_status.drop(op.get_bind(), checkfirst=True)
