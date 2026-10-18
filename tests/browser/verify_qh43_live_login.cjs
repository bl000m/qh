/* Explicit manual VPS acceptance: no QH writes, provider calls or realm mutations.
   Run only with QH43_LIVE_LOGIN_TEST=1 and private demo credentials. */
const {chromium,expect}=require('/workspace/node_modules/@playwright/test');
const fs=require('fs'),crypto=require('crypto');
const output=process.env.QH_BROWSER_OUTPUT||'/evidence';
const mode=process.argv[2]||'acceptance';
const origin='http://localhost:5173',issuer='http://localhost:8080/realms/qh';
const scopes=['eb122625-1830-4557-b805-473d3b66132a','780888ef-6ca6-4eba-b6f9-f1d192795b7f','a0e43025-aad1-457e-86f1-6a813fcd14c4'];
function check(value,label){if(!value)throw Error(label);}
function save(name,value){const fd=fs.openSync(output+'/'+name,'w',0o600);fs.writeFileSync(fd,JSON.stringify(value,null,2));fs.fsyncSync(fd);fs.closeSync(fd);}
function payload(jwt){return JSON.parse(Buffer.from(jwt.split('.')[1],'base64url').toString());}
(async()=>{if(process.env.QH43_LIVE_LOGIN_TEST!=='1')throw Error('explicit live-test opt-in required');
const browser=await chromium.launch({headless:true});let phase='initial',activePage;const results={target:'existing VPS stack',paid_calls:0,qh_writes:0,realm_writes:0,checks:{}};
try{
async function start(options={}){
 const ctx=await browser.newContext({locale:'en-US',viewport:options.mobile?{width:390,height:844}:{width:1280,height:900}});
 const page=await ctx.newPage();activePage=page;let auth,tokenData,tokenRequest;let apiCalls=0,exchanges=0,bearer;
 page.on('request',r=>{const u=new URL(r.url());if(u.pathname.endsWith('/auth'))auth=u;
  if(r.url().startsWith(origin+'/api/')){apiCalls++;if(r.headers().authorization)bearer=r.headers().authorization;}
  if(u.pathname.endsWith('/token')){exchanges++;tokenRequest=new URLSearchParams(r.postData()||'');}});
 if(options.tamperState||options.tamperNonce)await page.addInitScript(({state,nonce})=>{
  if(location.pathname!=='/oidc/callback')return;
  if(state){const u=new URL(location.href);u.searchParams.set('state','invalid-test-state');history.replaceState(null,'',u);}
  if(nonce)for(const key of Object.keys(sessionStorage))if(key.startsWith('qh.oidc.')){
   try{const data=JSON.parse(sessionStorage.getItem(key));if(data.nonce){data.nonce='invalid-test-nonce';sessionStorage.setItem(key,JSON.stringify(data));}}catch{}
  }
 },{state:!!options.tamperState,nonce:!!options.tamperNonce});
 if(options.wrongPkce)await page.route('**/protocol/openid-connect/token',route=>{const form=new URLSearchParams(route.request().postData()||'');form.set('code_verifier','x'.repeat(64));return route.continue({postData:form.toString()});});
 await page.goto(origin);await page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(page.locator('#username')).toBeVisible();
 check(auth.origin==='http://localhost:8080'&&auth.pathname==='/realms/qh/protocol/openid-connect/auth','fixed issuer');
 check(auth.searchParams.get('client_id')==='qh-web'&&auth.searchParams.get('response_type')==='code','existing code client');
 check(auth.searchParams.get('code_challenge_method')==='S256'&&auth.searchParams.get('state')&&auth.searchParams.get('nonce'),'PKCE/state/nonce');
 check(auth.searchParams.get('ui_locales')==='fr','explicit French request');
 if(mode==='old-render')await expect(page.locator('link[href*="css/qh.css"]')).toHaveCount(0);
 else{await expect(page.locator('html')).toHaveAttribute('lang','fr');await expect(page.locator('link[href*="css/qh.css"]')).toHaveCount(1);
  await expect(page.getByRole('heading',{name:'Connectez-vous à votre compte',exact:true})).toBeVisible();
  await expect(page.getByLabel('Mot de passe',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Connexion',exact:true})).toBeVisible();
  check((await page.locator('#kc-header-wrapper').evaluate(n=>getComputedStyle(n,'::before').backgroundImage)).includes('qh-logo.png'),'selected logo');}
 async function finish(user,wrong=false){
  await page.locator('#username').fill(user);await page.locator('#password').fill(wrong?'deliberately-wrong-qh43-password':process.env['QH_'+user.toUpperCase()+'_PASSWORD']);
  const received=wrong?null:page.waitForResponse(r=>r.url().endsWith('/protocol/openid-connect/token'));
  await page.locator('#kc-login').click();
  if(wrong){await expect(page.getByText(/Nom d['’]utilisateur ou mot de passe invalide\./,{exact:true})).toBeVisible();return;}
  const response=await received;tokenData=await response.json();
  if(options.wrongPkce){check(response.status()===400,'real PKCE rejection');return;}
  check(response.status()===200&&tokenRequest.get('grant_type')==='authorization_code'&&!tokenRequest.has('password'),'no password grant');
  check(crypto.createHash('sha256').update(tokenRequest.get('code_verifier')).digest('base64url')===auth.searchParams.get('code_challenge'),'exact verifier binding');
  check(payload(tokenData.id_token).nonce===auth.searchParams.get('nonce'),'real token nonce');
  if(options.tamperNonce)return;
  await expect(page.getByRole('heading',{name:'Mon environnement',exact:true})).toBeVisible();
  check(new URL(page.url()).pathname==='/','environment callback');
  check(!await page.evaluate(()=>[...Object.values(localStorage),...Object.values(sessionStorage)].some(v=>/access_token|id_token|refresh_token|eyJ[A-Za-z0-9_-]+\./.test(v))),'tokens only in memory');
 }
 return {ctx,page,finish,get token(){return tokenData;},get apiCalls(){return apiCalls;},get exchanges(){return exchanges;},get bearer(){return bearer;}};
}
if(mode==='render-only'||mode==='old-render'){
 phase=mode;const a=await start();
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844]]){await a.page.setViewportSize({width,height});await a.page.screenshot({path:output+'/'+mode+'-'+name+'.png',fullPage:true});}
 save(mode+'.json',{PASS:true,actual_vps:true,fr_requested:true,qh_theme:mode==='render-only'});await a.ctx.close();
}else if(mode==='password-only'){
 phase='wrong password';const a=await start({mobile:true});await a.finish('alice',true);phase='mobile successful retry';await a.finish('alice');save('password-only.json',{PASS:true});await a.ctx.close();
}else{
 phase='Alice login';const alice=await start();await alice.finish('alice');results.checks.alice_code_pkce_state_nonce_memory='PASS';
 const started=Date.now(),expires=payload(alice.token.access_token).exp;const aliceBearer=alice.bearer;
 check(expires*1000-Date.now()<=360000,'bounded natural expiry wait');
 phase='Alice canonical reads';
 for(const id of scopes){const r=await alice.ctx.request.get(origin+'/api/context-spaces/'+id+'/understanding?view=proposed&limit=20',{headers:{Authorization:aliceBearer}});check(r.status()===200,'Alice owned canonical read');const v=await r.json();check(v.items.length===6&&v.items.every(x=>x.validation_state==='proposed'),'retained six proposed revisions');}
 results.checks.alice_three_retained_spaces='PASS';
 phase='Bob isolation';const bob=await start();await bob.finish('bob');
 const list=await bob.ctx.request.get(origin+'/api/context-spaces?limit=20',{headers:{Authorization:bob.bearer}});check(list.status()===200,'Bob list');check(!(await list.json()).items.some(x=>scopes.includes(x.id)),'no Alice entries');
 for(const id of scopes){for(const tail of ['', '/understanding?view=history&limit=1']){const r=await bob.ctx.request.get(origin+'/api/context-spaces/'+id+tail,{headers:{Authorization:bob.bearer}});check(r.status()===404,'Bob denied');}}
 results.checks.bob_six_foreign_scope_denials='PASS';await bob.ctx.close();
 phase='wrong password';const mobile=await start({mobile:true});await mobile.finish('alice',true);results.checks.french_wrong_password='PASS';phase='mobile successful retry';await mobile.finish('alice');results.checks.mobile_authentication='PASS';
 phase='logout';await mobile.page.getByRole('button',{name:'Se déconnecter',exact:true}).click();await expect(mobile.page.locator('body')).toContainText(/déconnect|logout|logged out|logging out/i);
 await mobile.page.goto(origin);await mobile.page.getByRole('button',{name:'Se connecter',exact:true}).click();await expect(mobile.page.locator('#username')).toBeVisible();results.checks.logout_and_fresh_server_login='PASS';await mobile.ctx.close();
 for(const [label,options] of [['state',{tamperState:true}],['nonce',{tamperNonce:true}],['PKCE',{wrongPkce:true}]]){
  phase=label+' negative control';const bad=await start(options);
  if(label==='state'){
   await bad.page.locator('#username').fill('alice');await bad.page.locator('#password').fill(process.env.QH_ALICE_PASSWORD);await bad.page.locator('#kc-login').click();
  }else await bad.finish('alice');
  await expect(bad.page.getByRole('alert')).toContainText('La connexion n’a pas abouti');check(bad.apiCalls===0,'failed transaction never reaches private API');if(label==='state')check(bad.exchanges===0,'state mismatch before token exchange');
  results.checks[label.toLowerCase()+'_negative_control']='PASS';await bad.ctx.close();
 }
 phase='natural token expiry';save('progress.json',{phase,checks:results.checks,clock_acceleration:false});await expect(alice.page.getByRole('alert')).toContainText('Votre session a expiré',{timeout:360000});
 check(Date.now()/1000>=expires,'real wall-clock expiration');
 await expect(alice.page.getByRole('heading',{name:'Mon environnement',exact:true})).toHaveCount(0);
 const expired=await alice.ctx.request.get(origin+'/api/auth/me',{headers:{Authorization:aliceBearer}});check(expired.status()===401,'server rejects actually expired signed token');
 results.checks.natural_client_and_server_expiry='PASS';results.natural_expiry_wait_seconds=Math.round((Date.now()-started)/1000);results.clock_acceleration=false;
 const anonymous=await alice.ctx.request.get(origin+'/api/context-spaces/'+scopes[0]);check(anonymous.status()===401,'anonymous denied');results.checks.anonymous_denial='PASS';await alice.ctx.close();save('acceptance.json',results);
}
console.log('PASS: QH-43 '+mode+' on actual VPS; no QH writes or provider call');
}catch(error){const first=String(error.message).split('\n')[0];save('failure.json',{phase,error_type:error.name,assertion:first.startsWith('expect(')?first:first.match(/^[a-zA-Z /-]+$/)?first:'browser-operation'});if(activePage)await activePage.screenshot({path:output+'/failure-private.png',fullPage:true}).catch(()=>{});throw error;}finally{await browser.close();}})().catch(()=>{console.log('FAIL: QH-43 live login verification; protected diagnostics omitted');process.exitCode=1;});
