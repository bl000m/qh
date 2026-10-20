import {expect} from '@playwright/test';
import type {Page} from '@playwright/test';

export async function afterLogin(page:Page,scope?:string) {
  await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
  await expect(page).toHaveURL('http://localhost:5173/');
  if(scope)await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);
}
export async function showSupport(page:Page){
 await page.getByRole('tab',{name:'Éléments',exact:true}).click();
}
export async function expandUnderstanding(page:Page){
 await showSupport(page);
 const panel=page.locator('details.understanding-explorer');await panel.waitFor({state:'attached'});
 if(!await panel.evaluate((n:HTMLDetailsElement)=>n.open))await panel.locator(':scope > summary').click();
}
export async function includeProposals(page:Page,checked=true){
 await page.getByRole('tab',{name:'Modèle',exact:true}).click();
 const details=page.locator('.administrative-disclosure');if(!await details.evaluate((n:HTMLDetailsElement)=>n.open))await details.locator('summary').click();
 await page.getByLabel('Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.',{exact:true}).setChecked(checked);
 await page.getByRole('tab',{name:'Discussion',exact:true}).click();
}
