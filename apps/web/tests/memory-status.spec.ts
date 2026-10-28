import {test,expect} from '@playwright/test';
const owner='00000000-0000-0000-0000-000000000005';
const scope='00000000-0000-0000-0000-000000000001',version='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
const caps={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.0'};
const current={id:version,context_space_id:scope,version:1,has_recap:true,intake_ids:[],revision_ids:[revision],source_revision_id:revision,created_at:'2026-10-28T00:00:00Z'};
const recap={version_id:version,title:'Compréhension existante',text:'Un contexte conservé.',support_revision_ids:[revision]};

for(const success of [true,false])test('memory indicator follows publication, '+(success?'success before recap reload':'failure retains pending'),async({page})=>{
 let identify!:()=>void,complete!:()=>void,readRecap!:()=>void;
 const initialGate=new Promise<void>(r=>{identify=r;}),memoryGate=new Promise<void>(r=>{complete=r;}),recapGate=new Promise<void>(r=>{readRecap=r;});
 const intake:any[]=[];let published=false,reads=0;
 const state=()=>({context_id:scope,state:published?'current':intake.length?'pending':'current',pending_count:published?0:intake.length,intake,understanding:[],current:published?{...current,id:revision,version:2,intake_ids:intake.map(i=>i.id)}:current,recap:published?null:recap});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Atelier',status:'active',created_at:current.created_at,updated_at:current.created_at}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/intake')){intake.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){
   intake.push({id:revision,kind:'message',role:'assistant',text:'Réponse simulée.',name:null,context:null,reply_to:intake[0].id});
   return route.fulfill({json:{state:'completed'}});
  }
  if(path.endsWith('/workspace/consolidate')){
   await memoryGate;
   if(!success)return route.fulfill({status:503,json:{detail:'offline failure'}});
   published=true;return route.fulfill({json:state()});
  }
  if(path.endsWith('/workspace')){
   reads++;
   if(reads===1)await initialGate;
   if(published){await recapGate;return route.fulfill({status:503,json:{detail:'recap unavailable'}});}
   return route.fulfill({json:state()});
  }
  return route.fulfill({status:404,json:{detail:'offline only'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 const indicator=page.locator('.workspace-unsaved');
 await expect(page.locator('.workspace-log').getByRole('status')).toBeVisible();
 await expect(indicator).toHaveCount(0);
 identify();await expect(indicator).toHaveText('Compréhension à jour');
 const field=page.getByRole('textbox',{name:'Ton message',exact:true});
 await field.fill('Un nouvel échange à conserver.');
 // An unsent draft is not an added exchange.
 await expect(indicator).toHaveText('Compréhension à jour');
 await page.getByRole('button',{name:'Envoyer',exact:true}).click();
 await expect(page.locator('.workspace-message.assistant')).toContainText('Réponse simulée.');
 await expect(indicator).toHaveText('Nouveaux échanges à mémoriser');
 await page.getByRole('button',{name:'Mémoriser',exact:true}).click();
 await expect(indicator).toHaveText('Mémorisation en cours…');
 complete();
 if(success){
  // Publication itself updates the label; the subsequent recap read is blocked.
  await expect(indicator).toHaveText('Compréhension à jour');
  await expect.poll(()=>reads).toBe(3);
  await expect(page.getByRole('button',{name:'Mémorisation…',exact:true})).toBeDisabled();
  readRecap();await expect(page.getByText('Version enregistrée.',{exact:false})).toBeVisible();
  await expect(indicator).toHaveText('Compréhension à jour');
 }else{
  await expect(page.getByRole('alert')).toContainText('Le résultat n’est pas confirmé');
  await expect(indicator).toHaveText('Nouveaux échanges à mémoriser');
 }
});

test('server-side running memorization takes precedence over pending count',async({page})=>{
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace'))return route.fulfill({json:{context_id:scope,state:'running',pending_count:1,intake:[],understanding:[],current,recap}});
  return route.fulfill({status:404,json:{detail:'offline only'}});
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 await expect(page.locator('.workspace-unsaved')).toHaveText('Mémorisation en cours…');
});
