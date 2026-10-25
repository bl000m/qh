import {test,expect} from '@playwright/test';
import {DIMENSIONS} from '../src/uum';
const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005';
test('final memory: safe Markdown, no empty sources, accurate zero and closing after errors',async({page},info)=>{
 await page.setViewportSize({width:375,height:620});let mode='error',proposals=0;
 await page.route('**/api/**',async route=>{
  const u=new URL(route.request().url()),p=u.pathname.slice(4);let value:unknown;
  if(p==='/auth/me')value={user_id:owner};
  else if(p==='/context-spaces/'+scope)value={id:scope,owner_id:owner,name:'Atelier fictif',status:'active',created_at:'2026-10-24T00:00:00Z',updated_at:'2026-10-24T00:00:00Z'};
  else if(p==='/environment')value={version:1,domains:[],memberships:{},primary_domains:{},space_descriptions:{},usage:{}};
  else if(p.endsWith('/open'))value={};
  else if(p.endsWith('/understanding-presence'))value={context_id:scope,view:u.searchParams.get('view'),dimensions:Object.fromEntries(DIMENSIONS.map(([id])=>[id,false])),unclassified:false};
  else if(p.endsWith('/understanding'))value={view:u.searchParams.get('view'),items:[],next_after_revision_id:null};
  else if(p.endsWith('/chat-sessions'))value={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.99'};
  else if(p.endsWith('/enrichments/capabilities'))value={literal:true,semantic:true,external_disclosure:true};
  else if(p.endsWith('/ai/messages')||p.endsWith('/chat'))value={context_id:scope,answer:'**Atelier fictif**\n\nVoici une proposition.\n\n- Un objectif\n- Une question\n\n[piège](javascript:alert(1)) <img src=x onerror=alert(1)>',model:'mistral-small-2603',references:[],provided_revisions:[],support_basis:'dialogue',insufficient_context:true,partial_coverage:false,input_bound:1000,context_bytes:0,generation_seconds:.1};
  else if(p.endsWith('/ai/proposals')){proposals++;if(mode==='error')return route.fulfill({status:503,json:{detail:'unavailable'}});value={context_id:scope,source_revision_id:owner,revision_ids:[],replayed:false,provider_mode:'uum-mistral/3'};}
  else return route.fulfill({status:404,json:{detail:'outside fixture'}});
  return route.fulfill({json:value});
 });
 await page.goto('/tests/fixtures/radial-target.html');const field=page.getByLabel('Votre question sur ce contexte');await expect(field).toBeEnabled();await field.fill('Dans cet exemple fictif, je souhaite organiser un atelier.');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 const answer=page.locator('.chat-markdown');await expect(answer.locator('strong')).toHaveText('Atelier fictif');await expect(answer.locator('li')).toHaveText(['Un objectif','Une question']);await expect(answer.locator('img,a')).toHaveCount(0);await expect(answer).toContainText('<img src=x onerror=alert(1)>');await expect(page.getByRole('button',{name:/Sources de la réponse/})).toHaveCount(0);await expect(page.locator('[data-insufficient-context]')).toBeVisible();
 const open=page.getByRole('button',{name:'Mémoriser cette conversation',exact:false}),modal=page.getByRole('dialog',{name:'Mémoriser cette conversation',exact:true});
 for(const close of ['escape','button','x']){
  await open.click();await expect(modal.getByRole('checkbox')).toHaveCount(0);await modal.getByRole('button',{name:'Continuer',exact:true}).click();await expect(modal.getByRole('heading',{name:'L’analyse n’a pas pu être terminée'})).toBeVisible();await expect(modal.getByRole('alert')).toContainText('n’est pas confirmé');
  await modal.evaluate(n=>{n.scrollTop=n.scrollHeight;});await expect(modal.getByRole('button',{name:'Fermer la fenêtre',exact:true})).toBeInViewport();
  if(close==='escape')await page.keyboard.press('Escape');else await modal.getByRole('button',{name:close==='x'?'Fermer la fenêtre':'Fermer',exact:true}).click();await expect(modal).toHaveCount(0);
 }
 expect(proposals).toBe(3);mode='zero';await open.click();await modal.getByRole('button',{name:'Continuer',exact:true}).click();await expect(modal.getByRole('heading',{name:'Conversation enregistrée, aucune information proposée',exact:true})).toBeVisible();await expect.poll(()=>modal.evaluate(n=>n.scrollTop)).toBe(0);await expect(modal.getByRole('button',{name:'Voir les propositions',exact:true})).toHaveCount(0);await expect(modal).toContainText('aucune compréhension structurée');await page.screenshot({path:info.outputPath('final-memory-zero-mobile.png')});await modal.getByRole('button',{name:'Fermer',exact:true}).click();await expect(modal).toHaveCount(0);expect(proposals).toBe(4);
});
