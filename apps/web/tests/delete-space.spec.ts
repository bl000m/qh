import {test,expect} from '@playwright/test';

test('exact-name confirmation, incomplete failure, retry and refreshed environment',async({page})=>{
 let attempts=0,lists=0;
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(request.method()==='DELETE'){
   expect(path).toBe('/api/context-spaces/00000000-0000-0000-0000-000000000001');
   expect(request.postDataJSON()).toEqual({name:'Space à supprimer'});attempts++;
   return route.fulfill(attempts===1?{status:503,json:{detail:'Incomplete'}}:{status:204});
  }
  expect(path).toBe('/api/context-spaces');lists++;
  return route.fulfill({json:{items:[],next_after_id:null}});
 });
 await page.goto('/tests/fixtures/delete-space.html');await page.getByRole('button',{name:'Supprimer ce Context Space',exact:true}).click();
 const confirm=page.getByRole('button',{name:'Supprimer définitivement',exact:true});
 await expect(confirm).toBeDisabled();await page.getByLabel('Nom du Space à supprimer').fill('space à supprimer');await expect(confirm).toBeDisabled();expect(attempts).toBe(0);
 await page.getByLabel('Nom du Space à supprimer').fill('Space à supprimer');await confirm.click();
 await expect(page.getByRole('alert')).toContainText('incomplète');expect(new URL(page.url()).pathname).toBe('/tests/fixtures/delete-space.html');
 await confirm.click();await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
 expect(new URL(page.url()).pathname).toBe('/');await expect.poll(()=>lists).toBe(1);expect(attempts).toBe(2);
 await expect(page.locator('body')).not.toContainText('Space à supprimer');
});
