"""One owner document: organization plus minimal server-authored opening counters."""
import asyncio
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.spaces import space, FIELDS
from app.core.models import ContextStorageUnavailable, ContextSpaceNotFound
from app.environment.service import OrganizationConflict, defaults


class PostgresOrganizationRepository:
    def __init__(self, *, url):
        self.url = url

    @staticmethod
    def _store(c, subject, document):
        body = {k: document[k] for k in ('domains','memberships','primary_domains','usage')}
        c.execute('INSERT INTO owner_organization(owner_id,version,document) VALUES (%s,%s,%s) '
                  'ON CONFLICT(owner_id) DO UPDATE SET version=EXCLUDED.version,document=EXCLUDED.document',
                  (subject, document['version'], Jsonb(body)))

    @staticmethod
    def _public(document):
        return dict(document, usage={id: {k: value[k] for k in ('last_opened_at','open_count')}
                                    for id, value in document['usage'].items()})

    def _operation(self, subject, document=None, *, opening=None, creation=None, page=None):
        repo = CanonicalRepository(url=self.url, subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')
        try:
            with repo.connect() as c:
                if not c.execute("SELECT id FROM users WHERE id=%s AND status='active' FOR UPDATE", (subject,)).fetchone():
                    raise PermissionError('Owner access required')
                row = c.execute('SELECT version,document FROM owner_organization WHERE owner_id=%s', (subject,)).fetchone()
                current = dict(row['document'], version=row['version']) if row else defaults()
                if page:
                    sort, domain, limit, after = page
                    order = 'opened DESC,id' if sort=='recent' else 'uses DESC,opened DESC,id'
                    cte = '''WITH ranked AS (
                        SELECT cs.id,row_number() OVER(ORDER BY '''+order+''') AS position FROM (
                            SELECT cs.id,coalesce((%s::jsonb->cs.id::text->>'open_count')::bigint,0) AS uses,
                            coalesce((%s::jsonb->cs.id::text->>'last_opened_at')::timestamptz,'epoch'::timestamptz) AS opened
                            FROM context_spaces cs WHERE cs.owner_id=%s AND cs.status='active'
                            AND (%s::text IS NULL OR
                                (%s='unclassified' AND coalesce(jsonb_array_length(%s::jsonb->cs.id::text),0)=0) OR
                                (%s<>'unclassified' AND coalesce(%s::jsonb->cs.id::text,'[]'::jsonb) ? %s))
                        ) cs) '''
                    args=(Jsonb(current['usage']),Jsonb(current['usage']),subject,domain,domain,Jsonb(current['memberships']),domain,Jsonb(current['memberships']),domain)
                    if after and not c.execute(cte+'SELECT id FROM ranked WHERE id=%s', (*args,after)).fetchone():
                        raise ContextSpaceNotFound('Resume cursor unavailable')
                    return [str(r['id']) for r in c.execute(cte+'''SELECT id FROM ranked WHERE position>
                        coalesce((SELECT position FROM ranked WHERE id=%s::uuid),0) ORDER BY position LIMIT %s''',(*args,after,limit)).fetchall()]
                if opening:
                    scope,event_id=opening
                    repo._authorize(c,(scope,),lock=True)
                    value=current['usage'].get(scope,dict(open_count=0,recent_events=[]))
                    if event_id not in value['recent_events']:
                        value=dict(open_count=value['open_count']+1,
                            last_opened_at=c.execute('SELECT clock_timestamp() AS time').fetchone()['time'].isoformat(),
                            recent_events=[*value['recent_events'],event_id][-32:])
                        current['usage'][scope]=value
                        # Usage does not invalidate organization-editor versions.
                        if current['version']==0: current['version']=1
                        self._store(c,subject,current)
                    return {k:value[k] for k in ('last_opened_at','open_count')}
                if creation:
                    name,primary=creation
                    if primary not in {d['id'] for d in current['domains']}:
                        raise OrganizationConflict('Unknown primary domain; reload organization')
                    identifier=str(uuid4())
                    record=c.execute('INSERT INTO context_spaces AS cs(id,owner_id,name) VALUES(%s,%s,%s) RETURNING '+FIELDS,(identifier,subject,name)).fetchone()
                    current['memberships'][identifier]=[primary];current['primary_domains'][identifier]=primary
                    current['version']+=1
                    self._store(c,subject,current)
                    return space(record)
                # Never return private foreign membership/usage identities after revocation.
                scopes=set(current['memberships'])|set(current['usage'])
                if document is None:
                    if scopes: repo._authorize(c,scopes,lock=True)
                    return self._public(current)
                if document['version'] != current['version']:
                    raise OrganizationConflict('Organization changed; reload before editing')
                if document['memberships']: repo._authorize(c,document['memberships'],lock=True)
                # Read-only usage is never accepted from the browser.
                result=dict(document,version=current['version']+1,usage=current['usage'])
                self._store(c,subject,result)
                return self._public(result)
        except psycopg.Error:
            raise ContextStorageUnavailable('Organization unavailable') from None

    async def read(self, subject):
        return await asyncio.to_thread(self._operation, subject)

    async def replace(self, subject, document):
        return await asyncio.to_thread(self._operation, subject, document)

    async def opened(self, subject, scope, event_id):
        return await asyncio.to_thread(self._operation, subject, opening=(scope,event_id))

    async def create_space(self, subject, name, primary_domain_id):
        return await asyncio.to_thread(self._operation, subject, creation=(name,primary_domain_id))

    async def resume(self, subject, sort, domain, limit, after):
        return await asyncio.to_thread(self._operation, subject, page=(sort,domain,limit,after))
