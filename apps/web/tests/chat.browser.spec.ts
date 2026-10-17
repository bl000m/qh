import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
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
