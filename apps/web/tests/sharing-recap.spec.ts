import {test,expect} from '@playwright/test';

test('approved recap is identical in preview and sidebar; restricted recap has an explicit safe limit',async({page})=>{
 const id='00000000-0000-0000-0000-000000000001';let restricted=false,snapshot:any;
 const summary={title:'Parcours professionnel proposé',text:'Giulia souhaiterait évoluer vers l’architecture logicielle. Cette orientation reste une intention, sans décision contractuelle.'};
 const documents=[{title:'Expérience déclarée dans le CV',text:'Giulia décrit son expérience du développement.'},{title:'Orientation professionnelle envisagée',text:'Giulia souhaiterait évoluer, sans décision contractuelle.'}];
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents')||path.endsWith('/guest/documents'))return route.fulfill({json:[]});
  if(path.endsWith('/invitations')&&route.request().method()==='GET')return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){const body=route.request().postDataJSON();return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:body,payload:{format:'qh.disclosure/1',name:'RH',items:[{reference:'R1',text:'Une orientation reste à discuter.'}],...(!restricted&&{recap:summary,document_recaps:documents})},report:{risks:[],exclusions:[],masks:[],recap_status:restricted?'restricted':'available'}}});}
  if(path.endsWith('/approve')){snapshot=structuredClone({recap:summary,document_recaps:documents});return route.fulfill({json:{snapshot_id:id}});}
  if(path.endsWith('/invitations'))return route.fulfill({json:{id,snapshot_id:id,expires_at:'2030-01-01T00:00:00Z',invitation_token:'offline-token'}});
  if(path.endsWith('/guest/session'))return route.fulfill({json:{name:'RH',can_ask:true,recap:restricted?null:snapshot.recap,document_recaps:restricted?[]:snapshot.document_recaps,expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});
  if(path.endsWith('/guest/provider'))return route.fulfill({json:{enabled:false}});
  throw Error('Unexpected request: '+path);
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 await page.getByLabel('Email du destinataire',{exact:true}).fill('invite@example.test');
 const preview=page.getByLabel('Aperçu du contexte partagé');await expect(preview).toContainText(summary.title);await expect(preview).toContainText(summary.text);for(const doc of documents)await expect(preview).toContainText(doc.text);await expect(preview).not.toContainText('Conditions du contrat');
 await page.getByRole('button',{name:'Créer l’invitation',exact:true}).click();await expect(page.getByLabel('Lien d’invitation')).toBeVisible();
 await page.goto('/tests/fixtures/guest-understanding.html');await expect(page.locator('.guest-context')).toContainText(summary.title);await expect(page.locator('.guest-context')).toContainText(summary.text);for(const doc of snapshot.document_recaps)await expect(page.locator('.guest-context')).toContainText(doc.text);await expect(page.locator('.guest-context')).not.toContainText('Conditions du contrat');
 restricted=true;await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();await page.getByLabel('Email du destinataire',{exact:true}).fill('invite@example.test');
 await expect(preview).toContainText('Aucun résumé partiel vérifiable n’est disponible sans nouvelle analyse.');await expect(preview).not.toContainText(summary.text);
 await page.goto('/tests/fixtures/guest-understanding.html');await expect(page.locator('.guest-context')).toContainText('Aucun résumé n’a été autorisé pour cet accès.');await expect(page.locator('.guest-context')).not.toContainText(summary.title);
});
