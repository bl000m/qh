import {test,expect} from '@playwright/test';
import {afterLogin} from './navigation.browser';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
const enabled=process.env.QH45_SESSION_BROWSER_TEST==='1';
async function open(page:any,scope:string){
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page,scope);
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
}
async function preview(page:any){
 await page.getByLabel('Votre question sur ce contexte').fill('Di che cosa parla questo Context Space?');
 await page.getByLabel('Mode de discussion',{exact:true}).selectOption('mistral');
 await page.getByRole('button',{name:'Examiner les données avant envoi',exact:true}).click();
 await expect(page.getByRole('button',{name:'Autoriser cette session Mistral',exact:true})).toBeDisabled();
}
async function consent(page:any){
 await page.getByLabel('J’autorise l’envoi à Mistral',{exact:false}).check();
 await page.getByRole('button',{name:'Autoriser cette session Mistral',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:/Session autorisée/})).toBeVisible();
}
if(enabled)test('QH-45 real API simulated provider: separate consent, exact preview, canonical references and follow-up',async({page},info)=>{
 await open(page,expected.demo_spaces[0].scope);
 let generated=0;page.on('request',r=>{if(/chat-sessions\/.+\/messages$/.test(r.url()))generated++;});
 await expect(page.getByLabel('Mode de discussion',{exact:true})).toHaveValue('mock');
 await page.getByLabel('Inclure explicitement les propositions non confirmées').check();
 await preview(page);expect(generated).toBe(0);
 await expect(page.getByRole('button',{name:'Envoyer la question',exact:true})).toBeDisabled();
 const section=page.getByRole('region',{name:'Consentement Mistral'});
 await expect(section.getByRole('note')).toContainText('proposé et non confirmé');
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh45-consent-'+name+'.png'),fullPage:true});
 }
 await page.getByText('Données exactes et provenance avant envoi (6 révisions)',{exact:true}).click();
 await expect(section.getByRole('article')).toHaveCount(6);
 await expect(section.locator('blockquote').first()).toBeVisible();
 await page.getByText('Données exactes et provenance avant envoi (6 révisions)',{exact:true}).click();
 await consent(page);expect(generated).toBe(0);
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 const first=page.getByRole('article',{name:'Échange 1',exact:true});await expect(first).toContainText('Simulation hors réseau');
 await expect(first.getByRole('note').filter({hasText:/Tout le contexte fourni/})).toBeVisible();
 await expect(page.getByRole('status').filter({hasText:/1\/3 requêtes/})).toBeVisible();
 await page.getByLabel('Votre question sur ce contexte').fill('E quali sono le incertezze?');
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByRole('article',{name:'Échange 2',exact:true})).toBeVisible();expect(generated).toBe(2);
 await page.getByRole('button',{name:'Révoquer la session',exact:true}).click();
 await expect(page.locator('.chat-turn')).toHaveCount(0);await expect(page.getByRole('button',{name:'Envoyer la question',exact:true})).toBeDisabled();
 expect(await page.evaluate(()=>[...Object.values(localStorage),...Object.values(sessionStorage)].some(v=>v.includes('session_id')))).toBe(false);
});
if(enabled)test('QH-45 changing question invalidates preview; changing Space revokes active session and resets mock',async({page})=>{
 const scope=expected.demo_spaces[1].scope;await open(page,scope);await page.getByLabel('Inclure explicitement les propositions non confirmées').check();
 await preview(page);await page.getByLabel('Votre question sur ce contexte').fill('Domanda modificata');
 await expect(page.getByText('Question modifiée : préparez un nouvel aperçu avant de consentir.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Examiner les données avant envoi',exact:true}).click();await consent(page);
 const revoked=page.waitForResponse(r=>r.request().method()==='DELETE'&&r.url().includes('/chat-sessions/'));
 await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+expected.demo_spaces[2].scope);
 expect((await revoked).status()).toBe(200);
 await expect(page.getByLabel('Mode de discussion',{exact:true})).toHaveValue('mock');
 await expect(page.getByLabel('Inclure explicitement les propositions non confirmées')).not.toBeChecked();
});
if(enabled)test('QH-45 expiry and provider error terminate without retry or automatic mock fallback',async({page})=>{
 await page.clock.install();await open(page,expected.scope);await preview(page);await consent(page);
 let count=0;await page.route('**/chat-sessions/*/messages',r=>{count++;return r.fulfill({status:503,body:'private-provider-payload'});});
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByText(/Session arrêtée après erreur/)).toBeVisible();expect(count).toBe(1);
 await expect(page.getByLabel('Mode de discussion',{exact:true})).toHaveValue('mistral');
 await expect(page.locator('body')).not.toContainText('private-provider-payload');
 await expect(page.getByRole('button',{name:'Envoyer la question',exact:true})).toBeDisabled();
 await page.getByLabel('Votre question sur ce contexte').fill('Nouvelle question');
 await page.getByRole('button',{name:'Examiner les données avant envoi',exact:true}).click();await consent(page);
 // Advance only this offline browser clock; real server expiry is covered by API/clock tests.
 await page.clock.fastForward(301000);
 await expect(page.getByRole('alert')).toContainText('Votre session a expiré');
 await expect(page.locator('.context-chat')).toHaveCount(0);
});
if(enabled)test('QH-45 logout revokes before clearing tokens, without changing real OIDC logout',async({page})=>{
 await open(page,expected.scope);await preview(page);
 const consented=page.waitForResponse(r=>r.url().endsWith('/consent'));
 await consent(page);const receipt=await consented;const grant=await receipt.json();
 const authorization=receipt.request().headers()['authorization'];
 await page.getByRole('button',{name:'Se déconnecter',exact:true}).click();
 // keepalive can finish after navigation: assert server state, not a detached page's response event.
 await expect.poll(async()=>{
  const status=await page.request.get('/api/context-spaces/'+expected.scope+'/chat-sessions/'+grant.session_id,{headers:{Authorization:authorization}});
  return status.status()===200?(await status.json()).state:'unavailable';
 }).toBe('revoked');
 // Even this still-valid signed access token cannot reuse its explicitly revoked grant.
 const r=await page.request.post('/api/context-spaces/'+expected.scope+'/chat-sessions/'+grant.session_id+'/messages',{
  headers:{Authorization:authorization},data:{messages:[{role:'user',content:'x'}]}});
 expect(r.status()).toBe(409);
 await expect(page.locator('body')).toContainText(/déconnect|logout|logged out|logging out/i);
});
