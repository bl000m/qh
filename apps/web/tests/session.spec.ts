import {test,expect} from '@playwright/test';

test('QH-52 memory renewal serializes wake/API requests, preserves route, revokes and cannot resurrect after logout',async({page})=>{
 await page.goto('/');
 const result=await page.evaluate(async()=>{
  const {createSession}=await import(String('/src/auth.ts'));
  const {User}=await import(String('/node_modules/.vite/deps/oidc-client-ts.js'));
  history.replaceState(null,'','/oidc/callback');
  let refresh=0,removed=0,revoked=0;let expiry=()=>{};
  const make=(offset:number,token:string)=>new User({access_token:token,refresh_token:'memory-refresh-'+token,token_type:'Bearer',expires_at:Math.floor(Date.now()/1000)+offset,profile:{sub:'alice',iss:'issuer',aud:'client',exp:9999999999,iat:0},userState:'/context-spaces/00000000-0000-0000-0000-000000000001'});
  const manager={events:{addAccessTokenExpired:(fn:()=>void)=>{expiry=fn;}},clearStaleState:async()=>{},removeUser:async()=>{removed++;},signinRedirectCallback:async()=>make(300,'first'),signinSilent:async()=>{refresh++;await new Promise(r=>setTimeout(r,10));return make(300,'renewed');},revokeTokens:async()=>{revoked++;},signoutRedirect:async()=>{}};
  const session=createSession(manager as never,true);await session.initialize();
  const route=location.pathname;
  const realNow=Date.now;Date.now=()=>realNow()+241000;
  const tokens=await Promise.all([session.readyToken!(),session.readyToken!(),session.readyToken!()]);
  Date.now=realNow;
  const state=session.snapshot();await session.logout();expiry();
  return {refresh,revoked,removed,tokens,state,after:session.snapshot(),route,stored:[...Object.values(sessionStorage),...Object.values(localStorage)]};
 });
 expect(result.refresh).toBe(1);expect(result.tokens).toEqual(['renewed','renewed','renewed']);expect(result.state).toBe('authenticated');expect(result.after).toBe('starting');expect(result.revoked).toBe(1);
 expect(result.route).toBe('/context-spaces/00000000-0000-0000-0000-000000000001');expect(result.stored.join('')).not.toMatch(/memory-refresh|renewed|first/);
});

test('QH-52 suspended work expires at eight hours and failed refresh never signs in silently',async({page})=>{
 await page.goto('/');
 const result=await page.evaluate(async()=>{
  const {createSession}=await import(String('/src/auth.ts'));const {User}=await import(String('/node_modules/.vite/deps/oidc-client-ts.js'));
  let refresh=0,redirect=0;
  const manager={events:{addAccessTokenExpired:()=>{}},clearStaleState:async()=>{},removeUser:async()=>{},signinRedirectCallback:async()=>new User({access_token:'synthetic',refresh_token:'only-memory',token_type:'Bearer',expires_at:Date.now()/1000+300,profile:{sub:'alice',iss:'issuer',aud:'client',exp:9999999999,iat:0}}),signinSilent:async()=>{refresh++;throw new Error('revoked');},signinRedirect:async()=>{redirect++;}};
  history.replaceState(null,'','/oidc/callback');const s=createSession(manager as never,true);await s.initialize();
  const now=Date.now;Date.now=()=>now()+241000;let failed=false;try{await s.readyToken!();}catch{failed=true;}Date.now=now;
  history.replaceState(null,'','/oidc/callback');const ceiling=createSession(manager as never,true);await ceiling.initialize();Date.now=()=>now()+8*3600000;try{await ceiling.readyToken!();}catch{}Date.now=now;
  return {refresh,redirect,failed,state:s.snapshot(),ceiling:ceiling.snapshot()};
 });
 expect(result).toEqual({refresh:1,redirect:0,failed:true,state:'expired',ceiling:'expired'});
});

test('QH-52 failed rotation and account changes fail closed; logout wins an in-flight renewal',async({page})=>{
 await page.goto('/');
 const results=await page.evaluate(async()=>{
  const {createSession}=await import(String('/src/auth.ts'));const {User}=await import(String('/node_modules/.vite/deps/oidc-client-ts.js'));
  const now=Date.now,results=[];
  for(const mode of ['reused-refresh','different-account','logout-race']){
   history.replaceState(null,'','/oidc/callback');let release:()=>void=()=>{};let entered:()=>void=()=>{};
   const pending=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r);
   const make=(sub:string,refresh:string)=>new User({access_token:'synthetic',refresh_token:refresh,token_type:'Bearer',expires_at:Date.now()/1000+300,profile:{sub,iss:'issuer',aud:'client',exp:9999999999,iat:0}});
   const manager={events:{addAccessTokenExpired:()=>{}},clearStaleState:async()=>{},removeUser:async()=>{},signinRedirectCallback:async()=>make('alice','refresh-original'),signinSilent:async()=>{entered();if(mode==='logout-race')await pending;return make(mode==='different-account'?'bob':'alice',mode==='reused-refresh'?'refresh-original':'refresh-rotated');},revokeTokens:async()=>{},signoutRedirect:async()=>{}};
   const s=createSession(manager as never,true);await s.initialize();Date.now=()=>now()+241000;
   const renewed=s.readyToken!().then(()=>false,()=>true);await started;
   if(mode==='logout-race'){await s.logout();release();}
   const rejected=await renewed;Date.now=now;results.push({mode,rejected,state:s.snapshot()});
  }
  return results;
 });
 expect(results).toEqual([{mode:'reused-refresh',rejected:true,state:'expired'},{mode:'different-account',rejected:true,state:'expired'},{mode:'logout-race',rejected:true,state:'starting'}]);
});

test('QH-52 legacy profile keeps its approved home landing until the development gate',async({page})=>{
 await page.goto('/');
 const result=await page.evaluate(async()=>{
  const {createSession}=await import(String('/src/auth.ts'));const {User}=await import(String('/node_modules/.vite/deps/oidc-client-ts.js'));
  history.replaceState(null,'','/oidc/callback');
  const manager={events:{addAccessTokenExpired:()=>{}},clearStaleState:async()=>{},removeUser:async()=>{},signinRedirectCallback:async()=>new User({access_token:'synthetic',token_type:'Bearer',expires_at:Date.now()/1000+300,profile:{sub:'alice',iss:'issuer',aud:'client',exp:9999999999,iat:0},userState:'/context-spaces/00000000-0000-0000-0000-000000000001'})};
  const s=createSession(manager as never,false);await s.initialize();return {state:s.snapshot(),route:location.pathname};
 });
 expect(result).toEqual({state:'authenticated',route:'/'});
});
