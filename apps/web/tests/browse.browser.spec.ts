import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
async function open(page:Page){await page.goto('/context-spaces/'+expected.scope);await page.getByRole('button',{name:'Se connecter',exact:true}).click();await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await expect(page.getByRole('heading',{name:'Démo QH-8',exact:true})).toBeVisible();}
const browseUrl=(r:any)=>r.url().includes('/understanding?');
test('opens without search, separates current/proposed, and browses every retained revision',async({page},info)=>{
 let searches=0;page.on('request',r=>{if(r.url().endsWith('/context-spaces/query'))searches++;});await open(page);
 const overview=page.getByRole('region',{name:'Vue d’ensemble'});
 await expect(overview.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
 await expect(overview.getByRole('region',{name:'Compréhension confirmée courante'}).getByRole('button').first()).toContainText('Confirmé courant');
 await expect(overview.getByRole('region',{name:'Propositions à examiner'}).getByRole('button').first()).toContainText('Proposé · non confirmé');
 expect(searches).toBe(0);await expect(page.getByLabel('Texte à rechercher')).not.toBeVisible();
 await overview.getByRole('button',{name:'Consulter l’historique complet'}).click();
 const explorer=page.getByRole('region',{name:'Explorer les éléments'});
 await explorer.getByLabel('Éléments par page').selectOption('5');
 await expect(explorer.locator('.understanding-card')).toHaveCount(5);
 await expect(explorer.getByText('Regroupements locaux',{exact:false})).toBeVisible();
 while(await explorer.getByRole('button',{name:'Afficher les éléments suivants'}).count()){
  const before=await explorer.locator('.understanding-card').count();const response=page.waitForResponse(browseUrl);await explorer.getByRole('button',{name:'Afficher les éléments suivants'}).click();expect((await response).status()).toBe(200);await expect(explorer.locator('.understanding-card')).toHaveCount(Math.min(before+5,expected.all_ids.length));
 }
 await expect(explorer.locator('.understanding-card')).toHaveCount(expected.all_ids.length);expect(searches).toBe(0);
 await page.screenshot({path:info.outputPath('qh12-browse-history.png'),fullPage:true});
});
test('dynamic exact descriptors, unclassified entities, relation anchors and item history',async({page},info)=>{
 await open(page);await page.getByRole('button',{name:'Explorer la compréhension',exact:true}).click();
 const e=page.getByRole('region',{name:'Explorer les éléments'});
 await e.getByRole('button',{name:'Propositions à examiner',exact:true}).click();
 await e.getByRole('button',{name:'reversible_pause',exact:true}).click();await expect(e.locator('.understanding-card')).toHaveCount(1);
 await e.getByRole('button',{name:'Entités canoniques'}).click();await expect(e.locator('.understanding-card').first()).toContainText('entity');
 await e.getByRole('button',{name:'Sans descripteur reconnu'}).click();await expect(e.locator('.understanding-card').first()).toBeVisible();
 await e.getByRole('button',{name:'Relations explicites'}).click();await e.locator('.understanding-card').first().click();
 const d=page.getByRole('region',{name:'Détail de l’élément'});await expect(d.getByRole('region',{name:'Relation'})).toContainText(expected.relation.predicate);
 await expect(d.locator('blockquote').first()).toBeVisible();await page.screenshot({path:info.outputPath('qh12-browse-detail.png'),fullPage:true});
 await d.getByRole('button',{name:'Voir la révision source'}).click();await expect(d.getByRole('article',{name:'Révision '+expected.relation.source_revision_id,exact:true})).toBeVisible();
 await d.getByText('Révisions de cet élément',{exact:true}).click();await expect(d.getByRole('region',{name:'Révisions de cet élément'}).locator('.understanding-card')).toHaveCount(expected.decision_ids.length);
 await page.getByRole('button',{name:'Vue d’ensemble',exact:true}).click();await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
});
test('late browse pages and failed pagination cannot leave stale results; mobile keyboard works',async({page})=>{
 await page.setViewportSize({width:375,height:812});await open(page);
 const go=page.getByRole('button',{name:'Explorer la compréhension',exact:true});await go.focus();await page.keyboard.press('Enter');
 const e=page.getByRole('region',{name:'Explorer les éléments'});await expect(e.locator('.understanding-card')).toHaveCount(1);
 await e.getByRole('button',{name:'Historique complet',exact:true}).click();await e.getByLabel('Éléments par page').selectOption('5');await expect(e.locator('.understanding-card')).toHaveCount(5);
 await page.route('**/understanding?*',async route=>{if(new URL(route.request().url()).searchParams.has('after_revision_id'))await route.fulfill({status:503,body:'private-diagnostic'});else await route.continue();});
 await e.getByRole('button',{name:'Afficher les éléments suivants'}).click();await expect(e.getByRole('alert')).toContainText('Ce résultat ne signifie pas que le Space est vide');await expect(e.locator('.understanding-card')).toHaveCount(0);await expect(page.locator('body')).not.toContainText('private-diagnostic');
 await page.unroute('**/understanding?*');
 let release:()=>void=()=>{};const gate=new Promise<void>(r=>{release=r;});let waiting=false;
 await page.route('**/understanding?*',async route=>{if(new URL(route.request().url()).searchParams.get('view')==='proposed'){waiting=true;await gate;}await route.continue();});
 await e.getByRole('button',{name:'Propositions à examiner',exact:true}).click();await expect.poll(()=>waiting).toBe(true);await expect(e.locator('.understanding-card')).toHaveCount(0);
 await e.getByRole('button',{name:'Compréhension confirmée courante',exact:true}).click();await expect(e.locator('.understanding-card')).toHaveCount(1);const delayed=page.waitForResponse(r=>browseUrl(r) && new URL(r.url()).searchParams.get('view')==='proposed');release();await(await delayed).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 await expect(e.locator('.understanding-card')).toHaveCount(1);await expect(e.locator('.understanding-card')).toContainText('Confirmé courant');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('truly empty, proposed-only and historical-only Spaces have distinct honest previews',async({page})=>{
 await open(page);
 for(const [scope,label] of [[expected.empty_scope,'empty'],[expected.proposed_scope,'proposed'],[expected.historical_scope,'history']]){
  // SPA navigation preserves the approved ephemeral session; no full page reload.
  await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);
  const o=page.getByRole('region',{name:'Vue d’ensemble'});
  await expect(o.getByText('Chargement de l’aperçu…')).toHaveCount(0);
  if(label==='empty')await expect(o.getByRole('status')).toHaveText('Ce Context Space ne contient pas encore d’éléments de compréhension.');
  else {
   await expect(o.getByText('Ce Context Space ne contient pas encore d’éléments de compréhension.')).toHaveCount(0);
   await expect(o.getByText('Aucune révision confirmée courante.',{exact:true})).toBeVisible();
   if(label==='proposed'){
    await expect(o.locator('.understanding-card')).toHaveCount(1);await o.getByRole('button',{name:'Explorer : Propositions à examiner',exact:true}).click();
    const e=page.getByRole('region',{name:'Explorer les éléments'});await e.getByRole('button',{name:'Previously unseen Ω',exact:true}).click();await expect(e.locator('.understanding-card')).toHaveCount(1);await expect(e.locator('.understanding-card')).toContainText('tentative');
   } else await expect(o.getByRole('button',{name:'Consulter l’historique complet'})).toBeVisible();
  }
 }
});
