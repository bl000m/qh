import {test,expect} from '@playwright/test';

for(const width of [1440,375])test('guest sees an approved subject recap and explores projection details without source access '+width,async({page})=>{
 await page.setViewportSize({width,height:1000});
 const snapshot='00000000-0000-0000-0000-000000000003';
 const title='Organizzazione di un laboratorio informatico';
 const details=Array.from({length:30},(_,i)=>`${i+1}. Preparare l’attività pratica ${i+1}.`).join('\n');
 const requests:string[]=[];let asks=0;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;requests.push(path);
  if(path==='/api/guest/session')return route.fulfill({json:{snapshot_id:snapshot,rights:['READ','ASK_AI'],verification:'mailbox_control',expires_at:'2030-01-01T00:00:00Z'}});
  if(path==='/api/guest/provider')return route.fulfill({json:{enabled:true,simulated:true,model:'offline'}});
  if(path==='/api/guest/snapshots/'+snapshot)return route.fulfill({json:{format:'qh.disclosure/1',recap:{title,text:'Linee guida proposte per progettare e condurre un laboratorio informatico, con attività pratiche, strumenti digitali e valutazione.'},items:[{reference:'R1',text:details,origin_kind:'ai',validation_state:'proposed',sources:['S1']}]}});
  if(path==='/api/guest/snapshots/'+snapshot+'/ask'){asks++;return route.fulfill({json:{simulated:true,answer:details,reference_aliases:['R1'],insufficient_context:false}});}
  return route.fulfill({status:403,json:{detail:'outside approved projection'}});
 });
 await page.goto('/tests/fixtures/guest-understanding.html');
 const understanding=page.getByRole('region',{name:'Compréhension',exact:true});
 await expect(understanding.getByRole('heading',{name:title,exact:true})).toBeVisible();
 await expect(understanding.locator('.context-recap')).toContainText('Linee guida proposte');
 await expect(understanding.getByText('30. Preparare l’attività pratica 30.',{exact:false})).not.toBeVisible();
 await expect(understanding.locator('ul,li,blockquote')).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Exporter',exact:true})).toHaveCount(0);
 await expect(page.getByText('Consulter les sources',{exact:true})).toHaveCount(0);
 expect(asks).toBe(0);
 await page.getByRole('textbox',{name:'Votre question sur le snapshot',exact:true}).fill('Dammi i 30 passaggi completi.');
 await page.getByRole('button',{name:'Interroger le snapshot',exact:true}).click();
 await expect(page.locator('.guest-answer')).toContainText('30. Preparare l’attività pratica 30.');
 expect(asks).toBe(1);expect(requests.every(path=>path.startsWith('/api/guest/'))).toBe(true);
});

test('owner can explicitly refresh an older recap without adding a message or automatic generation',async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',version='00000000-0000-0000-0000-000000000006';
 let generated=0;
 const state=()=>({context_id:scope,state:'current',pending_count:0,intake:[],understanding:[],current:{id:version,context_space_id:scope,version:generated?2:1,has_recap:!!generated,intake_ids:[],revision_ids:[version],source_revision_id:version,created_at:'2026-10-27T00:00:00Z'},recap:{version_id:version,title:generated?'Organizzazione di un laboratorio informatico':'Old overview',text:generated?'Linee guida proposte per organizzare un laboratorio informatico.':'The user requests a workshop.',support_revision_ids:[version]}});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/api/auth/me')return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Atelier',status:'active',created_at:'2026-10-27T00:00:00Z',updated_at:'2026-10-27T00:00:00Z'}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.0'}});
  if(path.endsWith('/workspace/consolidate')){generated++;return route.fulfill({json:state()});}
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 const memory=page.getByRole('button',{name:'Mémoriser',exact:true});await expect(memory).toBeEnabled();expect(generated).toBe(0);
 await memory.click();
 await expect(page.getByRole('heading',{name:'Organizzazione di un laboratorio informatico',exact:true})).toBeVisible();
 expect(generated).toBe(1);await expect(memory).toBeDisabled();
});
