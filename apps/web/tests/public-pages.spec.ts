import {test, expect} from '@playwright/test';

test('public home, information pages and authenticated return on desktop and mobile', async ({page}) => {
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/auth/me') return route.fulfill({json: {user_id: '00000000-0000-0000-0000-000000000005'}});
    if (path === '/api/environment') return route.fulfill({json: {version: 0, domains: [], themes: [], memberships: {}, primary_domains: {}}});
    if (path === '/api/environment/spaces') return route.fulfill({json: {items: [], next_after_id: null}});
    return route.fulfill({status: 404, json: {detail: 'outside fixture'}});
  });
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({width, height: 900});
    await page.goto('/tests/fixtures/ux-consolidation.html');
    await expect(page.getByRole('heading', {level: 1})).toHaveText('Marre de tout réexpliquer à chaque IA ?');
    await expect(page.getByRole('button', {name: 'Se connecter', exact: true})).toHaveCount(1);
    await expect(page.getByRole('button', {name: 'Créer un compte', exact: true})).toBeDisabled();
    await expect(page.getByText('Inscription bientôt disponible')).toBeVisible();
    const image = page.locator('.public-sphere');
    await expect(image).toBeVisible();
    expect(await image.evaluate((node: HTMLImageElement) => node.complete && node.naturalWidth === 1266 && getComputedStyle(node).objectFit === 'contain')).toBe(true);
    if (width === 1440) {
      const bounds = (await image.boundingBox())!;
      expect(bounds.y + bounds.height).toBeLessThanOrEqual(900);
    }
    for (const [label, title] of [
      ["Qu'est-ce que QH ?", 'Tes contextes, accessibles à toutes tes IA'],
      ['Sécurité', 'Tes informations, sous ton contrôle'],
      ['Tarifs', 'Simple et transparent']
    ]) {
      await page.getByRole('link', {name: label, exact: true}).click();
      await expect(page.getByRole('heading', {level: 1})).toHaveText(title);
      await expect(page.getByRole('heading', {level: 1})).toBeFocused();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    await expect(page.getByText('Offre envisagée')).toBeVisible();
    await expect(page.getByText('QH — 5 € / mois')).toBeVisible();
    await page.getByRole('link', {name: 'QH — accueil', exact: true}).click();
    await expect(page.getByRole('heading', {level: 1})).toContainText('Marre de tout');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.getByRole('button', {name: 'Se connecter', exact: true}).click();
    // The fixture changes only session state; environment reads remain offline.
    await expect(page.getByRole('link', {name: 'Mon environnement'})).toBeVisible();
    await expect(page.getByRole('button', {name: 'Se connecter', exact: true})).toHaveCount(0);
    await page.getByRole('link', {name: 'Mon environnement'}).click();
    await expect(page.getByRole('heading', {name: 'Mon environnement', exact: true})).toBeVisible();
    await page.evaluate(() => {history.pushState(null, '', '/accueil'); dispatchEvent(new PopStateEvent('popstate'));});
    await expect(page.getByRole('link', {name: 'Mon environnement'})).toBeVisible();
  }
});

test('public sign in opens the existing Keycloak code and PKCE flow', async ({page}) => {
  test.skip(process.env.QH_PUBLIC_OIDC_TEST !== '1', 'Requires disposable Keycloak; never use the persistent runtime.');
  await page.goto('/');
  await page.getByRole('button', {name: 'Se connecter', exact: true}).click();
  await expect(page).toHaveURL(/\/realms\/qh\/protocol\/openid-connect\/auth\?/);
  const url = new URL(page.url());
  expect(url.searchParams.get('client_id')).toBe('qh-web');
  expect(url.searchParams.get('response_type')).toBe('code');
  expect(url.searchParams.get('code_challenge_method')).toBe('S256');
  expect(url.searchParams.get('redirect_uri')).toBe('http://localhost:5173/oidc/callback');
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();
});
