import {test,expect} from '@playwright/test';

for(const result of ['ready','empty','error'] as const)test(`initial understanding loading: ${result}`,async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',version='00000000-0000-0000-0000-000000000006';
 const requests:string[]=[];
 let release!:()=>void;
 const pending=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  requests.push(route.request().method()+' '+path);
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.0'}});
  if(path.endsWith('/workspace')){
   await pending;
   if(result==='error')return route.fulfill({status:503,json:{detail:'offline failure'}});
   return route.fulfill({json:{context_id:scope,state:result==='ready'?'current':'empty',pending_count:0,intake:[],understanding:[],current:result==='ready'?{id:version,context_space_id:scope,version:1,has_recap:true,intake_ids:[],revision_ids:[version],source_revision_id:version,created_at:'2026-10-27T00:00:00Z'}:null,recap:result==='ready'?{version_id:version,title:'Compréhension conservée',text:'Une synthèse déjà enregistrée.',support_revision_ids:[version]}:null}});
  }
  return route.fulfill({status:404,json:{detail:'unexpected offline request'}});
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 const toggle=page.getByRole('button',{name:'Compréhension',exact:true});
 await toggle.click();
 const panel=page.getByRole('complementary',{name:'Compréhension',exact:true});
 await expect(panel.getByRole('status')).toHaveText('Chargement de la compréhension…');
 await expect(panel).not.toContainText('pas encore été mémorisé');
 await expect(page.locator('.workspace-log').getByRole('status')).toBeVisible();
 // Availability is independent of the pending workspace request.
 await expect(page.locator('.workspace-availability')).toHaveCount(0);
 await panel.getByRole('button',{name:'Fermer',exact:true}).click();await toggle.click();
 await expect(panel.getByRole('status')).toBeVisible();
 release();
 if(result==='ready')await expect(panel.locator('.context-recap')).toHaveText('Une synthèse déjà enregistrée.');
 else if(result==='empty')await expect(panel).toContainText('pas encore été mémorisé');
 else{
  await expect(panel.getByRole('alert')).toContainText('n’a pas pu être chargée');
  await expect(panel).not.toContainText('pas encore été mémorisé');
 }
 await panel.getByRole('button',{name:'Fermer',exact:true}).click();await toggle.click();
 await expect(panel).toBeVisible();
 expect([...requests].sort()).toEqual(['GET /api/context-spaces/'+scope+'/workspace','GET /api/context-spaces/'+scope+'/chat-sessions'].sort());
});
