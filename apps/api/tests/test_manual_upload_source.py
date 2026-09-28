from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Document, KnowledgeSource
from app.core.errors import ApiError
from app.auth.workspaces import require_workspace_membership
from tests.test_document_upload import (
    ORGANIZATION_ID, WORKSPACE_ID, USER_ID, build_client, upload,
)


@pytest.fixture
def integration():
    engine = create_engine('sqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})

    @event.listens_for(engine, 'connect')
    def functions(connection, _):
        connection.isolation_level = None
        connection.create_function('btrim', 1, lambda value: value.strip())

    @event.listens_for(engine, 'begin')
    def begin(connection):
        connection.exec_driver_sql('BEGIN')

    KnowledgeSource.__table__.create(engine)
    Document.__table__.create(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    @event.listens_for(factory, 'before_flush')
    def timestamps(session, *_):
        for row in session.new:
            row.created_at = row.created_at or datetime.now(timezone.utc)
            row.updated_at = row.updated_at or datetime.now(timezone.utc)

    client, _, storage = build_client()
    client.app.state.session_factory = factory
    yield client, factory, storage
    client.close()
    engine.dispose()


def source(**values):
    defaults = dict(id=uuid4(), organization_id=ORGANIZATION_ID,
                    workspace_id=WORKSPACE_ID, created_by=USER_ID,
                    source_type='manual_upload', name='Manual Upload', status='active')
    return KnowledgeSource(**(defaults | values))


def test_creates_source_and_links_document_with_safe_response(integration):
    client, factory, _ = integration
    response = upload(client)
    assert response.status_code == 201
    assert set(response.json()) == {
        'id', 'organization_id', 'workspace_id', 'original_filename',
        'mime_type', 'size_bytes', 'status', 'created_at',
    }
    with factory() as db:
        sources = list(db.scalars(select(KnowledgeSource)))
        assert len(sources) == 1
        row = sources[0]
        assert (row.organization_id, row.workspace_id, row.created_by,
                row.source_type, row.name, row.status) == (
            ORGANIZATION_ID, WORKSPACE_ID, USER_ID, 'manual_upload', 'Manual Upload', 'active')
        assert db.scalar(select(Document)).source_id == row.id


def test_reuses_deterministic_existing_source(integration):
    client, factory, _ = integration
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = source(id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"), created_at=timestamp)
    second = source(id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"), created_at=timestamp)
    with factory() as db:
        db.add(first)
        db.commit()
    assert upload(client).status_code == 201
    with factory() as db:
        assert len(list(db.scalars(select(KnowledgeSource)))) == 1
        assert db.scalar(select(Document)).source_id == first.id


@pytest.mark.parametrize('values', [
    {'organization_id': uuid4()}, {'workspace_id': uuid4()},
    {'deleted_at': datetime.now(timezone.utc)},
])
def test_ineligible_source_is_never_reused(integration, values):
    client, factory, _ = integration
    other = source(**values)
    with factory() as db:
        db.add(other)
        db.commit()
    assert upload(client).status_code == 201
    with factory() as db:
        document = db.scalar(select(Document))
        assert document.source_id != other.id
        chosen = db.get(KnowledgeSource, document.source_id)
        assert (chosen.organization_id, chosen.workspace_id) == (ORGANIZATION_ID, WORKSPACE_ID)


@pytest.mark.parametrize('failure', ['commit', 'storage'])
def test_failures_roll_back_new_source_and_document(integration, failure):
    client, factory, storage = integration
    rolled_back = []
    event.listen(factory, 'after_rollback', lambda session: rolled_back.append(True))
    if failure == 'commit':
        def fail(session):
            if not session.in_nested_transaction():
                raise SQLAlchemyError('private DB detail')
        event.listen(factory, 'before_commit', fail)
    else:
        storage.fail_upload = True
    response = upload(client)
    assert response.status_code == (500 if failure == 'commit' else 502)
    assert rolled_back
    assert 'private' not in response.text
    with factory() as db:
        assert list(db.scalars(select(KnowledgeSource))) == []
        assert list(db.scalars(select(Document))) == []
    assert storage.deletes == ([storage.uploads[0][0]] if failure == 'commit' else [])


def test_authorization_precedes_source_lookup(integration):
    client, factory, storage = integration
    def deny():
        raise ApiError(403, 'WORKSPACE_ACCESS_DENIED', 'Access denied.')
    client.app.dependency_overrides[require_workspace_membership] = deny
    queries = []
    event.listen(factory, 'do_orm_execute', lambda state: queries.append(True))
    assert upload(client).status_code == 403
    assert queries == []
    assert storage.uploads == []


@pytest.mark.parametrize('status', ['disabled', 'error'])
def test_unavailable_canonical_source_is_not_replaced(integration, status):
    client, factory, storage = integration
    with factory() as db:
        db.add(source(status=status))
        db.commit()
    response = upload(client)
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'SOURCE_UNAVAILABLE'
    assert not storage.uploads
    with factory() as db:
        assert len(list(db.scalars(select(KnowledgeSource)))) == 1
        assert not list(db.scalars(select(Document)))


@pytest.mark.parametrize('constraint', [
    'uq_knowledge_sources_manual_upload_workspace', 'unrelated_constraint',
])
def test_simulated_source_race(integration, monkeypatch, constraint):
    from types import SimpleNamespace
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    client, factory, storage = integration
    canonical = source()
    with factory() as db:
        db.add(canonical)
        db.commit()
    scalar = Session.scalar
    calls = []

    def race_lookup(session, statement, *args, **kwargs):
        calls.append(statement)
        if len(calls) == 1:
            return None  # Another transaction wins after the initial lookup.
        return scalar(session, statement, *args, **kwargs)

    def conflict(session, *_):
        if session.in_nested_transaction():
            original = Exception('private conflict detail')
            original.sqlstate = '23505'
            original.diag = SimpleNamespace(constraint_name=constraint)
            raise IntegrityError('insert', {}, original)

    monkeypatch.setattr(Session, 'scalar', race_lookup)
    event.listen(factory, 'before_flush', conflict)
    response = upload(client)
    if constraint == 'unrelated_constraint':
        assert response.status_code == 500
        assert len(calls) == 1
        assert not storage.uploads
    else:
        assert response.status_code == 201
        assert len(calls) == 2
        assert str(calls[0]) == str(calls[1])
        with factory() as db:
            assert db.scalar(select(Document)).source_id == canonical.id
    assert 'private conflict' not in response.text


def test_partial_index_blocks_duplicate_but_allows_other_workspace(integration):
    from sqlalchemy.exc import IntegrityError
    _, factory, _ = integration
    with factory() as db:
        db.add_all([source(), source(workspace_id=uuid4())])
        db.commit()
        db.add(source(status='disabled'))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


def test_partial_index_and_migration_exact_sql():
    import importlib.util
    from io import StringIO
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateIndex

    name = 'uq_knowledge_sources_manual_upload_workspace'
    index = next(i for i in KnowledgeSource.__table__.indexes if i.name == name)
    assert list(index.columns.keys()) == ['organization_id', 'workspace_id']
    assert index.unique
    expected = (
        f'CREATE UNIQUE INDEX {name} ON knowledge_sources '
        "(organization_id, workspace_id) WHERE source_type = 'manual_upload' "
        'AND deleted_at IS NULL'
    )
    assert str(CreateIndex(index).compile(dialect=postgresql.dialect())) == expected
    path = Path(__file__).parents[1] / 'alembic/versions/20260928_0011_manual_upload_source_uniqueness.py'
    spec = importlib.util.spec_from_file_location('manual_unique', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.down_revision == '20260928_0010'
    assert module.revision == '20260928_0011'
    for action, sql in [('upgrade', expected + ';'), ('downgrade', f'DROP INDEX {name};')]:
        output = StringIO()
        context = MigrationContext.configure(dialect_name='postgresql', opts={
            'as_sql': True, 'output_buffer': output,
        })
        with Operations.context(context):
            getattr(module, action)()
        assert ' '.join(output.getvalue().split()) == sql
