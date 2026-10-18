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
