import {test,expect} from '@playwright/test';
test.use({locale:'fr-FR'});

test('original sharing default, exact selection, preview and authorized recipient library',async({page})=>{
 await page.setViewportSize({width:1664,height:1024});
 const id='00000000-0000-0000-0000-000000000001';
 const docs=[{source_revision_id:'00000000-0000-0000-0000-000000000011',display_name:'CV Mathia Pagani',filename:'CV Mathia_Pagani.pdf'},
 {source_revision_id:'00000000-0000-0000-0000-000000000012',display_name:'Contrat de travail',filename:'contrat finale.pdf'},
 {source_revision_id:'00000000-0000-0000-0000-000000000013',display_name:'Entretien professionnel 2026',filename:'Synanto_Entretien_2026.pdf'}];
 let selected:string[]=[],approved:string[]=[],lastBody:any;let blocked=false,holdPreview=false;let releasePreview:(()=>void)|undefined;
 const recap={title:'Parcours professionnel',text:'Parcours professionnel, compétences et évolution de carrière. Les informations restent filtrées selon les autorisations du partage.'};
 const capture=async(name:string)=>{if(process.env.QH_SHARE_PREVIEW)await page.screenshot({path:process.env.QH_SHARE_PREVIEW+'/'+name+'.png'});};
 await page.context().route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:docs});
  if(path.endsWith('/invitations')&&route.request().method()==='GET')return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){lastBody=route.request().postDataJSON();selected=[...lastBody.original_documents];if(holdPreview)await new Promise<void>(resolve=>{releasePreview=resolve;});return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:lastBody,payload:{format:'qh.disclosure/1',name:'RH',recap,items:[{reference:'R1',text:'Parcours professionnel.'}]},report:{risks:[],exclusions:[],masks:[],anchors:[]}}});}
  if(path.endsWith('/approve')){approved=[...selected];return route.fulfill({json:{snapshot_id:id}});}
  if(path.endsWith('/invitations'))return route.fulfill({json:{id,snapshot_id:id,expires_at:'2030-01-01T00:00:00Z',invitation_token:'offline-token'}});
  if(path.endsWith('/guest/session'))return route.fulfill({json:{name:'RH',recap,can_ask:true,expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});
  if(path.endsWith('/guest/provider'))return route.fulfill({json:{enabled:false}});
  if(path.endsWith('/guest/documents'))return route.fulfill({json:blocked?[]:docs.filter(doc=>approved.includes(doc.source_revision_id))});
  if(path.includes('/guest/documents/'))return route.fulfill({body:'%PDF-synthetic',headers:{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="CV Mathia_Pagani.pdf"'}});
  if(path.endsWith('/guest/ask'))return route.fulfill({json:{answer:'Voici le document original.',insufficient_context:false,simulated:false,documents:[docs[0]]}});
  return route.fulfill({status:404});
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const dialog=page.getByRole('dialog'),toggle=dialog.getByRole('switch'),create=dialog.locator('.sharing-footer button').last();
 await expect(toggle).toHaveAttribute('aria-checked','false');await expect(dialog.locator('.originals-choice')).toHaveCount(0);
 await dialog.getByLabel('Email du destinataire',{exact:true}).fill('destinataire@example.test');await expect(create).toBeEnabled();expect(lastBody.original_documents).toEqual([]);
 const preview=dialog.getByRole('region',{name:'Documents accessibles'});await expect(preview).toContainText('Aucun');await capture('01-private');
 await toggle.click();await dialog.getByRole('region',{name:'Documents originaux',exact:true}).getByRole('button',{name:'Tous les documents actuels',exact:true}).click();await expect.poll(()=>selected.length).toBe(3);
 await dialog.getByRole('button',{name:'Choisir les documents',exact:true}).click();holdPreview=true;await dialog.locator('.originals-choice').filter({hasText:'Contrat de travail'}).getByRole('checkbox').uncheck();
 await expect(create).toBeDisabled();await expect(preview).toContainText('2 sur 3');await expect(preview).not.toContainText('Contrat de travail');
 await expect.poll(()=>selected.length).toBe(2);holdPreview=false;releasePreview?.();await expect(create).toBeEnabled();expect(selected).toEqual([docs[0].source_revision_id,docs[2].source_revision_id]);await capture('02-selection');
 await create.click();await expect(dialog.getByLabel('Lien d’invitation')).toBeVisible();expect(approved).toEqual(selected);
 await dialog.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();await expect(dialog).toHaveCount(0);
 await page.goto('/tests/fixtures/guest-understanding.html');
 const library=page.getByRole('region',{name:'Documents autorisés'});await expect(library.locator('.guest-document-row')).toHaveCount(2);await expect(library).not.toContainText('Contrat');
 await expect(page.locator('body')).not.toContainText(docs[1].source_revision_id);
 const search=library.getByRole('searchbox');await search.fill('Synanto');await expect(library.locator('.guest-document-row')).toHaveCount(1);await search.fill('');
 const download=page.waitForEvent('download');await library.getByRole('button',{name:'Télécharger CV Mathia Pagani',exact:true}).click();const saved=await download;expect(await saved.failure()).toBeNull();const stream=await saved.createReadStream();let bytes='';for await(const chunk of stream!)bytes+=chunk.toString();expect(bytes).toBe('%PDF-synthetic');
 await page.getByLabel('Votre question',{exact:true}).fill('Télécharge le CV Mathia Pagani');await page.getByRole('button',{name:'Envoyer',exact:true}).click();await expect(page.locator('.guest-answer')).toContainText('Télécharger');await capture('03-recipient');
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 blocked=true;await page.reload();await expect(library).toHaveCount(0);
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();await expect(toggle).toHaveAttribute('aria-checked','false');await page.mouse.click(1,1);await expect(dialog).toHaveCount(0);
});
