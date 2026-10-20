import {test,expect} from '@playwright/test';
import {QhApi,ApiError} from '../src/api';
const scope='00000000-0000-0000-0000-000000000001',source='00000000-0000-0000-0000-000000000002',revision='00000000-0000-0000-0000-000000000003';
test('enrichment wire contract rejects foreign scope, duplicate IDs and misleading provider mode',async()=>{
 const original=globalThis.fetch;
 const payload={conversation_id:scope,operation_id:source,turns:[{id:revision,role:'user' as const,content:'Une hypothèse, pas un fait confirmé.',captured_at:'2026-10-19T12:00:00Z'}],persist_consent:true};
 const receipt={context_id:scope,source_revision_id:source,revision_ids:[revision],replayed:false,provider_mode:'offline-literal/1'};
 let value:unknown=receipt;let sent:RequestInit|undefined;let path='';
 globalThis.fetch=async(p,init)=>{path=String(p);sent=init;return new Response(JSON.stringify(value));};
 try{
  const api=new QhApi(()=>'synthetic-test-only',()=>{});expect(await api.enrich(scope,payload)).toEqual(receipt);
  expect(path).toBe('/api/context-spaces/'+scope+'/enrichments');expect(sent?.method).toBe('POST');expect(JSON.parse(String(sent?.body))).toEqual(payload);expect(sent?.redirect).toBe('error');
  for(const changed of [{context_id:source},{revision_ids:[revision,revision]},{source_revision_id:'invented'},{provider_mode:'mistral-small-2603'},{replayed:'yes'}]){value={...receipt,...changed};await expect(api.enrich(scope,payload)).rejects.toBeInstanceOf(ApiError);}
 }finally{globalThis.fetch=original;}
});
