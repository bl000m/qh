import {test, expect} from '@playwright/test';
import type {Page, BrowserContext, ElementHandle} from '@playwright/test';

test.describe.serial('real isolated OIDC session transitions', () => {
  test.skip(process.env.QH_SESSION_REAL !== '1', 'Opt-in disposable Keycloak only; never use the persistent runtime.');
  let context: BrowserContext, page: Page;
  let identityReads = 0, organizationReads = 0, tokenRequests = 0, silentRequests = 0;
  let releaseToken: () => void, releaseIdentity: () => void, releaseOrganization: () => void;
  let tokenGate: Promise<void>, identityGate: Promise<void>, organizationGate: Promise<void>;
  const block = () => {
    tokenGate = new Promise(resolve => {releaseToken = resolve;});
    identityGate = new Promise(resolve => {releaseIdentity = resolve;});
    organizationGate = new Promise(resolve => {releaseOrganization = resolve;});
  };
  const names = ['Travail & projets', 'Santé & bien-être', 'Finances & démarches', 'Apprentissage & évolution', 'Relations & proches', 'Vie quotidienne & habitat', 'Loisirs & découvertes', 'test'];
  const id = (index: number) => `00000000-0000-0000-0000-${String(index).padStart(12, '0')}`;
  test.beforeAll(async ({browser}) => {
    context = await browser.newContext({viewport: {width: 1440, height: 900}});
    page = await context.newPage();
    await context.addInitScript(() => {
      if (self !== top) return;
      const seen = new WeakSet<Element>(), audit = {screens: [] as string[], loaderMounts: 0, environmentMounts: 0};
      (window as any).sessionAudit = audit;
      const record = () => {
        const loader = document.querySelector('.qh-session-loading'), environment = document.querySelector('.environment-home-visual');
        if (loader && !seen.has(loader)) {seen.add(loader); audit.loaderMounts++;}
        if (environment && !seen.has(environment)) {seen.add(environment); audit.environmentMounts++;}
        const screen = loader ? 'loading' : environment ? 'environment' : document.querySelector('.public-hero') ? 'landing' : document.querySelector('.qh-session-failure') ? 'error' : '';
        if (screen && audit.screens.at(-1) !== screen) audit.screens.push(screen);
        requestAnimationFrame(record);
      };
      requestAnimationFrame(record);
    });
    page.on('request', request => {
      const url = new URL(request.url());
      if (url.pathname.endsWith('/openid-connect/auth') && url.searchParams.get('prompt') === 'none') silentRequests++;
    });
    await page.route('**/protocol/openid-connect/token', async route => {tokenRequests++; await tokenGate; await route.continue();});
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path === '/api/auth/me') {identityReads++; await identityGate; return route.fulfill({json: {user_id: id(99)}});}
      if (path === '/api/environment') {
        organizationReads++; await organizationGate;
        return route.fulfill({json: {version: 1, domains: names.map((name, index) => ({id: id(index + 1), name})), memberships: {}, primary_domains: {}, usage: {}}});
      }
      return route.fulfill({status: 404, json: {detail: 'outside isolated session test'}});
    });
  });
  test.afterAll(async () => {await context?.close();});

  async function loader() {
    await expect(page.locator('.qh-session-loading')).toHaveCount(1);
    await expect(page.locator('.app-shell,.public-shell,.environment-home-visual')).toHaveCount(0);
    const ring = (await page.locator('.qh-session-ring').elementHandle())!;
    await expect.poll(() => ring.evaluate(node => node.getAnimations()[0]?.startTime)).not.toBeNull();
    return {ring, start: await ring.evaluate(node => node.getAnimations()[0]?.startTime), logo: await page.locator('.qh-session-logo').getAttribute('src')};
  }
  async function sameLoader(ring: ElementHandle<SVGElement | HTMLElement>, start: unknown) {
    expect(await ring.evaluate(node => node === document.querySelector('.qh-session-ring'))).toBe(true);
    expect(await ring.evaluate(node => node.getAnimations()[0]?.startTime)).toBe(start);
    await expect(page.locator('.app-shell,.public-shell,.environment-home-visual')).toHaveCount(0);
  }
  async function finishBootstrap(loading: Awaited<ReturnType<typeof loader>>, expectedReads: number) {
    releaseToken();
    await expect.poll(() => identityReads).toBe(expectedReads);
    await sameLoader(loading.ring, loading.start);
    releaseIdentity();
    await expect.poll(() => organizationReads).toBe(expectedReads);
    await sameLoader(loading.ring, loading.start);
    releaseOrganization();
    await expect(page.getByRole('heading', {name: 'Mon environnement', exact: true})).toBeVisible();
    await expect(page.locator('.qh-session-loading')).toHaveCount(0);
    await expect(page.locator('.environment-domain')).toHaveCount(8);
    await expect.poll(() => page.evaluate(() => (window as any).sessionAudit.environmentMounts)).toBe(1);
    expect(await page.evaluate(() => (window as any).sessionAudit)).toEqual({screens: ['loading', 'environment'], loaderMounts: 1, environmentMounts: 1});
    expect(await page.locator('.topbar .brand img').getAttribute('src')).toBe(loading.logo);
  }

  test('landing → real Keycloak → fully ready environment keeps one uninterrupted loader', async ({}, info) => {
    block();
    await page.goto('http://localhost:5173/');
    await expect(page.locator('.public-hero')).toBeVisible();
    await page.getByRole('button', {name: 'Se connecter', exact: true}).click();
    await page.locator('input[name="username"]').fill('alice');
    await page.locator('input[name="password"]').fill(process.env.QH_ALICE_PASSWORD!);
    await page.locator('#kc-login').click();
    await expect.poll(() => tokenRequests).toBe(1);
    const loading = await loader();
    expect(await page.locator('.qh-session-logo').evaluate(node => ({transform: getComputedStyle(node).transform, filter: getComputedStyle(node).filter, animation: getComputedStyle(node).animationName}))).toEqual({transform: 'none', filter: 'none', animation: 'none'});
    await page.screenshot({path: info.outputPath('authentic-logo-loader.png')});
    await finishBootstrap(loading, 1);
    const background = page.locator('.environment-sphere>.environment-bubble-art');
    await expect(background).toHaveJSProperty('naturalWidth', 1400);
    expect(await background.evaluate(node => ({opacity: getComputedStyle(node).opacity, filter: getComputedStyle(node).filter, pointerEvents: getComputedStyle(node).pointerEvents}))).toEqual({opacity: '0.4', filter: 'blur(8px)', pointerEvents: 'none'});
    await page.screenshot({path: info.outputPath('visible-background.png')});
  });

  test('active session reload verifies SSO, then token renewal preserves the mounted environment', async () => {
    block();
    await page.reload();
    await expect.poll(() => tokenRequests).toBe(2);
    const loading = await loader();
    expect(silentRequests).toBe(1);
    await finishBootstrap(loading, 2);
    const shell = (await page.locator('.app-shell').elementHandle())!, environment = (await page.locator('.environment-home-visual').elementHandle())!;
    const renewed = page.waitForResponse(response => response.url().endsWith('/openid-connect/token') && response.request().postData()?.includes('grant_type=refresh_token') === true);
    await page.evaluate(() => {
      const originalFetch = window.fetch, now = Date.now;
      window.fetch = async (...args) => {
        try {return await originalFetch(...args);} finally {if (String(args[0]).includes('/openid-connect/token')) {Date.now = now; window.fetch = originalFetch;}}
      };
      Date.now = () => now() + 241000;
      window.dispatchEvent(new Event('focus'));
    });
    expect((await renewed).ok()).toBe(true);
    expect(await shell.evaluate(node => node === document.querySelector('.app-shell'))).toBe(true);
    expect(await environment.evaluate(node => node === document.querySelector('.environment-home-visual'))).toBe(true);
    expect(identityReads).toBe(2); expect(organizationReads).toBe(2);
    await expect(page.locator('.qh-session-loading,.public-shell')).toHaveCount(0);
    expect(await page.evaluate(() => (window as any).sessionAudit)).toEqual({screens: ['loading', 'environment'], loaderMounts: 1, environmentMounts: 1});
    expect(await page.evaluate(() => Object.keys(sessionStorage).filter(key => key.startsWith('qh.oidc.resume.')).every(key => Object.keys(JSON.parse(sessionStorage.getItem(key)!)).sort().join(',') === 'issuer,started,subject'))).toBe(true);
  });
});
