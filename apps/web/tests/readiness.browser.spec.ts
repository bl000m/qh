import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
const enabled=process.env.QH52_PRODUCT_BROWSER_TEST==='1';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
async function login(page:Page,user='alice'){
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await expect(page.locator('#username')).toHaveAttribute('name','username');
 await expect(page.locator('#username')).toHaveAttribute('autocomplete','username');
 await expect(page.locator('#password')).toHaveAttribute('name','password');
 await expect(page.locator('#password')).toHaveAttribute('autocomplete','current-password');
 await expect(page.locator('#kc-form-login')).toHaveAttribute('method',/post/i);
 await expect(page.locator('#password')).toHaveAttribute('type','password');
 await page.locator('#username').fill(user);await page.locator('#password').fill(process.env[user==='alice'?'QH_ALICE_PASSWORD':'QH_BOB_PASSWORD']!);await page.locator('#kc-login').click();
 await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
}
async function open(page:Page,scope:string){await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();}
if(enabled)test('QH-52 product: native password form, descriptions, offline first information, no mock, reopen and owner isolation',async({page},info)=>{
 await login(page);
 await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
 await page.getByLabel('Nom du Context Space',{exact:true}).fill('QH-52 budget synthetic');await page.getByLabel('Domaine principal',{exact:true}).selectOption({index:1});await page.getByRole('button',{name:'Créer',exact:true}).click();
 await page.getByRole('link',{name:'Ouvrir ce Space',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Construisez et explorez votre contexte'})).toBeVisible();
 const scope=new URL(page.url()).pathname.split('/').at(-1)!;
 await expect(page.getByLabel('Mode de discussion',{exact:true})).toHaveCount(0);await expect(page.locator('body')).not.toContainText('Démonstration mock');
 await expect(page.getByRole('button',{name:'Envoyer la question',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Modifier le Space',exact:true}).click();
 await page.getByLabel('Nom du Space',{exact:true}).fill('Budget personnel synthétique');await page.getByLabel('Description du Space',{exact:true}).fill('Repère personnel, sans classification automatique.');await page.getByRole('button',{name:'Enregistrer le Space',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.getByRole('tab',{name:'Discussion',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Budget personnel synthétique',exact:true})).toBeVisible();
 await expect(page.locator('.space-title>p')).toBeVisible();
 await page.getByRole('link',{name:'Paramètres de mon environnement',exact:true}).click();
 await page.getByRole('button',{name:'Organiser mes domaines',exact:true}).click();await page.getByLabel('Nom du domaine 1',{exact:true}).fill('Organisation QH-52');await page.getByLabel('Description du domaine 1',{exact:true}).fill('Description organisationnelle du domaine.');await page.getByRole('button',{name:'Enregistrer l’organisation',exact:true}).click();
 await page.getByRole('link',{name:'Mon environnement',exact:true}).first().click();await page.getByRole('link',{name:'Organisation QH-52',exact:true}).click();await expect(page.getByText('Description organisationnelle du domaine.',{exact:true})).toBeVisible();await page.getByRole('link',{name:'Budget personnel synthétique',exact:true}).click();
 for(const [label,width,height,zoom] of [['desktop',1448,1086,1],['mobile',390,844,1],['desktop-200',1448,1086,2],['keyboard',390,450,1]] as const){
  await page.setViewportSize({width,height});await page.evaluate(z=>{document.documentElement.style.zoom=String(z);},zoom);
  await page.getByLabel('Votre question sur ce contexte').fill('Brouillon conservé en mémoire');
  const bounds=await page.evaluate(()=>({notice:document.querySelector('.chat-empty')!.getBoundingClientRect().bottom,composer:document.querySelector('.chat-composer')!.getBoundingClientRect().top,width:innerWidth,scroll:document.documentElement.scrollWidth}));
  if(width===390)expect(await page.locator('.space-title').evaluate(n=>n.getBoundingClientRect().width)).toBeGreaterThanOrEqual(width/2);
  expect(bounds.notice).toBeLessThanOrEqual(bounds.composer);expect(bounds.scroll).toBeLessThanOrEqual(bounds.width+1);
  await page.screenshot({path:info.outputPath('qh52-empty-'+label+'.png'),fullPage:true});
 }
 await page.evaluate(()=>{document.documentElement.style.zoom='1';});await page.setViewportSize({width:1448,height:1086});
 await page.getByRole('button',{name:'Ajouter un élément',exact:true}).click();
 const text='Pour mon budget de démonstration, je prévois 2 500 € de revenus mensuels et 1 300 € de dépenses fixes.';
 await page.getByLabel('Votre information',{exact:true}).fill(text);await expect(page.getByRole('button',{name:'Conserver cette information',exact:true})).toBeDisabled();
 await page.getByLabel('Je souhaite conserver ce texte comme proposition non confirmée dans ce contexte.',{exact:true}).check();
 const saving=page.waitForResponse(r=>r.url().endsWith('/enrichments')&&r.request().method()==='POST');await page.getByRole('button',{name:'Conserver cette information',exact:true}).click();
 const response=await saving;expect(response.status()).toBe(200);const receipt=await response.json();expect(receipt.provider_mode).toBe('offline-literal/1');expect(receipt.revision_ids).toHaveLength(1);
 await expect(page.getByText(/Votre information est conservée/)).toBeVisible();await page.getByRole('button',{name:'Examiner l’information 1',exact:true}).click();await expect(page.locator('blockquote').filter({hasText:text}).first()).toBeVisible();
 await page.screenshot({path:info.outputPath('qh52-first-information.png'),fullPage:true});
 await page.reload();await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 // Existing SSO reconnects without entering credentials. Explicit Space route survives.
 await expect(page.getByRole('heading',{name:'Budget personnel synthétique',exact:true})).toBeVisible();await expect(page.locator('.space-title>p')).toBeVisible();
 const disabledMock=await page.request.post('/api/context-spaces/'+scope+'/chat',{headers:{Authorization:response.request().headers()['authorization']},data:{messages:[{role:'user',content:'No implicit mock'}]}});expect(disabledMock.status()).toBe(503);
 const persisted=await page.request.get('/api/context-spaces/'+scope+'/understanding?view=proposed&limit=20',{headers:{Authorization:response.request().headers()['authorization']}});
 expect(persisted.status()).toBe(200);const rows=(await persisted.json()).items;
 expect(rows.some((r:any)=>r.content.text===text&&r.validation_state==='proposed'&&r.provenance.some((p:any)=>p.source_revision_id===receipt.source_revision_id))).toBe(true);
 await page.getByRole('button',{name:'Se déconnecter',exact:true}).click();await page.waitForURL(/:8080.*logout/);await expect(page.locator('body')).toContainText(/déconnect|logout|logged out|logging out/i);
 await login(page,'bob');await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);await expect(page.getByRole('alert').filter({hasText:/introuvable|inaccessible/})).toBeVisible();await expect(page.locator('body')).not.toContainText(text);
});

if(enabled)test('QH-52 product: real OIDC renewal preserves draft and disclosure, fake HTTP accounting, revocation',async({page},info)=>{
 await page.clock.install();await login(page);await open(page,expected.demo_spaces[0].scope);
 await page.getByLabel('Votre question sur ce contexte').fill('Question synthétique sur ce contexte');
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();const region=page.getByRole('region',{name:'Consentement Mistral'});
 const previewed=page.waitForResponse(r=>r.url().endsWith('/chat-sessions/preview')&&r.status()===200);await region.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.',{exact:true}).check();const preview=await previewed;expect(preview.status()).toBe(200);await expect(region).toContainText('30 minutes');
 await expect(region.locator('article.revision')).toHaveCount(6);
 for(const [label,width,height,zoom] of [['desktop',1448,1086,1],['mobile',390,844,1],['zoom',1448,1086,2]] as const){await page.setViewportSize({width,height});await page.evaluate(z=>{document.documentElement.style.zoom=String(z);},zoom);const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('*')].filter(n=>n.getBoundingClientRect().right>innerWidth+1).slice(0,10).map(n=>({tag:n.tagName,class:n.className,box:n.getBoundingClientRect().toJSON()}))}));expect(overflow.scroll,JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.width+1);await page.screenshot({path:info.outputPath('qh52-expanded-provider-'+label+'.png'),fullPage:true});}
 await page.evaluate(()=>{document.documentElement.style.zoom='1';});await page.setViewportSize({width:1448,height:1086});
 await page.getByLabel('J’autorise l’envoi à Mistral',{exact:false}).check();const consented=page.waitForResponse(r=>r.url().endsWith('/consent'));await page.getByRole('button',{name:'Autoriser cette session Mistral',exact:true}).click();expect((await consented).status()).toBe(200);
 const draft=await page.getByLabel('Votre question sur ce contexte').inputValue();
 // Pause timers, advance only browser time to the renewal boundary; the IdP and
 // resource-server clocks remain real. Restore browser time after the HTTP refresh.
 await page.clock.pauseAt(Date.now()+1000);await page.clock.setFixedTime(Date.now()+241000);
 const renewed=page.waitForResponse(r=>r.url().includes('/protocol/openid-connect/token')&&r.request().postData()?.includes('refresh_token')===true);
 await page.evaluate(()=>dispatchEvent(new Event('focus')));const refresh=await renewed;expect(refresh.status()).toBe(200);await page.clock.setFixedTime(Date.now());
 await expect(page.getByLabel('Votre question sur ce contexte')).toHaveValue(draft);await page.getByRole('tab',{name:'Modèle',exact:true}).click();await page.locator('.administrative-disclosure>summary').click();await expect(page.getByRole('status').filter({hasText:/Autorisation active/})).toBeVisible();await page.getByRole('tab',{name:'Discussion',exact:true}).click();
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toContainText('Simulation hors réseau');
 await page.getByRole('tab',{name:'Modèle',exact:true}).click();await expect(page.getByRole('status').filter({hasText:/1\/3 requêtes/})).toBeVisible();
 await page.getByRole('button',{name:'Révoquer la session',exact:true}).click();await page.getByRole('tab',{name:'Discussion',exact:true}).click();await expect(page.getByRole('button',{name:'Envoyer la question',exact:true})).toBeDisabled();
 expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toMatch(/access_token|refresh_token|Question synthétique/);
 const tokens=await refresh.json();
 await page.getByLabel('Votre question sur ce contexte').fill('Brouillon après révocation');
 const revoked=await page.request.post('http://localhost:8080/realms/qh/protocol/openid-connect/revoke',{form:{client_id:'qh-web',token:tokens.refresh_token,token_type_hint:'refresh_token'}});expect(revoked.status()).toBe(200);
 // The SDK derives expires_at from expires_in under the advanced browser clock.
 // Cross that derived expiry as well; the IdP clock is intentionally unchanged.
 await page.clock.setFixedTime(Date.now()+601000);await page.evaluate(()=>dispatchEvent(new Event('focus')));
 await expect(page.getByRole('dialog')).toContainText('Reconnectez-vous pour continuer');await expect(page.getByLabel('Votre question sur ce contexte')).toHaveValue('Brouillon après révocation');
 await page.getByRole('button',{name:'Se déconnecter et effacer les brouillons',exact:true}).click();await expect(page.locator('#chat-question')).toHaveCount(0);
});
