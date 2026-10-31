import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('persisted owner recap crosses preview and guest UI with unchanged PDF knowledge',async({page})=>{
 test.skip(!process.env.QH_RECAP_BROWSER_EVIDENCE,'Requires outputs of the isolated SQL/native/OTP integration test.');
 const evidence=JSON.parse(readFileSync(process.env.QH_RECAP_BROWSER_EVIDENCE!,'utf8'));
 const recap=evidence.previews[0].payload.recap;
 expect(evidence.owner.recap.text).toBe(recap.text);
 for(const preview of evidence.previews)expect(preview.payload.recap).toEqual(recap);
 for(const session of evidence.sessions)expect(session.recap).toEqual(recap);
 let count=0;
 await page.route('**/tests/fixtures/**',async route=>{
  const response=await route.fetch();
  const body=(await response.text()).replaceAll('00000000-0000-0000-0000-000000000001',evidence.owner.context_id);
  await route.fulfill({response,body}); // Bind existing UI harnesses to the real test Space.
 });
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:evidence.documents});
  if(path.endsWith('/workspace'))return route.fulfill({json:evidence.owner});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:false,enabled:false}});
  if(path.endsWith('/invitations'))return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){
   const body=route.request().postDataJSON();count=body.documents.length;
   const captured=evidence.previews[count];
   // Keep real backend payload/report; adapt only the replay's UI form values.
   return route.fulfill({json:{...captured,policy:{...captured.policy,recipient_email:body.recipient_email,purpose:body.purpose,expires_at:body.expires_at}}});
  }
  if(path.endsWith('/guest/session'))return route.fulfill({json:evidence.sessions[count]});
  if(path.endsWith('/guest/documents'))return route.fulfill({json:evidence.documents.slice(0,count)});
  if(path.endsWith('/guest/provider'))return route.fulfill({json:{enabled:false}});
  throw Error('Unexpected request '+path); // No provider or alternative recap.
 });
 await page.goto('/tests/fixtures/workspace-loading.html');
 await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 await expect(page.getByRole('complementary',{name:'Compréhension',exact:true})).toContainText(recap.text);
 await page.goto('/tests/fixtures/sharing-simple.html');
 await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 await page.getByLabel('Email du destinataire',{exact:true}).fill('clement@example.test');
 const preview=page.getByLabel('Aperçu du contexte partagé');
 const originals=page.getByRole('region',{name:'Documents originaux accessibles',exact:true});
 for(let selected=0;selected<=2;selected++){
  if(selected)await originals.getByRole('checkbox').nth(selected-1).check();
  await expect.poll(()=>count).toBe(selected);
  await expect(page.getByRole('region',{name:'Documents accessibles',exact:true})).toContainText(`${selected} sur 2`);
  await expect(preview).toContainText(recap.title);await expect(preview).toContainText(recap.text);
  await expect(preview).not.toContainText('Le résumé général n’est pas disponible');
 }
 await page.goto('/tests/fixtures/guest-understanding.html');
 await expect(page.locator('.guest-context')).toContainText(recap.title);
 await expect(page.locator('.guest-context')).toContainText(recap.text);
});
