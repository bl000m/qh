import {test,expect} from '@playwright/test';
const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006',revision='00000000-0000-0000-0000-000000000007';
const caps={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.0'};
const space={id:scope,owner_id:owner,name:'Atelier UX',status:'active',created_at:'2026-10-28T00:00:00Z',updated_at:'2026-10-28T00:00:00Z'};
const org={version:1,domains:[{id:domain,name:'Travail'}],memberships:{},primary_domains:{},usage:{}};

for(const width of [1366,375])test('connection, creation and immediate committed recap '+width,async({page})=>{
 await page.setViewportSize({width,height:width===1366?768:812});
 let identify!:()=>void,memorized!:()=>void;
 const identity=new Promise<void>(r=>{identify=r;}),memory=new Promise<void>(r=>{memorized=r;});
 const intake:any[]=[];let created=0,published=false,reads=0;
 const state=()=>({context_id:scope,state:published?'current':intake.length?'pending':'empty',pending_count:published?0:intake.length,intake,understanding:[],current:published?{id:revision,version:1,has_recap:true,context_space_id:scope,intake_ids:[],revision_ids:[revision],source_revision_id:revision,created_at:space.created_at}:null,recap:published?{version_id:revision,title:'Atelier proposé',text:'Un atelier reste à préparer.',support_revision_ids:[revision]}:null});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/api/auth/me'){await identity;return route.fulfill({json:{user_id:owner}});}
  if(path==='/api/environment')return route.fulfill({json:org});
  if(path==='/api/environment/spaces'&&route.request().method()==='POST'){created++;return created===1?route.fulfill({status:503,json:{detail:'offline'}}):route.fulfill({status:201,json:space});}
  if(path==='/api/environment/spaces')return route.fulfill({json:{items:[],next_after_id:null}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:space});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/open'))return route.fulfill({json:{}});
  if(path.endsWith('/workspace/intake')){intake.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){intake.push({id:revision,kind:'message',role:'assistant',text:'Préparons cet atelier.',name:null,context:null,reply_to:intake[0].id});return route.fulfill({json:{state:'completed'}});}
  if(path.endsWith('/workspace/consolidate')){await memory;published=true;return route.fulfill({json:state()});}
  if(path.endsWith('/workspace')){reads++;return published?route.fulfill({status:503,json:{detail:'projection pending'}}):route.fulfill({json:state()});}
  if(path.endsWith('/invitations'))return route.fulfill({json:{items:[]}});
  return route.fulfill({status:404,json:{detail:'outside fixture'}});
 });
 await page.goto('/tests/fixtures/ux-consolidation.html');
 await expect(page.getByRole('heading',{name:'Marre de tout réexpliquer à chaque IA ?'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const logo=await page.locator('.public-brand img').getAttribute('src');
 await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('.loading-overlay')).toBeVisible();
 await expect(page.locator('.signin')).toBeVisible();identify();
 await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
 await expect(page.locator('.loading-overlay')).toHaveCount(0);
 expect(await page.locator('#environment-title').evaluate(n=>getComputedStyle(n).outlineStyle)).toBe('none');
 await page.getByRole('link',{name:'Travail',exact:true}).click();
 await page.getByRole('button',{name:'Créer mon premier Context Space',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Créer un Context Space',exact:true});
 await dialog.getByRole('textbox',{name:'Nom du Context Space'}).fill(space.name);
 await dialog.getByRole('button',{name:'Créer et ouvrir',exact:true}).click();await expect(dialog.getByRole('alert')).toBeVisible();
 await expect(dialog.getByRole('textbox')).toHaveValue(space.name);await dialog.getByRole('button',{name:'Créer et ouvrir',exact:true}).click();
 await expect(page.getByRole('heading',{name:space.name,exact:true})).toBeVisible();await expect(page.locator('.brand img')).toBeVisible();
 expect(await page.locator('.brand img').getAttribute('src')).toBe(logo);await expect(page.locator('.loading-overlay')).toHaveCount(0);
 await expect(page.getByText('Commence à discuter.',{exact:true})).toBeVisible();
 const field=page.getByRole('textbox',{name:'Ton message',exact:true});await field.fill('Préparons un atelier.');
 await page.getByRole('button',{name:'Envoyer',exact:true}).click();await expect(page.locator('.workspace-message.assistant')).toContainText('Préparons cet atelier.');
 const before=reads;await page.getByRole('button',{name:'Mémoriser',exact:true}).click();
 await expect(page.getByText('Compréhension en cours de préparation et d’enregistrement…')).toBeVisible();memorized();
 await expect(page.getByRole('heading',{name:'Atelier proposé',exact:true})).toBeVisible();expect(reads).toBe(before);
 await expect(page.getByText('Compréhension mise à jour',{exact:true})).toBeVisible();
 if(width<850)await page.getByRole('dialog',{name:'Compréhension',exact:true}).getByRole('button',{name:'Fermer la fenêtre'}).click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('button',{name:'Partager',exact:true}).click();await expect(page.getByRole('dialog',{name:'Partager ce contexte',exact:true})).toBeVisible();
});

test('one fallback read cannot replace a new version with an older recap',async({page})=>{
 let saved=false,reads=0;
 const old={context_id:scope,state:'current',pending_count:0,intake:[],understanding:[],current:{id:domain,context_space_id:scope,version:1,has_recap:true,intake_ids:[],revision_ids:[revision],source_revision_id:revision,created_at:space.created_at},recap:{version_id:domain,title:'Ancienne compréhension',text:'Ancien état.',support_revision_ids:[revision]}};
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:space});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/regenerate')){saved=true;return route.fulfill({json:{...old,current:{...old.current,id:revision,version:2},recap:null}});}
  if(path.endsWith('/workspace')){reads++;return route.fulfill({json:old});}
  return route.fulfill({status:404,json:{detail:'offline'}});
 });
 await page.goto('/tests/fixtures/context-space.html');await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Ancienne compréhension'})).toBeVisible();
 await page.getByRole('button',{name:'Régénérer',exact:true}).click();
 await expect(page.getByText('Version enregistrée. Le récapitulatif n’a pas pu être chargé. Actualise l’état pour le consulter.')).toBeVisible();
 expect(saved).toBe(true);expect(reads).toBe(2);await expect(page.getByRole('heading',{name:'Ancienne compréhension'})).toHaveCount(0);
});

test('an older source request cannot overwrite a newly committed recap',async({page})=>{
 let reads=0,release!:()=>void;
 const pending=new Promise<void>(r=>{release=r;});
 const old={context_id:scope,state:'current',pending_count:0,intake:[],understanding:[],current:{id:domain,context_space_id:scope,version:1,has_recap:true,intake_ids:[],revision_ids:[revision],source_revision_id:revision,created_at:space.created_at},recap:{version_id:domain,title:'Ancienne compréhension',text:'Ancien état.',support_revision_ids:[revision]}};
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:space});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/regenerate'))return route.fulfill({json:{...old,current:{...old.current,id:revision,version:2},recap:{...old.recap,version_id:revision,title:'Nouvelle compréhension'}}});
  if(path.endsWith('/workspace')){if(++reads===2)await pending;return route.fulfill({json:old});}
  return route.fulfill({status:404,json:{detail:'offline'}});
 });
 await page.goto('/tests/fixtures/context-space.html');await page.getByRole('button',{name:'Compréhension',exact:true}).click();
 await page.getByRole('button',{name:'Paramètres',exact:true}).click();
 const settings=page.getByRole('dialog',{name:'Paramètres du Space',exact:true});
 await settings.getByText('Sources et traçabilité',{exact:true}).click();await expect.poll(()=>reads).toBe(2);
 await settings.getByRole('button',{name:'Fermer la fenêtre',exact:true}).click();
 await page.getByRole('button',{name:'Régénérer',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Nouvelle compréhension'})).toBeVisible();
 const completed=page.waitForResponse(r=>r.url().endsWith('/workspace'));release();await completed;
 await expect(page.getByRole('heading',{name:'Nouvelle compréhension'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Ancienne compréhension'})).toHaveCount(0);
});
