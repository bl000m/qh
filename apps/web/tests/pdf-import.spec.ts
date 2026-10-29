import {test,expect} from '@playwright/test';
// One UI path, offline HTTP. Real parsing/SQL/provenance/authorization are checked in API tests.
test('PDF import, explicit memorization, original Sources and per-document sharing consent',async({page})=>{
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',revision='00000000-0000-0000-0000-000000000007';
 let imported=false,memorized=false,uploads=0,calls=0,requests=0;const messages:any[]=[];const previews:Record<string,unknown>[]=[];
 const intake={id:owner,kind:'document',role:'user',text:null,context:null,name:'demo.pdf',source_revision_id:revision,document_turns:[{id:owner+':page:1',speaker:'document demo.pdf, page 1 (unverified source)',text:'Un atelier est proposé.'}]};
 const current={id:revision,context_space_id:scope,version:1,intake_ids:[owner],source_revision_id:revision,revision_ids:[revision],created_at:'2026-10-29T10:00:00Z'};
 const state=()=>({context_id:scope,state:memorized?'current':imported?'pending':'empty',pending_count:imported&&!memorized?1:0,intake:imported?[intake,...messages]:[],current:memorized?current:null,understanding:[],recap:memorized?{version_id:revision,title:'Atelier',text:'Un atelier est proposé.',support_revision_ids:[revision]}:null});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'PDF Space',status:'active',created_at:current.created_at,updated_at:current.created_at}});
  if(path.endsWith('/open'))return route.fulfill({json:{}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:!memorized,model:memorized?null:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:memorized?null:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.9'}});
  if(path.includes('/workspace/documents/')&&route.request().method()==='PUT'){
   uploads++;expect(route.request().headers()['content-type']).toBe('application/pdf');expect(route.request().postDataBuffer()?.toString()).toBe('%PDF-offline-ui');
   imported=true;return route.fulfill({json:state()});
  }
  if(path.endsWith('/workspace/intake')){messages.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){requests++;messages.push({id:crypto.randomUUID(),kind:'message',role:'assistant',text:'Voici le document original.',name:null,context:null,reply_to:messages.at(-1).id,documents:[{source_revision_id:revision,filename:'demo.pdf'}]});return route.fulfill({json:{state:'completed'}});}
  if(path.endsWith('/workspace/consolidate')){calls++;memorized=true;return route.fulfill({json:state()});}
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:imported?[{source_revision_id:revision,filename:'demo.pdf'}]:[]});
  if(path.includes('/workspace/documents/'))return route.fulfill({body:'%PDF-offline-ui',headers:{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="demo.pdf"'}});
  if(path.endsWith('/invitations'))return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){previews.push(route.request().postDataJSON());return route.fulfill({status:503,json:{detail:'offline preview'}});}
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 await expect(page.getByRole('button',{name:'Joindre un document'})).toBeEnabled();
 await page.locator('input[type=file]').first().setInputFiles({name:'demo.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-offline-ui')});
 await expect(page.locator('.workspace-feedback').getByRole('status')).toContainText('demo.pdf conservé');expect(uploads).toBe(1);expect(calls).toBe(0);
 const direct=page.waitForEvent('download');await page.locator('.workspace-message').getByRole('button',{name:'Télécharger l’original'}).click();expect((await direct).suggestedFilename()).toBe('demo.pdf');
 await page.getByRole('button',{name:'Mémoriser',exact:true}).click();await expect(page.getByRole('heading',{name:'Atelier',exact:true})).toBeVisible();expect(calls).toBe(1);
 await expect(page.getByText('L’IA est indisponible pour ce contexte.',{exact:true})).toBeVisible();
 await page.getByRole('textbox',{name:'Ton message',exact:true}).fill('Télécharge le PDF original demo.pdf');
 await page.getByRole('button',{name:'Envoyer',exact:true}).click();await expect(page.locator('.workspace-message.assistant')).toContainText('Voici le document original.');expect(requests).toBe(1);expect(calls).toBe(1);
 const recovered=page.waitForEvent('download');await page.locator('.workspace-message.assistant').getByRole('button',{name:'Télécharger l’original'}).click();expect((await recovered).suggestedFilename()).toBe('demo.pdf');
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const settings=page.getByRole('dialog',{name:'Paramètres du Space'});await settings.getByText('Sources et traçabilité',{exact:true}).click();
 await settings.getByText('Consulter le texte extrait',{exact:true}).click();await expect(settings.getByText('Page 1',{exact:true})).toBeVisible();
 const download=page.waitForEvent('download');await settings.getByRole('button',{name:'Télécharger l’original'}).click();expect((await download).suggestedFilename()).toBe('demo.pdf');
 await settings.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 await page.getByRole('button',{name:'Partager',exact:true}).click();const sharing=page.getByRole('dialog',{name:'Partager ce contexte'});
 await sharing.getByRole('textbox',{name:'Email du destinataire'}).fill('recipient@example.test');
 await expect.poll(()=>previews.length).toBeGreaterThan(0);expect(previews.at(-1)?.original_documents).toEqual([]);
 await sharing.getByText('Confidentialité avancée',{exact:true}).click();
 await sharing.getByRole('checkbox',{name:'Autoriser le téléchargement de demo.pdf'}).check();
 await expect.poll(()=>previews.at(-1)?.original_documents).toEqual([revision]);
 await expect(sharing.getByText(/Un original peut contenir des informations exclues/)).toBeVisible();
});
