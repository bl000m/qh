import {closeUnderstanding} from './navigation.browser';
import {newDiscussion} from './navigation.browser';
import {includeProposals} from './navigation.browser';
import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
import {afterLogin,expandUnderstanding} from './navigation.browser';
const fixture=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
async function login(page:Page,scope?:string){
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page,scope);
}
async function ask(page:Page,question:string){
 await page.getByLabel('Votre question sur ce contexte').fill(question);
 const r=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/chat'));
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();return await (await r).json();
}
test('UX V2 hierarchical domains, real activity, origin navigation and owner editing',async({page,browser},info)=>{
 test.setTimeout(90000);await login(page);
 await expect(page.locator('.domain-orb')).toHaveCount(7);
 expect(await page.getByRole('list',{name:'Carrousel Mes domaines'}).evaluate(e=>getComputedStyle(e).overflowX)).toBe('auto');
 await expect(page.getByRole('button',{name:'Tous les domaines',exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Projet pilote',exact:true})).toBeVisible();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath('qh50-environment-'+name+'.png'),fullPage:true});}
 await page.getByRole('link',{name:'Projet pilote',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.getByRole('navigation',{name:'Fil d’Ariane'}).getByRole('link')).toHaveCount(1);
 const metadata=page.waitForResponse(r=>r.request().method()==='GET'&&new URL(r.url()).pathname==='/api/environment');
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();const activity=await (await metadata).json();
 await expect(page.locator('.space-card').first().getByRole('link')).toHaveAccessibleName('Projet pilote');
 const usedResponse=page.waitForResponse(r=>r.request().method()==='GET'&&r.url().includes('/environment/spaces?')&&new URL(r.url()).searchParams.get('sort')==='used');
 await page.getByLabel('Ordre des Spaces').selectOption('used');const ordered=await (await usedResponse).json();const counts=ordered.items.map((s:{id:string})=>activity.usage[s.id]?.open_count??0);expect(counts).toEqual([...counts].sort((a,b)=>b-a));
 await page.getByRole('link',{name:'Loisirs & découvertes',exact:true}).focus();await page.keyboard.press('Enter');
 const domainPath=new URL(page.url()).pathname;expect(domainPath).toMatch(/^\/domains\/[0-9a-f-]{36}$/);
 await expect(page.getByRole('heading',{level:1})).toHaveText('Loisirs & découvertes');await expect(page.getByRole('heading',{level:1})).toBeFocused();
 await expect(page.locator('.domain-orb')).toHaveCount(0);await expect(page.getByRole('heading',{name:'Reprendre mes Context Spaces'})).toHaveCount(0);
 await expect(page.getByText('Ce domaine est encore vide.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Créer mon premier Context Space',exact:true}).click();await page.getByLabel('Nom du Context Space').fill('Primary domain UX control');
 await expect(page.getByRole('combobox',{name:'Domaine principal',exact:true}).locator('option:checked')).toHaveText('Loisirs & découvertes');
 await page.getByRole('button',{name:'Créer',exact:true}).click();await expect(page.getByRole('status').filter({hasText:'Context Space créé'})).toBeVisible();
 const card=page.locator('.space-card').filter({has:page.getByRole('link',{name:'Primary domain UX control',exact:true})});await expect(card).toHaveCount(1);
 await card.getByRole('link',{name:'Primary domain UX control',exact:true}).click();await page.getByRole('button',{name:'Gérer les domaines de ce Space',exact:true}).click();const assignment=page.getByRole('dialog',{name:'Assigner à un domaine'});await assignment.getByLabel('Travail & projets',{exact:true}).check();await expect(assignment.getByRole('combobox',{name:'Domaine principal',exact:true}).locator('option:checked')).toHaveText('Loisirs & découvertes');await assignment.getByRole('button',{name:'Enregistrer les domaines',exact:true}).click();await expect(assignment).toHaveCount(0);await page.getByRole('link',{name:'Loisirs & découvertes',exact:true}).click();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});if(name==='desktop')expect((await card.boundingBox())!.width).toBeLessThan(400);await page.screenshot({path:info.outputPath('qh50-domain-'+name+'.png'),fullPage:true});}
 await card.getByRole('link',{name:'Primary domain UX control',exact:true}).click();
 await expect(page.getByRole('navigation',{name:'Fil d’Ariane'})).toContainText('Loisirs & découvertes');await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 const nestedPath=new URL(page.url()).pathname;
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh50-domain-space-'+name+'.png'),fullPage:true});}
 await page.getByRole('link',{name:'Loisirs & découvertes',exact:true}).click();await expect(page).toHaveURL('http://localhost:5173'+domainPath);
 await page.goBack();await expect(page).toHaveURL('http://localhost:5173'+nestedPath);await page.goForward();await expect(page).toHaveURL('http://localhost:5173'+domainPath);
 await page.reload();await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.getByRole('heading',{level:1})).toHaveText('Loisirs & découvertes');
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await page.getByRole('link',{name:'Travail & projets',exact:true}).click();
 await page.getByRole('link',{name:'Primary domain UX control',exact:true}).click();await expect(page.getByRole('navigation',{name:'Fil d’Ariane'})).toContainText('Travail & projets');
 await expect(page.getByRole('navigation',{name:'Fil d’Ariane'})).not.toContainText('Loisirs');
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await closeUnderstanding(page);await page.getByRole('link',{name:'Paramètres de mon environnement'}).click();
 await page.getByRole('button',{name:'Organiser mes domaines'}).click();await page.getByLabel('Nom du domaine 1',{exact:true}).fill('Travail personnalisé');await page.getByRole('button',{name:'Enregistrer l’organisation'}).click();
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await page.getByRole('link',{name:'Travail personnalisé',exact:true}).click();await expect(page.getByRole('heading',{level:1})).toHaveText('Travail personnalisé');
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await closeUnderstanding(page);await page.getByRole('link',{name:'Paramètres de mon environnement'}).click();await page.getByRole('button',{name:'Organiser mes domaines'}).click();await page.getByLabel('Nom du domaine 1',{exact:true}).fill('Travail & projets');
 await page.getByLabel('Nouveau domaine',{exact:true}).fill('Domaine privé de contrôle');await page.getByRole('button',{name:'Ajouter le domaine',exact:true}).click();await page.getByRole('button',{name:'Enregistrer l’organisation'}).click();
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();const privatePath=await page.getByRole('link',{name:'Domaine privé de contrôle',exact:true}).getAttribute('href');
 const context=await browser.newContext({baseURL:'http://localhost:5173'});const bob=await context.newPage();try{await bob.goto(privatePath!);await bob.getByRole('button',{name:'Se connecter',exact:true}).click();await bob.locator('#username').fill('bob');await bob.locator('#password').fill(process.env.QH_BOB_PASSWORD!);await bob.locator('#kc-login').click();await expect(bob.getByRole('alert')).toHaveText('Ce domaine est introuvable ou inaccessible.');await expect(bob.getByText('Domaine privé de contrôle',{exact:true})).toHaveCount(0);await bob.evaluate(p=>{history.pushState(null,'',p);dispatchEvent(new PopStateEvent('popstate'));},nestedPath);await expect(bob.getByRole('alert')).toHaveText('Ce Context Space est introuvable ou inaccessible.');await expect(bob.getByText('Primary domain UX control',{exact:true})).toHaveCount(0);}finally{await context.close();}
 await closeUnderstanding(page);await page.getByRole('link',{name:'Paramètres de mon environnement'}).click();await page.getByRole('button',{name:'Organiser mes domaines'}).click();await page.getByRole('link',{name:'Non classés',exact:true}).click();await expect(page.getByRole('link',{name:'Projet pilote',exact:true})).toBeVisible();await expect(page.getByRole('link',{name:'Primary domain UX control',exact:true})).toHaveCount(0);
 await closeUnderstanding(page);await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await closeUnderstanding(page);await page.getByRole('link',{name:'Paramètres de mon environnement'}).click();await page.getByRole('button',{name:'Organiser mes domaines'}).click();await page.getByRole('button',{name:'Retirer le domaine 8',exact:true}).click();await page.getByRole('button',{name:'Enregistrer l’organisation'}).click();
 await page.evaluate(p=>{history.pushState(null,'',p);dispatchEvent(new PopStateEvent('popstate'));},privatePath!);await expect(page.getByRole('alert')).toHaveText('Ce domaine est introuvable ou inaccessible.');
});
test('UX V2 chat follows latest, respects deliberate scroll, source drawer traps and returns focus',async({page},info)=>{
 await login(page,fixture.demo_spaces[0].scope);await includeProposals(page);
 const original=await ask(page,'Question de contrôle');await newDiscussion(page);
 await page.route('**/chat',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...original,answer:Array(12).fill('Texte long de contrôle de défilement, sans inférence ni nouvelle information.').join('\n\n')})}));
 const log=page.getByRole('log',{name:'Conversation temporaire'});
 await ask(page,'Première question');await ask(page,'Deuxième question');
 const second=page.getByRole('article',{name:'Échange 2',exact:true});
 await expect.poll(async()=>second.evaluate(e=>{const p=e.closest('.conversation-scroll')!;return Math.abs(e.getBoundingClientRect().top-p.getBoundingClientRect().top)<50;})).toBe(true);
 await log.evaluate(e=>{e.scrollTop=0;e.dispatchEvent(new Event('scroll'));});
 await ask(page,'Troisième question');await expect(page.getByRole('button',{name:'Voir la nouvelle réponse ↓'})).toBeVisible();
 expect(await log.evaluate(e=>e.scrollTop)).toBe(0);
 await page.getByRole('button',{name:'Voir la nouvelle réponse ↓'}).click();
 const source=page.getByRole('button',{name:'Sources de la réponse 3',exact:true});await source.click();
 const drawer=page.getByRole('dialog',{name:'Sources & compréhension'});await expect(drawer).toBeVisible();
 await expect(drawer.getByRole('button',{name:'Fermer les sources'})).toBeFocused();await page.keyboard.press('Shift+Tab');expect(await page.evaluate(()=>document.activeElement?.closest('dialog')!==null)).toBe(true);
 await expect(drawer.getByRole('heading',{name:'Ce que cette réponse cite'})).toBeVisible();
 await expect(drawer.locator('blockquote').first()).toBeVisible();
 expect(await drawer.locator('.technical-details[open]').count()).toBe(0);
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh50-sources-'+name+'.png'),fullPage:true});}
 await page.keyboard.press('Escape');await expect(drawer).toHaveCount(0);await expect(source).toBeFocused();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh50-chat-'+name+'.png'),fullPage:true});}
 await page.setViewportSize({width:320,height:812});await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('UX V2 isolated owner review confirms, rejects and corrects without rewriting history',async({page},info)=>{
 test.setTimeout(90000); // Three real review/publication cycles with both canonical views mounted.
 await login(page,fixture.review_scope);await expandUnderstanding(page);
 for(const action of ['confirm','reject','correct'] as const){
  await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();
  const cards=page.getByRole('region',{name:'Explorer les éléments'}).locator('.understanding-card');await expect(cards.first()).toBeVisible();await cards.first().click();
  const panel=page.locator('.workspace-advanced').getByRole('region',{name:'Révision par le propriétaire'});await expect(panel.getByRole('button',{name:'Examiner une confirmation'})).toBeVisible();
  const before=await page.locator('.human-revision').getAttribute('data-revision-id');
  const button=action==='confirm'?'Examiner une confirmation':action==='reject'?'Examiner un refus':'Proposer une correction';await panel.getByRole('button',{name:button,exact:true}).click();
  if(action==='correct')await panel.getByLabel('Texte corrigé').fill('Proposition humaine corrigée, toujours incertaine.');
  const result=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/review'));
  await panel.getByRole('button',{name:action==='confirm'?'Confirmer explicitement cet élément':action==='reject'?'Refuser explicitement cette proposition':'Enregistrer la correction comme proposition',exact:true}).click();
  const response=await result;expect(response.status()).toBe(200);const receipt=await response.json();expect(receipt.revision_id).not.toBe(before);
  const auth=response.request().headers()['authorization'];
  await expect.poll(async()=>{const r=await page.request.get('/api/context-spaces/'+fixture.review_scope+'/understanding?view=history&limit=1&revision_id='+receipt.revision_id,{headers:{Authorization:auth}});return r.status();}).toBe(200);
  const retry=page.locator('.workspace-advanced').getByRole('button',{name:'Réessayer la navigation',exact:true});if(await retry.count())await retry.click();
  await expect(page.locator('.human-revision')).toHaveAttribute('data-revision-id',receipt.revision_id);
  await expect(page.locator('.human-revision')).toContainText(action==='confirm'?'Confirmée actuellement':action==='reject'?'Révision rejetée':'Contribution humaine');
  if(action==='correct')await expect(page.locator('.human-revision')).toContainText('Proposition non confirmée');
  await expect(page.locator('.human-revision')).toContainText('version précédente est conservée');
  await page.screenshot({path:info.outputPath('qh50-review-'+action+'.png'),fullPage:true});
 }
});
