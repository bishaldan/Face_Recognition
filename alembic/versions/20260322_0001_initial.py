"""Initial schema for face recognition v2."""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enrollment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_full_name", "users", ["full_name"])

    op.create_table(
        "operator_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_operator_accounts_username", "operator_accounts", ["username"], unique=True)

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backend_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("version_label", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "enrollment_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requested_name", sa.String(length=255), nullable=False),
        sa.Column("requested_email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operator_accounts.id"), nullable=False),
        sa.Column("finalized_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "enrollment_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("enrollment_sessions.id"), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("capture_index", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("enrollment_sessions.id"), nullable=True),
        sa.Column("enrollment_image_id", sa.Integer(), sa.ForeignKey("enrollment_images.id"), nullable=True),
        sa.Column("backend_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("vector", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "verification_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("matched_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operator_accounts.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("threshold_used", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=50), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("backend_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operator_accounts.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("verification_attempts")
    op.drop_table("face_embeddings")
    op.drop_table("enrollment_images")
    op.drop_table("enrollment_sessions")
    op.drop_table("model_versions")
    op.drop_table("system_settings")
    op.drop_index("ix_operator_accounts_username", table_name="operator_accounts")
    op.drop_table("operator_accounts")
    op.drop_index("ix_users_full_name", table_name="users")
    op.drop_table("users")

