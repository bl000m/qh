import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';
import {DIMENSIONS} from '../src/uum';
const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005',domain='00000000-0000-0000-0000-000000000006';
async function fixture(page:Page){
 await page.route('**/api/**',async route=>{
  const u=new URL(route.request().url()),p=u.pathname.slice(4);let value:unknown;
  if(p==='/auth/me')value={user_id:owner};
  else if(p==='/context-spaces/'+scope)value={id:scope,owner_id:owner,name:'Projet QH',status:'active',created_at:'2026-10-22T00:00:00Z',updated_at:'2026-10-22T00:00:00Z'};
  else if(p==='/environment')value={version:1,domains:[{id:domain,name:'Travail & projets',description:''}],memberships:{[scope]:[domain]},primary_domains:{[scope]:domain},space_descriptions:{[scope]:'Compréhension portable entre IA'},usage:{}};
  else if(p.endsWith('/open'))value={};
  else if(p.endsWith('/understanding-presence'))value={context_id:scope,view:u.searchParams.get('view'),dimensions:Object.fromEntries(DIMENSIONS.map(([id])=>[id,false])),unclassified:false};
  else if(p.endsWith('/understanding')||p.endsWith('/review'))value={view:u.searchParams.get('view')??'proposed',items:[],next_after_revision_id:null};
  else if(p.endsWith('/chat-sessions'))value={enabled:false,model:null,max_seconds:1800,max_calls:3,max_usd:'0.01',provider_expires_at:null,remaining_calls:0,remaining_usd:'0'};
  else if(p.endsWith('/enrichments/capabilities'))value={literal:true,semantic:false,external_disclosure:false};
  else return route.fulfill({status:404,json:{detail:'outside isolated fixture'}});
  await route.fulfill({json:value});
 });
 await page.goto('/tests/fixtures/radial-target.html');await expect(page.getByRole('heading',{name:'Carte de compréhension',exact:true})).toBeVisible();
 await expect(page.locator('.orbit-node-state').first()).toHaveText('Aucun élément dans cette vue');await page.evaluate(()=>document.fonts.ready);
}
for(const [name,width,height] of [['desktop',1600,956],['mobile-target',390,1160],['narrow',320,1000],['intermediate',1200,1000]] as const)test('radial target: '+name,async({page},info)=>{
 await page.setViewportSize({width,height});await fixture(page);
 await page.screenshot({path:info.outputPath('radial-'+name+'.png'),fullPage:false});
 if(width===390)await page.screenshot({path:info.outputPath('radial-mobile-full.png'),fullPage:true});
 const map=page.locator('.space-context-map');const m=await map.boundingBox(),chat=await page.locator('.assistant-card').boundingBox();
 if(width===1600){expect(chat!.x).toBeGreaterThan(m!.x+m!.width);expect(m!.width/(m!.width+chat!.width)).toBeGreaterThan(.6);await expect(page.locator('.orbit-connections path')).toHaveCount(6);}
 if(width<=1200)expect(chat!.y).toBeGreaterThan(m!.y);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
 await expect(page.getByRole('button',{name:'Ajouter un élément',exact:true})).toHaveCount(1);
});
test('radial target: mobile navigation closes its menu before returning to view controls',async({page})=>{
 await page.setViewportSize({width:375,height:1000});await fixture(page);await page.getByLabel('Options de la carte',{exact:true}).click();await page.getByRole('button',{name:'Non classés',exact:true}).filter({visible:true}).click();const w=page.getByRole('dialog',{name:'Compréhension du contexte',exact:true});await expect(w).toBeVisible();await w.getByRole('button',{name:'Revenir aux éléments',exact:true}).click();await page.getByRole('tab',{name:'Discussion',exact:true}).click();await expect(page.locator('.map-navigation')).not.toHaveAttribute('open','');await page.getByRole('button',{name:'Compréhension courante',exact:true}).click();await expect(page.getByRole('button',{name:'Compréhension courante',exact:true})).toHaveAttribute('aria-pressed','true');
});
test('radial target: closing domain assignment dismisses the menu and restores its keyboard trigger',async({page})=>{
 await page.setViewportSize({width:1600,height:956});await fixture(page);const summary=page.locator('.space-domains-control>summary');await summary.click();await page.getByRole('button',{name:'Gérer les domaines de ce Space',exact:true}).click();await expect(page.getByRole('dialog',{name:'Assigner à un domaine',exact:true})).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.locator('.space-domains-control')).not.toHaveAttribute('open','');await expect(summary).toBeFocused();await page.getByRole('button',{name:'Ajouter un élément',exact:true}).click();await expect(page.getByRole('dialog',{name:'Ajouter un élément',exact:true})).toBeVisible();
});
