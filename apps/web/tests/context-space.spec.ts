import {test,expect} from '@playwright/test';
// UI wiring only. HTTP fixtures are offline and do not demonstrate real AI quality.
for(const width of [1440,375])test('Context Space discussion, pending intake, failure, consolidation and portable import '+width,async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
 let version=0,failed=false,consolidations=0,consumed=0,sends=0;
 const inputs:any[]=[];
 const state=()=>({context_id:scope,state:failed?'failed':inputs.length>consumed?'pending':version?'current':'empty',pending_count:inputs.length-consumed,intake:inputs,recap:version?{version_id:domain,title:'Préparation du projet',text:'Ce contexte rassemble les objectifs du projet et les informations utiles à sa préparation. Certains points restent à préciser.',support_revision_ids:[revision]}:null,current:version?{id:domain,context_space_id:scope,version,intake_ids:inputs.slice(0,consumed).map(i=>i.id),source_revision_id:domain,revision_ids:[revision],created_at:'2026-10-26T12:00:00Z'}:null,understanding:version?[{context_space_id:scope,item_id:revision,revision_id:revision,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:3,content:{text:'Préparer le projet.',primary_dimension:{value:'objectives_intentions',certainty:'tentative',review_state:'proposed',evidence_refs:[0]},extraction:{key:'qh-context-uum/3',input_sha256:'offline'},citations:[{source_revision_id:domain,quote:'Préparer le projet.',start:0,end:19}]},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-26T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:domain,source_revision_id:domain,revision_no:1,origin:{}}]}]:[]});
 await page.setViewportSize({width,height:1000});
 await page.route('**/api/**',async route=>{
  const p=new URL(route.request().url()).pathname.slice(4);let value:any;
  if(p==='/auth/me')value={user_id:owner};
  else if(p==='/context-spaces/'+scope)value={id:scope,owner_id:owner,name:'Projet QH',status:'active',created_at:'2026-10-23T00:00:00Z',updated_at:'2026-10-23T00:00:00Z'};
  else if(p==='/environment')value={version:1,domains:[{id:domain,name:'Travail',description:''}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},space_descriptions:{},usage:{}};
  else if(p.endsWith('/open'))value={};
  else if(p.endsWith('/chat-sessions'))value={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.9'};
  else if(p.includes('/workspace/documents/')&&route.request().method()==='PUT')return route.fulfill({status:422,json:{detail:'PDF corrompu ou non pris en charge.'}});
  else if(p.endsWith('/workspace'))value=state();
  else if(p.endsWith('/workspace/intake')){const input=route.request().postDataJSON();if(!inputs.some(i=>i.id===input.id))inputs.push(input);value=state();}
  else if(p.endsWith('/workspace/messages')){
   sends++;const text='Per un risotto: riso Carnaroli, brodo, cipolla, burro e Parmigiano. '.repeat(16);
   inputs.push({id:crypto.randomUUID(),kind:'message',role:'assistant',text,name:null,context:null,attribution:{model:'mistral-small-2603',support_basis:'general',reference_ids:[],insufficient_context:false,partial_coverage:false}});
   value={context_id:scope,answer:text,model:'mistral-small-2603',references:[],provided_revisions:[],support_basis:'general',insufficient_context:false,partial_coverage:false,input_bound:1000,context_bytes:100,generation_seconds:.1};
  }
  else if(p.endsWith('/workspace/consolidate')){consolidations++;if(consolidations===1){failed=true;return route.fulfill({status:503,json:{detail:'offline failure'}});}version++;consumed=inputs.length;failed=false;value=state();}
  else return route.fulfill({status:404,json:{detail:'outside fixture'}});
  return route.fulfill({json:value});
 });
 await page.goto('/tests/fixtures/context-space.html');
 const field=page.getByRole('textbox',{name:'Ton message',exact:true});await expect(field).toBeEnabled();
 await expect(page.getByRole('tab')).toHaveCount(0);await expect(page.getByRole('button',{name:'Mémoriser',exact:true})).toBeDisabled();
 await expect(page.getByRole('complementary',{name:'Compréhension'})).toHaveCount(0);expect(consolidations).toBe(0);
 await page.locator('input[type=file]').first().setInputFiles({name:'contexte.md',mimeType:'text/markdown',buffer:Buffer.from('Préparer le projet.')});
 await expect(page.getByText('Nouveaux échanges à mémoriser',{exact:true})).toBeVisible();
 await field.fill('La date reste incertaine.');await page.getByRole('button',{name:'Mémoriser',exact:true}).click();await expect(page.locator('.workspace-feedback').getByRole('alert')).toContainText('n’est pas confirmé');
 expect(inputs).toHaveLength(2);expect(consolidations).toBe(1);
 if(width<850)await page.getByRole('dialog',{name:'Compréhension',exact:true}).getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 await page.getByRole('button',{name:'Mémoriser',exact:true}).click();const panel=width>850?page.getByRole('complementary',{name:'Compréhension'}):page.getByRole('dialog',{name:'Compréhension',exact:true});await expect(panel).toBeVisible();
 await expect(panel.getByText('Version 1', {exact:false})).toHaveCount(0);await expect(panel.locator('.context-recap')).toContainText('Ce contexte rassemble');await expect(panel.locator('.context-recap')).not.toContainText('Préparer le projet.');
 await expect(panel.locator('blockquote')).not.toBeVisible();await expect(panel.getByText('Consulter les sources',{exact:true})).toHaveCount(0);
 if(width<850)await panel.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const traceSettings=page.getByRole('dialog',{name:'Paramètres du Space',exact:true});
 await traceSettings.getByText('Sources et traçabilité',{exact:true}).click();await expect(traceSettings.locator('blockquote')).toContainText('Préparer le projet.');
 await traceSettings.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 if(width<850)await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 await expect(page.getByRole('button',{name:'Agrandir',exact:true})).toHaveCount(0);
 if(width>850){const box=await panel.boundingBox(),workspace=await page.locator('.context-space-workspace').boundingBox();expect(box!.width/workspace!.width).toBeGreaterThan(.35);expect(box!.width/workspace!.width).toBeLessThan(.41);}
 await panel.getByRole('button',{name:width>850?'Fermer':'Fermer la fenêtre',exact:true}).click();
 await expect(page.getByText('Compréhension mise à jour',{exact:true})).toBeVisible();
 await expect(page.getByRole('complementary',{name:'Compréhension'})).toHaveCount(0);
 await page.locator('input[type=file]').first().setInputFiles({name:'not-supported.pdf',mimeType:'application/pdf',buffer:Buffer.from('offline')});await expect(page.locator('.workspace-feedback').getByRole('alert')).toContainText('PDF corrompu');expect(inputs).toHaveLength(2);
 const portable={schema_version:'qh.context-space/1',logical_id:domain,name:'Import',version:1,consolidated_at:'2026-10-26T12:00:00Z',understanding:[{id:revision,text:'Préparer le projet.',primary_dimension:'objectives_intentions',certainty:'tentative',validation_state:'proposed',evidence:[{source_revision_id:domain,quote:'Préparer le projet.',turn_id:null}]}]};
 await page.locator('input[type=file]').nth(1).setInputFiles({name:'context.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(portable))});
 await expect(page.getByRole('status').filter({hasText:'Contexte importé'})).toBeVisible();expect(inputs[2].context).toEqual(portable);expect(consolidations).toBe(2);
 await expect(page.getByRole('button',{name:'Données envoyées',exact:true})).toHaveCount(0);
 await expect(page.getByText('En attente de mémorisation',{exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const settings=page.getByRole('dialog',{name:'Paramètres du Space'});await settings.getByText('Diagnostics IA (développement)',{exact:true}).click();
 await expect(settings.getByRole('button',{name:'Charger les diagnostics privés'})).toBeVisible();await settings.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 for(let i=0;i<3;i++){await field.fill('Proponimi una lista della spesa per fare un risotto '+i);await page.getByRole('button',{name:'Envoyer',exact:true}).click();await expect(page.locator('.workspace-message.assistant')).toHaveCount(i+1);}
 expect(sends).toBe(3);await expect(page.getByText('Appui non établi',{exact:true})).toHaveCount(0);
 await page.mouse.move(0,0);const send=page.getByRole('button',{name:'Envoyer',exact:true});expect(await send.evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgb(36, 36, 38)');
 const composer=await page.locator('.workspace-composer').boundingBox();expect(composer!.y+composer!.height).toBeLessThanOrEqual(1000);
 expect(await page.locator('.workspace-log').evaluate(e=>e.scrollHeight>e.clientHeight)).toBe(true);
 expect(await page.evaluate(()=>document.documentElement.scrollHeight-innerHeight)).toBeLessThanOrEqual(1);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
});

test('AI availability failures and accounting suspension are visible and can be refreshed without generation',async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005';
 let checks=0,posts=0;
 await page.route('**/api/**',async route=>{
  const p=new URL(route.request().url()).pathname.slice(4);
  if(route.request().method()==='POST'&&!p.endsWith('/open'))posts++;
  if(p==='/auth/me')return route.fulfill({json:{user_id:owner}});
  if(p==='/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Disponibilité IA',status:'active',created_at:'2026-10-27T00:00:00Z',updated_at:'2026-10-27T00:00:00Z'}});
  if(p.endsWith('/workspace'))return route.fulfill({json:{context_id:scope,state:'pending',pending_count:1,current:null,recap:null,understanding:[],intake:[]}});
  if(p.endsWith('/chat-sessions')){
   checks++;if(checks===1)return route.fulfill({status:503,json:{detail:'offline unavailable'}});
   const blocked=checks===2;
   return route.fulfill({json:{automatic:true,enabled:!blocked,accounting_blocked:blocked,plafond_reached:false,model:blocked?null:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:blocked?null:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.0'}});
  }
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 await page.getByRole('textbox',{name:'Ton message',exact:true}).fill('Un message à envoyer.');
 const send=page.getByRole('button',{name:'Envoyer',exact:true}),memory=page.getByRole('button',{name:'Mémoriser',exact:true});
 await expect(page.getByText('La disponibilité de l’IA n’a pas pu être vérifiée.',{exact:true})).toBeVisible();
 await expect(send).toBeDisabled();await expect(memory).toBeDisabled();
 await page.getByRole('button',{name:'Actualiser la disponibilité',exact:true}).click();
 await expect(page.getByText('L’IA est suspendue après une erreur du fournisseur. Tes messages sont conservés.',{exact:true})).toBeVisible();
 await expect(send).toBeDisabled();await expect(memory).toBeDisabled();
 await page.getByRole('button',{name:'Actualiser la disponibilité',exact:true}).click();
 await expect(send).toBeEnabled();await expect(memory).toBeEnabled();expect(posts).toBe(0);
});
