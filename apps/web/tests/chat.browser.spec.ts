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
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();
 await page.getByRole('button',{name:'Discuter avec ce contexte',exact:true}).click();
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
 await turn.getByText('Sources utilisées (1 références déclarées)',{exact:true}).click();
 const sources=turn.locator('details').filter({has:page.locator('summary').filter({hasText:/^Sources utilisées/})});
 await expect(sources.locator('blockquote')).toBeVisible();
 await expect(sources.getByRole('article',{name:'Révision '+data.references[0].revision_id,exact:true})).toBeVisible();
 const next=await ask(page,'Et que savons-nous encore ?');expect(next.status()).toBe(200);
 const body=next.request().postDataJSON();expect(body.messages.map((m:any)=>m.role)).toEqual(['user','assistant','user']);
 await expect(page.getByRole('article',{name:'Échange 2',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>Object.keys(localStorage).length)).toBe(0);
 await page.screenshot({path:info.outputPath('qh13-context-chat.png'),fullPage:true});
 await page.getByLabel('Inclure explicitement les propositions non confirmées').check();
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toHaveCount(0);
 const proposed=await ask(page);expect(proposed.request().postDataJSON().include_proposed).toBe(true);
 expect((await proposed.json()).provided_revisions.some((r:any)=>r.validation_state==='proposed')).toBe(true);
});
test('proposed-only Space needs explicit choice and empty context invents no evidence',async({page})=>{
 await open(page,expected.proposed_scope);await expect(page.getByText('Ce Space contient uniquement des propositions utilisables après votre choix explicite.',{exact:false})).toBeVisible();
 let r=await ask(page);expect((await r.json()).insufficient_context).toBe(true);
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('insuffisant');
 await page.getByLabel('Inclure explicitement les propositions non confirmées').check();r=await ask(page);
 const data=await r.json();expect(data.provided_revisions).toHaveLength(1);expect(data.provided_revisions[0].validation_state).toBe('proposed');
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('Proposé, non confirmé');
 await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+expected.empty_scope);
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Discuter avec ce contexte',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 r=await ask(page);expect((await r.json()).references).toHaveLength(0);
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
 release();await page.getByRole('button',{name:'Discuter avec ce contexte',exact:true}).click();
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();await expect(page.locator('.chat-turn')).toHaveCount(0);
});
test('real Bob OIDC cannot chat with Alice Space, arbitrary IDs reveal no private data',async({page})=>{
 let authorization='';page.on('request',r=>{if(r.url().endsWith('/auth/me'))authorization=r.headers()['authorization']||'';});
 await page.goto('/context-spaces/'+expected.scope);await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('bob');await page.locator('#password').fill(process.env.QH_BOB_PASSWORD!);await page.locator('#kc-login').click();
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
   await expect(page.getByRole('button',{name:'Discuter avec ce contexte',exact:true})).toHaveAttribute('aria-expanded','false');
   await expect(page.getByRole('heading',{name:'Aperçu structuré',exact:true})).toBeVisible();
   await expect(page.locator('section[aria-label="Détail de l’élément"]')).toHaveCount(0);
   await page.getByRole('button',{name:'Discuter avec ce contexte',exact:true}).click();
  }
  const field=page.getByLabel('Votre question sur ce contexte');
  await expect(field).toBeEnabled();await expect(field).toHaveValue('');
  await expect(page.locator('.chat-turn')).toHaveCount(0);
  const opt=page.getByLabel('Inclure explicitement les propositions non confirmées');
  await expect(opt).not.toBeChecked();await opt.check();
  const response=await ask(page,'Di che cosa parla questo Context Space?');expect(response.status()).toBe(200);
  const answer=await response.json();expect(answer.provided_revisions).toHaveLength(6);
  expect(answer.partial_coverage).toBe(false);expect(answer.references).toHaveLength(3);
  expect(answer.provided_revisions.every((r:any)=>r.context_space_id===demo.scope&&r.validation_state==='proposed')).toBe(true);
  const turn=page.getByRole('article',{name:'Échange 1',exact:true});await expect(turn.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toBeVisible();
  await expect(turn.getByRole('heading',{name:'Réponse de l’IA',exact:true})).toHaveCount(0);
  await field.fill('Brouillon du Space précédent');
  await page.getByRole('button',{name:'Explorer la compréhension',exact:true}).click();
  await page.getByRole('button',{name:'Propositions à examiner',exact:true}).click();
  await page.getByRole('button',{name:'Entités canoniques',exact:true}).click();
  await expect(page.locator('.understanding-card')).toHaveCount(1);
  await page.locator('.understanding-card').click();
  await expect(page.locator('section[aria-label="Détail de l’élément"]')).toBeVisible();
 }
});

test('non-mock answer heading remains distinct without any real provider call',async({page})=>{
 await open(page);const first=await ask(page);const data=await first.json();
 await page.getByRole('button',{name:'Nouvelle discussion',exact:true}).click();
 await page.route('**/chat',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...data,model:'mistral-small-2603',answer:'Synthetic UI label control; no model call.'})}));
 await ask(page);const turn=page.getByRole('article',{name:'Échange 1',exact:true});
 await expect(turn.getByRole('heading',{name:'Réponse de l’IA',exact:true})).toBeVisible();
 await expect(turn.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toHaveCount(0);
});
