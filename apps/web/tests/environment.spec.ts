import {test,expect} from '@playwright/test';
import {organization} from '../src/environment';
const id='00000000-0000-0000-0000-000000000001';
test('organization wire contract accepts multiple memberships but rejects aliasing and invalid domains',()=>{
 const doc={version:1,domains:[{id,name:'Travail & projets'}],memberships:{[id]:[id]},primary_domains:{[id]:id},usage:{}};
 expect(organization(doc)).toEqual(doc);
 for(const changed of [{version:-1},{domains:[...doc.domains,...doc.domains]},{memberships:{[id]:['unknown']}},{memberships:{foreign:[id]}},{memberships:{[id]:[id,id]}}])expect(()=>organization({...doc,...changed})).toThrow();
});

test('returning to environment waits for actual opening write and deduplicates its event',async()=>{
 const {QhApi}=await import('../src/api');const original=globalThis.fetch;const seen:string[]=[];
 let release:()=>void=()=>{};const gate=new Promise<void>(r=>release=r);
 globalThis.fetch=async(path)=>{const url=String(path);seen.push(url);if(url.endsWith('/open')){await gate;return new Response('{}');}
  return new Response(JSON.stringify(url.includes('/environment/spaces?')?{items:[],next_after_id:null}:{version:1,domains:[],memberships:{},primary_domains:{},usage:{}}));};
 try{
  const api=new QhApi(()=> 'synthetic-test-only',()=>{});
  const first=api.opened(id,id),duplicate=api.opened(id,id),resume=api.resumeSpaces('recent',null),metadata=api.organization();
  await Promise.resolve();expect(seen).toEqual(['/api/environment/spaces/'+id+'/open']);
  release();await Promise.all([first,duplicate,resume,metadata]);expect(seen.filter(v=>v.endsWith('/open'))).toHaveLength(1);
  expect(seen.some(v=>v.includes('/environment/spaces?sort=recent'))).toBe(true);expect(seen).toContain('/api/environment');
 }finally{globalThis.fetch=original;release();}
});


test('domain navigation waits for an in-flight organization save, including removal',async()=>{
 const {QhApi}=await import('../src/api');const original=globalThis.fetch;const seen:string[]=[];
 let release:()=>void=()=>{};const gate=new Promise<void>(r=>release=r);const doc={version:2,domains:[],memberships:{},primary_domains:{},usage:{}};
 globalThis.fetch=async(path,init)=>{seen.push((init?.method??'GET')+' '+String(path));if(init?.method==='PUT')await gate;return new Response(JSON.stringify(String(path).includes('/environment/spaces?')?{items:[],next_after_id:null}:doc));};
 try{const api=new QhApi(()=> 'synthetic-test-only',()=>{});const saved=api.organize({...doc,version:1}),read=api.organization(),spaces=api.resumeSpaces('recent',id);await Promise.resolve();expect(seen).toEqual(['PUT /api/environment']);release();expect(await saved).toEqual(doc);expect(await read).toEqual(doc);expect(await spaces).toEqual({items:[],next_after_id:null});expect(seen).toHaveLength(3);}finally{release();globalThis.fetch=original;}
});
