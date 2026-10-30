import {test,expect} from '@playwright/test';
// One offline UI path; real persistence/authorization are verified separately.
test('document naming, horizontal library, lookup and private original download',async({page})=>{
 await page.setViewportSize({width:1664,height:941});
 const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',revision='00000000-0000-0000-0000-000000000007',domain='00000000-0000-0000-0000-000000000008';
 const now=new Date();now.setHours(10,24,0,0);
 const pdf=Buffer.alloc(321000,32);pdf.write('%PDF-offline-ui');
 let uploaded=false,uploads=0,analysis=0;const messages:any[]=[];
 const intake={id:owner,kind:'document',role:'user',text:null,context:null,name:'CV Mathia_Pagani.pdf',display_name:'',size_bytes:pdf.length,created_at:now.toISOString(),source_revision_id:revision,document_turns:[{id:owner+':page:1',speaker:'document, page 1',text:'Texte synthétique.'}]};
 const catalog=()=>uploaded?[
  {source_revision_id:revision,filename:intake.name,display_name:intake.display_name,size_bytes:pdf.length,created_at:intake.created_at},
  {source_revision_id:domain,filename:'contrat_finale.pdf',display_name:'contrat de travail',size_bytes:845000,created_at:'2026-03-12T12:00:00Z'},
  {source_revision_id:scope,filename:'Entretien_2026.pdf',display_name:'entretien professionnel 2026',size_bytes:1200000,created_at:'2026-02-03T12:00:00Z'},
  ...[1,2,3].map((n)=>({source_revision_id:'10000000-0000-0000-0000-00000000000'+n,filename:'Annexe_'+n+'.pdf',size_bytes:20000,created_at:'2025-01-01T12:00:00Z'}))]:[];
 const state=()=>({context_id:scope,state:uploaded?'pending':'empty',pending_count:uploaded?1:0,intake:uploaded?[intake,...messages]:[],current:null,understanding:[],recap:null});
 const preview=async(name:string)=>{if(process.env.QH_DOC_PREVIEW){await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.effect?.getComputedTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:process.env.QH_DOC_PREVIEW+'/'+name+'.png'});}};
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/environment')return route.fulfill({json:{version:1,domains:[{id:domain,name:'Travail',description:''}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},space_descriptions:{},usage:{}}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:{id:scope,owner_id:owner,name:'Context Space',status:'active',created_at:now.toISOString(),updated_at:now.toISOString()}});
  if(path.endsWith('/open'))return route.fulfill({json:{}});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:{automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:Date.now()/1000+3600,remaining_calls:null,remaining_usd:'4.9'}});
  if(path.includes('/workspace/documents/')&&route.request().method()==='PUT'){
   uploads++;expect(route.request().postDataBuffer()?.length).toBe(pdf.length);
   intake.display_name=decodeURIComponent(route.request().headers()['x-document-display-name']);
   expect(intake.display_name).toBe('Profil Mathia Pagani');uploaded=true;return route.fulfill({json:state()});
  }
  if(path.endsWith('/workspace/intake')){messages.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){messages.push({id:crypto.randomUUID(),kind:'message',role:'assistant',text:'Voici le document original.',created_at:now.toISOString(),name:null,context:null,reply_to:messages.at(-1).id,documents:[catalog()[0]]});return route.fulfill({json:{state:'completed'}});}
  if(path.endsWith('/workspace/consolidate')){analysis++;return route.fulfill({status:503,json:{detail:'No inference in this test'}});}
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:catalog()});
  if(path.includes('/workspace/documents/'))return route.fulfill({body:pdf,headers:{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="CV Mathia_Pagani.pdf"'}});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 await expect(page.getByRole('button',{name:'Joindre un document',exact:true})).toBeEnabled();
 await page.locator('input[type=file]').first().setInputFiles({name:intake.name,mimeType:'application/pdf',buffer:pdf});
 const naming=page.getByRole('dialog',{name:'Nommer le document',exact:true});
 await expect(naming.getByRole('textbox',{name:'Nom du document',exact:true})).toHaveValue('CV Mathia Pagani');
 expect(uploads).toBe(0);await preview('02-name');
 await naming.getByRole('textbox').fill('Profil Mathia Pagani');await naming.getByRole('button',{name:'Continuer',exact:true}).click();
 await expect(naming).toHaveCount(0);
 const upload=page.locator('.document-chat-entry').first();await expect(upload).toContainText('Document ajouté au contexte');
 await expect(upload).toContainText('Profil Mathia Pagani');await expect(upload).toContainText('Nom du fichier original : CV Mathia_Pagani.pdf');
 await expect(upload.getByRole('button')).toHaveCount(0);expect(analysis).toBe(0);await preview('03-upload');
 const toggle=page.getByRole('button',{name:'Documents',exact:true});await toggle.click();
 const library=page.getByRole('region',{name:'Documents du contexte',exact:true});await expect(library).toBeVisible();await expect(toggle).toHaveAttribute('aria-expanded','true');
 await expect(library.locator('.document-file-card')).toHaveCount(6);
 const panelBox=(await library.boundingBox())!,height=panelBox.height;
 const cardBox=(await library.locator('.document-file-card').first().boundingBox())!;expect(cardBox.y+cardBox.height).toBeLessThanOrEqual(panelBox.y+height);
 const tops=await library.locator('.document-file-card').evaluateAll(nodes=>nodes.map(n=>Math.round(n.getBoundingClientRect().top)));expect(new Set(tops).size).toBe(1);
 await library.getByRole('button',{name:'Documents suivants',exact:true}).click();await expect.poll(()=>library.locator('.documents-track').evaluate(n=>n.scrollLeft)).toBeGreaterThan(0);
 const search=library.getByRole('searchbox',{name:'Rechercher un document',exact:true});
 await search.fill('profil');await expect(library.locator('.document-file-card')).toHaveCount(1);
 await search.fill('CV Mathia_Pagani.pdf');await expect(library.locator('.document-file-card')).toHaveCount(1);
 expect((await library.boundingBox())!.height).toBe(height);
 const download=page.waitForEvent('download');await library.getByRole('button',{name:'Télécharger Profil Mathia Pagani',exact:true}).click();expect((await download).suggestedFilename()).toBe(intake.name);
 await library.getByRole('button',{name:'Fermer les documents',exact:true}).click();await expect(toggle).toHaveAttribute('aria-expanded','false');
 await page.getByRole('textbox',{name:'Ton message',exact:true}).fill('Télécharge le PDF Profil Mathia Pagani');await page.getByRole('button',{name:'Envoyer',exact:true}).click();
 const reply=page.locator('.document-chat-entry').filter({hasText:'Voici le document original.'});await expect(reply).toBeVisible();
 await expect(reply).toContainText('CV Mathia_Pagani.pdf');await expect(reply).toContainText('PDF · 321 Ko');await preview('01-download');
 const recovered=page.waitForEvent('download');await reply.getByRole('button',{name:'Télécharger',exact:true}).click();expect((await recovered).suggestedFilename()).toBe(intake.name);
 await toggle.click();await expect(library).toBeVisible();await preview('04-panel');
 await toggle.click();await expect(library).toHaveCount(0);expect(analysis).toBe(0);
 // Responsive essentials: one row remains bounded and chat stays available.
 await page.setViewportSize({width:390,height:844});await toggle.click();await expect(library).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect((await library.boundingBox())!.height).toBeLessThan(260);await expect(page.getByRole('textbox',{name:'Ton message'})).toBeVisible();
});
