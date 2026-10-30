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


test('compact confirmation matches actions layout, dismisses safely and returns to parent domain',async({page})=>{
 let deletions=0;
 await page.route('**/api/**',async route=>{
  expect(route.request().method()).toBe('DELETE');deletions++;
  expect(route.request().postDataJSON()).toEqual({name:'Space à supprimer'});
  await route.fulfill({status:204});
 });
 await page.setViewportSize({width:768,height:1024});
 await page.goto('/tests/fixtures/delete-space.html?parent=1');
 const trigger=page.getByRole('button',{name:'Supprimer ce Context Space',exact:true});
 const assign=await page.getByRole('button',{name:'Assigner à un domaine',exact:true}).boundingBox();
 const deletion=await trigger.boundingBox();
 const rename=await page.getByRole('button',{name:'Renommer le Space',exact:true}).boundingBox();
 expect(Math.abs(rename!.x-deletion!.x)).toBeLessThan(2);
 expect(deletion!.y).toBeGreaterThan(assign!.y+assign!.height);
 const dialog=page.getByRole('dialog',{name:'Supprimer ce Context Space',exact:true});
 for(const close of ['X','Escape','outside','Annuler']){
  await trigger.click();await expect(dialog).toBeVisible();
  const box=await dialog.boundingBox();expect(box!.width).toBeLessThanOrEqual(480);
  expect(Math.abs(box!.x+box!.width/2-384)).toBeLessThan(2);
  expect(Math.abs(box!.y+box!.height/2-512)).toBeLessThan(2);
  await expect(dialog.getByRole('button',{name:'Supprimer définitivement',exact:true})).toBeDisabled();
  if(close==='X')await dialog.getByRole('button',{name:'Fermer la fenêtre'}).click();
  else if(close==='Escape')await page.keyboard.press('Escape');
  else if(close==='outside')await page.mouse.click(box!.x-8,box!.y+12);
  else await dialog.getByRole('button',{name:'Annuler',exact:true}).click();
  await expect(dialog).toHaveCount(0);expect(deletions).toBe(0);
 }
 await page.setViewportSize({width:375,height:812});await trigger.click();
 const box=await dialog.boundingBox();expect(box!.x).toBeGreaterThanOrEqual(16);expect(box!.x+box!.width).toBeLessThanOrEqual(359);
 expect(await dialog.evaluate(node=>node.scrollWidth<=node.clientWidth)).toBe(true);
 await dialog.getByLabel('Nom du Space à supprimer').fill('Space à supprimer');
 await dialog.getByRole('button',{name:'Supprimer définitivement',exact:true}).click();
 await expect(page).toHaveURL(/\/domains\/00000000-0000-0000-0000-000000000002$/);
 await expect(page.getByRole('heading',{name:'Compétences',exact:true})).toBeVisible();expect(deletions).toBe(1);
});
