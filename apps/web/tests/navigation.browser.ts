import {expect} from '@playwright/test';
import type {Page} from '@playwright/test';

export async function afterLogin(page:Page,scope?:string) {
  await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
  await expect(page).toHaveURL('http://localhost:5173/');
  if(scope)await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);
}
export async function showSupport(page:Page){
 if(await page.locator('.understanding-workspace').isVisible()||await page.locator('#space-tab-1').getAttribute('aria-selected')==='true')return;
 await page.getByRole('tab',{name:'Éléments',exact:true}).click();
}
export async function expandUnderstanding(page:Page){
 await showSupport(page);
 const panel=page.locator('details.understanding-explorer');await panel.waitFor({state:'attached'});
 if(!await panel.evaluate((n:HTMLDetailsElement)=>n.open))await panel.locator(':scope > summary').click();
 const advanced=page.locator('.workspace-advanced');await advanced.waitFor({state:'attached'});if(!await advanced.evaluate((n:HTMLDetailsElement)=>n.open))await advanced.locator(':scope>summary').click();
}
export async function includeProposals(page:Page,checked=true){
 await closeUnderstanding(page);
 await page.getByRole('tab',{name:'Modèle',exact:true}).click();
 const details=page.locator('.administrative-disclosure');if(!await details.evaluate((n:HTMLDetailsElement)=>n.open))await details.locator('summary').click();
 await page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.',{exact:true}).setChecked(checked);
 await page.getByRole('tab',{name:'Discussion',exact:true}).click();
}
export async function newDiscussion(page:Page){
 const menu=page.locator('.composer-options');if(!await menu.evaluate((n:HTMLDetailsElement)=>n.open))await menu.locator('summary').click();
 await page.getByRole('button',{name:'Nouvelle discussion',exact:true}).click();
}

export async function closeUnderstanding(page:Page){const close=page.getByRole('button',{name:'Revenir aux éléments',exact:true});if(await close.isVisible())await close.click();}
