import {newDiscussion} from './navigation.browser';
import {includeProposals} from './navigation.browser';
import {afterLogin,expandUnderstanding} from './navigation.browser';
import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
// React development warnings must fail regressions, not merely appear in CI logs.
const keyWarnings=new WeakMap<Page,string[]>();
test.beforeEach(async({page})=>{
 const messages:string[]=[];keyWarnings.set(page,messages);
 page.on('console',message=>{if(/same key|unique[\s\S]*key|Encountered two children/i.test(message.text()))messages.push(message.text());});
 page.on('pageerror',error=>{if(/same key|unique[\s\S]*key/i.test(error.message))messages.push(error.message);});
});
test.afterEach(async({page})=>{expect(keyWarnings.get(page)||[],'React key warnings').toEqual([]);});
async function open(page:Page,scope=expected.scope){
 await page.goto('/context-spaces/'+scope);await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page,scope);
 await expect(page.getByRole('tab',{name:'Discussion',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
}
async function ask(page:Page,question='Quelles décisions avons-nous prises pour ce projet ?'){
 await page.getByLabel('Votre question sur ce contexte').fill(question);
 const response=page.waitForResponse(r=>r.url().endsWith('/chat') && r.request().method()==='POST');
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 return response;
}
test('real scoped chat preserves current state, sources and temporary follow-up',async({page},info)=>{
 await open(page);
 const response=await ask(page);expect(response.status()).toBe(200);
 const data=await response.json();expect(data.model).toBe('qh-mock-extractive/1');
 expect(data.provided_revisions).toHaveLength(1);expect(data.provided_revisions[0].is_current_confirmed).toBe(true);
 expect(data.references[0].provenance[0].source_revision_id).toBe(expected.source_revision_id);
 const turn=page.getByRole('article',{name:'Échange 1',exact:true});await expect(turn).toContainText('Mode mock');
 await expect(turn.getByRole('note')).toHaveCount(0);
 await turn.getByRole('button',{name:'Sources de la réponse 1',exact:true}).click();
 const sources=page.getByRole('dialog',{name:'Sources & compréhension'});
 await expect(sources.locator('blockquote').first()).toBeVisible();
 await expect(sources.getByRole('region',{name:'Éléments cités dans cette réponse'}).locator('.human-revision[data-revision-id="'+data.references[0].revision_id+'"]')).toBeVisible();
 await sources.getByRole('button',{name:'Fermer les sources'}).click();
 const next=await ask(page,'Et que savons-nous encore ?');expect(next.status()).toBe(200);
 const body=next.request().postDataJSON();expect(body.messages.map((m:any)=>m.role)).toEqual(['user','assistant','user']);
 await expect(page.getByRole('article',{name:'Échange 2',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>Object.keys(localStorage).length)).toBe(0);
 await page.screenshot({path:info.outputPath('qh13-context-chat.png'),fullPage:true});
 await includeProposals(page);
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toHaveCount(0);
 const proposed=await ask(page);expect(proposed.request().postDataJSON().include_proposed).toBe(true);
 expect((await proposed.json()).provided_revisions.some((r:any)=>r.validation_state==='proposed')).toBe(true);
});
test('proposed-only Space needs explicit choice and empty context invents no evidence',async({page})=>{
 await open(page,expected.proposed_scope);await expect(page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.')).not.toBeChecked();
 let r=await ask(page);expect((await r.json()).insufficient_context).toBe(true);
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('insuffisant');
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('Les éléments disponibles ne suffisent pas');
 await includeProposals(page);r=await ask(page);
 const data=await r.json();expect(data.provided_revisions).toHaveLength(1);expect(data.provided_revisions[0].validation_state).toBe('proposed');
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('Éléments à vérifier');
 await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+expected.empty_scope);
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toHaveCount(0);
 await expect(page.getByRole('tab',{name:'Discussion',exact:true})).toHaveAttribute('aria-selected','true');await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.getByRole('heading',{name:'Construisez et explorez votre contexte',exact:true})).toBeVisible();
 r=await ask(page);expect((await r.json()).references).toHaveLength(0);
});

test('history-only Space is not labelled empty; history verification errors fail closed',async({page})=>{
 await open(page,expected.historical_scope);
 await expect(page.getByRole('heading',{name:'Construisez et explorez votre contexte',exact:true})).toBeVisible();
 await expect(page.getByText('Ce Space attend sa première compréhension.',{exact:true})).toHaveCount(0);
 await page.route('**/understanding?*',route=>new URL(route.request().url()).searchParams.get('view')==='history'
  ?route.fulfill({status:503,contentType:'application/json',body:'{"detail":"unavailable"}'}) :route.continue());
 await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+expected.empty_scope);
 await expect(page.getByRole('alert')).toBeVisible();
 await expect(page.getByText('Ce Space attend sa première compréhension.',{exact:true})).toHaveCount(0);
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeDisabled();
});
test('provider failure is sanitized, never retried, and clears prior answers',async({page})=>{
 await open(page);await ask(page);await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 let attempts=0;await page.route('**/chat',route=>{attempts++;return route.fulfill({status:503,body:'private-key-provider-detail'});});
 await ask(page);await expect(page.getByRole('alert')).toContainText('Aucun nouvel essai automatique');
 expect(attempts).toBe(1);await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toHaveCount(0);
 await expect(page.locator('body')).not.toContainText('private-key-provider-detail');
});
test('late answer after navigation cannot populate a different Space',async({page})=>{
 await open(page);let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/chat',async route=>{await gate;await route.continue();});
 await page.getByLabel('Votre question sur ce contexte').fill('Question différée');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+expected.empty_scope);
 release();await expect(page.getByRole('tab',{name:'Discussion',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();await expect(page.locator('.chat-turn')).toHaveCount(0);
});
test('real Bob OIDC cannot chat with Alice Space, arbitrary IDs reveal no private data',async({page})=>{
 let authorization='';page.on('request',r=>{if(r.url().endsWith('/auth/me'))authorization=r.headers()['authorization']||'';});
 await page.goto('/context-spaces/'+expected.scope);await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('bob');await page.locator('#password').fill(process.env.QH_BOB_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page,expected.scope);
 await expect(page.getByText('Ce Context Space est introuvable ou inaccessible.',{exact:true})).toBeVisible();
 expect(authorization.startsWith('Bearer ')).toBe(true);
 const body={messages:[{role:'user',content:'Décisions privées ?'}]};
 for(const scope of [expected.scope,'ffffffff-ffff-4fff-8fff-ffffffffffff']){
  const r=await page.request.post('/api/context-spaces/'+scope+'/chat',{headers:{Authorization:authorization},data:body});
  expect(r.status()).toBe(404);expect(await r.json()).toEqual({detail:'Context space not found'});
 }
 const r=await page.request.post('/api/context-spaces/'+expected.scope+'/chat',{data:body});expect(r.status()).toBe(401);
});


test('Alice navigates all three fixture Spaces without duplicate keys or retained dialogue',async({page})=>{
 expect(expected.demo_spaces).toHaveLength(3);
 await open(page,expected.demo_spaces[0].scope);
 const visits=[...expected.demo_spaces,expected.demo_spaces[0]];
 for(let i=0;i<visits.length;i++){
  const demo=visits[i];
  if(i){
   await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+demo.scope);
   await expect(page.getByRole('heading',{name:demo.name,exact:true})).toBeVisible();
   await expect(page.locator('details.understanding-explorer')).not.toHaveAttribute('open','');
   await expect(page.getByRole('heading',{name:'Aperçu structuré',exact:true})).toHaveCount(0);
   await expect(page.locator('section[aria-label="Détail de l’élément"]')).toHaveCount(0);
   await expect(page.getByRole('tab',{name:'Discussion',exact:true})).toHaveAttribute('aria-selected','true');
  }
  const field=page.getByLabel('Votre question sur ce contexte');
  await expect(field).toBeEnabled();await expect(field).toHaveValue('');
  await expect(page.locator('.chat-turn')).toHaveCount(0);
  const opt=page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.');
  await expect(opt).not.toBeChecked();await includeProposals(page);
  const response=await ask(page,'Di che cosa parla questo Context Space?');expect(response.status()).toBe(200);
  const answer=await response.json();expect(answer.provided_revisions).toHaveLength(6);
  expect(answer.partial_coverage).toBe(false);expect(answer.references).toHaveLength(3);
  expect(answer.provided_revisions.every((r:any)=>r.context_space_id===demo.scope&&r.validation_state==='proposed')).toBe(true);
  const turn=page.getByRole('article',{name:'Échange 1',exact:true});await expect(turn.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toBeVisible();
  await expect(turn.getByRole('heading',{name:'Réponse de l’IA',exact:true})).toHaveCount(0);
  await field.fill('Brouillon du Space précédent');
  await expandUnderstanding(page);await page.getByRole('button',{name:'Parcourir les éléments',exact:true}).click();
  await page.getByRole('button',{name:'Révisions proposées conservées',exact:true}).click();
  await page.getByRole('button',{name:'Entités canoniques',exact:true}).click();
  await expect(page.locator('.understanding-card')).toHaveCount(1);
  await page.locator('.understanding-card').click();
  await expect(page.locator('section[aria-label="Détail de l’élément"]')).toBeVisible();
 }
});

test('non-mock answer heading remains distinct without any real provider call',async({page})=>{
 await open(page);const first=await ask(page);const data=await first.json();
 await newDiscussion(page);
 await page.route('**/chat',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...data,model:'mistral-small-2603',answer:'Synthetic UI label control; no model call.'})}));
 await ask(page);const turn=page.getByRole('article',{name:'Échange 1',exact:true});
 await expect(turn.getByRole('heading',{name:'Réponse de l’IA',exact:true})).toBeVisible();
 await expect(turn.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toHaveCount(0);
});

test('all-proposed canonical context warns even when generated prose omits or contradicts status',async({page})=>{
 await open(page,expected.proposed_scope);
 await includeProposals(page);
 const original=await (await ask(page)).json();
 await newDiscussion(page);
 let noReferences=false;
 await page.route('**/chat',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
  ...original,model:'mistral-small-2603',answer:'Tout est confirmé. (Contrôle UI, aucune inférence.)',
  references:noReferences?[]:original.references,insufficient_context:noReferences})}));
 await ask(page);
 const turn=page.getByRole('article',{name:'Échange 1',exact:true});
 await expect(turn.getByRole('note')).toBeVisible();
 await expect(turn.getByRole('note')).toHaveText('Éléments à vérifier');
 await turn.locator('.answer-details>summary').click();await expect(turn.locator('.answer-details')).toContainText('Tout le contexte fourni est proposé');
 await expect(turn).toContainText('Tout est confirmé.'); // Prose remains untrusted, never rewritten.
 noReferences=true;await newDiscussion(page);await ask(page);
 await expect(turn.getByRole('note')).toHaveCount(1);
 await expect(turn.getByRole('note')).toHaveText('Éléments à vérifier');
 await turn.locator('.answer-details>summary').click();await expect(turn.locator('.answer-details')).toContainText('Tout le contexte fourni est proposé');
});

test('mixed canonical support warns only for actually cited proposals',async({page})=>{
 await open(page);await includeProposals(page);
 const original=await (await ask(page)).json();
 const confirmed=original.provided_revisions.filter((r:any)=>r.validation_state==='confirmed'&&r.is_current_confirmed);
 const proposed=original.provided_revisions.filter((r:any)=>r.validation_state==='proposed');
 expect(confirmed.length).toBeGreaterThan(0);expect(proposed.length).toBeGreaterThan(0);
 await newDiscussion(page);
 let references=confirmed;
 await page.route('**/chat',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
  ...original,model:'mistral-small-2603',answer:'Contrôle de statut canonique, aucune inférence.',references})}));
 await ask(page);const turn=page.getByRole('article',{name:'Échange 1',exact:true});
 await expect(turn.getByRole('note')).toHaveCount(0);
 references=proposed;await newDiscussion(page);await ask(page);
 await expect(turn.getByRole('note')).toBeVisible();
 await turn.locator('.answer-details>summary').click();await expect(turn.locator('.answer-details')).not.toContainText('Tout le contexte fourni est proposé');
});
