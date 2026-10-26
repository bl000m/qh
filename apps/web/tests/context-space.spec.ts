import {test,expect} from '@playwright/test';
// UI wiring only. HTTP fixtures are offline and do not demonstrate real AI quality.
for(const width of [1440,375])test('Context Space discussion, pending intake, failure, consolidation and portable import '+width,async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
 let version=0,failed=false,consolidations=0;
 const inputs:any[]=[];
 const state=()=>({context_id:scope,state:failed?'failed':inputs.length>(version?2:0)?'pending':version?'current':'empty',pending_count:inputs.length-(version?2:0),intake:inputs,current:version?{id:domain,context_space_id:scope,version,intake_ids:inputs.slice(0,2).map(i=>i.id),source_revision_id:domain,revision_ids:[revision],created_at:'2026-10-26T12:00:00Z'}:null,understanding:version?[{context_space_id:scope,item_id:revision,revision_id:revision,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:3,content:{text:'Préparer le projet.',primary_dimension:{value:'objectives_intentions',certainty:'tentative',review_state:'proposed',evidence_refs:[0]},extraction:{key:'qh-context-uum/3',input_sha256:'offline'},citations:[{source_revision_id:domain,quote:'Préparer le projet.',start:0,end:19}]},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-26T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:domain,source_revision_id:domain,revision_no:1,origin:{}}]}]:[]});
 await page.setViewportSize({width,height:1000});
 await page.route('**/api/**',async route=>{
  const p=new URL(route.request().url()).pathname.slice(4);let value:any;
  if(p==='/auth/me')value={user_id:owner};
  else if(p==='/context-spaces/'+scope)value={id:scope,owner_id:owner,name:'Projet QH',status:'active',created_at:'2026-10-23T00:00:00Z',updated_at:'2026-10-23T00:00:00Z'};
  else if(p==='/environment')value={version:1,domains:[{id:domain,name:'Travail',description:''}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},space_descriptions:{},usage:{}};
  else if(p.endsWith('/open'))value={};
  else if(p.endsWith('/chat-sessions'))value={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.9'};
  else if(p.endsWith('/workspace'))value=state();
  else if(p.endsWith('/workspace/intake')){const input=route.request().postDataJSON();if(!inputs.some(i=>i.id===input.id))inputs.push(input);value=state();}
  else if(p.endsWith('/workspace/consolidate')){consolidations++;if(consolidations===1){failed=true;return route.fulfill({status:503,json:{detail:'offline failure'}});}version++;failed=false;value=state();}
  else return route.fulfill({status:404,json:{detail:'outside fixture'}});
  return route.fulfill({json:value});
 });
 await page.goto('/tests/fixtures/context-space.html');
 const field=page.getByRole('textbox',{name:'Votre message',exact:true});await expect(field).toBeEnabled();
 await expect(page.getByRole('tab')).toHaveCount(0);await expect(page.getByRole('button',{name:'Mémoriser',exact:true})).toBeDisabled();
 await expect(page.getByRole('complementary',{name:'Compréhension'})).toHaveCount(0);expect(consolidations).toBe(0);
 await page.locator('input[type=file]').first().setInputFiles({name:'contexte.md',mimeType:'text/markdown',buffer:Buffer.from('Préparer le projet.')});
 await expect(page.getByRole('status').filter({hasText:'apports en attente'})).toContainText('1 apports');
 await field.fill('La date reste incertaine.');await page.getByRole('button',{name:'Mémoriser',exact:true}).click();await expect(page.getByRole('alert')).toContainText('n’est pas confirmé');
 expect(inputs).toHaveLength(2);expect(consolidations).toBe(1);
 await page.getByRole('button',{name:'Mémoriser',exact:true}).click();await expect(page.getByRole('complementary',{name:'Compréhension'})).toBeVisible();
 await expect(page.getByText('Version 1', {exact:false})).toBeVisible();await expect(page.locator('.understanding-statement>p').filter({hasText:'Préparer le projet.'})).toBeVisible();
 await page.getByText('Provenance',{exact:true}).click();await expect(page.getByText('Interprétation de QH · non confirmée par un humain')).toBeVisible();
 await page.getByRole('button',{name:'Agrandir',exact:true}).click();await page.getByRole('button',{name:'Fermer',exact:true}).click();
 await expect(page.getByRole('complementary',{name:'Compréhension'})).toHaveCount(0);
 await page.locator('input[type=file]').first().setInputFiles({name:'not-supported.pdf',mimeType:'application/pdf',buffer:Buffer.from('offline')});await expect(page.getByRole('alert')).toContainText('PDF n’est pas encore disponible');expect(inputs).toHaveLength(2);
 const portable={schema_version:'qh.context-space/1',logical_id:domain,name:'Import',version:1,consolidated_at:'2026-10-26T12:00:00Z',understanding:[{id:revision,text:'Préparer le projet.',primary_dimension:'objectives_intentions',certainty:'tentative',validation_state:'proposed',evidence:[{source_revision_id:domain,quote:'Préparer le projet.',turn_id:null}]}]};
 await page.locator('input[type=file]').nth(1).setInputFiles({name:'context.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(portable))});
 await expect(page.getByRole('status').filter({hasText:'Contexte importé'})).toBeVisible();expect(inputs[2].context).toEqual(portable);expect(consolidations).toBe(2);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
});
