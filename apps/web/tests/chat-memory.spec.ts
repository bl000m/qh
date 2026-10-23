import {test,expect} from '@playwright/test';
import {DIMENSIONS} from '../src/uum';
const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
for(const [width,height] of [[1600,956],[1122,1402],[1470,848],[375,1000],[320,1000]])test('chat/memorisation visual and full conversation '+width,async({page},info)=>{
 let submissions:any[]=[],sent=0,saved=false,fail=true,remaining='4.9995';
 await page.setViewportSize({width,height});
 await page.route('**/api/**',async route=>{
  const req=route.request(),u=new URL(req.url()),p=u.pathname.slice(4);let value:any;
  if(p==='/auth/me')value={user_id:owner};
  else if(p==='/context-spaces/'+scope)value={id:scope,owner_id:owner,name:'Projet QH',status:'active',created_at:'2026-10-23T00:00:00Z',updated_at:'2026-10-23T00:00:00Z'};
  else if(p==='/environment')value={version:1,domains:[{id:domain,name:'Travail & projets',description:''}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},space_descriptions:{[scope]:'Compréhension portable entre IA'},usage:{}};
  else if(p.endsWith('/open'))value={};
  else if(p.endsWith('/understanding-presence'))value={context_id:scope,view:u.searchParams.get('view'),dimensions:Object.fromEntries(DIMENSIONS.map(([id])=>[id,saved&&id==='objectives_intentions'])),unclassified:false};
  else if(p.endsWith('/understanding'))value={view:u.searchParams.get('view'),items:[],next_after_revision_id:null};
  else if(p.endsWith('/chat-sessions'))value={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:remaining};
  else if(p.endsWith('/enrichments/capabilities'))value={literal:true,semantic:true,external_disclosure:true};
  else if(p.endsWith('/chat')||p.endsWith('/ai/messages')){sent++;value={context_id:scope,answer:'Nous pouvons préciser ce projet étape par étape.',model:'mistral-small-2603',references:[],provided_revisions:[],support_basis:'dialogue',insufficient_context:false,partial_coverage:false,input_bound:1000,context_bytes:100,generation_seconds:.1};}
  else if(p.endsWith('/ai/proposals')){submissions.push(req.postDataJSON());if(fail)return route.fulfill({status:503,json:{detail:'unavailable'}});saved=true;value={context_id:scope,source_revision_id:domain,revision_ids:[revision],replayed:false,provider_mode:'uum-mistral/3'};}
  else return route.fulfill({status:404,json:{detail:'outside fixture'}});
  return route.fulfill({json:value});
 });
 await page.goto('/tests/fixtures/radial-target.html');await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();await expect(page.locator('.assistant-model')).toContainText('4.9995 USD');
 const mapBefore=await page.locator('.space-context-map').boundingBox();const field=page.getByLabel('Votre question sur ce contexte');
 const composer=await page.locator('.product-composer').boundingBox(),memory=await page.locator('.memory-card').boundingBox(),footer=await page.locator('.chat-footer').boundingBox();expect(composer!.y+composer!.height).toBeLessThanOrEqual(memory!.y);expect(memory!.y).toBeLessThan(footer!.y);
 await expect(page.getByRole('button',{name:'Mémoriser cette conversation',exact:false})).toBeDisabled();
 for(let i=0;i<5;i++){await field.fill('Je veux clarifier mon projet, point '+i+'.');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.locator('.chat-turn')).toHaveCount(i+1);}
 expect(sent).toBe(5);await page.evaluate(()=>window.scrollTo(0,0));expect(await page.locator('.space-context-map').boundingBox()).toEqual(mapBefore);
 await page.screenshot({path:info.outputPath('chat-'+width+'.png'),fullPage:true});await page.locator('.assistant-card').screenshot({path:info.outputPath('chat-panel-'+width+'.png')});if(width===1122){await page.getByRole('button',{name:'Agrandir la discussion',exact:true}).click();await expect.poll(()=>page.evaluate(()=>!!document.fullscreenElement)).toBe(true);await page.screenshot({path:info.outputPath('chat-reference-resolution.png')});await page.evaluate(()=>document.exitFullscreen());}
 remaining='4.998';await page.evaluate(()=>dispatchEvent(new Event('focus')));await expect(page.locator('.assistant-model')).toContainText('4.998 USD');expect(sent).toBe(5);
 await page.getByRole('button',{name:'Mémoriser cette conversation',exact:false}).click();const modal=page.getByRole('dialog',{name:'Mémoriser cette conversation',exact:true});
 await expect(modal.getByRole('checkbox')).toHaveCount(0);await expect(modal.locator('.memory-steps>section')).toHaveCount(3);await expect(modal).toContainText('Mistral Small');expect(submissions).toHaveLength(0);
 await page.screenshot({path:info.outputPath('memorisation-'+width+'.png'),fullPage:false});
 await modal.getByRole('button',{name:'Continuer',exact:true}).click();await expect(modal.getByRole('alert')).toContainText('n’est pas confirmé');expect(submissions).toHaveLength(1);await page.waitForTimeout(200);expect(submissions).toHaveLength(1);
 fail=false;await modal.getByRole('button',{name:'Continuer',exact:true}).click();await expect(modal.getByRole('button',{name:'Voir la proposition',exact:true})).toBeVisible();expect(submissions).toHaveLength(2);expect(submissions[1]).toEqual(submissions[0]);expect(submissions[0].turns).toHaveLength(10);expect(submissions[0].turns.map((t:any)=>t.role)).toEqual(Array.from({length:10},(_,i)=>i%2?'assistant':'user'));expect(submissions[0].persist_consent).toBe(true);expect(submissions[0].extraction_mode).toBe('semantic');
 await modal.getByRole('button',{name:'Voir la proposition',exact:true}).click();await expect(page.getByRole('tab',{name:'Éléments',exact:true})).toHaveAttribute('aria-selected','true');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
});
