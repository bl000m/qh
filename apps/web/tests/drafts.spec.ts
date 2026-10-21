import {test,expect} from '@playwright/test';
import {createDrafts} from '../src/drafts';
const alice='00000000-0000-0000-0000-000000000001',bob='00000000-0000-0000-0000-000000000002',space='00000000-0000-0000-0000-000000000003',other='00000000-0000-0000-0000-000000000004';
function fixture(){let time=100000;const data=new Map<string,string>();const storage={getItem:(k:string)=>data.get(k)??null,setItem:(k:string,v:string)=>{data.set(k,v);},removeItem:(k:string)=>{data.delete(k);}};return {data,storage,now:()=>time,advance:(delta:number)=>{time+=delta;},make:()=>createDrafts(()=>storage,()=>time)};}
test('QH-54 drafts: explicit reconnection saves only bounded unsent text, verified exact owner and Space restore once',()=>{
 const f=fixture(),d=f.make();d.verifyOwner(alice);d.enter(alice,space);d.update('message','Question non envoyée');d.update('element','Information non enregistrée');expect(f.data.size).toBe(0);expect(d.suspend()).toBe(true);
 const saved=JSON.parse([...f.data.values()][0]);expect(Object.keys(saved).sort()).toEqual(['element','message','owner','savedAt','scope','version']);
 const next=f.make();expect(next.snapshot()).toEqual({message:'',element:''});next.verifyOwner(alice);expect(next.snapshot().message).toBe('');next.enter(alice,space);expect(next.snapshot()).toEqual(d.snapshot());expect(f.data.size).toBe(0);
 next.enter(alice,space);expect(next.snapshot().element).toBe('Information non enregistrée');next.enter(alice,other);expect(next.snapshot()).toEqual({message:'',element:''});
});
test('QH-54 drafts: wrong account or Space, exact thirty-minute expiry, future clocks and malformed fields fail closed',()=>{
 for(const mode of ['owner','space','expiry','future','extra','oversized','malformed']){
  const f=fixture(),d=f.make();d.verifyOwner(alice);d.enter(alice,space);d.update('message','Alice private draft');d.suspend();
  const key=[...f.data.keys()][0],raw=JSON.parse(f.data.get(key)!);
  if(mode==='expiry')f.advance(30*60000);if(mode==='future')f.advance(-1);if(mode==='extra')f.data.set(key,JSON.stringify({...raw,access_token:'forbidden'}));if(mode==='oversized')f.data.set(key,JSON.stringify({...raw,message:'x'.repeat(4097)}));if(mode==='malformed')f.data.set(key,'[]');
  const next=f.make();next.verifyOwner(mode==='owner'?bob:alice);next.enter(mode==='owner'?bob:alice,mode==='space'?other:space);expect(next.snapshot()).toEqual({message:'',element:''});expect(f.data.size).toBe(0);
 }
});
test('QH-54 drafts: logout, account change and explicit clear erase memory/storage and notify controlled editors',()=>{
 for(const action of ['clear','logout','owner'] as const){const f=fixture(),d=f.make();d.verifyOwner(alice);d.enter(alice,space);d.update('message','private');d.update('element','private element');d.suspend();let notified=0;const off=d.subscribe(()=>notified++);if(action==='owner')d.verifyOwner(bob);else d[action]();expect(d.snapshot()).toEqual({message:'',element:''});expect(f.data.size).toBe(0);expect(notified).toBe(1);off();}
});
test('QH-54 drafts: unavailable storage never discards the current text or promises recovery',()=>{
 const d=createDrafts(()=>{throw Error('storage disabled');});d.verifyOwner(alice);d.enter(alice,space);d.update('message','Copy me');expect(d.suspend()).toBe(false);expect(d.snapshot().message).toBe('Copy me');
});
