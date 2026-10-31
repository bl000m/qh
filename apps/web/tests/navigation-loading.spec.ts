import {test,expect} from '@playwright/test';
import {NavigationReads} from '../src/navigation-reads';
import {QhApi} from '../src/api';

const scope='00000000-0000-0000-0000-000000000001',owner='00000000-0000-0000-0000-000000000005';
const empty={context_id:scope,state:'empty',pending_count:0,intake:[],understanding:[],current:null,recap:null};

test('prefetch is session scoped, bounded, expires and cannot restore invalidated reads',async()=>{
 const cache=new NavigationReads();let resolve!:(v:number)=>void;
 const pending=cache.read('pending',()=>new Promise<number>(r=>{resolve=r;}),10000);
 await Promise.resolve();cache.clear();resolve(1);await pending;
 expect(await cache.read('pending',async()=>2)).toBe(2);
 let loads=0;
 for(let i=0;i<5;i++)await cache.read(String(i),async()=>++loads,10000);
 await cache.read('0',async()=>++loads,10000);expect(loads).toBe(6);
 await expect(cache.read('failed',async()=>{throw Error('offline');})).rejects.toThrow('offline');
 expect(await cache.read('failed',async()=>3)).toBe(3);
 const original=Date.now;let now=original();Date.now=()=>now;
 try{await cache.read('expiry',async()=>++loads,10);now+=11;await cache.read('expiry',async()=>++loads,10);expect(loads).toBe(8);}finally{Date.now=original;}
});

test('workspace prefetch reuses one read and invalidates on mutation, user change and logout',async()=>{
 const original=globalThis.fetch;let currentOwner=owner,reads=0;
 globalThis.fetch=async(path)=>{
  const url=String(path);
  if(url.endsWith('/auth/me'))return new Response(JSON.stringify({user_id:currentOwner}));
  if(url.endsWith('/workspace')){reads++;return new Response(JSON.stringify(empty));}
  return new Response(JSON.stringify(empty));
 };
 try{
  const api=new QhApi(()=> 'offline-fixture',()=>{});await api.me();
  api.prefetchWorkspace(scope);await api.workspace(scope);await api.workspace(scope);expect(reads).toBe(1);
  await api.addIntake(scope,{id:scope,kind:'message',role:'user',text:'Offline',name:null,context:null});
  await api.workspace(scope);expect(reads).toBe(2);
  currentOwner='00000000-0000-0000-0000-000000000006';await api.me();await api.workspace(scope);expect(reads).toBe(3);
  const otherApi=new QhApi(()=> 'other-offline-session',()=>{});await otherApi.workspace(scope);expect(reads).toBe(4);
  api.revokeSessionsBeforeLogout(null);api.prefetchWorkspace(scope);await api.workspace(scope);expect(reads).toBe(5);
 }finally{globalThis.fetch=original;}
});

test('prefetch requires a verified owner and limits concurrent reads to two',async()=>{
 const original=globalThis.fetch;let reads=0,release!:()=>void;
 const gate=new Promise<void>(r=>{release=r;});
 globalThis.fetch=async(path)=>{
  if(String(path).endsWith('/auth/me'))return new Response(JSON.stringify({user_id:owner}));
  reads++;await gate;return new Response(JSON.stringify({...empty,context_id:String(path).split('/').at(-2)}));
 };
 try{
  const api=new QhApi(()=> 'offline-fixture',()=>{});api.prefetchWorkspace(scope);await Promise.resolve();expect(reads).toBe(0);
  await api.me();
  for(let i=1;i<=3;i++)api.prefetchWorkspace('00000000-0000-0000-0000-'+String(i).padStart(12,'0'));
  await expect.poll(()=>reads).toBe(2);release();await api.workspace(scope);
 }finally{release();globalThis.fetch=original;}
});

test('cold Space starts metadata and content together and does not await organization',async({page})=>{
 const paths:string[]=[];let metadata!:()=>void,content!:()=>void,organization!:()=>void;
 const metadataGate=new Promise<void>(r=>{metadata=r;}),contentGate=new Promise<void>(r=>{content=r;}),organizationGate=new Promise<void>(r=>{organization=r;});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;paths.push(path);
  if(path.endsWith('/auth/me'))return route.fulfill({json:{user_id:owner}});
  if(path==='/api/context-spaces/'+scope){await metadataGate;return route.fulfill({json:{id:scope,owner_id:owner,name:'Cold Space',status:'active',created_at:'2026-10-27T00:00:00Z',updated_at:'2026-10-27T00:00:00Z'}});}
  if(path.endsWith('/workspace')){await contentGate;return route.fulfill({json:empty});}
  if(path==='/api/environment'){await organizationGate;return route.fulfill({json:{version:1,domains:[],memberships:{},primary_domains:{},usage:{}}});}
  return route.fulfill({status:404,json:{detail:'offline'}});
 });
 await page.goto('/tests/fixtures/context-space.html');
 await expect.poll(()=>paths.includes('/api/context-spaces/'+scope+'/workspace')).toBe(true);
 expect(paths).toContain('/api/context-spaces/'+scope);
 metadata();await expect(page.getByRole('heading',{name:'Cold Space',exact:true})).toBeVisible();
 expect(paths).not.toContain('/api/environment');
 content();await expect(page.getByRole('textbox',{name:'Ton message',exact:true})).toBeEnabled();
 organization();expect(paths.filter(path=>path.endsWith('/workspace'))).toHaveLength(1);
});
