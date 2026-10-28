import {test,expect} from '@playwright/test';
const scope='00000000-0000-0000-0000-000000000001',other='00000000-0000-0000-0000-000000000002',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006';
const space={id:scope,owner_id:owner,name:'Atelier UX',status:'active',created_at:'2026-10-28T00:00:00Z',updated_at:'2026-10-28T00:00:00Z'};
const caps={automatic:true,enabled:true,model:'mistral-small-2603',max_seconds:null,max_calls:null,max_usd:'5.00',provider_expires_at:2000000000,remaining_calls:null,remaining_usd:'4.0'};
const empty={context_id:scope,state:'empty',pending_count:0,intake:[],understanding:[],current:null,recap:null};

for(const width of [1366,375])test('stable home, domain, Space, transparent branding '+width,async({page})=>{
 await page.setViewportSize({width,height:812});
 let releaseDomain!:()=>void,releaseSpace!:()=>void;
 const domainGate=new Promise<void>(r=>{releaseDomain=r;}),spaceGate=new Promise<void>(r=>{releaseSpace=r;});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/environment')return route.fulfill({json:{version:1,domains:[{id:domain,name:'Travail'}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},usage:{}}});
  if(path==='/api/environment/spaces'){
   if(new URL(route.request().url()).searchParams.has('domain'))await domainGate;
   return route.fulfill({json:{items:[space],next_after_id:null}});
  }
  if(path==='/api/context-spaces/'+scope){await spaceGate;return route.fulfill({json:space});}
  if(path==='/api/context-spaces/'+other){await spaceGate;return route.fulfill({status:403,json:{detail:'offline denied'}});}
  if(path.endsWith('/workspace'))return route.fulfill({json:empty});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/open'))return route.fulfill({json:{}});
  return route.fulfill({status:404,json:{detail:'offline'}});
 });
 await page.goto('/tests/fixtures/ux-consolidation.html');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
 await expect(page.getByRole('link',{name:space.name,exact:true})).toBeVisible();
 const header=page.locator('.topbar'),logo=page.locator('.brand img');
 await header.evaluate(n=>n.setAttribute('data-retained','yes'));
 const bounds=await header.boundingBox();
 const branding=await page.evaluate(async()=>{
  const image=document.querySelector('.brand img') as HTMLImageElement;await image.decode();
  const html=await (await fetch('/index.html')).text();
  const href=new DOMParser().parseFromString(html,'text/html').querySelector('link[rel="icon"]')!.getAttribute('href')!;
  const icon=new Image();icon.src=href;await icon.decode();
  function inspect(im:HTMLImageElement){const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const ctx=c.getContext('2d')!;ctx.drawImage(im,0,0);const pixels=ctx.getImageData(0,0,c.width,c.height).data;return {width:c.width,height:c.height,corner:pixels[3],transparent:pixels.filter((_,i)=>i%4===3&&pixels[i]===0).length,solid:pixels.filter((_,i)=>i%4===3&&pixels[i]===255).length};}
  return {logo:inspect(image),icon:inspect(icon),background:getComputedStyle(document.body).backgroundColor};
 });
 expect(branding.logo.corner).toBe(0);expect(branding.icon.corner).toBe(0);expect(branding.icon.width).toBe(64);expect(branding.icon.height).toBe(64);expect(branding.logo.transparent).toBeGreaterThan(200000);expect(branding.icon.solid).toBeGreaterThan(1000);
 await page.getByRole('link',{name:'Travail',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Travail',exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:space.name,exact:true})).toHaveCount(0);
 await expect(page.locator('.loading-overlay')).toHaveCount(0);
 releaseDomain();await page.getByRole('link',{name:space.name,exact:true}).click();
 await expect(page.locator('.context-space-workspace')).toBeVisible();
 await expect(page.getByRole('textbox',{name:'Ton message',exact:true})).toBeDisabled();
 await expect(page.locator('.loading-overlay')).toHaveCount(0);
 releaseSpace();await expect(page.getByRole('heading',{name:space.name,exact:true})).toBeVisible();
 await expect(page.getByRole('textbox',{name:'Ton message',exact:true})).toBeEnabled();
 expect(await header.getAttribute('data-retained')).toBe('yes');expect(await header.boundingBox()).toEqual(bounds);await expect(logo).toBeVisible();
 // A different, inaccessible Space must never display this Space's content.
 await page.evaluate(other=>{history.pushState(null,'','/context-spaces/'+other);dispatchEvent(new PopStateEvent('popstate'));},other);
 await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('heading',{name:space.name,exact:true})).toHaveCount(0);
});

for(const succeeds of [true,false])test('single response indicator and exact question; '+(succeeds?'answer':'error'),async({page})=>{
 let finish!:()=>void;const gate=new Promise<void>(r=>{finish=r;});const intake:any[]=[];
 const state=()=>({...empty,state:intake.length?'pending':'empty',intake,pending_count:intake.length});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope)return route.fulfill({json:space});
  if(path.endsWith('/chat-sessions'))return route.fulfill({json:caps});
  if(path.endsWith('/workspace/intake')){intake.push(route.request().postDataJSON());return route.fulfill({json:state()});}
  if(path.endsWith('/workspace/messages')){
   await gate;
   if(!succeeds)return route.fulfill({status:503,json:{detail:'offline error'}});
   intake.push({id:other,kind:'message',role:'assistant',text:'Réponse simulée.',name:null,context:null,reply_to:intake[0].id,attribution:{support_basis:'general',reference_ids:[],insufficient_context:false,partial_coverage:false}});
   return route.fulfill({json:{state:'completed'}});
  }
  if(path.endsWith('/workspace'))return route.fulfill({json:state()});
  return route.fulfill({status:404,json:{detail:'offline'}});
 });
 await page.goto('/tests/fixtures/context-space.html');const field=page.getByRole('textbox',{name:'Ton message',exact:true});await expect(field).toBeEnabled();
 const question='  Une question\navec du Markdown **intact**.  ';await field.fill(question);await page.getByRole('button',{name:'Envoyer',exact:true}).click();
 const pending=page.getByText('Préparation de la réponse…',{exact:true});await expect(pending).toHaveCount(1);
 const user=page.locator('.workspace-message.user');await expect(user.locator('p').first()).toHaveJSProperty('textContent',question);await expect(user).not.toContainText('Préparation');
 expect(await pending.evaluate(n=>n.closest('.workspace-message')?.classList.contains('assistant'))).toBe(true);
 finish();
 if(succeeds){await expect(page.locator('.workspace-message.assistant')).toContainText('Réponse simulée.');await expect(page.getByText('Réponse générale',{exact:true})).toHaveCount(0);}
 else await expect(page.getByText('La réponse n’a pas pu être obtenue. Ta question est conservée.',{exact:true})).toBeVisible();
 await expect(pending).toHaveCount(0);await expect(user.locator('p').first()).toHaveJSProperty('textContent',question);
});
