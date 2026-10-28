import {test, expect} from '@playwright/test';

test('landing to verified environment uses one loading screen, handles callback failure and reveals the background', async ({page}, info) => {
  let releaseIdentity!: () => void, releaseOrganization!: () => void;
  const identity = new Promise<void>(resolve => {releaseIdentity = resolve;});
  const organization = new Promise<void>(resolve => {releaseOrganization = resolve;});
  let identityReads = 0, organizationReads = 0;
  const names = ['Travail & projets', 'Santé & bien-être', 'Finances & démarches', 'Apprentissage & évolution', 'Relations & proches', 'Vie quotidienne & habitat', 'Loisirs & découvertes', 'test'];
  const id = (index: number) => `00000000-0000-0000-0000-${String(index).padStart(12, '0')}`;
  await page.addInitScript(() => {
    const record = () => {
      const screen = document.querySelector('.qh-session-failure') ? 'error' : document.querySelector('.qh-session-loading') ? 'loading' : document.querySelector('.public-hero') ? 'landing' : document.querySelector('#environment-title') ? 'environment' : document.querySelector('.signin') ? 'legacy' : '';
      const trace: string[] = JSON.parse(sessionStorage.getItem('isolated-screen-trace') ?? '[]');
      if (screen && trace.at(-1) !== screen) {trace.push(screen); sessionStorage.setItem('isolated-screen-trace', JSON.stringify(trace));}
      requestAnimationFrame(record);
    };
    requestAnimationFrame(record);
  });
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/auth/me') {identityReads++; await identity; return route.fulfill({json: {user_id: id(99)}});}
    if (path === '/api/environment') {
      organizationReads++; await organization;
      return route.fulfill({json: {version: 1, domains: names.map((name, index) => ({id: id(index + 1), name})), memberships: {}, primary_domains: {}, usage: {}}});
    }
    return route.fulfill({status: 404, json: {detail: 'outside isolated transition'}});
  });
  const loading = page.locator('.qh-session-loading');
  const control = (action: string) => page.evaluate(name => (window as any).transitionControl[name](), action);
  const screens = () => page.evaluate<string[]>(() => JSON.parse(sessionStorage.getItem('isolated-screen-trace') ?? '[]'));
  await page.goto('/tests/fixtures/session-transition.html?fail=1');
  await expect(page.locator('.public-hero')).toBeVisible();
  await expect.poll(screens).toContain('landing');
  await page.getByRole('button', {name: 'Se connecter', exact: true}).click();
  await expect(loading).toHaveCount(1);
  await expect(page.locator('.public-hero,.signin,#environment-title')).toHaveCount(0);
  await page.screenshot({path: info.outputPath('session-loading.png')});
  await Promise.all([page.waitForEvent('domcontentloaded'), control('releaseRedirect')]);
  await expect.poll(() => control('counts')).toEqual({redirectCalls: 0, callbackCalls: 1});
  await expect(loading).toHaveCount(1);
  await control('releaseCallback');
  await expect(page.getByRole('alert')).toContainText('La connexion à QH n’a pas abouti');
  await expect.poll(screens).toContain('error');
  await expect(page.locator('.public-hero,.signin')).toHaveCount(0);
  expect(identityReads).toBe(0);
  expect(await control('counts')).toEqual({redirectCalls: 0, callbackCalls: 1});
  await page.getByRole('button', {name: 'Se reconnecter', exact: true}).click();
  await expect(loading).toHaveCount(1);
  await Promise.all([page.waitForEvent('domcontentloaded'), control('releaseRedirect')]);
  await expect.poll(() => control('counts')).toEqual({redirectCalls: 0, callbackCalls: 1});
  await expect(loading).toHaveCount(1);
  await control('releaseCallback');
  await expect.poll(() => identityReads).toBeGreaterThan(0);
  await expect(loading).toHaveCount(1);
  await expect(page.locator('#environment-title')).toHaveCount(0);
  releaseIdentity();
  await expect.poll(() => organizationReads).toBeGreaterThan(0);
  await expect(loading).toHaveCount(1);
  await expect(page.locator('#environment-title')).toHaveCount(0);
  releaseOrganization();
  await expect(page.getByRole('heading', {name: 'Mon environnement', exact: true})).toBeVisible();
  await expect(loading).toHaveCount(0);
  await expect(page.locator('.environment-domain')).toHaveCount(8);
  const background = page.locator('.environment-sphere>.environment-bubble-art');
  await expect(background).toHaveJSProperty('naturalWidth', 1400);
  expect(await background.evaluate(node => ({opacity: getComputedStyle(node).opacity, filter: getComputedStyle(node).filter, pointerEvents: getComputedStyle(node).pointerEvents}))).toEqual({opacity: '0.3', filter: 'blur(10px)', pointerEvents: 'none'});
  expect(await control('counts')).toEqual({redirectCalls: 0, callbackCalls: 1});
  await expect.poll(screens).toContain('environment');
  await page.screenshot({path: info.outputPath('environment-background.png')});
  const trace = await screens();
  const afterStart = trace.slice(trace.indexOf('landing') + 1);
  expect(afterStart).not.toContain('landing');
  expect(afterStart).not.toContain('legacy');
  expect(afterStart).toContain('error');
  expect(afterStart).toContain('loading');
});
