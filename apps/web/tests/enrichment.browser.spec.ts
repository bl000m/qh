import {writeFile} from 'node:fs/promises';
import {test,expect} from '@playwright/test';
import {afterLogin} from './navigation.browser';
const fixture=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');

test('QH-39 browser selected conversation persists, reopens, reviews and denies Bob',async({page,browser},info)=>{
 test.setTimeout(90000);
 let aliceToken='';page.on('request',r=>{if(r.url().endsWith('/auth/me'))aliceToken=r.headers()['authorization']||'';});
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page);
 await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
 const name='QH39 isolated living context';await page.getByLabel('Nom du Context Space',{exact:true}).fill(name);await page.getByLabel('Domaine principal',{exact:true}).selectOption({index:1});
 const creation=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/environment/spaces'));
 await page.getByRole('button',{name:'Créer',exact:true}).click();const created=await (await creation).json();
 await page.getByRole('link',{name:'Ouvrir ce Space',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.getByRole('button',{name:'Enrichir ce contexte',exact:true})).toBeDisabled();
 const claim='Nous proposons un pilote réversible avec Jo, sans commande approuvée. 🌱';
 await page.getByLabel('Votre question sur ce contexte').fill(claim);await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Enrichir ce contexte',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Enrichir ce contexte',exact:true});
 await expect(dialog).toContainText('Aucune analyse sémantique ni inférence Mistral');
 const selections=dialog.locator('.enrichment-turn input');await expect(selections.nth(0)).toBeChecked();await expect(selections.nth(1)).not.toBeChecked();
 await expect(dialog.getByRole('button',{name:'Conserver et proposer',exact:true})).toBeDisabled();
 await dialog.getByRole('checkbox',{name:'J’autorise la conservation',exact:false}).check();
 await page.screenshot({path:info.outputPath('qh39-selected-source-desktop.png'),fullPage:true});
 const published=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/enrichments'));
 await dialog.getByRole('button',{name:'Conserver et proposer',exact:true}).click();const response=await published;expect(response.status()).toBe(200);const receipt=await response.json();
 expect(receipt.revision_ids).toHaveLength(1);await expect(page.getByText('1 nouvelle proposition à vérifier.',{exact:false})).toBeVisible();
 // Exact same browser submission replay is durable, not a second model invocation.
 await expect.poll(async()=>{const r=await page.request.get('/api/context-spaces/'+created.id+'/understanding?view=proposed&limit=20',{headers:{Authorization:aliceToken}});return r.status();}).toBe(200);
 const payload=response.request().postDataJSON();
 await page.getByRole('button',{name:'Enrichir ce contexte',exact:true}).click();
 await expect(dialog.locator('.enrichment-turn input').nth(0)).not.toBeChecked();
 await expect(dialog).toContainText('Déjà conservé dans une source sélectionnée');
 await dialog.locator('.enrichment-turn input').nth(0).check();await dialog.getByRole('checkbox',{name:'J’autorise la conservation',exact:false}).check();
 const repeated=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/enrichments'));
 await dialog.getByRole('button',{name:'Conserver et proposer',exact:true}).click();const replay=await repeated;
 expect(replay.status()).toBe(200);expect((await replay.json()).revision_ids).toEqual(receipt.revision_ids);expect(replay.request().postDataJSON().operation_id).toBe(payload.operation_id);
 await writeFile(info.outputPath('qh39-canonical-receipt.json'),JSON.stringify({scope:created.id,proposed_receipt:receipt,source_text:claim,replay_same_ids:true,provider:'offline-literal/1',paid_calls:0},null,2));
 await page.getByRole('button',{name:'Examiner la proposition 1',exact:true}).click();
 await expect(page.locator('.human-revision[data-revision-id="'+receipt.revision_ids[0]+'"]')).toBeVisible();
 await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText(claim);
 await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText('Proposé');
 await page.screenshot({path:info.outputPath('qh39-proposed-with-source-desktop.png'),fullPage:true});
 await page.locator('details.understanding-explorer > summary').click();await expect(page.locator('.human-revision')).not.toBeVisible();
 await page.getByRole('button',{name:'Examiner la proposition 1',exact:true}).click();await expect(page.locator('.human-revision[data-revision-id="'+receipt.revision_ids[0]+'"]')).toBeVisible();
 // Fresh page + actual OIDC reauthentication: ephemeral conversation is gone,
 // canonical proposal and original source remain retrievable through the product.
 await page.reload();await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 if(await page.locator('#username').isVisible()){await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();}
 await afterLogin(page,created.id);await expect(page.getByRole('log',{includeHidden:true})).toBeEmpty();
 await page.locator('details.understanding-explorer > summary').click();await page.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();
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
 const review=page.getByRole('region',{name:'Révision par le propriétaire'});await review.getByRole('button',{name:'Examiner une confirmation',exact:true}).click();
 await review.getByRole('button',{name:'Confirmer explicitement cet élément',exact:true}).click();await expect(page.getByRole('region',{name:'Détail de l’élément'})).toContainText('Confirmé courant');expect(detailReads).toBeGreaterThanOrEqual(3);expect(detailReads).toBeLessThanOrEqual(4);expect(reviewWrites).toBe(1);
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Sources & compréhension',exact:true}).click();
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
