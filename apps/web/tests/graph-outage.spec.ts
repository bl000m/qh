import {afterLogin,expandUnderstanding} from './navigation.browser';
import { test, expect } from '@playwright/test';
test('real graph outage is unavailable, never an empty Space', async ({page},info) => {
  const {scope}=JSON.parse(process.env.QH12_EXPECTED_JSON!);
  await page.goto('/context-spaces/'+scope); await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill('alice'); await page.locator('#password').fill(process.env.QH_ALICE_PASSWORD!); await page.locator('#kc-login').click();await afterLogin(page,scope);await expandUnderstanding(page);
  await expect(page.getByRole('heading',{name:'Démo QH-8',exact:true})).toBeVisible();
  await page.getByText('Rechercher dans ce contexte',{exact:true}).click();await page.getByRole('button',{name:'Propositions',exact:true}).click(); await page.getByLabel('Texte à rechercher').fill('pilot');
  const response=page.waitForResponse(r=>r.url().endsWith('/api/context-spaces/query'));
  await page.getByRole('button',{name:'Rechercher',exact:true}).click(); expect((await response).status()).toBe(503);
  await expect(page.getByRole('region',{name:'Recherche complémentaire'}).getByRole('alert')).toContainText('Ce résultat ne signifie pas que le Space est vide');
  await expect(page.getByRole('region',{name:'Vue d’ensemble'}).getByRole('alert')).toContainText('Ce résultat ne signifie pas que le Space est vide');
  await expect(page.locator('article.revision')).toHaveCount(0);
  await expect(page.getByText('Aucune révision ne correspond à cette recherche.',{exact:true})).toHaveCount(0);
  await page.screenshot({path:info.outputPath('qh12-graph-unavailable.png'),fullPage:true});
});
