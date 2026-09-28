from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("auth.users.id", name="fk_profiles_user",
                   ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(name)) > 0", name="ck_organizations_name_not_blank"
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="ck_organizations_slug_format",
        ),
        UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'admin', 'member')",
            name="ck_organization_members_role",
        ),
        UniqueConstraint(
            "organization_id", "user_id", name="uq_organization_members_org_user"
        ),
        Index("ix_organization_members_user_org",
              "user_id", "organization_id"),
        Index("ix_organization_members_org_role", "organization_id", "role"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            name="fk_organization_members_organization",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "profiles.id", name="fk_organization_members_user", ondelete="CASCADE"
        ),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0",
                        name="ck_workspaces_name_not_blank"),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_workspaces_slug_format"
        ),
        UniqueConstraint("organization_id", "slug",
                         name="uq_workspaces_org_slug"),
        UniqueConstraint("id", "organization_id", name="uq_workspaces_id_org"),
        Index("ix_workspaces_organization_created",
              "organization_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organizations.id", name="fk_workspaces_organization", ondelete="CASCADE"
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'member')", name="ck_workspace_members_role"
        ),
        ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_workspace_members_workspace_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["organization_members.organization_id",
                "organization_members.user_id"],
            name="fk_workspace_members_organization_user",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "workspace_id", "user_id", name="uq_workspace_members_workspace_user"
        ),
        Index("ix_workspace_members_user_org", "user_id", "organization_id"),
        Index("ix_workspace_members_org_workspace",
              "organization_id", "workspace_id"),
        Index("ix_workspace_members_workspace_role", "workspace_id", "role"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(original_filename)) > 0",
            name="ck_documents_original_filename_not_blank",
        ),
        CheckConstraint(
            "storage_bucket = 'knowledge-documents'",
            name="ck_documents_storage_bucket",
        ),
        CheckConstraint(
            "length(btrim(storage_path)) > 0",
            name="ck_documents_storage_path_not_blank",
        ),
        CheckConstraint(
            "status IN ('uploaded', 'processing', 'ready', 'failed')",
            name="ck_documents_status",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_documents_workspace_org",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["uploaded_by"],
            ["profiles.id"],
            name="fk_documents_uploaded_by",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_id", "organization_id", "workspace_id"],
            ["knowledge_sources.id", "knowledge_sources.organization_id",
             "knowledge_sources.workspace_id"],
            name="fk_documents_source_tenant",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            "workspace_id",
            name="uq_documents_id_organization_workspace",
        ),
        UniqueConstraint("storage_path", name="uq_documents_storage_path"),
        Index("ix_documents_organization_id", "organization_id"),
        Index("ix_documents_workspace_id", "workspace_id"),
        Index("ix_documents_uploaded_by", "uploaded_by"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_source_id", "source_id"),
        Index(
            "ix_documents_organization_workspace",
            "organization_id",
            "workspace_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=True
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_bucket: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(
        Text, server_default="uploaded", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_ingestion_jobs_status",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_ingestion_jobs_attempt_count_nonnegative",
        ),
        ForeignKeyConstraint(
            ["document_id", "organization_id", "workspace_id"],
            [
                "documents.id",
                "documents.organization_id",
                "documents.workspace_id",
            ],
            name="fk_ingestion_jobs_document_tenant",
            ondelete="RESTRICT",
        ),
        Index("ix_ingestion_jobs_document_id", "document_id"),
        Index("ix_ingestion_jobs_status", "status"),
        Index(
            "ix_ingestion_jobs_organization_workspace",
            "organization_id",
            "workspace_id",
        ),
        Index("ix_ingestion_jobs_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, server_default="pending", nullable=False)
    attempt_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(name)) > 0",
            name="ck_knowledge_sources_name_not_blank",
        ),
        CheckConstraint(
            "source_type IN ('manual_upload')",
            name="ck_knowledge_sources_source_type",
        ),
        CheckConstraint(
            "status IN ('active', 'disabled', 'error')",
            name="ck_knowledge_sources_status",
        ),
        CheckConstraint(
            "sync_status IS NULL OR sync_status IN "
            "('idle', 'syncing', 'success', 'failed')",
            name="ck_knowledge_sources_sync_status",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_knowledge_sources_workspace_org",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["profiles.id"],
            name="fk_knowledge_sources_created_by",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            "workspace_id",
            name="uq_knowledge_sources_id_organization_workspace",
        ),
        Index(
            "uq_knowledge_sources_manual_upload_workspace",
            "organization_id", "workspace_id",
            unique=True,
            postgresql_where=text("source_type = 'manual_upload' AND deleted_at IS NULL"),
            sqlite_where=text("source_type = 'manual_upload' AND deleted_at IS NULL"),
        ),
        Index("ix_knowledge_sources_organization_id", "organization_id"),
        Index("ix_knowledge_sources_workspace_id", "workspace_id"),
        Index("ix_knowledge_sources_created_by", "created_by"),
        Index("ix_knowledge_sources_source_type", "source_type"),
        Index("ix_knowledge_sources_status", "status"),
        Index(
            "ix_knowledge_sources_organization_workspace",
            "organization_id",
            "workspace_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        server_default="gen_random_uuid()",
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default="active", nullable=False)
    connection_reference: Mapped[str | None] = mapped_column(Text)
    sync_status: Mapped[str | None] = mapped_column(Text)
    sync_cursor: Mapped[str | None] = mapped_column(Text)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    last_sync_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
