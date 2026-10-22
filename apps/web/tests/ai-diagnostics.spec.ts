import {test,expect} from '@playwright/test';
import {capabilities} from '../src/provider-session';
import {QhApi} from '../src/api';
const scope='00000000-0000-0000-0000-000000000001';
test('development capability accepts the explicit hundred-call envelope without widening legacy sessions',()=>{
 const cap={automatic:true,plafond_reached:false,enabled:true,model:'mistral-small-2603',max_seconds:1800,max_calls:100,max_usd:'2.50',provider_expires_at:1900000000,remaining_calls:94,remaining_usd:'2.49701920'};
 expect(capabilities(cap)).toEqual(cap);
 for(const change of [{automatic:false},{max_calls:101},{remaining_calls:101},{max_usd:'5.00'},{remaining_usd:'2.51'}])expect(()=>capabilities({...cap,...change})).toThrow();
});
test('diagnostic client scopes authenticated reads and deletes, rejects foreign records, retains no browser storage',async()=>{
 const original=globalThis.fetch;const requests:{path:unknown;init?:RequestInit}[]=[];
 let result:unknown={retention_seconds:3600,items:[{id:scope,context_id:scope,expires_at:1900000000,checks:[],raw_response:{id:'synthetic'}}]};
 globalThis.fetch=async(path,init)=>{requests.push({path,init});return new Response(JSON.stringify(result));};
 try{
  const api=new QhApi(()=>'synthetic-only',()=>{});
  expect(await api.aiDiagnostics(scope)).toHaveLength(1);
  await api.deleteAIDiagnostic(scope,scope);
  expect(requests.map(r=>r.path)).toEqual(['/api/context-spaces/'+scope+'/ai/diagnostics','/api/context-spaces/'+scope+'/ai/diagnostics/'+scope]);
  expect(requests[1].init?.method).toBe('DELETE');expect(requests[0].init?.cache).toBe('no-store');
  result={retention_seconds:3600,items:[{id:scope,context_id:'foreign',expires_at:1900000000,checks:[]}]};
  await expect(api.aiDiagnostics(scope)).rejects.toMatchObject({status:502});
  await expect(api.aiDiagnostics('../foreign')).rejects.toMatchObject({status:404});
 }finally{globalThis.fetch=original;}
});
