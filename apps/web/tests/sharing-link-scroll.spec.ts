import {test,expect} from '@playwright/test';

test('new invitation focuses its link and scrolls only the dialog after loading',async({page})=>{
 let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>release=resolve);let requested=false;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:[]});
  if(path.endsWith('/invitations')&&route.request().method()==='GET')return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews'))return route.fulfill({json:{id:'preview',fingerprint:'safe',policy:route.request().postDataJSON(),payload:{format:'qh.disclosure/1',items:[{reference:'R1',text:'Authorized synthetic information.'}]},report:{risks:[],exclusions:[],masks:[],anchors:[]}}});
  if(path.endsWith('/approve'))return route.fulfill({json:{snapshot_id:'snapshot'}});
  if(path.endsWith('/invitations')){requested=true;await gate;return route.fulfill({json:{invitation_token:'synthetic-only'}});}
  return route.fulfill({status:404});
 });
 await page.setViewportSize({width:1100,height:600});
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const dialog=page.getByRole('dialog');await dialog.getByLabel('Email du destinataire',{exact:true}).fill('recipient@example.test');
 await expect(dialog.getByRole('button',{name:'Créer l’invitation',exact:true})).toBeEnabled();
 await page.evaluate(()=>{document.body.style.minHeight='2400px';window.scrollTo(0,200);});
 await dialog.getByRole('button',{name:'Créer l’invitation',exact:true}).click();await expect.poll(()=>requested).toBe(true);
 const before=await dialog.evaluate(el=>el.scrollTop),outer=await page.evaluate(()=>scrollY);
 const link=dialog.getByLabel('Lien d’invitation',{exact:true});await expect(link).toHaveCount(0);
 await page.waitForTimeout(100);expect(await dialog.evaluate(el=>el.scrollTop)).toBe(before);
 release();await expect(link).toHaveValue(/synthetic-only/);await expect(link).toBeFocused();
 await expect.poll(()=>dialog.evaluate(el=>el.scrollTop)).toBeGreaterThan(before);
 const box=(await link.boundingBox())!,modal=(await dialog.boundingBox())!,footer=(await dialog.locator('.sharing-footer').boundingBox())!;
 expect(box.y).toBeGreaterThanOrEqual(modal.y);expect(box.y+box.height).toBeLessThanOrEqual(footer.y);
 expect(await page.evaluate(()=>scrollY)).toBe(outer);
});
