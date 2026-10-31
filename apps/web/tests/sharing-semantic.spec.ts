import {test,expect} from '@playwright/test';

test('original downloads are independent of unified knowledge and its recap',async({page})=>{
 const id='00000000-0000-0000-0000-000000000001';
 const docs=['CV personnalisé','Contrat de travail','Entretien professionnel'].map((name,i)=>({source_revision_id:`00000000-0000-0000-0000-00000000001${i}`,display_name:name,filename:`source-${i}.pdf`}));
 const recap={title:'Parcours professionnel',text:'Parcours et orientations professionnelles à examiner.'};
 const legacyRecaps=[{title:'PRIVATE DOCUMENT RECAP',text:'PRIVATE DOCUMENT SYNOPSIS'}];
 let body:any,approved:string[]=[],snapshot:any;let paid=0;
 await page.context().route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:docs});
  if(path.endsWith('/invitations')&&route.request().method()==='GET')return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){
   body=route.request().postDataJSON();
   return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:{...body,original_documents:body.documents},payload:{format:'qh.disclosure/1',name:'RH',items:[{reference:'R1',text:'Authorized knowledge from all current documents.'}],recap,document_recaps:legacyRecaps,semantic_document_count:docs.length},report:{risks:[],exclusions:[],masks:[],recap_status:'available'}}});
  }
  if(path.endsWith('/approve')){approved=[...body.documents];snapshot={recap,semantic_document_count:docs.length};return route.fulfill({json:{snapshot_id:id}});}
  if(path.endsWith('/invitations'))return route.fulfill({json:{id,snapshot_id:id,expires_at:'2030-01-01T00:00:00Z',invitation_token:'offline-token'}});
  if(path.endsWith('/guest/session'))return route.fulfill({json:{name:'RH',can_ask:true,...snapshot,document_recaps:legacyRecaps,expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});
  if(path.endsWith('/guest/documents'))return route.fulfill({json:docs.filter(d=>approved.includes(d.source_revision_id))});
  if(path.endsWith('/guest/provider'))return route.fulfill({json:{enabled:false}});
  if(path.endsWith('/ask'))paid++;
  throw Error('Unexpected API request: '+path);
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const selection=page.getByRole('region',{name:'Documents originaux accessibles',exact:true});
 const preview=page.getByLabel('Aperçu du contexte partagé'),create=page.getByRole('button',{name:'Créer l’invitation',exact:true});
 await expect(selection.getByRole('checkbox')).toHaveCount(3);await expect(selection.getByRole('checkbox',{checked:true})).toHaveCount(0);
 await expect(page.getByRole('region',{name:'Informations des documents',exact:true})).toHaveCount(0);
 await expect(page.getByRole('region',{name:'Documents originaux',exact:true})).toHaveCount(0);
 await page.getByLabel('Email du destinataire',{exact:true}).fill('invite@example.test');
 await expect(preview).toContainText(recap.text);await expect(create).toBeEnabled();expect(body.documents).toEqual([]);expect(body.knowledge_scope).toBe('context');expect(body.excluded).toBeUndefined();
 await selection.getByRole('checkbox',{name:'CV personnalisé',exact:true}).check();await expect.poll(()=>body.documents).toEqual([docs[0].source_revision_id]);await expect(preview.locator('.sharing-preview-card')).not.toContainText('document(s)');
 await expect(preview).toContainText(recap.text);expect(body.documents).toEqual([docs[0].source_revision_id]);await expect(preview).not.toContainText('PRIVATE DOCUMENT');
 await selection.getByRole('button',{name:'Tous les documents actuels',exact:true}).click();await expect.poll(()=>body.documents).toEqual(docs.map(d=>d.source_revision_id));
 await expect(preview).toContainText(recap.text);await selection.getByRole('button',{name:'Aucun document',exact:true}).click();await expect.poll(()=>body.documents).toEqual([]);
 await selection.getByRole('checkbox',{name:'CV personnalisé',exact:true}).check();await expect(create).toBeEnabled();await create.click();await expect(page.getByLabel('Lien d’invitation')).toBeVisible();
 expect(approved).toEqual([docs[0].source_revision_id]);docs.push({source_revision_id:'00000000-0000-0000-0000-000000000099',display_name:'Document ultérieur',filename:'later.pdf'});
 await page.goto('/tests/fixtures/guest-understanding.html');await expect(page.locator('.guest-context')).toContainText(snapshot.recap.text);
 await expect(page.locator('.guest-context .shared-recap-component')).toHaveCount(1);await expect(page.locator('.guest-context')).not.toContainText('PRIVATE DOCUMENT');
 const downloads=page.getByRole('region',{name:'Documents autorisés',exact:true});await expect(downloads).toContainText('CV personnalisé');
 await expect(downloads).not.toContainText('Contrat de travail');await expect(downloads).not.toContainText('Document ultérieur');expect(paid).toBe(0);
});
