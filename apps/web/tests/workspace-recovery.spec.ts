import {test,expect} from '@playwright/test';
const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005';
const revision='00000000-0000-0000-0000-000000000007',source='00000000-0000-0000-0000-000000000008';
const caps={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.0'};

for(const uncertain of [false,true])test('same-question manual recovery without duplication, uncertain='+uncertain,async({page})=>{
 const intake:any[]=[],attempts:any[]=[],sent:any[]=[];let saves=0;
 const state=()=>({context_id:scope,state:'pending',pending_count:intake.length,current:null,recap:null,understanding:[],intake,chat_attempts:attempts});
 const complete=()=>{attempts[0].state='completed';intake.push({id:revision,kind:'message',role:'assistant',text:'Planning détaillé sur six jours.',name:null,context:null,reply_to:intake[0].id});};
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/api/auth/me')return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Planning',status:'active',created_at:'2026-10-27T00:00:00Z',updated_at:'2026-10-27T00:00:00Z'}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/intake')){saves++;intake.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){
   const body=route.request().postDataJSON();sent.push(body);expect(body.question_id).toBe(intake[0].id);
   attempts[0]={...body,state:uncertain?'running':'failed'};
   if(sent.length===1){if(uncertain)return route.abort('failed');return route.fulfill({status:502,json:{detail:'Response generation failed'}});}
   complete();return route.fulfill({json:{state:'completed'}});
  }
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 await page.getByRole('textbox',{name:'Ton message',exact:true}).fill('Prépare un planning détaillé sur six jours.');
 await page.getByRole('button',{name:'Envoyer',exact:true}).click();
 const message=page.locator('.workspace-message.user');await expect(message).toHaveCount(1);
 if(uncertain){
  await expect(message).toContainText('en attente de synchronisation');await expect(message.getByRole('button',{name:'Réessayer',exact:true})).toHaveCount(0);
  complete();await message.getByRole('button',{name:'Actualiser l’état',exact:true}).click();
 }else{
  await expect(message).toContainText('Ta question est conservée');
  await expect(page.getByText(/Le résultat n’est pas confirmé/)).toHaveCount(0);
  await message.getByRole('button',{name:'Réessayer',exact:true}).evaluate((button:HTMLButtonElement)=>{button.click();button.click();});
 }
 await expect(page.locator('.workspace-message.assistant')).toContainText('Planning détaillé sur six jours.');
 await expect(message.getByRole('button',{name:'Réessayer',exact:true})).toHaveCount(0);
 expect(saves).toBe(1);expect(intake).toHaveLength(2);expect(sent).toHaveLength(uncertain?1:2);
 if(!uncertain)expect(sent[0].operation_id).not.toBe(sent[1].operation_id);
});

test('regenerate without new intake keeps previous version on failure and blocks double clicks',async({page})=>{
 let version=1,failed=false;const operations:string[]=[];let additions=0;
 const state=()=>({context_id:scope,state:failed?'failed':'current',pending_count:0,intake:[],understanding:[],chat_attempts:[],current:{id:version===1?source:revision,context_space_id:scope,version,has_recap:true,intake_ids:[],source_revision_id:source,revision_ids:[revision],created_at:'2026-10-27T00:00:00Z'},recap:{version_id:version===1?source:revision,title:version===1?'Compréhension précédente':'Compréhension régénérée',text:'Linee guida per organizzare un atelier informatico.',support_revision_ids:[revision]}});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/api/auth/me')return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Atelier',status:'active',created_at:'2026-10-27T00:00:00Z',updated_at:'2026-10-27T00:00:00Z'}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/intake')){additions++;return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/regenerate')){
   operations.push(route.request().postDataJSON().operation_id);
   if(operations.length===1){failed=true;return route.fulfill({status:422,json:{detail:'offline rejected output'}});}
   failed=false;version++;return route.fulfill({json:state()});
  }
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 const regenerate=page.getByRole('button',{name:'Régénérer',exact:true});await expect(regenerate).toBeEnabled();
 await regenerate.evaluate((button:HTMLButtonElement)=>{button.click();button.click();});
 await expect(page.getByRole('alert')).toContainText('L’analyse ou ses citations');
 await expect(page.getByRole('heading',{name:'Compréhension précédente',exact:true})).toBeVisible();expect(operations).toHaveLength(1);
 await regenerate.click();await expect(page.getByRole('heading',{name:'Compréhension régénérée',exact:true})).toBeVisible();
 expect(operations).toHaveLength(2);expect(operations[0]).not.toBe(operations[1]);expect(additions).toBe(0);
});
