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
test('UX V2 two horizontal shelves, actual opening order, primary domain and owner editing',async({page},info)=>{
 await login(page);
 await expect(page.locator('.domain-orb')).toHaveCount(7);
 const shelf=page.getByRole('list',{name:'Carrousel Mes domaines'});
 expect(await shelf.evaluate(e=>getComputedStyle(e).overflowX)).toBe('auto');
 await expect(page.getByRole('button',{name:'Tous les domaines',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Non classés',exact:true}).click();
 await expect(page.getByRole('link',{name:'Projet pilote',exact:true})).toBeVisible();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath('qh50-environment-'+name+'.png'),fullPage:true});
 }
 await page.getByRole('link',{name:'Projet pilote',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await page.getByRole('link',{name:'Mon environnement',exact:true}).click();
 await expect(page.locator('.space-card').first().getByRole('link')).toHaveAccessibleName('Projet pilote');
 await page.getByLabel('Ordre des Spaces').selectOption('used');
 await expect(page.locator('.space-card').first().getByRole('link')).toHaveAccessibleName('Projet pilote');
 await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
 await page.getByLabel('Nom du Context Space').fill('Primary domain UX control');
 await expect(page.getByRole('button',{name:'Créer',exact:true})).toBeDisabled();
 await page.getByLabel('Domaine principal',{exact:true}).selectOption({label:'Loisirs & découvertes'});
 await page.getByRole('button',{name:'Créer',exact:true}).click();await expect(page.getByRole('status').filter({hasText:'Context Space créé'})).toBeVisible();
 await page.getByRole('button',{name:'Loisirs & découvertes',exact:true}).click();
 const card=page.locator('.space-card').filter({has:page.getByRole('link',{name:'Primary domain UX control',exact:true})});await expect(card).toBeVisible();
 await card.getByText('Domaines de ce Space',{exact:true}).click();
 await card.getByLabel('Travail & projets',{exact:true}).check();
 await expect(card.getByLabel('Domaine principal',{exact:true}).locator('option:checked')).toHaveText('Loisirs & découvertes');
 await page.getByRole('button',{name:'Travail & projets',exact:true}).click();await expect(card).toBeVisible();
 await page.getByRole('button',{name:'Tous les domaines',exact:true}).click();
 await page.getByRole('button',{name:'Organiser mes domaines'}).click();
 await page.getByLabel('Nom du domaine 1',{exact:true}).fill('Travail personnalisé');await page.getByRole('button',{name:'Enregistrer l’organisation'}).click();
 await expect(page.getByRole('button',{name:'Travail personnalisé',exact:true})).toBeVisible();
 // Restore only this synthetic owner's editable label so other regression expectations remain stable.
 await page.getByRole('button',{name:'Organiser mes domaines'}).click();await page.getByLabel('Nom du domaine 1',{exact:true}).fill('Travail & projets');await page.getByRole('button',{name:'Enregistrer l’organisation'}).click();
});
test('UX V2 chat follows latest, respects deliberate scroll, source drawer traps and returns focus',async({page},info)=>{
 await login(page,fixture.demo_spaces[0].scope);await page.getByLabel('Inclure explicitement les propositions non confirmées').check();
 const original=await ask(page,'Question de contrôle');await page.getByRole('button',{name:'Nouvelle discussion',exact:true}).click();
 await page.route('**/chat',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...original,answer:Array(12).fill('Texte long de contrôle de défilement, sans inférence ni nouvelle information.').join('\n\n')})}));
 const log=page.getByRole('log',{name:'Conversation temporaire'});
 await ask(page,'Première question');await ask(page,'Deuxième question');
 const second=page.getByRole('article',{name:'Échange 2',exact:true});
 await expect.poll(async()=>second.evaluate(e=>{const p=e.closest('.conversation-scroll')!;return Math.abs(e.getBoundingClientRect().top-p.getBoundingClientRect().top)<50;})).toBe(true);
 await log.evaluate(e=>{e.scrollTop=0;e.dispatchEvent(new Event('scroll'));});
 await ask(page,'Troisième question');await expect(page.getByRole('button',{name:'Voir la nouvelle réponse ↓'})).toBeVisible();
 expect(await log.evaluate(e=>e.scrollTop)).toBe(0);
 await page.getByRole('button',{name:'Voir la nouvelle réponse ↓'}).click();
 const source=page.getByRole('button',{name:'Voir les sources de la réponse 3',exact:true});await source.click();
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
 await login(page,fixture.review_scope);await expandUnderstanding(page);
 for(const action of ['confirm','reject','correct'] as const){
  await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();
  const cards=page.getByRole('region',{name:'Explorer les éléments'}).locator('.understanding-card');await expect(cards.first()).toBeVisible();await cards.first().click();
  const panel=page.getByRole('region',{name:'Révision par le propriétaire'});await expect(panel.getByRole('button',{name:'Examiner une confirmation'})).toBeVisible();
  const before=await page.locator('.human-revision').getAttribute('data-revision-id');
  const button=action==='confirm'?'Examiner une confirmation':action==='reject'?'Examiner un refus':'Proposer une correction';await panel.getByRole('button',{name:button,exact:true}).click();
  if(action==='correct')await panel.getByLabel('Texte corrigé').fill('Proposition humaine corrigée, toujours incertaine.');
  const result=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/review'));
  await panel.getByRole('button',{name:action==='confirm'?'Confirmer explicitement cet élément':action==='reject'?'Refuser explicitement cette proposition':'Enregistrer la correction comme proposition',exact:true}).click();
  const response=await result;expect(response.status()).toBe(200);const receipt=await response.json();expect(receipt.revision_id).not.toBe(before);
  const auth=response.request().headers()['authorization'];
  await expect.poll(async()=>{const r=await page.request.get('/api/context-spaces/'+fixture.review_scope+'/understanding?view=history&limit=1&revision_id='+receipt.revision_id,{headers:{Authorization:auth}});return r.status();}).toBe(200);
  const retry=page.getByRole('button',{name:'Réessayer la navigation',exact:true});if(await retry.count())await retry.click();
  await expect(page.locator('.human-revision')).toHaveAttribute('data-revision-id',receipt.revision_id);
  await expect(page.locator('.human-revision')).toContainText(action==='confirm'?'Confirmée actuellement':action==='reject'?'Révision rejetée':'Contribution humaine');
  if(action==='correct')await expect(page.locator('.human-revision')).toContainText('Proposition non confirmée');
  await expect(page.locator('.human-revision')).toContainText('version précédente est conservée');
  await page.screenshot({path:info.outputPath('qh50-review-'+action+'.png'),fullPage:true});
 }
});
