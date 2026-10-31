import {test,expect} from '@playwright/test';
const id='00000000-0000-0000-0000-000000000001',revision='00000000-0000-0000-0000-000000000002';

for(const advanced of [false,true])test('main owner sharing stays simple, advanced='+advanced,async({page})=>{
 const bodies:any[]=[];let questions=0,approvals=0;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/workspace/documents'))return route.fulfill({json:[]});
  if(path.endsWith('/workspace'))return route.fulfill({json:{context_id:id,state:'current',pending_count:0,intake:[],understanding:[],current:{id:revision,version:1,revision_ids:[revision]},recap:{version_id:revision,title:'Organizzazione di un atelier informatico',text:'PRIVATE-RECAP-CANARY',support_revision_ids:[revision]}}});
  if(path.endsWith('/invitations')&&route.request().method()==='GET')return route.fulfill({json:{items:[]}});
  if(path.endsWith('/sharing/previews')){const body=route.request().postDataJSON();bodies.push(body);
   return route.fulfill({json:{id,fingerprint:'a'.repeat(64),policy:body,payload:{format:'qh.disclosure/1',name:'Atelier informatique',recap:{title:'Organizzazione di un atelier informatico',text:'Linee guida per progettare un atelier.'},items:[{reference:'R1',text:'Utilizzare Jupyter Notebook.'},{reference:'R2',text:'Attività pratiche guidate.'}]},report:{risks:['unassessed_free_text'],exclusions:[],masks:[],anchors:[]}}});}
  if(path.endsWith('/ask')){questions++;return route.fulfill({json:{answer:'Sono previste attività pratiche guidate.',insufficient_context:false,simulated:true}});}
  if(path.endsWith('/approve')){approvals++;if(advanced&&approvals===1)return route.fulfill({status:409,json:{detail:'Context changed'}});expect(route.request().postDataJSON()).toEqual({fingerprint:'a'.repeat(64),exceptions:['unassessed_free_text']});return route.fulfill({json:{snapshot_id:revision}});}
  if(path.endsWith('/invitations'))return route.fulfill({json:{id,snapshot_id:revision,expires_at:'2030-01-01T00:00:00Z',invitation_token:'offline-token'}});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Partager ce contexte',exact:true});await expect(dialog.getByRole('checkbox',{name:/Autoriser les propositions/})).not.toBeChecked();
 await expect(dialog.getByRole('heading',{name:'Organizzazione di un atelier informatico',exact:true})).toHaveCount(0);
 await expect(dialog.getByRole('button',{name:'Vérifier le partage',exact:true})).toHaveCount(0);
 await expect(dialog.getByRole('button',{name:'Exclure cette information',exact:true})).toHaveCount(0);
 await expect(dialog.getByText('Informations susceptibles d’être communiquées',{exact:true})).toHaveCount(0);
 await dialog.getByLabel('Email du destinataire',{exact:true}).fill('invite@example.test');
 expect(await dialog.locator('.sharing-preview').evaluate(el=>el.getBoundingClientRect().left)).toBeGreaterThanOrEqual(await dialog.locator('.sharing-settings').evaluate(el=>el.getBoundingClientRect().right));
 const create=dialog.getByRole('button',{name:'Créer l’invitation',exact:true});await expect(create).toBeEnabled();
 await expect(dialog.getByText('Utilizzare Jupyter Notebook.',{exact:true})).not.toBeVisible();
 expect(questions).toBe(0);expect(approvals).toBe(0);expect(Object.keys(bodies[0]).sort()).toEqual(['allow_update_proposals','documents','expires_at','knowledge_scope','purpose','recipient_email']);
 await expect(dialog.getByRole('heading',{name:'Organizzazione di un atelier informatico',exact:true})).toBeVisible();
 await expect(dialog).not.toContainText('PRIVATE-RECAP-CANARY');expect(bodies[0].allow_update_proposals).toBe(false);
 if(advanced){
  await dialog.getByRole('checkbox',{name:/Autoriser les propositions/}).check();await expect.poll(()=>bodies.at(-1).allow_update_proposals).toBe(true);
  await dialog.getByText('Confidentialité avancée',{exact:true}).click();await dialog.getByText('Consulter les informations communicables',{exact:true}).click();
  await dialog.getByText('Tester une question comme le destinataire',{exact:true}).click();await dialog.getByLabel('Question de test',{exact:true}).fill('Quelles activités ?');await dialog.getByRole('button',{name:'Tester la question',exact:true}).click();
  await expect(dialog.locator('.guest-answer')).toContainText('attività pratiche guidate');expect(questions).toBe(1);
 }
 await expect(create).toBeEnabled();await create.click();
 if(advanced){await dialog.getByRole('button',{name:'Réessayer',exact:true}).click();await expect(create).toBeEnabled();expect(questions).toBe(1);await create.click();}
 await expect(dialog.getByLabel('Lien d’invitation',{exact:true})).toHaveValue(/\/guest#invite=offline-token/);expect(approvals).toBe(advanced?2:1);
});

test('recipient sees authorized recap and chat without requesting a raw snapshot',async({page})=>{
 const requests:string[]=[];
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;requests.push(path);
  if(path==='/api/guest/session')return route.fulfill({json:{name:'Atelier informatique',recap:{title:'Atelier partagé',text:'Un résumé général autorisé.'},can_ask:true,expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});
  if(path==='/api/guest/provider')return route.fulfill({json:{enabled:true,simulated:true}});
  if(path==='/api/guest/ask')return route.fulfill({json:{answer:'Utiliser Jupyter Notebook pour les exercices.',insufficient_context:false,simulated:true}});
  return route.fulfill({status:404,json:{detail:'not available'}});});
 await page.goto('/tests/fixtures/guest-understanding.html');await expect(page.getByRole('heading',{name:'Atelier informatique',exact:true})).toBeVisible();
 await expect(page.getByText('Un résumé général autorisé.',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Proposer une mise à jour',exact:true})).toBeDisabled();
 await expect(page.locator('body')).not.toContainText(/Snapshot|R1|S1|proposed|non confirmé|USD/);await expect(page.locator('ul.shared-items,blockquote')).toHaveCount(0);
 await page.getByLabel('Votre question',{exact:true}).fill('Quels outils ?');await page.getByRole('button',{name:'Envoyer',exact:true}).click();
 await expect(page.locator('.guest-answer')).toContainText('Jupyter Notebook');expect(requests.some(p=>p.includes('snapshots'))).toBe(false);expect(requests.filter(p=>p.endsWith('/ask'))).toHaveLength(1);
});

for(const method of ['backdrop','escape','cross'] as const)test(`sharing modal closes with ${method}, never on inside click`,async({page})=>{
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname.endsWith('/workspace/documents')?[]:{items:[]}}));
 await page.goto('/tests/fixtures/sharing-simple.html');await page.getByRole('button',{name:'Partager ce contexte',exact:true}).click();
 const modal=page.getByRole('dialog');await modal.locator('.sharing-intro').click();await expect(modal).toBeVisible();
 if(method==='escape')await page.keyboard.press('Escape');
 else if(method==='cross')await modal.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 else await page.mouse.click(2,2);
 await expect(modal).toHaveCount(0);
});

test('email and OTP share one form, resend and editing preserve secure flow',async({page})=>{
 let codes=0;const requests:any[]=[];
 await page.route('**/api/guest/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/code')){codes++;expect(route.request().postDataJSON()).toEqual({invitation_token:'offline-invite',email:'bob@example.test'});return route.fulfill({status:202,json:{challenge_id:'challenge-'+codes,message:'Si cet accès est autorisé, un code a été envoyé à la boîte invitée.'}});}
  if(path.endsWith('/verify')){requests.push(route.request().postDataJSON());if(requests.length===1)return route.fulfill({status:401});return route.fulfill({json:{name:'Contexte autorisé',can_ask:true,recap:{title:'Présentation',text:'Résumé autorisé après vérification.'},expires_at:'2030-01-01T00:00:00Z',verification:'mailbox_control'}});}
  if(path.endsWith('/provider'))return route.fulfill({json:{enabled:true,simulated:true}});
  return route.fulfill({status:401});
 });
 await page.clock.install();
 await page.goto('/tests/fixtures/guest-understanding.html#invite=offline-invite');
 expect(await page.locator('.guest-access-card').evaluate(el=>el.getBoundingClientRect().left)).toBeGreaterThan(await page.locator('.guest-access-intro').evaluate(el=>el.getBoundingClientRect().right));
 await page.setViewportSize({width:390,height:740});
 const email=page.getByLabel('Votre email',{exact:true});await email.fill('bob@example.test');
 await expect(page.getByText('Résumé autorisé après vérification.',{exact:true})).toHaveCount(0);
 await email.evaluate(el=>el.setAttribute('data-same-form','yes'));
 await page.getByRole('button',{name:'Recevoir mon code',exact:true}).click();
 await expect(email).toHaveValue('bob@example.test');await expect(email).toHaveAttribute('data-same-form','yes');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const otp=page.getByLabel('Insérez ici le code reçu par mail',{exact:true});await expect(otp).toBeFocused();
 await otp.fill('00000000');await page.getByRole('button',{name:'Accéder au contexte',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Vérification impossible');
 await page.clock.fastForward(61000);await page.getByRole('button',{name:'Renvoyer le code',exact:true}).click();expect(codes).toBe(2);
 await page.getByRole('button',{name:'Modifier l’email',exact:true}).click();await expect(email).toBeEditable();await expect(email).toHaveValue('bob@example.test');
 await page.getByRole('button',{name:'Recevoir mon code',exact:true}).click();await otp.fill('12345678');await page.getByRole('button',{name:'Accéder au contexte',exact:true}).click();
 await expect(page.getByText('Résumé autorisé après vérification.',{exact:true})).toBeVisible();expect(requests[1].challenge_id).toBe('challenge-3');
 await expect(page.getByRole('button',{name:'Proposer une mise à jour',exact:true})).toBeDisabled();
});
