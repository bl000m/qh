import {test,expect} from '@playwright/test';

test('recipient clarifies and follows up in one temporary conversation',async({page})=>{
 page.on('pageerror',error=>{throw error;});
 const requests:any[]=[];let failed=false;let releaseFirst:(()=>void)|undefined;
 await page.setViewportSize({width:390,height:740});
 const replies=['Ti interessano gli obiettivi o il programma?','1. Imparare Python.\n2. Collaborare in coppia.','Il secondo obiettivo riguarda gli esercizi in coppia.'];
 await page.route('**/api/guest/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/session'))return route.fulfill({json:{name:'Progetto',can_ask:true,expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});
  if(path.endsWith('/provider'))return route.fulfill({json:{enabled:true,simulated:false}});
  if(path.endsWith('/logout'))return route.fulfill({status:204});
  if(path.endsWith('/ask')){
   const body=route.request().postDataJSON();requests.push(body);
   if(requests.length===1)await new Promise<void>(resolve=>{releaseFirst=resolve;});
   if(body.question==='Riprova'&&!failed){failed=true;return route.fulfill({status:503,json:{detail:'unavailable'}});}
   return route.fulfill({json:{answer:replies[requests.length-1]??'Informazione disponibile.',insufficient_context:true,simulated:false}});
  }
  return route.fulfill({status:404});
 });
 await page.goto('/tests/fixtures/guest-understanding.html');
 const field=page.getByLabel('Votre question',{exact:true});
 for(const [index,question] of ['Mi dai i dati del progetto?','Gli obiettivi.','Puoi sviluppare il secondo?'].entries()){
  await field.fill(question);await field.press('Enter');
  if(index===0){await expect(page.getByRole('status')).toHaveText('Réponse en cours…');await expect(field).toBeVisible();releaseFirst?.();}
  await expect(page.locator('.guest-answer')).toHaveCount(index+1);
  await expect(field).toHaveValue('');
 }
 expect(requests[0].history).toEqual([]);
 expect(requests[1].history).toEqual([{role:'user',content:'Mi dai i dati del progetto?'},{role:'assistant',content:replies[0]}]);
 expect(requests[2].history.at(-1)).toEqual({role:'assistant',content:replies[1]});
 await expect(page.locator('.guest-question')).toHaveCount(3);
 await expect(page.locator('body')).not.toContainText('Les informations autorisées ne suffisent pas');
 await field.fill('Riga uno');await field.press('Shift+Enter');await field.press('x');
 await expect(field).toHaveValue('Riga uno\nx');expect(requests).toHaveLength(3);
 await field.fill('Riprova');await field.press('Enter');await expect(page.getByRole('button',{name:'Réessayer',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Réessayer',exact:true}).click();await expect(page.locator('.guest-answer')).toHaveCount(4);
 await expect(page.locator('.guest-question')).toHaveCount(4);expect(requests[4]).toEqual(requests[3]);
 for(let index=0;index<4;index++){await field.fill('Approfondisci '+index);await field.press('Enter');await expect(page.locator('.guest-answer')).toHaveCount(5+index);}
 expect(requests.at(-1).history).toHaveLength(12);
 await expect.poll(()=>page.locator('.guest-messages').evaluate(el=>el.scrollHeight-el.scrollTop-el.clientHeight)).toBeLessThan(3);
 expect(await field.evaluate(el=>el.getBoundingClientRect().bottom<=window.innerHeight)).toBe(true);
 expect(requests.at(-1).history[0].content).toBe('Gli obiettivi.');
 await page.getByRole('button',{name:'Fermer mon accès',exact:true}).click();await expect(page.locator('.guest-question,.guest-answer')).toHaveCount(0);
});
