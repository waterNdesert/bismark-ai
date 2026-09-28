import importlib.util
from io import StringIO
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.models import Document


def test_source_id_is_nullable_uuid() -> None:
    column = Document.__table__.c.source_id
    assert isinstance(column.type, UUID)
    assert column.nullable is True
    assert column.server_default is None


def test_source_fk_is_tenant_scoped_and_restrictive() -> None:
    fk = next(c for c in Document.__table__.foreign_key_constraints
              if c.name == "fk_documents_source_tenant")
    assert list(fk.column_keys) == ["source_id", "organization_id", "workspace_id"]
    assert [e.target_fullname for e in fk.elements] == [
        "knowledge_sources.id", "knowledge_sources.organization_id",
        "knowledge_sources.workspace_id",
    ]
    assert fk.ondelete == "RESTRICT"


def test_source_index_and_existing_document_keys() -> None:
    table = Document.__table__
    index = next(i for i in table.indexes if i.name == "ix_documents_source_id")
    assert list(index.columns.keys()) == ["source_id"]
    assert index.unique is False
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert {c.name: list(c.columns.keys()) for c in table.constraints
            if isinstance(c, UniqueConstraint)} == {
        "uq_documents_storage_path": ["storage_path"],
        "uq_documents_id_organization_workspace": [
            "id", "organization_id", "workspace_id"
        ],
    }


def test_source_migration_changes_only_column_fk_and_index() -> None:
    path = (Path(__file__).parents[1]
            / "alembic/versions/20260928_0010_documents_source_link.py")
    spec = importlib.util.spec_from_file_location("document_source_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "20260928_0010"
    assert migration.down_revision == "20260928_0009"
    expected = {
        "upgrade": (
            "ALTER TABLE documents ADD COLUMN source_id UUID; "
            "ALTER TABLE documents ADD CONSTRAINT fk_documents_source_tenant "
            "FOREIGN KEY(source_id, organization_id, workspace_id) "
            "REFERENCES knowledge_sources (id, organization_id, workspace_id) "
            "ON DELETE RESTRICT; "
            "CREATE INDEX ix_documents_source_id ON documents (source_id);"
        ),
        "downgrade": (
            "DROP INDEX ix_documents_source_id; "
            "ALTER TABLE documents DROP CONSTRAINT fk_documents_source_tenant; "
            "ALTER TABLE documents DROP COLUMN source_id;"
        ),
    }
    for action, sql in expected.items():
        output = StringIO()
        context = MigrationContext.configure(
            dialect_name="postgresql",
            opts={"as_sql": True, "output_buffer": output},
        )
        with Operations.context(context):
            getattr(migration, action)()
        assert " ".join(output.getvalue().split()) == sql
