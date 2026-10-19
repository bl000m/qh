import {expect} from '@playwright/test';
import type {Page} from '@playwright/test';

export async function afterLogin(page:Page,scope?:string) {
  await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
  await expect(page).toHaveURL('http://localhost:5173/');
  if(scope)await page.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/context-spaces/'+scope);
}
export async function showSupport(page:Page){
 const toggle=page.getByRole('button',{name:'Sources & compréhension',exact:true});
 if(await toggle.isVisible())await toggle.click();
}
export async function expandUnderstanding(page:Page) {
  await showSupport(page);
  const panel=page.locator('details.understanding-explorer');
  if(!await panel.evaluate((node:HTMLDetailsElement)=>node.open))await panel.locator(':scope > summary').click();
}
