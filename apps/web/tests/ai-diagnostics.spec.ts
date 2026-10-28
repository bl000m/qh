import {test,expect} from '@playwright/test';
import {capabilities} from '../src/provider-session';
import {QhApi} from '../src/api';
const scope='00000000-0000-0000-0000-000000000001';
test('UUM measurements and advisory flags appear only inside private development diagnostics',async({page})=>{
 let reads=0;
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.00'}});
  if(path.endsWith('/workspace'))return route.fulfill({json:{context_id:scope,state:'empty',pending_count:0,current:null,recap:null,intake:[],understanding:[]}});
  if(path.endsWith('/ai/diagnostics')){
   reads++;expect(route.request().method()).toBe('GET');
   return route.fulfill({json:{retention_seconds:3600,items:[{id:scope,context_id:scope,created_at:Date.now()/1000,expires_at:Date.now()/1000+3600,kind:'uum',outcome:'accepted',attempt_index:0,http_status:200,checks:[],raw_response:{},accounting:{},metrics:{input_tokens:1000,output_tokens:5000,provider_ms:125,consolidation_ms:250,atomic_items:12,passage_references:15,source_chars:3000,source_tokens:null,output_json_chars:8000},warnings:['output_tokens_over_3x_input']}]}});
  }
  return route.fulfill({status:404,json:{detail:'offline only'}});
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 await expect(page.getByRole('region',{name:'Performances UUM privées'})).toHaveCount(0);expect(reads).toBe(0);
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 await page.getByText('Diagnostics IA (développement)',{exact:true}).click();
 await page.getByRole('button',{name:'Charger les diagnostics privés'}).click();
 await page.getByText('uum · tentative 0 · accepted · HTTP 200',{exact:true}).click();
 const metrics=page.getByRole('region',{name:'Performances UUM privées'});
 await expect(metrics).toBeVisible();await expect(metrics).toContainText('Appel Mistral · ms');
 await expect(metrics.locator('dd').filter({hasText:/^125$/})).toHaveCount(1);
 await expect(metrics).toContainText('non isolés');await expect(metrics).toContainText('—');
 await expect(metrics).toContainText('Sortie supérieure à trois fois l’entrée');
 await expect(metrics).toContainText('sans refus, plafond ou nouvelle tentative automatique');
 expect(reads).toBe(1);
});
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


test('development POC has no call/session quota and retains the one economic envelope',()=>{
 const value={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.999'};
 expect(capabilities(value)).toEqual(value);expect(()=>capabilities({...value,remaining_usd:'5.01'})).toThrow();
});
