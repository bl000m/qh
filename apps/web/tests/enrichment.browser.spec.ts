import {expandUnderstanding} from './navigation.browser';
import {closeUnderstanding} from './navigation.browser';
import {writeFile} from 'node:fs/promises';
import {test,expect} from '@playwright/test';
import {afterLogin,showSupport} from './navigation.browser';
const fixture=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');

test('QH-39 literal API persistence/replay/review/isolation survives while memory UI refuses implicit literal fallback',async({page,browser},info)=>{
 test.setTimeout(90000);
 let aliceToken='';page.on('request',r=>{if(r.url().endsWith('/auth/me'))aliceToken=r.headers()['authorization']||'';});
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page);
 await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
 const name='QH39 isolated living context';await page.getByLabel('Nom du Context Space',{exact:true}).fill(name);await page.getByLabel('Domaine principal',{exact:true}).selectOption({index:1});
 const creation=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/environment/spaces'));
 await page.getByRole('button',{name:'Créer',exact:true}).click();const created=await (await creation).json();
 await page.getByRole('link',{name:'Ouvrir ce Space',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.getByRole('button',{name:'Mémoriser cette conversation',exact:false})).toBeDisabled();
 const claim='Nous proposons un pilote réversible avec Jo, sans commande approuvée. 🌱';
 await page.getByLabel('Votre question sur ce contexte').fill(claim);await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Mémoriser cette conversation',exact:false}).click();const dialog=page.getByRole('dialog',{name:'Mémoriser cette conversation',exact:false});
 await expect(dialog.getByRole('checkbox')).toHaveCount(0);await expect(dialog.getByRole('button',{name:'Continuer',exact:true})).toBeDisabled();await expect(dialog).toContainText('extraction sémantique est indisponible');await dialog.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 const payload={conversation_id:crypto.randomUUID(),operation_id:crypto.randomUUID(),turns:[{id:crypto.randomUUID(),role:'user',content:claim,captured_at:new Date().toISOString()}],persist_consent:true};
 const response=await page.request.post('/api/context-spaces/'+created.id+'/enrichments',{headers:{Authorization:aliceToken},data:payload});expect(response.status()).toBe(200);const receipt=await response.json();expect(receipt.revision_ids).toHaveLength(1);
 await expect.poll(async()=>{const r=await page.request.get('/api/context-spaces/'+created.id+'/understanding?view=proposed&limit=20',{headers:{Authorization:aliceToken}});return r.status();}).toBe(200);
 const replay=await page.request.post('/api/context-spaces/'+created.id+'/enrichments',{headers:{Authorization:aliceToken},data:payload});expect(replay.status()).toBe(200);expect((await replay.json()).revision_ids).toEqual(receipt.revision_ids);
 await writeFile(info.outputPath('qh39-canonical-receipt.json'),JSON.stringify({scope:created.id,proposed_receipt:receipt,source_text:claim,replay_same_ids:true,provider:receipt.provider_mode,paid_calls:0},null,2));
 await expandUnderstanding(page);await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();await page.locator('.understanding-card').filter({hasText:claim}).click();
 await expect(page.locator('.human-revision[data-revision-id="'+receipt.revision_ids[0]+'"]')).toBeVisible();
 await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText(claim);
 await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText('Proposé');
 await page.screenshot({path:info.outputPath('qh39-proposed-with-source-desktop.png'),fullPage:true});
 await closeUnderstanding(page);await expect(page.locator('.human-revision')).not.toBeVisible();await closeUnderstanding(page);await page.getByRole('tab',{name:'Discussion',exact:true}).click();
 await expandUnderstanding(page);await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();await page.locator('.understanding-card').filter({hasText:claim}).click();await expect(page.locator('.human-revision[data-revision-id="'+receipt.revision_ids[0]+'"]')).toBeVisible();
 // Fresh page + actual OIDC reauthentication: ephemeral conversation is gone,
 // canonical proposal and original source remain retrievable through the product.
 await page.reload();await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 if(await page.locator('#username').isVisible()){await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();}
 await afterLogin(page,created.id);await expect(page.getByRole('log',{includeHidden:true})).toBeEmpty();
 await expandUnderstanding(page);await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();
 const card=page.locator('.understanding-card').filter({hasText:claim});await expect(card).toBeVisible();await card.click();
 let detailReads=0,reviewWrites=0;
 page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/review'))reviewWrites++;});
 await page.route('**/understanding?*',route=>{
  const url=new URL(route.request().url()),revision=url.searchParams.get('revision_id');
  if(url.pathname.includes(created.id)&&revision&&revision!==receipt.revision_ids[0]){
   detailReads++;if(detailReads<=2)return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"projection pending"}'});
  }
  return route.continue();
 });
 const review=page.locator('.workspace-advanced').getByRole('region',{name:'Révision par le propriétaire'});await review.getByRole('button',{name:'Examiner une confirmation',exact:true}).click();
 await review.getByRole('button',{name:'Confirmer explicitement cet élément',exact:true}).click();await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText('Confirmé courant');expect(detailReads).toBeGreaterThanOrEqual(3);expect(detailReads).toBeLessThanOrEqual(4);expect(reviewWrites).toBe(1);
 await page.setViewportSize({width:390,height:844});await showSupport(page);
 await expect(page.locator('.human-revision')).toContainText(claim);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('qh39-confirmed-mobile.png'),fullPage:true});
 const session=await browser.newContext({baseURL:'http://localhost:5173'}),bob=await session.newPage();let bobToken='';bob.on('request',r=>{if(r.url().endsWith('/auth/me'))bobToken=r.headers()['authorization']||'';});
 try{
  await bob.goto('/');await bob.getByRole('button',{name:'Se connecter',exact:true}).click();await bob.locator('#username').fill('bob');await bob.locator('#password').fill(process.env.QH_BOB_PASSWORD!);await bob.locator('#kc-login').click();await afterLogin(bob);
  for(const id of [created.id,fixture.scope]){
   const denied=await bob.request.post('/api/context-spaces/'+id+'/enrichments',{headers:{Authorization:bobToken},data:payload});expect(denied.status()).toBe(404);
   const read=await bob.request.get('/api/context-spaces/'+id+'/understanding?view=history&limit=20',{headers:{Authorization:bobToken}});expect(read.status()).toBe(404);
  }
 }finally{await session.close();}
});
