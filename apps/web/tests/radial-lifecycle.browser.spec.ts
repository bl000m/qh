import {test,expect} from '@playwright/test';
import type {Page,TestInfo} from '@playwright/test';
import {writeFileSync} from 'node:fs';
const enabled=process.env.QH_DEVELOPMENT_AI_BROWSER_TEST==='1';
test.use({actionTimeout:15000});
test.setTimeout(180000);
async function login(page:Page){await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();}
async function create(page:Page,name:string){await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();await page.getByLabel('Nom du Context Space',{exact:true}).fill(name);await page.getByLabel('Domaine principal',{exact:true}).selectOption({index:1});await page.getByRole('button',{name:'Créer',exact:true}).click();await page.getByRole('link',{name:'Ouvrir ce Space',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();return new URL(page.url()).pathname.split('/').at(-1)!;}
async function boxes(page:Page,info:TestInfo,name:string){
 await page.evaluate(()=>document.fonts.ready);
 const value=await page.evaluate(()=>{
  const keys=['.space-context-map','.context-center',...Array.from({length:6},(_,i)=>'.orbit-node-'+i),'.assistant-card','.product-composer'];
  const boxes=keys.map(k=>{const r=document.querySelector(k)!.getBoundingClientRect();return {key:k,x:r.x,y:r.y+scrollY,w:r.width,h:r.height};});
  const nodes=boxes.slice(2,8),orb=boxes[1],map=boxes[0];const errors:string[]=[];
  const overlap=(a:typeof map,b:typeof map)=>Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>1&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>1;
  nodes.forEach((a,i)=>{if(overlap(a,orb))errors.push('orb collision');for(const b of nodes.slice(i+1))if(overlap(a,b))errors.push('node collision');if(a.x<map.x||a.x+a.w>map.x+map.w+1||a.y<map.y||a.y+a.h>map.y+map.h+1)errors.push('node outside map');});
  if(document.documentElement.scrollWidth>innerWidth+1)errors.push('horizontal overflow');return {boxes,errors};
 });
 expect(value.errors).toEqual([]);writeFileSync(info.outputPath(name+'.json'),JSON.stringify(value,null,2));return value.boxes;
}
if(enabled)for(const width of [1600,1200,768,375,320])test('QH-51 radial lifecycle: '+width+'px same Space, first item, QH46, views and no remount',async({page},info)=>{
 test.setTimeout(180000);await page.setViewportSize({width,height:width===1600?956:1160});await login(page);await create(page,'Cycle radial '+width);
 const question=page.getByLabel('Votre question sur ce contexte');await expect(page.locator('.assistant-model')).toContainText('Disponible');
 await question.fill('Brouillon conservé pendant la révision');
 await page.evaluate(()=>{(window as any).originalNodes=[document.querySelector('.assistant-card'),document.querySelector('#chat-question'),document.querySelector('.context-center')];});
 await expect(page.locator('.orbit-node-state')).toHaveText(Array(6).fill('Aucun élément dans cette vue'));
 const before=await boxes(page,info,'01-empty');await page.screenshot({path:info.outputPath('01-empty.png'),fullPage:width!==1600});
 await page.getByRole('button',{name:'Ajouter un élément',exact:true}).click();const form=page.getByRole('dialog',{name:'Ajouter un élément',exact:true});await form.getByLabel('Votre information',{exact:true}).fill('Je veux garder une heure pour mon projet.');await form.getByRole('button',{name:'Ajouter au contexte',exact:true}).click();await expect(form).toHaveCount(0);await expect(page.locator('.orbit-node-state').first()).not.toHaveText('Chargement…');
 const after=await boxes(page,info,'02-first-item');expect(after).toEqual(before);await page.screenshot({path:info.outputPath('02-first-item.png'),fullPage:width!==1600});
 // Literal input is never classified by a keyword heuristic. Explicit QH46 assigns it.
 await expect(page.locator('.orbit-node-state')).toHaveText(Array(6).fill('Aucun élément dans cette vue'));
 if(width<=650)await page.getByLabel('Options de la carte',{exact:true}).click();
 await page.getByRole('button',{name:/Non classés/}).filter({visible:true}).click();const workspace=page.getByRole('dialog',{name:'Compréhension du contexte',exact:true});await expect(workspace.locator('.context-literal')).toContainText('une heure pour mon projet');
 await workspace.getByRole('button',{name:'Examiner la dimension',exact:true}).click();await workspace.getByRole('combobox',{name:'Dimension proposée',exact:true}).selectOption('objectives_intentions');await workspace.getByRole('button',{name:'Enregistrer la dimension',exact:true}).click();await expect(workspace).toContainText('Objectifs & intentions');await workspace.getByRole('button',{name:'Revenir aux éléments',exact:true}).click();await page.getByRole('tab',{name:'Discussion',exact:true}).click();
 await expect(page.locator('.orbit-node-1')).toContainText('Éléments proposés');expect(await boxes(page,info,'03-classified')).toEqual(before);
 await page.getByRole('button',{name:'Compréhension courante',exact:true}).click();await expect(page.locator('.orbit-node-state')).toHaveText(Array(6).fill('Aucun élément dans cette vue'));expect(await boxes(page,info,'04-current-empty')).toEqual(before);
 await page.getByRole('button',{name:'Propositions',exact:true}).click();await expect(page.locator('.orbit-node-1')).toContainText('Éléments proposés');expect(await boxes(page,info,'05-proposed')).toEqual(before);
 await expect(question).toHaveValue('Brouillon conservé pendant la révision');await question.focus();await expect(question).toBeFocused();expect(await page.evaluate(()=>(window as any).originalNodes.every((n:Element,i:number)=>n===document.querySelector(['.assistant-card','#chat-question','.context-center'][i])))).toBe(true);
 await page.screenshot({path:info.outputPath('05-classified.png'),fullPage:width!==1600});
 if(width===1600){
  await page.locator('.orbit-node-1').click();const w=page.getByRole('dialog',{name:'Compréhension du contexte',exact:true});const advanced=w.locator('.workspace-advanced');await advanced.locator(':scope>summary').click();await advanced.getByRole('button',{name:'Examiner les propositions en attente',exact:true}).click();await advanced.locator('.understanding-card').first().click();await advanced.getByRole('button',{name:'Examiner une confirmation',exact:true}).click();await advanced.getByRole('button',{name:'Confirmer explicitement cet élément',exact:true}).click();await expect(advanced).toContainText('Cette version est actuellement confirmée.');await w.getByRole('button',{name:'Revenir aux éléments',exact:true}).click();await page.getByRole('tab',{name:'Discussion',exact:true}).click();await page.getByRole('button',{name:'Compréhension courante',exact:true}).click();await expect(page.locator('.orbit-node-1')).toContainText('Éléments conservés',{timeout:30000});expect(await boxes(page,info,'06-confirmed')).toEqual(before);await page.screenshot({path:info.outputPath('06-confirmed.png'),fullPage:width!==1600});
 }

});
if(enabled)test('QH-51 ordinary AI: login, new Spaces, send and UUM proposal have no provider popup; global ceiling blocks',async({page},info)=>{
 test.setTimeout(180000);await page.setViewportSize({width:1600,height:956});await login(page);const first=await create(page,'IA ordinaire A');let paidRequests=0,legacy=0;page.on('request',r=>{if(r.method()==='POST'&&/\/ai\/(messages|proposals)$/.test(r.url()))paidRequests++;if(/chat-sessions\/(preview|activation|[^/]+\/consent)/.test(r.url()))legacy++;});
 await expect(page.locator('.assistant-model')).toContainText('Disponible');await page.getByLabel('Votre question sur ce contexte').fill('Comment préciser mon objectif ?');const firstResponse=page.waitForResponse(r=>r.url().endsWith('/ai/messages')&&r.request().method()==='POST');const ordinaryBefore=await boxes(page,info,'ordinary-before');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();await expect(page.getByRole('dialog')).toHaveCount(0);expect(paidRequests).toBe(1);expect(legacy).toBe(0);expect(await boxes(page,info,'ordinary-reply')).toEqual(ordinaryBefore);
 const sent=await firstResponse;const firstAnswer=await sent.json();expect(firstAnswer.support_basis).toBe('dialogue');expect(firstAnswer.references).toEqual([]);expect(firstAnswer.provided_revisions).toEqual([]);await expect(page.locator('[data-support-basis="dialogue"]')).toContainText('Conversation envoyée');await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('ne sont pas des connaissances confirmées');const empty=await page.request.get('/api/context-spaces/'+first+'/understanding?view=history&limit=20',{headers:{Authorization:sent.request().headers()['authorization']}});expect(empty.status()).toBe(200);expect((await empty.json()).items).toEqual([]);
 await page.getByRole('button',{name:'Mémoriser cette conversation',exact:false}).click();const memory=page.getByRole('dialog',{name:'Mémoriser cette conversation',exact:true});await memory.getByLabel('Proposer aussi une compréhension sémantique',{exact:false}).check();await memory.getByLabel('J’autorise la conservation',{exact:false}).check();await memory.getByRole('button',{name:'Proposer avec Mistral',exact:true}).click();await expect(memory).toHaveCount(0);expect(paidRequests).toBe(2);expect(legacy).toBe(0);await expect(page.locator('.orbit-node-1')).toContainText('Éléments proposés');
 expect(await boxes(page,info,'ordinary-proposed')).toEqual(ordinaryBefore);await page.screenshot({path:info.outputPath('ordinary-ai-proposed.png'),fullPage:true});
 await page.getByRole('tab',{name:'Modèles',exact:true}).click();
 const diagnostics=page.getByRole('region',{name:'Diagnostics IA privés',exact:true});
 await diagnostics.getByRole('button',{name:'Charger les diagnostics privés',exact:true}).click();
 await expect(diagnostics.locator(':scope > details')).toHaveCount(2);
 const diagnostic=diagnostics.locator(':scope > details').last();await diagnostic.locator(':scope > summary').click();
 await expect(diagnostic).toContainText('accepted');await expect(diagnostic).toContainText('chat.support_basis_matches_transmitted_inputs');
 await diagnostic.getByText('JSON original Mistral',{exact:true}).click();await expect(diagnostic.locator('pre').last()).toContainText('mistral-small-2603');
 await diagnostic.getByRole('button',{name:'Supprimer ce diagnostic',exact:true}).click();await expect(diagnostics.locator(':scope > details')).toHaveCount(1);
 expect(paidRequests).toBe(2);await page.getByRole('tab',{name:'Discussion',exact:true}).click();
 await page.getByRole('link',{name:'QH — accueil',exact:true}).click();const second=await create(page,'IA ordinaire B');expect(second).not.toBe(first);await expect(page.locator('.assistant-model')).toContainText('Disponible');await page.getByLabel('Votre question sur ce contexte').fill('Une autre question.');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();expect(paidRequests).toBe(3);expect(legacy).toBe(0);await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.route('**/ai/messages',r=>r.fulfill({status:402,json:{detail:'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.'}}));await page.getByLabel('Votre question sur ce contexte').fill('Requête bloquée simulée');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.getByRole('alert')).toHaveText('Plafond IA atteint. Aucune nouvelle requête ne sera facturée.');await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();await expect(page.getByLabel('Votre question sur ce contexte')).toHaveValue('Requête bloquée simulée');await expect(page.getByRole('dialog')).toHaveCount(0);expect(legacy).toBe(0);
});
