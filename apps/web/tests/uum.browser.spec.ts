import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
import {DIMENSIONS} from '../src/uum';
test.use({actionTimeout:15000});
const enabled=process.env.QH_UUM_BROWSER_TEST==='1';
const fixture=JSON.parse(process.env.QH12_EXPECTED_JSON??'{}');
async function login(page:Page,user='alice'){
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 const input=page.locator('#username'),home=page.getByRole('heading',{name:'Mon environnement',exact:true});await expect(input.or(home)).toBeVisible();if(await input.isVisible()){await input.fill(user);await page.locator('#password').fill(process.env[user==='alice'?'QH_ALICE_PASSWORD':'QH_BOB_PASSWORD']!);await page.locator('#kc-login').click();}await expect(home).toBeVisible();
}
async function open(page:Page,id:string){await page.evaluate(s=>{history.pushState(null,'','/context-spaces/'+s);dispatchEvent(new PopStateEvent('popstate'));},id);await expect(page.getByLabel('Votre question sur ce contexte')).toBeVisible();}
if(enabled)test('QH-51 UUM: five clean Spaces, six universal nodes, exact members, primary review, refresh and isolation',async({page},info)=>{
 test.setTimeout(180000);await page.setViewportSize({width:1672,height:941});await login(page);
 for(const s of fixture.demo_spaces){
  await open(page,s.scope);await expect(page.locator('.context-orbit-node')).toHaveCount(6);
  expect(await page.locator('.context-orbit-node strong').allTextContents()).toEqual(DIMENSIONS.map(([,label])=>label));
  for(const node of await page.locator('.context-orbit-node').all())await expect(node).toContainText('Éléments proposés');
  const objective=page.locator('.context-orbit-node').filter({hasText:'Objectifs & intentions'});
  await objective.click();const w=page.getByRole('dialog',{name:'Compréhension du contexte',exact:true});await expect(w).toBeVisible();
  await expect(w.locator('.context-item-list li')).toHaveCount(1);await w.locator('.context-item-list li button').click();await expect(w.locator('.context-literal')).toHaveText(s.objective);
  await w.getByRole('button',{name:'Voir la source',exact:true}).click();await expect(w.locator('blockquote').first()).toHaveText(s.objective);await w.getByRole('navigation',{name:'Vues de la compréhension'}).getByRole('button',{name:'Éléments',exact:true}).click();
  await w.getByRole('button',{name:'Examiner la dimension',exact:true}).click();await w.getByRole('combobox',{name:'Décision sur la dimension',exact:true}).selectOption('accepted');await w.getByRole('button',{name:'Enregistrer la dimension',exact:true}).click();await expect(w).toContainText('affectation acceptée');
  await expect(w.locator('.context-item-detail .item-state')).toHaveText('À vérifier');await w.getByRole('button',{name:'Revenir aux éléments',exact:true}).click();
 }
 await open(page,fixture.demo_spaces[0].scope);await page.screenshot({path:info.outputPath('uum-map-desktop.png')});
 await page.setViewportSize({width:390,height:844});await expect(page.locator('.context-orbit-node')).toHaveCount(6);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);await page.screenshot({path:info.outputPath('uum-map-mobile.png'),fullPage:true});
 await page.reload();await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('.context-orbit-node').filter({hasText:'Objectifs & intentions'})).toContainText('Éléments proposés');
 await page.getByRole('button',{name:'Se déconnecter',exact:true}).click();await page.waitForURL(/:8080.*logout/);await login(page,'bob');const denied=page.waitForResponse(r=>r.url().endsWith('/api/context-spaces/'+fixture.scope));await page.evaluate(s=>{history.pushState(null,'','/context-spaces/'+s);dispatchEvent(new PopStateEvent('popstate'));},fixture.scope);expect((await denied).status()).toBe(404);await expect(page.locator('.context-orbit-node')).toHaveCount(0);
});
if(enabled)test('QH-51 UUM: empty dimensions, literal stays unclassified and unavailable never means empty',async({page})=>{
 test.setTimeout(90000);await login(page);await open(page,fixture.empty_scope);
 await expect(page.locator('.context-orbit-node')).toHaveCount(6);await expect(page.locator('.context-orbit-node').first()).toContainText('Aucun élément dans cette vue');
 await page.getByRole('button',{name:'Ajouter un élément',exact:true}).first().click();const form=page.getByRole('dialog',{name:'Ajouter un élément',exact:true});await form.getByLabel('Votre information',{exact:true}).fill('Une information manuelle sans classification automatique.');const saved=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/enrichments'));await form.getByRole('button',{name:'Ajouter au contexte',exact:true}).click();expect((await saved).status()).toBe(200);await expect(form).toHaveCount(0);
 await expect(page.getByRole('button',{name:/Non classés/})).toContainText('éléments disponibles');await page.getByRole('button',{name:/Non classés/}).click();const w=page.getByRole('dialog',{name:'Compréhension du contexte',exact:true});await expect(w.locator('.context-item-list li')).toHaveCount(1);await w.getByRole('button',{name:'Revenir aux éléments',exact:true}).click();
 await page.route('**/understanding-presence?*',r=>r.fulfill({status:503,json:{detail:'unavailable'}}));await page.reload();await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('.context-orbit-node')).toHaveCount(6);await expect(page.locator('.context-orbit-node').first()).toContainText('Indisponible');await expect(page.locator('.space-context-map')).not.toContainText('Aucun élément dans cette vue');
});
