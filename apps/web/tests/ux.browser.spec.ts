import {test,expect} from '@playwright/test';
import {afterLogin} from './navigation.browser';
import type {Page} from '@playwright/test';
const expected=JSON.parse(process.env.QH12_EXPECTED_JSON||'{}');
async function login(page:Page){
 await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 const username=page.locator('#username');
 await expect(username.or(page.getByRole('heading',{name:'Mon environnement',exact:true}))).toBeVisible();
 if(await username.isVisible()){await username.fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();}
 await afterLogin(page);
}
test('protected login and reload land at the environment, with no per-card understanding fanout',async({page},info)=>{
 let reads=0;page.on('request',r=>{if(r.url().includes('/understanding?'))reads++;});
 await page.goto('/context-spaces/'+expected.scope);await login(page);
 await expect(page.getByRole('heading',{level:1})).toHaveText('Mon environnement');
 await expect(page.getByRole('link',{name:'Démo QH-8',exact:true})).toBeVisible();
 await expect(page.locator('.space-card details[open]')).toHaveCount(0);expect(reads).toBe(0);
 await page.screenshot({path:info.outputPath('qh43-environment-desktop.png'),fullPage:true});
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();
 await expect(page.getByRole('heading',{level:1})).toHaveText('Démo QH-8');
 await page.reload();await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();await login(page);
 await expect(page.getByRole('heading',{level:1})).toHaveText('Mon environnement');
 expect(await page.evaluate(()=>[...Object.values(localStorage),...Object.values(sessionStorage)].some(x=>/access_token|refresh_token|id_token/.test(x)))).toBe(false);
});
test('primary chat and lazy keyboard explorer preserve opt-in, draft, focus and canonical access',async({page},info)=>{
 await page.goto('/');await login(page);let posts=0;
 page.on('request',r=>{if(r.url().endsWith('/chat')&&r.method()==='POST')posts++;});
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();
 const question=page.getByLabel('Votre question sur ce contexte');await expect(question).toBeEnabled();
 const panel=page.locator('details.understanding-explorer');const summary=panel.locator(':scope > summary');
 await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toHaveCount(0);
 expect(await page.locator('.context-chat').evaluate(n=>!!(n.compareDocumentPosition(document.querySelector('.understanding-explorer')!)&Node.DOCUMENT_POSITION_FOLLOWING))).toBe(true);
 await page.getByLabel('Inclure explicitement les propositions non confirmées').check();await question.fill('Brouillon conservé');
 await summary.focus();await page.keyboard.press('Enter');await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
 await page.getByRole('button',{name:'Parcourir les éléments',exact:true}).click();
 await expect(page.getByRole('region',{name:'Explorer les éléments'})).toBeVisible();
 await page.keyboard.press('Escape');await expect(summary).toBeFocused();await expect(panel).not.toHaveAttribute('open','');
 await expect(question).toHaveValue('Brouillon conservé');await expect(page.getByLabel('Inclure explicitement les propositions non confirmées')).toBeChecked();
 await page.keyboard.press('Space');await expect(page.getByRole('region',{name:'Explorer les éléments'})).toBeVisible();
 await summary.click();expect(posts).toBe(0);
 await page.screenshot({path:info.outputPath('qh43-space-desktop.png'),fullPage:true});
 await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await expect(page).toHaveURL('http://localhost:5173/');
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();await expect(question).toHaveValue('');
 await expect(page.getByLabel('Inclure explicitement les propositions non confirmées')).not.toBeChecked();
});
test('narrow mobile and 200 percent text resizing keep navigation and controls reachable',async({page},info)=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await login(page);
 await page.screenshot({path:info.outputPath('qh43-environment-mobile.png'),fullPage:true});
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await page.screenshot({path:info.outputPath('qh43-space-mobile.png'),fullPage:true});
 await page.setViewportSize({width:320,height:812});
 await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const summary=page.locator('.understanding-explorer > summary');await summary.focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('chat composer leads on mobile while technical details remain available and consent stays explicit',async({page},info)=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await login(page);
 await afterLogin(page,expected.proposed_scope);
 const field=page.getByLabel('Votre question sur ce contexte');await expect(field).toBeEnabled();
 const help=page.locator('.chat-help');await expect(help).not.toHaveAttribute('open','');
 await expect(page.getByText('Compréhension disponible : propositions non confirmées uniquement.',{exact:true})).toBeVisible();
 const opt=page.getByLabel('Inclure explicitement les propositions non confirmées');await expect(opt).toBeVisible();await expect(opt).not.toBeChecked();
 await expect(page.getByText(/La discussion utilise une sélection bornée/)).toBeHidden();
 expect((await field.boundingBox())!.y).toBeLessThan(650);
 await help.locator('summary').click();await expect(page.getByText(/La discussion utilise une sélection bornée/)).toBeVisible();
 await help.locator('summary').click();await opt.check();await field.fill('Question en attente');
 let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/chat',async route=>{await gate;await route.continue();});
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.locator('.chat-pending .chat-question-message')).toContainText('Question en attente');
 await expect(field).toBeDisabled();await expect(page.locator('.chat-turn')).toHaveCount(0);
 release();await expect(page.locator('.chat-turn')).toHaveCount(1);await expect(page.locator('.chat-pending')).toHaveCount(0);
 await expect(page.getByText('Tout le contexte fourni est proposé et non confirmé. Aucune révision confirmée courante n’a été transmise.',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toBeVisible();
 await expect(help).not.toHaveAttribute('open','');
 await expect(page.locator('.chat-turn details[open]')).toHaveCount(0);
 await page.screenshot({path:info.outputPath('qh43-conversation-mobile.png'),fullPage:true});
});
test('skip link is first keyboard stop, focuses main, then disappears without covering chat',async({page},info)=>{
 await page.goto('/');const skip=page.getByRole('link',{name:'Aller au contenu',exact:true});
 const clipped=()=>skip.evaluate(n=>getComputedStyle(n).clipPath);
 expect(await clipped()).toBe('inset(50%)');await page.keyboard.press('Tab');await expect(skip).toBeFocused();expect(await clipped()).toBe('none');
 await page.screenshot({path:info.outputPath('qh43-skip-focus-desktop.png')});
 await page.keyboard.press('Enter');await expect(page.locator('#main-content')).toBeFocused();expect(await clipped()).toBe('inset(50%)');
 await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeFocused();
 await login(page);await afterLogin(page,expected.scope);const field=page.getByLabel('Votre question sur ce contexte');await expect(field).toBeEnabled();
 await skip.focus();await page.keyboard.press('Enter');await expect(page.locator('#main-content')).toBeFocused();expect(await clipped()).toBe('inset(50%)');
 await field.focus();await expect(field).toBeFocused();
 expect(await field.evaluate(n=>{const r=n.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===n;})).toBe(true);
 expect(await field.evaluate(n=>{
  const color=(s:string)=>s.match(/[\d.]+/g)!.slice(0,3).map(Number).map(x=>{const v=x/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
  const luminance=(s:string)=>color(s).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
  const style=getComputedStyle(n),b=luminance(style.backgroundColor);
  return Math.min(...[style.color,getComputedStyle(n,'::placeholder').color].map(c=>{const a=luminance(c);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);}));
 })).toBeGreaterThanOrEqual(4.5);
 await field.blur();await page.screenshot({path:info.outputPath('qh43-unfocused-desktop.png'),fullPage:true});
});

test('selected original mark and central hero bubble load on welcome without external artwork',async({page},info)=>{
 await page.goto('/');const logo=page.locator('.brand img');await expect(logo).toHaveAttribute('alt','QH');
 await expect(logo).toHaveJSProperty('naturalWidth',876);
 const logoBox=await logo.boundingBox();expect(logoBox).not.toBeNull();
 expect(logoBox!.width/logoBox!.height).toBeCloseTo(876/768,2);
 await expect(page.locator('.signin .qh-bubble')).toHaveAttribute('aria-hidden','true');
 await expect(page.locator('.signin .qh-bubble')).toHaveJSProperty('naturalWidth',400);
 const bubbleBox=await page.locator('.signin .qh-bubble').boundingBox();expect(bubbleBox).not.toBeNull();
 expect(bubbleBox!.width/bubbleBox!.height).toBeCloseTo(4/3,2);
 expect(bubbleBox!.width).toBeGreaterThanOrEqual(450);
 expect(Math.abs(bubbleBox!.x+bubbleBox!.width/2-(await page.locator('.signin').boundingBox())!.x-(await page.locator('.signin').boundingBox())!.width/2)).toBeLessThan(2);
 expect((await page.locator('.signin').boundingBox())!.width).toBeGreaterThan(1000);
 const icon=await page.locator('link[rel="icon"]').getAttribute('href');expect(icon).toBeTruthy();
 expect((await page.request.get(icon!)).status()).toBe(200);
 await page.screenshot({path:info.outputPath('qh43-branded-welcome-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:info.outputPath('qh43-branded-welcome-mobile.png'),fullPage:true});
 await page.setViewportSize({width:320,height:812});await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('one approved identity spans environment and Space without decorative clutter before chat',async({page},info)=>{
 // A clean owner-review fixture: retain exact API records for the three real
 // synthetic demo Spaces; exclude unrelated acceptance/security controls only
 // in this capture's list response. No production filter or invented cards.
 await page.route('**/api/context-spaces?*',async route=>{
  const response=await route.fetch();const data=await response.json();
  const ids=new Set(expected.demo_spaces.map((demo:{scope:string})=>demo.scope));
  const items=data.items.filter((item:{id:string})=>ids.has(item.id));expect(items).toHaveLength(3);
  await route.fulfill({response,json:{...data,items,next_after_id:null}});
 });
 await page.goto('/');await login(page);
 await expect(page.getByRole('link',{name:'Projet pilote',exact:true})).toBeVisible();
 await expect(page.locator('.environment-heading .qh-bubble')).toHaveJSProperty('naturalWidth',400);
 expect((await page.locator('.environment-heading .qh-bubble').boundingBox())!.width).toBeGreaterThanOrEqual(380);
 await expect(page.locator('.space-card .qh-bubble')).toHaveCount(await page.locator('.space-card').count());
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh43-branded-environment-'+name+'.png'),fullPage:true});
  await page.locator('.space-grid').screenshot({path:info.outputPath('qh43-spaces-'+name+'.png')});
 }
 await page.getByRole('link',{name:'Projet pilote',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.locator('.brand img')).toHaveJSProperty('naturalWidth',876);await expect(page.locator('.qh-bubble')).toHaveCount(0);
 await expect(page.locator('.chat-help')).not.toHaveAttribute('open','');await expect(page.getByLabel('Inclure explicitement les propositions non confirmées')).not.toBeChecked();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh43-branded-space-'+name+'.png'),fullPage:true});
 }
});

test('capsule captions truncate visually while full names and distinct IDs remain keyboard-accessible',async({page})=>{
 const names=['Organisation personnelle','Organisation alternative','123456789👩🏽‍🔬suite'];
 await page.route('**/api/context-spaces?*',async route=>{
  const response=await route.fetch();const data=await response.json();
  await route.fulfill({response,json:{...data,items:expected.demo_spaces.map((demo:{scope:string},i:number)=>({...data.items[0],id:demo.scope,name:names[i]}))}});
 });
 await page.goto('/');await login(page);
 const cards=page.locator('.space-card');await expect(cards).toHaveCount(3);
 for(let i=0;i<3;i++){
  const link=cards.nth(i).getByRole('link',{name:names[i],exact:true});
  await expect(link).toHaveAttribute('title',names[i]);await expect(link).toHaveAttribute('href','/context-spaces/'+expected.demo_spaces[i].scope);
  await expect(link.locator('h3 > span[aria-hidden]')).toHaveText(i===2?'123456789👩🏽‍🔬…':'Organisati…');
 }
 const last=cards.nth(2).getByRole('link');await last.focus();await expect(last).toBeFocused();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{level:1,name:expected.demo_spaces[2].name,exact:true})).toBeVisible();
});
if(process.env.QH43_LOGIN_THEME_TEST==='1')test.describe('French QH login preview',()=>{
test.use({locale:'fr-FR'});
test('source-only QH login theme preserves the real Keycloak form and PKCE completion',async({page},info)=>{
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('#username')).toBeVisible();
 const url=new URL(page.url());expect(url.origin).toBe('http://localhost:8080');expect(url.searchParams.get('code_challenge_method')).toBe('S256');
 await expect(page.locator('link[href*="css/qh.css"]')).toHaveCount(1);await expect(page.locator('#password')).toHaveAttribute('type','password');
 await expect(page.locator('html')).toHaveAttribute('lang','fr');
 await expect(page.getByRole('heading',{name:'Connectez-vous à votre compte',exact:true})).toBeVisible();
 await expect(page.getByLabel('Mot de passe',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Connexion',exact:true})).toBeVisible();
 expect(await page.locator('#kc-header-wrapper').evaluate(n=>getComputedStyle(n,'::before').backgroundImage)).toContain('qh-logo.png');
 expect(await page.locator('#kc-header-wrapper').evaluate(n=>getComputedStyle(n,'::before').backgroundSize)).toBe('contain');
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh43-keycloak-preview-'+name+'.png'),fullPage:true});
 }
 await page.setViewportSize({width:320,height:812});await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page);
 await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
});
});
