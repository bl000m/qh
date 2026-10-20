import {includeProposals} from './navigation.browser';
import {test,expect} from '@playwright/test';
import {afterLogin,showSupport} from './navigation.browser';
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
 await includeProposals(page);await question.fill('Brouillon conservé');
 await showSupport(page);await summary.focus();await page.keyboard.press('Enter');await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
 await page.getByRole('button',{name:'Parcourir les éléments',exact:true}).click();
 await expect(page.getByRole('region',{name:'Explorer les éléments'})).toBeVisible();
 await page.keyboard.press('Escape');await expect(summary).toBeFocused();await expect(panel).not.toHaveAttribute('open','');
 await page.getByRole('tab',{name:'Discussion',exact:true}).click();await expect(question).toHaveValue('Brouillon conservé');await expect(page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.')).toBeChecked();
 await showSupport(page);await summary.focus();await page.keyboard.press('Space');await expect(page.getByRole('region',{name:'Explorer les éléments'})).toBeVisible();
 await summary.click();expect(posts).toBe(0);
 await page.screenshot({path:info.outputPath('qh43-space-desktop.png'),fullPage:true});
 await page.getByRole('link',{name:'Mon environnement',exact:true}).click();await expect(page).toHaveURL('http://localhost:5173/');
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();await expect(question).toHaveValue('');
 await expect(page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.')).not.toBeChecked();
});
test('narrow mobile and 200 percent text resizing keep navigation and controls reachable',async({page},info)=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await login(page);
 await page.screenshot({path:info.outputPath('qh43-environment-mobile.png'),fullPage:true});
 await page.getByRole('link',{name:'Démo QH-8',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await page.screenshot({path:info.outputPath('qh43-space-mobile.png'),fullPage:true});
 await page.setViewportSize({width:320,height:812});
 await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await showSupport(page);const summary=page.locator('.understanding-explorer > summary');await summary.focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'Aperçu structuré'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('chat composer leads on mobile while technical details remain available and consent stays explicit',async({page},info)=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await login(page);
 await afterLogin(page,expected.proposed_scope);
 const field=page.getByLabel('Votre question sur ce contexte');await expect(field).toBeEnabled();
 await expect(page.getByText('Compréhension disponible : propositions non confirmées uniquement.',{exact:true})).toHaveCount(0);
 expect((await field.boundingBox())!.y).toBeLessThan(844);await includeProposals(page);await field.fill('Question en attente');
 let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/chat',async route=>{await gate;await route.continue();});
 await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.locator('.chat-pending .chat-question-message')).toContainText('Question en attente');
 await expect(field).toBeDisabled();await expect(page.locator('.chat-turn')).toHaveCount(0);
 release();await expect(page.locator('.chat-turn')).toHaveCount(1);await expect(page.locator('.chat-pending')).toHaveCount(0);
 await expect(page.getByRole('note').filter({hasText:'Éléments à vérifier'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Extraits de démonstration — sans compréhension de la question',exact:true})).toBeVisible();
 await expect(page.locator('.chat-help')).toHaveCount(0);
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
 await page.setViewportSize({width:390,height:844});
 const mobileBubble=await page.locator('.signin .qh-bubble').boundingBox();
 expect(Math.abs(mobileBubble!.x+mobileBubble!.width/2-195)).toBeLessThan(2);
 await page.screenshot({path:info.outputPath('qh43-branded-welcome-mobile.png'),fullPage:true});
 await page.setViewportSize({width:320,height:812});await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('one approved identity spans environment and Space without decorative clutter before chat',async({page},info)=>{
 // A clean owner-review fixture: retain exact API records for the three real
 // synthetic demo Spaces; exclude unrelated acceptance/security controls only
 // in this capture's list response. No production filter or invented cards.
 await page.route('**/api/environment/spaces?*',async route=>{
  const response=await route.fetch();const data=await response.json();
  const ids=new Set(expected.demo_spaces.map((demo:{scope:string})=>demo.scope));
  const items=data.items.filter((item:{id:string})=>ids.has(item.id));expect(items).toHaveLength(3);
  await route.fulfill({response,json:{...data,items,next_after_id:null}});
 });
 await page.goto('/');await login(page);
 await expect(page.getByRole('link',{name:'Projet pilote',exact:true})).toBeVisible();
 // QH-50 owner refinement replaces the large dashboard hero with two compact shelves.
 await expect(page.locator('.domain-orb img').first()).toHaveJSProperty('naturalWidth',400);
 await expect(page.locator('.domain-orb')).toHaveCount(7);
 await expect(page.locator('.space-card .qh-bubble')).toHaveCount(await page.locator('.space-card').count());
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});
  const bubble=await page.locator('.domain-orb img').first().boundingBox();
  expect(Math.abs(bubble!.width/bubble!.height-4/3)).toBeLessThan(.01);
  await page.screenshot({path:info.outputPath('qh43-branded-environment-'+name+'.png'),fullPage:true});
  await page.locator('.space-grid').screenshot({path:info.outputPath('qh43-spaces-'+name+'.png')});
 }
 await page.getByRole('link',{name:'Projet pilote',exact:true}).click();await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await expect(page.locator('.brand img')).toHaveJSProperty('naturalWidth',876);await expect(page.locator('.space-heading .qh-bubble')).toHaveCount(1);
 await expect(page.locator('.chat-help')).toHaveCount(0);await expect(page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.')).not.toBeChecked();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});await page.screenshot({path:info.outputPath('qh43-branded-space-'+name+'.png'),fullPage:true});
 }
});

test('approved cards show full names within two lines while distinct IDs remain keyboard-accessible',async({page})=>{
 const names=['Organisation personnelle','Organisation alternative','123456789👩🏽‍🔬suite'];
 await page.route('**/api/environment/spaces?*',async route=>{
  const response=await route.fetch();const data=await response.json();
  await route.fulfill({response,json:{...data,items:expected.demo_spaces.map((demo:{scope:string},i:number)=>({...data.items[0],id:demo.scope,name:names[i]}))}});
 });
 await page.goto('/');await login(page);
 const cards=page.locator('.space-card');await expect(cards).toHaveCount(3);
 for(let i=0;i<3;i++){
  const link=cards.nth(i).getByRole('link',{name:names[i],exact:true});
  await expect(link).toHaveAttribute('title',names[i]);await expect(link).toHaveAttribute('href','/context-spaces/'+expected.demo_spaces[i].scope);
  await expect(link.locator('h3')).toHaveText(names[i]);expect(await link.locator('h3').evaluate(e=>getComputedStyle(e).webkitLineClamp)).toBe('2');
 }
 const last=cards.nth(2).getByRole('link');await last.focus();await expect(last).toBeFocused();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{level:1,name:expected.demo_spaces[2].name,exact:true})).toBeVisible();
});
if(process.env.QH43_LOGIN_THEME_TEST==='1')test.describe('French QH login preview',()=>{
test.use({locale:'fr-FR'});
test('source-only QH login theme matches the approved form, switches FR EN and preserves PKCE',async({page},info)=>{
 await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('#username')).toBeVisible();
 const initial=new URL(page.url());expect(initial.origin).toBe('http://localhost:8080');expect(initial.searchParams.get('code_challenge_method')).toBe('S256');
 await expect(page.locator('link[href*="css/qh.css"]')).toHaveCount(1);await expect(page.locator('#password')).toHaveAttribute('type','password');
 for(const [locale,label,username,submit] of [['fr','Français','Email ou identifiant','Continuer'],['en','English','Email or username','Continue']] as const){
  await page.getByRole('link',{name:label,exact:true}).click();await expect(page.locator('html')).toHaveAttribute('lang',locale);await expect(page.getByRole('link',{name:label,exact:true})).toHaveAttribute('aria-current','true');
  await expect(page.locator('#kc-page-title')).toHaveCount(0);await expect(page.getByLabel(username,{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:submit,exact:true})).toBeVisible();
  expect(await page.locator('#kc-form-login').getAttribute('action')).toContain('/login-actions/authenticate');
  for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]] as const){await page.setViewportSize({width,height});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const bubble=await page.locator('.pf-v5-c-login__main-header').evaluate(n=>({width:parseFloat(getComputedStyle(n,'::after').width),available:n.getBoundingClientRect().width-parseFloat(getComputedStyle(n).paddingLeft)-parseFloat(getComputedStyle(n).paddingRight)}));expect(Math.abs(bubble.width-bubble.available)).toBeLessThan(2);await page.screenshot({path:info.outputPath('qh50-keycloak-'+locale+'-'+name+'.png'),fullPage:true});}
 }
 await page.locator('#username').fill('alice');await page.locator('#password').fill('invalid-synthetic-password');await page.locator('#kc-login').click();await expect(page.locator('#input-error-username')).toBeVisible();await expect(page.locator('#password')).toHaveValue('');
 await page.getByRole('link',{name:'Français',exact:true}).focus();await page.keyboard.press('Enter');await expect(page.locator('html')).toHaveAttribute('lang','fr');
 await page.locator('#password').fill('visibility-control');await page.locator('#password-show-password').click();await expect(page.locator('#password')).toHaveAttribute('type','text');await page.locator('#password-show-password').click();await expect(page.locator('#password')).toHaveAttribute('type','password');
 await page.setViewportSize({width:320,height:812});await page.evaluate(()=>document.documentElement.style.fontSize='200%');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);await page.locator('#kc-login').click();await afterLogin(page);
 await page.getByRole('button',{name:'Se déconnecter'}).click();await expect(page).toHaveURL(/localhost:8080/);
});
});
