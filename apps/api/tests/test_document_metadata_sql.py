"""One disposable PostgreSQL check: custom name, replay, metadata and owner isolation."""
import asyncio
from uuid import uuid4

import pytest
from alembic import command

from adapters.postgres.config import database_url
from adapters.postgres.consolidation import PostgresConsolidationRepository
from adapters.postgres.source_documents import document_metadata
from app.core.models import ContextSpaceNotFound
from app.understanding.documents import prepare_document
from app.understanding.enrichment import EnrichmentConflict
from tests.test_migrations import empty_database as empty_database
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_pdf_documents import pdf_bytes


def test_custom_document_name_persists_without_changing_original_or_schema(empty_database):
    command.upgrade(empty_database,'0011_source_documents')
    owner,other,scope=(str(uuid4()) for _ in range(3))
    repository=PostgresConsolidationRepository(url=database_url(),subject_id=owner)
    with repository.connect() as c:
        c.execute("INSERT INTO users(id,display_name) VALUES (%s,'Synthetic'),(%s,'Synthetic')",(owner,other))
        c.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Document UX test')",(scope,owner))
    data=pdf_bytes();operation=str(uuid4())
    doc,source=prepare_document(scope,operation,'CV_original.pdf',data,['Synthetic page.'],'Profil technique')
    run=asyncio.run
    saved=run(repository.import_document(scope,doc,source,data))
    assert saved['intake'][0]['display_name']=='Profil technique'
    reopened=PostgresConsolidationRepository(url=database_url(),subject_id=owner)
    assert run(reopened.import_document(scope,doc,source,data))==saved
    with pytest.raises(EnrichmentConflict):
        run(reopened.import_document(scope,dict(doc,display_name='Changed replay'),source,data))
    assert bytes(run(reopened.document(scope,source['id']))['original'])==data
    legacy,legacy_source=prepare_document(scope,str(uuid4()),'legacy.pdf',data,['Legacy page.'])
    run(reopened.import_document(scope,legacy,legacy_source,data))
    metadata=run(reopened.documents(scope))
    assert [r['filename'] for r in metadata]==['legacy.pdf','CV_original.pdf']
    assert metadata[0]['display_name']=='legacy.pdf'
    assert metadata[1]['display_name']=='Profil technique' and metadata[1]['size_bytes']==len(data)
    assert isinstance(metadata[1]['created_at'],str)
    with repository.connect() as c:
        assert len(document_metadata(c,scope,[source['id']]))==1
        assert document_metadata(c,scope,[])==[]
        assert c.execute('SELECT version_num FROM alembic_version').fetchone()['version_num']=='0011_source_documents'
    denied=PostgresConsolidationRepository(url=database_url(),subject_id=other)
    with pytest.raises(ContextSpaceNotFound):run(denied.documents(scope))
    with pytest.raises(ContextSpaceNotFound):run(denied.document(scope,source['id']))
