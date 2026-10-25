import {test,expect} from '@playwright/test';
import type {Page,TestInfo} from '@playwright/test';
import {writeFileSync} from 'node:fs';
import {DIMENSIONS} from '../src/uum';

async function settled(page:Page,query=''){
 await page.goto('/tests/fixtures/uum-layout.html'+query);
 await expect(page.locator('.context-orbit-node')).toHaveCount(6);
 if(!query.includes('state=loading'))await expect(page.locator('.orbit-node-state').first()).not.toHaveText('Chargement…');
 await page.evaluate(()=>document.fonts.ready);
 for(const image of await page.locator('.context-center img').all())expect(await image.evaluate(n=>(n as HTMLImageElement).complete&&(n as HTMLImageElement).naturalWidth>0)).toBe(true);
}
async function geometry(page:Page,info:TestInfo,label:string){
 const result=await page.locator('.space-context-map').evaluate(map=>{
  const rect=(e:Element)=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,right:b.right,bottom:b.bottom,width:b.width,height:b.height};};
  const within=(a:ReturnType<typeof rect>,b:ReturnType<typeof rect>)=>a.x>=b.x-1&&a.y>=b.y-1&&a.right<=b.right+1&&a.bottom<=b.bottom+1;
  const intersects=(a:ReturnType<typeof rect>,b:ReturnType<typeof rect>)=>Math.min(a.right,b.right)-Math.max(a.x,b.x)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)>1;
  const boundary=rect(map),nodes=[...map.querySelectorAll('.context-orbit-node')],orb=rect(map.querySelector('.context-center')!);
  const cards=nodes.map(n=>({label:n.querySelector('strong')!.textContent!,box:rect(n)}));
  const errors:string[]=[];
  cards.forEach((a,i)=>{if(!within(a.box,boundary))errors.push('card outside map: '+a.label);if(intersects(a.box,orb))errors.push('card intersects orb: '+a.label);cards.slice(i+1).forEach(b=>{if(intersects(a.box,b.box))errors.push('cards intersect: '+a.label+' / '+b.label);});});
  if(!within(orb,boundary))errors.push('orb outside map');
  for(const n of nodes){
   for(const selector of ['strong','.orbit-node-state','.orbit-node-icon','.node-chevron']){
    const e=n.querySelector(selector)!;const style=getComputedStyle(e);if(selector==='.node-chevron'&&style.display==='none')continue;if(selector==='.orbit-node-state'&&style.position==='absolute'&&e.clientWidth<=1)continue;const b=rect(e);if(b.width<=0||b.height<=0)errors.push('hidden content '+selector);
    if(!within(b,rect(n)))errors.push('content outside card '+selector);
    if(e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+1)errors.push('clipped content '+selector);
    if(selector==='strong'||selector==='.orbit-node-state'){
     const text=e.firstChild!,value=text.textContent!;
     for(const m of value.matchAll(/\S+/g)){
      const range=document.createRange();range.setStart(text,m.index!);range.setEnd(text,m.index!+m[0].length);
      const lines=[...range.getClientRects()];if(lines.length!==1)errors.push('word split: '+m[0]);
      for(const r of lines)if(r.left<b.x-1||r.right>b.right+1||r.top<b.y-1||r.bottom>b.bottom+1)errors.push('text outside box: '+m[0]);
     }
    }
   }
  }
  // Every visible map descendant is within its inline boundary, including controls/footer.
  for(const e of map.querySelectorAll('*')){const b=rect(e);if(b.width&&b.height&&(b.x<boundary.x-1||b.right>boundary.right+1))errors.push('map child horizontal overflow: '+e.className);}
  if(document.documentElement.scrollWidth>innerWidth+1)errors.push('page horizontal overflow');
  return {errors,boundary,orb,cards,viewport:innerWidth,fontSize:getComputedStyle(nodes[0].querySelector('strong')!).fontSize,columns:getComputedStyle(map.querySelector('.context-orbit')!).gridTemplateColumns};
 });
 const artifact=info.outputPath(label+'-geometry.json');writeFileSync(artifact,JSON.stringify(result,null,2));
 await info.attach(label+'-geometry',{path:artifact,contentType:'application/json'});
 if(result.errors.length)await page.locator('.space-context-map').screenshot({path:info.outputPath(label+'-failure.png')});
 expect(result.errors,JSON.stringify(result,null,2)).toEqual([]);
 expect(await page.locator('.context-orbit-node strong').allTextContents()).toEqual(DIMENSIONS.map(([,name])=>name));
 return result;
}
async function activateAll(page:Page){
 const nodes=page.locator('.context-orbit-node');
 for(let i=0;i<DIMENSIONS.length;i++){
  await nodes.nth(i).click();await expect(page.locator('#map-selection')).toHaveText(DIMENSIONS[i][0]+':proposed');
  const count=Number(await page.locator('#map-selection').getAttribute('data-activations'));
  await nodes.nth(i).focus();await page.keyboard.press('Enter');await expect(nodes.nth(i)).toBeFocused();await expect(page.locator('#map-selection')).toHaveAttribute('data-activations',String(count+1));
  await expect(page.locator('#map-selection')).toHaveText(DIMENSIONS[i][0]+':proposed');
  await page.keyboard.press('Tab');if(i<5)await expect(nodes.nth(i+1)).toBeFocused();
 }
 await page.getByRole('button',{name:'Compréhension courante',exact:true}).focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('button',{name:'Compréhension courante',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(page.getByRole('button',{name:'Propositions',exact:true})).toHaveAttribute('aria-pressed','false');
 await expect(nodes.first()).toContainText('Aucun élément dans cette vue');
 for(let i=0;i<DIMENSIONS.length;i++){await nodes.nth(i).focus();await page.keyboard.press('Space');await expect(page.locator('#map-selection')).toHaveText(DIMENSIONS[i][0]+':current');}
 await page.getByRole('button',{name:'Recentrer sur ce contexte',exact:true}).click();await expect(page.locator('.context-center')).toBeFocused();
 await page.keyboard.press('Enter');await expect(page.locator('#map-selection')).toHaveText('explore');
}
async function enlargeText(page:Page){
 await page.evaluate(()=>{const text=[...document.querySelectorAll('.space-context-map *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent?.trim())).map(e=>({e,size:parseFloat(getComputedStyle(e).fontSize)}));document.documentElement.style.fontSize='200%';for(const {e,size} of text)(e as HTMLElement).style.fontSize=size*2+'px';});
}
for(const width of [320,375,768,1672])test('UUM layout: '+width+'px, complete labels, geometry and all mouse/keyboard targets',async({page},info)=>{
 await page.setViewportSize({width,height:1000});await settled(page);
 const result=await geometry(page,info,'normal');
 if(width===1672){const chat=await page.locator('.assistant-card').boundingBox();expect(chat!.x).toBeGreaterThanOrEqual(result.boundary.right);expect(result.columns.split(' ').length).toBe(3);}
 await page.locator('.space-context-map').screenshot({path:info.outputPath('uum-'+width+'.png')});
 if(width===1672)await page.screenshot({path:info.outputPath('uum-desktop-with-chat.png'),fullPage:true});
 await activateAll(page);
});
for(const width of [320,375,768,1672])test('UUM layout: '+width+'px with text enlarged to 200 percent',async({page},info)=>{
 await page.setViewportSize({width,height:1000});await settled(page);
 // Enlarge actual label/control/status fonts, including legacy px rules, without scaling the viewport.
 await enlargeText(page);
 const result=await geometry(page,info,'text200');expect(parseFloat(result.fontSize)).toBeGreaterThanOrEqual(28);
 await page.locator('.space-context-map').screenshot({path:info.outputPath('uum-'+width+'-text200.png')});
 await activateAll(page);
});
test('UUM layout: wide fullscreen uses three rows around the original orb; exits before navigation',async({page},info)=>{
 await page.setViewportSize({width:1672,height:1000});await settled(page);
 await page.getByRole('button',{name:'Agrandir la carte',exact:true}).click();await expect.poll(()=>page.evaluate(()=>document.fullscreenElement?.className)).toBe('space-context-map');
 const r=await geometry(page,info,'fullscreen');expect(r.cards[0].box.right).toBeLessThanOrEqual(r.orb.x);expect(r.cards[1].box.x).toBeGreaterThanOrEqual(r.orb.right);
 for(const i of [0,2,4])expect(Math.abs(r.cards[i].box.y-r.cards[i+1].box.y)).toBeLessThanOrEqual(1);
 await page.screenshot({path:info.outputPath('uum-fullscreen.png'),fullPage:true});
 await page.locator('.context-orbit-node').first().focus();await page.keyboard.press('Enter');await expect.poll(()=>page.evaluate(()=>document.fullscreenElement)).toBeNull();await expect(page.locator('#map-selection')).toHaveText(DIMENSIONS[0][0]+':proposed');
});
test('UUM layout: narrow container on desktop and loading/unavailable/real-state text',async({page},info)=>{
 await page.setViewportSize({width:1672,height:1000});
 for(const state of ['loading','unavailable','populated']){
  await settled(page,'?width=600&state='+state);const r=await geometry(page,info,state);expect(r.columns.split(' ').length).toBe(2);
  await expect(page.locator('.orbit-node-state')).toHaveText(Array(6).fill(state==='loading'?'Chargement…':state==='unavailable'?'Indisponible':'Éléments proposés'));
 }
});

test('UUM layout: fullscreen with actual text at 200 percent remains readable and clickable',async({page},info)=>{
 await page.setViewportSize({width:1672,height:1200});await settled(page);await enlargeText(page);
 await page.getByRole('button',{name:'Agrandir la carte',exact:true}).click();await expect.poll(()=>page.evaluate(()=>!!document.fullscreenElement)).toBe(true);
 await geometry(page,info,'fullscreen-text200');await page.screenshot({path:info.outputPath('uum-fullscreen-text200.png'),fullPage:true});
 await page.getByRole('button',{name:'Agrandir la carte',exact:true}).click();await expect.poll(()=>page.evaluate(()=>document.fullscreenElement)).toBeNull();await activateAll(page);
});
test('UUM layout: desktop content at 200 percent zoom reflows without collisions or horizontal overflow',async({page},info)=>{
 await page.setViewportSize({width:1672,height:1000});await settled(page);await page.evaluate(()=>{document.documentElement.style.zoom='2';});
 await geometry(page,info,'zoom200');await page.locator('.space-context-map').screenshot({path:info.outputPath('uum-desktop-zoom200.png')});await activateAll(page);
});
