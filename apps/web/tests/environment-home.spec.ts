import {test, expect} from '@playwright/test';
import type {Page} from '@playwright/test';
import type {Organization} from '../src/environment';

const id = (index: number) => `00000000-0000-0000-0000-${String(index).padStart(12, '0')}`;
function organization(count = 5): Organization {
  const domains = Array.from({length: count}, (_, index) => ({id: id(index + 1), name: `Projet ${index + 1}`}));
  const memberships = Object.fromEntries(Array.from({length: 16}, (_, index) => [id(index + 100), domains.filter((_, d) => index < d * d).map(domain => domain.id)]));
  return {version: 1, domains, memberships, primary_domains: Object.fromEntries(Object.entries(memberships).filter(([, domains]) => domains.length).map(([space, domains]) => [space, domains[0]])), usage: {}};
}

async function open(page: Page, count = 5, failSave = false) {
  let document = organization(count), saves = 0, spaceReads = 0;
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/auth/me') return route.fulfill({json: {user_id: id(900)}});
    if (path === '/api/environment') {
      if (route.request().method() === 'PUT') {
        saves++;
        if (failSave) return route.fulfill({status: 409, json: {detail: 'conflict'}});
        const next = route.request().postDataJSON();
        expect(next.memberships).toEqual(document.memberships);
        expect(next.primary_domains).toEqual(document.primary_domains);
        document = {...next, version: document.version + 1, usage: document.usage};
      }
      return route.fulfill({json: document});
    }
    if (path === '/api/environment/spaces') {spaceReads++; return route.fulfill({json: {items: [], next_after_id: null}});}
    return route.fulfill({status: 404, json: {detail: 'outside fixture'}});
  });
  await page.goto('/tests/fixtures/ux-consolidation.html');
  await page.getByRole('button', {name: 'Se connecter', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Mon environnement', exact: true})).toBeVisible();
  await expect(page.locator('.environment-domain')).toHaveCount(count);
  return {saved: () => saves, spaceReads: () => spaceReads};
}

for (const width of [1440, 1366, 390]) test(`environment displays real domains, creates and navigates at ${width}px`, async ({page}) => {
  await page.setViewportSize({width, height: width === 1366 ? 768 : 900});
  const calls = await open(page);
  await expect(page.locator('.topbar .brand img')).toBeVisible();
  await expect(page.getByRole('link', {name: 'Paramètres de mon environnement'})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Se déconnecter', exact: true})).toBeVisible();
  await expect(page.locator('.environment-domain-count')).toHaveText(['0 espace', '1 espace', '4 espaces', '9 espaces', '16 espaces']);
  expect(calls.spaceReads()).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  if (width > 700) {
    expect(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight)).toBe(true);
    const add = (await page.locator('.environment-add').boundingBox())!, sphere = (await page.locator('.environment-sphere').boundingBox())!;
    expect(add.x).toBeGreaterThan(sphere.x + sphere.width);
  }
  const links = page.locator('.environment-domain-link');
  expect((await links.last().boundingBox())!.width).toBeGreaterThan((await links.first().boundingBox())!.width);
  await expect(page.locator('.environment-sphere>.environment-bubble-art')).toHaveJSProperty('naturalWidth', 1261);
  const before = await links.first().evaluate(node => getComputedStyle(node.parentElement!).transform);
  await expect.poll(() => links.first().evaluate(node => getComputedStyle(node.parentElement!).transform)).not.toBe(before);
  await page.emulateMedia({reducedMotion: 'reduce'});
  expect(await links.first().evaluate(node => getComputedStyle(node.parentElement!).animationName)).toBe('none');
  await page.getByRole('button', {name: 'Ajouter un domaine', exact: true}).click();
  await page.getByRole('textbox', {name: 'Nom du domaine', exact: true}).fill('Nouveau projet');
  await page.getByRole('button', {name: 'Ajouter le domaine', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('link', {name: 'Nouveau projet — 0 Context Space', exact: true})).toBeVisible();
  expect(calls.saved()).toBe(1);
  expect(calls.spaceReads()).toBe(0);
  await page.getByRole('link', {name: 'Projet 3 — 4 Context Spaces', exact: true}).click({position: {x: 25, y: 25}});
  await expect(page).toHaveURL(new RegExp(`/domains/${id(3)}$`));
  await expect(page.getByRole('heading', {name: 'Projet 3', exact: true})).toBeVisible();
  await expect(page.getByRole('heading', {name: 'Context Spaces', exact: true})).toBeVisible();
  await expect(page.locator('.environment-sphere')).toHaveCount(0);
});

test('rejected domain save keeps the empty environment, dialog and input', async ({page}) => {
  const calls = await open(page, 0, true);
  await expect(page.getByText('Ton environnement attend son premier domaine.', {exact: false})).toBeVisible();
  await page.getByRole('button', {name: 'Ajouter un domaine', exact: true}).click();
  await page.getByRole('textbox', {name: 'Nom du domaine', exact: true}).fill('Projet conservé');
  await page.getByRole('button', {name: 'Ajouter le domaine', exact: true}).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('L’organisation a changé');
  await expect(page.getByRole('textbox', {name: 'Nom du domaine', exact: true})).toHaveValue('Projet conservé');
  await expect(page.locator('.environment-domain')).toHaveCount(0);
  expect(calls.saved()).toBe(1);
});

test('first domain appears without a reload; keyboard focus returns to the add control', async ({page}) => {
  await open(page, 0);
  await page.getByRole('button', {name: 'Ajouter un domaine', exact: true}).click();
  await page.getByRole('textbox', {name: 'Nom du domaine', exact: true}).fill('Premier projet');
  await page.getByRole('button', {name: 'Ajouter le domaine', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('link', {name: 'Premier projet — 0 Context Space', exact: true})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Ajouter un domaine', exact: true})).toBeFocused();
});

test('dense mobile environments keep fifty readable click targets in the page', async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await page.emulateMedia({reducedMotion: 'reduce'});
  await open(page, 50);
  await expect(page.getByRole('button', {name: 'Ajouter un domaine', exact: true})).toBeDisabled();
  await expect(page.locator('.environment-domain-label')).toHaveCount(50);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const geometry = await page.locator('.environment-domain-link').evaluateAll(nodes => nodes.map(node => {
    const circle = node.getBoundingClientRect(), text = node.querySelector('.environment-domain-text')!.getBoundingClientRect();
    return {diameter: circle.width, textHeight: text.height};
  }));
  for (const bubble of geometry) {expect(bubble.diameter).toBeGreaterThanOrEqual(63); expect(bubble.textHeight).toBeLessThan(bubble.diameter);}
  const last = page.getByRole('link', {name: 'Projet 50 — 16 Context Spaces', exact: true});
  await last.focus();
  await last.press('Enter');
  await expect(page).toHaveURL(new RegExp(`/domains/${id(50)}$`));
});
