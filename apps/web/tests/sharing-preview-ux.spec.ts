import {test,expect} from '@playwright/test';

const id='00000000-0000-0000-0000-000000000001';
const docs=['CV','Contrat'].map((name,i)=>({source_revision_id:`00000000-0000-0000-0000-00000000001${i}`,filename:name+'.pdf',display_name:name}));
const recap={title:'Compréhension canonique',text:'Profil et décisions déjà mémorisés, dans le périmètre autorisé.'};

test('valid email loads canonical recap; pending download permissions never replace it',async({page})=>{
 let hold=false,release:()=>void=()=>{},body:any,requests=0;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:docs});
  if(path.endsWith('/invitations'))return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){
   body=route.request().postDataJSON();requests++;
   if(hold)await new Promise<void>(resolve=>{release=resolve;});
   return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:{...body,original_documents:[...body.documents].sort()},payload:{format:'qh.disclosure/1',name:'RH synthétique',recap,semantic_document_count:2,items:[{reference:'R1',text:'Connaissance stable des deux sources.'}]},report:{risks:[],exclusions:[],masks:[]}}});
  }
  throw Error('Unexpected request: '+path); // No ask/paid inference in this fixture.
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const dialog=page.getByRole('dialog'),card=dialog.locator('.sharing-preview-card');
 const library=dialog.getByRole('region',{name:'Documents accessibles',exact:true});
 const selection=dialog.getByRole('region',{name:'Documents originaux',exact:true});
 const create=dialog.locator('.sharing-footer button').last();
 await expect(library).toContainText('Aucun');expect(requests).toBe(0);
 await dialog.getByLabel('Email du destinataire',{exact:true}).fill('recipient@example.test');
 await expect(card).toContainText(recap.text);await expect(create).toBeEnabled();
 await expect(card).not.toContainText('document(s)');await expect(card).not.toContainText('Indiquez le destinataire');
 await card.locator('.shared-recap-component').evaluate(el=>el.setAttribute('data-retained','yes'));
 await selection.getByRole('switch',{name:'Autoriser l’accès aux documents originaux',exact:true}).click();
 hold=true;await selection.locator('.originals-choice').filter({hasText:'Contrat'}).getByRole('checkbox').check();
 await expect.poll(()=>requests).toBe(2);await expect(create).toBeDisabled();
 await expect(library).toContainText('1 sur 2');await expect(card).toContainText(recap.text);
 await expect(card.locator('.shared-recap-component')).toHaveAttribute('data-retained','yes');
 hold=false;release();await expect(create).toBeEnabled();
 await selection.locator('.originals-choice').filter({hasText:'CV'}).getByRole('checkbox').check();await expect(create).toBeEnabled();
 await expect.poll(()=>body.documents.length).toBe(2);await expect(library).toContainText('2 sur 2');
 await expect(card).toContainText(recap.text);await expect(card.locator('.shared-recap-component')).toHaveAttribute('data-retained','yes');
 const rows=dialog.locator('.sharing-permission');await expect(rows).toHaveCount(2);
 const metrics=await rows.evaluateAll(elements=>elements.map(el=>{const s=getComputedStyle(el),box=el.getBoundingClientRect(),input=el.querySelector('input')!,i=getComputedStyle(input);return {background:s.backgroundColor,border:s.border,borderRadius:s.borderRadius,padding:s.padding,font:s.font,gap:s.gap,width:box.width,height:box.height,checkbox:[i.width,i.height,i.margin,i.borderRadius]};}));
 expect(metrics[0]).toEqual(metrics[1]);expect(metrics[0].background).not.toBe('rgba(0, 0, 0, 0)');
 await expect(rows.first().getByRole('checkbox')).toBeChecked();await expect(rows.first().getByRole('checkbox')).toBeDisabled();
 const optional=rows.last().getByRole('checkbox');await expect(optional).not.toBeChecked();await expect(optional).toBeEnabled();
 await expect(rows.last()).not.toContainText('Toujours inclus');
 await optional.check();await expect.poll(()=>body.allow_update_proposals).toBe(true);await expect(card).toContainText(recap.text);
 await optional.uncheck();await expect.poll(()=>body.allow_update_proposals).toBe(false);
 await dialog.getByLabel('Email du destinataire',{exact:true}).fill('invalid');await expect(card).not.toContainText(recap.text);
});

test('valid email loading failure is distinct from missing email and guarded recap',async({page})=>{
 let failing=true;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:[]});
  if(path.endsWith('/invitations'))return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){
   if(failing)return route.fulfill({status:503});
   const body=route.request().postDataJSON();
   return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:body,payload:{format:'qh.disclosure/1',recap,items:[{reference:'R1',text:'Authorized.'}]},report:{risks:[],exclusions:[],masks:[]}}});
  }
  throw Error('Unexpected request');
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const dialog=page.getByRole('dialog'),card=dialog.locator('.sharing-preview-card');
 await dialog.getByLabel('Email du destinataire',{exact:true}).fill('recipient@example.test');
 await expect(card).toContainText('L’aperçu n’a pas pu être chargé');
 await expect(card).not.toContainText('Indiquez le destinataire');await expect(card).not.toContainText('Le résumé général n’est pas disponible');
 failing=false;await dialog.getByRole('button',{name:'Réessayer',exact:true}).click();await expect(card).toContainText(recap.text);
});
