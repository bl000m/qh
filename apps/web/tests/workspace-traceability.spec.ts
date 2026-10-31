import {test,expect} from '@playwright/test';
const scope='00000000-0000-0000-0000-000000000001',question='00000000-0000-0000-0000-000000000002',answer='00000000-0000-0000-0000-000000000003',version='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
const row={context_space_id:scope,item_id:revision,revision_id:revision,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:3,content:{text:'Objectif proposé.',extraction:{key:'qh-context-uum/3',input_sha256:'offline'},citations:[{source_revision_id:version,quote:'Un atelier à préparer.',start:0,end:21}]},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-28T00:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:version,source_revision_id:version,revision_no:1,origin:{}}]};

for(const width of [1366,375])test('content-focused understanding and settings-only sources '+width,async({page})=>{
 await page.setViewportSize({width,height:900});let sourceReads=0;
 await page.route('**/api/**',route=>{
  const url=new URL(route.request().url()),path=url.pathname;
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.0'}});
  if(path.endsWith('/workspace'))return route.fulfill({json:{context_id:scope,state:'current',pending_count:0,current:{id:version,context_space_id:scope,version:3,intake_ids:[question,answer],revision_ids:[revision],source_revision_id:version,created_at:row.created_at,has_recap:true},recap:{version_id:version,title:'Un atelier',text:'Un résumé lisible.',support_revision_ids:[revision]},understanding:[row],intake:[{id:question,kind:'message',role:'user',text:'Préparer quoi ?',name:null,context:null},{id:answer,kind:'message',role:'assistant',reply_to:question,text:'Préparons cet atelier.',name:null,context:null,attribution:{model:'mistral-small-2603',support_basis:'canonical',reference_ids:[revision],insufficient_context:true,partial_coverage:true}}]}});
  if(path.endsWith('/understanding')){
   sourceReads++;expect(url.searchParams.get('revision_id')).toBe(revision);expect(url.searchParams.get('view')).toBe('history');expect(path).toContain('/'+scope+'/');
   return route.fulfill({json:{view:'history',items:[row],next_after_revision_id:null}});
  }
  return route.fulfill({status:404,json:{detail:'offline only'}});
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 const conversation=page.getByRole('log');await expect(conversation).toContainText('Préparons cet atelier.');
 await expect(conversation.getByText('Sources du contexte',{exact:true})).toHaveCount(0);
 await expect(conversation).toContainText('Les informations disponibles ne suffisent pas');
 await expect(conversation).toContainText('Seule une partie de la compréhension');
 await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 const panel=width>850?page.getByRole('complementary',{name:'Compréhension',exact:true}):page.getByRole('dialog',{name:'Compréhension',exact:true});
 await expect(panel.getByRole('heading',{name:'Un atelier',exact:true})).toBeVisible();await expect(panel.locator('.context-recap')).toHaveText('Un résumé lisible.');
 await expect(panel).not.toContainText('Version 3');await expect(panel).toContainText('Mis à jour le');
 await expect(panel.getByText('Consulter les sources',{exact:true})).toHaveCount(0);
 await expect(panel).toContainText("Cette compréhension évolue avec tes échanges. Mémorise-les pour l'actualiser.");
 await expect(panel.getByRole('button',{name:'Exporter',exact:true})).toBeVisible();await expect(panel.getByRole('button',{name:'Régénérer',exact:true})).toBeEnabled();
 await panel.getByRole('button',{name:width>850?'Fermer':'Fermer la fenêtre',exact:true}).click();
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const settings=page.getByRole('dialog',{name:'Paramètres du Space',exact:true});
 await settings.getByText('Sources et traçabilité',{exact:true}).click();
 await expect(settings.getByText('Objectif proposé.',{exact:true})).toBeVisible();
 await expect(settings.locator('blockquote')).toHaveText('Un atelier à préparer.');
 await expect(settings).toContainText('Question : Préparer quoi ?');await expect(settings).toContainText('Préparons cet atelier.');
 expect(sourceReads).toBe(0);
 await settings.getByText('Sources du contexte',{exact:true}).click();
 await expect(settings.locator('blockquote')).toHaveCount(2);expect(sourceReads).toBe(1);
 await settings.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 await expect(conversation.getByText('Sources du contexte',{exact:true})).toHaveCount(0);
});

test('shared source passages appear once without losing distinct items or source identities',async({page})=>{
 const rows=Array.from({length:12},(_,i)=>({...row,item_id:crypto.randomUUID(),revision_id:crypto.randomUUID(),content:{...row.content,text:`Sens distinct ${i+1}.`}}));
 const otherSource='00000000-0000-0000-0000-000000000008';
 const separate={...rows[0],item_id:crypto.randomUUID(),revision_id:crypto.randomUUID(),provenance:[{...row.provenance[0],source_revision_id:otherSource}],content:{...row.content,text:'Une autre source indépendante.',citations:[{...row.content.citations[0],source_revision_id:otherSource}]}};
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:false,enabled:false,model:null}});
  if(path.endsWith('/workspace'))return route.fulfill({json:{context_id:scope,state:'current',pending_count:0,current:{id:version,context_space_id:scope,version:1,intake_ids:[],revision_ids:[...rows.map(r=>r.revision_id),separate.revision_id],source_revision_id:version,created_at:row.created_at,has_recap:true},recap:{version_id:version,title:'Synthèse partielle',text:'Un résumé.',support_revision_ids:[rows[0].revision_id]},understanding:[...rows,separate],intake:[]}});
  return route.fulfill({status:404,json:{detail:'offline only'}});
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const settings=page.getByRole('dialog',{name:'Paramètres du Space',exact:true});
 await settings.getByText('Sources et traçabilité',{exact:true}).click();
 const shared=settings.getByRole('region',{name:'Source 1',exact:true});
 await expect(shared.locator('blockquote')).toHaveCount(1);
 await expect(shared).toContainText('Éléments de compréhension liés (12)');
 for(let i=1;i<=12;i++)await expect(shared.getByText(`Sens distinct ${i}.`,{exact:true})).toBeVisible();
 await expect(shared.getByText('Proposé · passages 1',{exact:true})).toHaveCount(12);
 await shared.getByText('Référence précise',{exact:true}).click();
 await expect(shared).toContainText(`Source : ${version} · caractères 0–21`);
 await expect(settings.getByRole('region',{name:'Source 2',exact:true}).locator('blockquote')).toHaveText('Un atelier à préparer.');
 await expect(settings.getByText('Une autre source indépendante.',{exact:true})).toBeVisible();
});
