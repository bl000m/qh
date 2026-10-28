import {afterLogin} from './navigation.browser';
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

const aliceId = 'b9c1acb0-8e4a-4abd-a284-12112acfa101';
async function login(page: Page, name = 'alice') {
  await page.getByRole('button', {name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill(name);
  const password = process.env['QH_' + name.toUpperCase() + '_PASSWORD'];
  if (!password) throw new Error('Isolated browser credential missing');
  await page.locator('#password').fill(password);
  await page.locator('#kc-login').click();
  await expect(page.getByRole('button', {name:'Se déconnecter'})).toBeVisible();
  await afterLogin(page);
}
async function create(page: Page, name: string) {
  await page.getByRole('button', {name:'Créer un Context Space',exact:true}).click();
  await page.getByLabel('Nom du Context Space').fill(name);
  await page.getByLabel('Domaine principal',{exact:true}).selectOption({label:'Travail & projets'});
  await page.getByRole('button', {name:'Créer',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Context Space créé'})).toBeVisible();
}
async function storageIsTokenFree(page: Page) {
  expect(await page.evaluate(() => [...Object.values(localStorage), ...Object.values(sessionStorage)].some(v => /access_token|refresh_token|id_token/.test(v)))).toBe(false);
}

test('Alice creates Projet QH, opens it and returns; Bob is denied even by direct URL', async ({page,browser}, info) => {
  await page.goto('/');
  let pkce = false;
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname.endsWith('/auth')) pkce = url.searchParams.get('code_challenge_method') === 'S256' && !!url.searchParams.get('state') && !!url.searchParams.get('nonce') && url.searchParams.get('ui_locales') === 'fr' && !url.searchParams.has('client_secret');
  });
  await login(page);
  expect(pkce).toBe(true);
  await page.getByRole('link',{name:'Paramètres de mon environnement',exact:true}).click();await page.getByText('Informations du compte',{exact:true}).click();
  await expect(page.getByText('Identité QH : ' + aliceId)).toBeVisible();
  await page.getByRole('link',{name:'Mon environnement',exact:true}).click();
  await create(page,'Projet QH');
  await page.getByRole('link', {name:'Projet QH',exact:true}).click();
  await expect(page.getByRole('heading', {name:'Projet QH',exact:true})).toBeVisible();
  const path = new URL(page.url()).pathname;
  await page.getByRole('tab',{name:'Éléments',exact:true}).click();await page.getByText('Métadonnées du Space',{exact:true}).click();
  await expect(page.getByText('Actif', {exact:true})).toBeVisible();
  await page.getByRole('link', {name:'Mon environnement',exact:true}).click();
  await expect(page.getByRole('link', {name:'Projet QH',exact:true})).toBeVisible();
  await storageIsTokenFree(page);
  await page.screenshot({path:info.outputPath('alice-dashboard.png'),fullPage:true});
  const context = await browser.newContext({baseURL:'http://localhost:5173'});
  const bob = await context.newPage();
  try {
    await bob.goto(path); // A protected deep link must now land at the environment after login.
    await login(bob,'bob');
    await expect(bob.getByRole('link', {name:'Projet QH',exact:true})).toHaveCount(0);
    await bob.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},path);
    await expect(bob.getByRole('alert')).toHaveText('Ce Context Space est introuvable ou inaccessible.');
    await expect(bob.getByRole('heading', {name:'Projet QH',exact:true})).toHaveCount(0);
    await bob.getByRole('link', {name:'Mon environnement',exact:true}).click();
    await expect(bob.getByRole('link', {name:'Projet QH',exact:true})).toHaveCount(0);
    await expect(bob.getByText('Votre premier contexte commence ici.')).toBeVisible();
    await storageIsTokenFree(bob);
    await bob.screenshot({path:info.outputPath('bob-denied-dashboard.png'),fullPage:true});
  } finally { await context.close(); }
});
test('anonymous requests are not sent and unrequested callbacks fail closed', async ({page}) => {
  let calls = 0; page.on('request', r => { if (new URL(r.url()).pathname.startsWith('/api/')) calls++; });
  await page.goto('/'); await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();
  expect(calls).toBe(0);
  await page.goto('/oidc/callback?code=unrequested&state=forged');
  await expect(page.getByRole('alert')).toContainText('La connexion n’a pas abouti');
  expect(new URL(page.url()).search).toBe(''); expect(calls).toBe(0);
});
test('tampering with callback state prevents token exchange', async ({page}) => {
  let exchanges = 0;
  page.on('request', r => { if (new URL(r.url()).pathname.endsWith('/token')) exchanges++; });
  await page.addInitScript(() => {
    if (location.pathname === '/oidc/callback') {
      const query = new URLSearchParams(location.search);
      const fragment = new URLSearchParams(location.hash.slice(1));
      if (query.has('state')) query.set('state','tampered');
      if (fragment.has('state')) fragment.set('state','tampered');
      history.replaceState(null,'',location.pathname + '?' + query + (fragment.size ? '#' + fragment : ''));
      sessionStorage.setItem('test.callback.tampered','yes');
    }
  });
  await page.goto('/');
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill('alice'); await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!); await page.locator('#kc-login').click();
  await expect(page.getByRole('alert')).toContainText('La connexion n’a pas abouti');
  expect(exchanges).toBe(0);
  expect(await page.evaluate(() => sessionStorage.getItem('test.callback.tampered'))).toBe('yes');
  await storageIsTokenFree(page);
});
test('tampered transaction nonce rejects the real ID token before private API access', async ({page}) => {
  let apiCalls=0;
  page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/api/'))apiCalls++;});
  await page.addInitScript(()=>{
    if(location.pathname!=='/oidc/callback')return;
    for(const key of Object.keys(sessionStorage))if(key.startsWith('qh.oidc.')){
      const raw=sessionStorage.getItem(key);if(!raw)continue;
      const state=JSON.parse(raw);if(state.nonce){state.nonce='invalid-test-nonce';sessionStorage.setItem(key,JSON.stringify(state));}
    }
  });
  await page.goto('/');await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill('alice');await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!);
  const token=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/token'));
  await page.locator('#kc-login').click();expect((await token).status()).toBe(200);
  await expect(page.getByRole('alert')).toContainText('La connexion n’a pas abouti');
  expect(apiCalls).toBe(0);await storageIsTokenFree(page);
});
test('API failure is sanitized, recoverable; invalid name and failed creation preserve the form', async ({page}) => {
  await page.goto('/'); await login(page);
  await page.route('**/api/environment/spaces?*', r => r.fulfill({status:503,body:'private database diagnostic'}));
  await page.getByRole('link',{name:'QH — accueil'}).click();
  // Force a real route remount, without reloading the ephemeral session.
  await page.evaluate(() => { history.pushState(null,'','/absent'); dispatchEvent(new PopStateEvent('popstate')); });
  await page.getByRole('link',{name:'Mon environnement',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Le service est indisponible');
  await expect(page.locator('body')).not.toContainText('private database');
  await page.unroute('**/api/environment/spaces?*'); await page.getByRole('button',{name:'Réessayer'}).click();
  await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
  await page.getByLabel('Domaine principal',{exact:true}).selectOption({label:'Travail & projets'});
  await page.getByLabel('Nom du Context Space').fill('   '); await page.getByRole('button',{name:'Créer',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Saisissez un nom');
  await page.route('**/api/environment/spaces', r => r.fulfill({status:503,body:'private creation diagnostic'}));
  await page.getByLabel('Nom du Context Space').fill('Retry space'); await page.getByRole('button',{name:'Créer',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Le service est indisponible');
  await expect(page.getByLabel('Nom du Context Space')).toHaveValue('Retry space');
});
test('401 discards private UI and requires login; reload does not persist tokens', async ({page}) => {
  await page.goto('/'); await login(page);
  await page.route('**/api/environment/spaces', r => r.fulfill({status:401,body:'unauthorized'}));
  await page.getByRole('button',{name:'Créer un Context Space',exact:true}).click();
  await page.getByLabel('Domaine principal',{exact:true}).selectOption({label:'Travail & projets'});
  await page.getByLabel('Nom du Context Space').fill('Should fail'); await page.getByRole('button',{name:'Créer',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Votre session a expiré');
  await expect(page.getByRole('heading',{name:'Mes Context Spaces',exact:true})).toHaveCount(0);
  await storageIsTokenFree(page);
  await page.reload(); await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();
});
test('logout clears local state and returns from Keycloak to public home', async ({page}) => {
  await page.goto('/'); await login(page);
  await page.getByRole('button',{name:'Se déconnecter'}).click();
  await expect(page.getByRole('heading',{name:'Marre de tout réexpliquer à chaque IA ?',exact:true})).toBeVisible();
  await page.goto('/'); await expect(page.getByRole('button',{name:'Se connecter',exact:true})).toBeVisible();
  await storageIsTokenFree(page);
});
test('keyboard creation, mobile layout, back/forward and names render as text', async ({page}) => {
  await page.setViewportSize({width:375,height:812}); await page.goto('/'); await login(page);
  await page.getByRole('button',{name:'Créer un Context Space',exact:true}).focus(); await page.keyboard.press('Enter');
  const name = '<script>window.QH_XSS=true</script>';
  await page.getByLabel('Nom du Context Space').fill(name);
  await page.getByLabel('Domaine principal',{exact:true}).selectOption({label:'Travail & projets'}); await page.getByLabel('Nom du Context Space').focus();await page.keyboard.press('Enter');
  await expect(page.getByRole('link',{name,exact:true})).toBeVisible();
  await page.getByRole('link',{name,exact:true}).click(); await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
  await page.goBack(); await expect(page.getByRole('link',{name,exact:true})).toBeVisible();
  await page.goForward(); await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
  expect(await page.evaluate(() => 'QH_XSS' in window)).toBe(false);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
test('natural access-token expiration discards the private view', async ({page}) => {
  await page.clock.install(); await page.goto('/'); await login(page);
  await page.clock.fastForward(360_000);
  await expect(page.getByRole('alert')).toContainText('Votre session a expiré');
  await expect(page.getByRole('heading',{name:'Mes Context Spaces',exact:true})).toHaveCount(0);
  await storageIsTokenFree(page);
});
test('wrong PKCE verifier is rejected by real Keycloak without API disclosure', async ({page}) => {
  let apiCalls = 0;
  page.on('request', r => { if (new URL(r.url()).pathname.startsWith('/api/')) apiCalls++; });
  await page.route('**/protocol/openid-connect/token', async route => {
    const body = new URLSearchParams(route.request().postData() || '');
    body.set('code_verifier','x'.repeat(64)); await route.continue({postData:body.toString()});
  });
  await page.goto('/'); await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill('alice'); await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!); await page.locator('#kc-login').click();
  await expect(page.getByRole('alert')).toContainText('La connexion n’a pas abouti');
  expect(apiCalls).toBe(0); await storageIsTokenFree(page);
});
test('loading and bounded pagination render explicitly (UI fault/response simulation)', async ({page}) => {
  let release: () => void = () => {};
  const gate = new Promise<void>(resolve => { release = resolve; });
  let releaseOrganization:()=>void=()=>{};
  const organizationGate=new Promise<void>(resolve=>{releaseOrganization=resolve;});
  await page.route('**/api/environment',async route=>{if(route.request().method()==='GET')await organizationGate;await route.continue();});
  let firstPageRequests=0;
  const first = '00000000-0000-0000-0000-000000000001';
  const second = '00000000-0000-0000-0000-000000000002';
  const item = (id:string,name:string) => ({id,name,owner_id:aliceId,status:'active',created_at:'2026-10-17T12:00:00Z',updated_at:'2026-10-17T12:00:00Z'});
  await page.route('**/api/environment/spaces?*', async route => {
    const params = new URL(route.request().url()).searchParams;
    expect(params.get('limit')).toBe('20');
    if (!params.has('after_id')) {
      firstPageRequests++;
      await gate;
      await route.fulfill({json:{items:[item(first,'Page A')],next_after_id:first}});
    } else {
      expect(params.get('after_id')).toBe(first);
      await route.fulfill({json:{items:[item(second,'Page B')],next_after_id:null}});
    }
  });
  await page.goto('/'); await login(page);
  await expect(page.getByRole('status').filter({hasText:'Chargement des Context Spaces'})).toBeVisible();
  expect(firstPageRequests).toBe(0);releaseOrganization();
  await expect.poll(()=>firstPageRequests).toBe(1);release();
  await expect(page.getByRole('link',{name:'Page A',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Afficher plus'}).click();
  await expect(page.getByRole('link',{name:'Page B',exact:true})).toBeVisible();
  await expect(page.getByRole('link',{name:'Page A',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Afficher plus'})).toHaveCount(0);
});
