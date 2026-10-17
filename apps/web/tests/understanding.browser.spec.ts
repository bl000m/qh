import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
const expected = JSON.parse(process.env.QH12_EXPECTED_JSON || '{}');
async function open(page:Page, name='alice') {
  await page.goto('/context-spaces/' + expected.scope);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.locator('#username').fill(name);
  await page.locator('#password').fill(process.env['QH_' + name.toUpperCase() + '_PASSWORD']!);
  await page.locator('#kc-login').click();
  if (name === 'alice') await expect(page.getByRole('heading',{name:'Démo QH-8',exact:true})).toBeVisible();
}
async function search(page:Page, view:string, input:string, descriptors=false) {
  await page.getByRole('button',{name:view,exact:true}).click();
  if (descriptors) await page.getByRole('radio',{name:'Descripteurs',exact:true}).check();
  await page.getByLabel(descriptors ? 'Descripteurs exacts, un par ligne' : 'Texte à rechercher').fill(input);
  const response = page.waitForResponse(r => {
    if (!r.url().endsWith('/api/context-spaces/query') || r.request().method() !== 'POST') return false;
    const body=r.request().postDataJSON();
    return body.view === ({'Confirmé':'current','Propositions':'proposed','Historique':'history'} as Record<string,string>)[view] &&
      (descriptors ? body.descriptors?.join('\n') === input : body.text === input);
  });
  await page.getByRole('button',{name:'Rechercher',exact:true}).click();
  const r = await response; expect(r.status()).toBe(200); return r.json();
}
test('QH-8 rows, canonical provenance, open meanings, history and pagination use real REST', async ({page},info) => {
  await open(page);
  await expect(page.getByText('L’API ne fournit pas de liste complète sans recherche.',{exact:false})).toBeVisible();
  const none = await search(page,'Confirmé','reversible pause');
  expect(none.items).toHaveLength(0);
  await expect(page.getByRole('status')).toContainText('Aucune révision confirmée courante');
  const rows = await search(page,'Propositions','decision\nhypothesis\nopen_question\nreversible_pause',true);
  expect(rows.items.length).toBeGreaterThanOrEqual(5);
  for (const meaning of ['decision','hypothesis','open_question','reversible_pause']) await expect(page.locator('.assignments code').filter({hasText:new RegExp('^'+meaning+'$')}).first()).toBeVisible();
  expect(rows.items.every((r:any) => r.validation_state==='proposed' && !r.is_current_confirmed)).toBe(true);
  expect(rows.items.every((r:any) => r.provenance[0].source_revision_id===expected.source_revision_id)).toBe(true);
  await expect(page.locator('blockquote').first()).toBeVisible();
  await expect(page.locator('.state-confirmed')).toHaveCount(0);
  await page.getByRole('button',{name:'Confirmé',exact:true}).click();
  await expect(page.locator('.state-confirmed')).toHaveCount(1);
  await expect(page.locator('.state-proposed')).toHaveCount(0);
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await expect(page.locator('.state-rejected')).toHaveCount(1);
  for (const id of expected.decision_ids) await expect(page.getByRole('article',{name:'Révision '+id,exact:true})).toBeVisible();
  await page.getByLabel('Résultats par page').selectOption('5');
  const paged = await search(page,'Historique','decision\nhypothesis\nopen_question\nreversible_pause\nstated_by',true);
  expect(paged.items).toHaveLength(5); expect(paged.next_after_revision_id).toBeTruthy();
  await page.getByRole('button',{name:'Afficher les révisions suivantes'}).click();
  await expect(page.locator('article.revision')).toHaveCount(8);
  await expect(page.getByRole('button',{name:'Afficher les révisions suivantes'})).toHaveCount(0);
  await page.screenshot({path:info.outputPath('qh12-history.png'),fullPage:true});
});
test('unclassified entity, relations and temporal bounds retain exact anchors', async ({page},info) => {
  await open(page);
  const entity = await search(page,'Propositions','Alex');
  expect(entity.items.some((r:any) => r.structural_kind==='entity' && !r.content.descriptors?.length)).toBe(true);
  await expect(page.getByText('Aucun descripteur déclaré.',{exact:true}).first()).toBeVisible();
  const relation = await search(page,'Propositions','stated_by',true);
  expect(relation.items[0].relation).toEqual(expected.relation);
  await expect(page.getByRole('region',{name:'Relation'})).toBeVisible();
  await expect(page.locator('.revision').getByText(expected.relation.source_revision_id,{exact:true})).toBeVisible();
  await expect(page.locator('.revision').getByText(expected.relation.target_revision_id,{exact:true})).toBeVisible();
  await page.screenshot({path:info.outputPath('qh12-relation.png'),fullPage:true});
  const timed = await search(page,'Propositions','reported_timestamp',true);
  const fact = timed.items[0].temporal.fact_from;
  expect(Date.parse(fact)).toBe(Date.parse('2026-10-01T12:00:00Z'));
  await page.getByText('Temporalité',{exact:true}).click();
  await expect(page.getByText(fact,{exact:true}).first()).toBeVisible();
  await expect(page.getByText('Non renseigné',{exact:true})).toHaveCount(2);
});
test('tentative selection is opt-in; legacy citation properties are not asserted as verified quotes', async ({page}) => {
  await open(page);
  const empty = await search(page,'Propositions','expected_effect',true); expect(empty.items).toHaveLength(0);
  await page.getByLabel('Inclure les attributions tentative').check();
  const response = page.waitForResponse(r => r.url().endsWith('/api/context-spaces/query'));
  await page.getByRole('button',{name:'Rechercher',exact:true}).click();
  expect((await (await response).json()).items).toHaveLength(1);
  await expect(page.locator('.assignments').getByText('· attribution : tentative',{exact:true})).toBeVisible();
  await search(page,'Historique','bibliography',true);
  await expect(page.locator('blockquote')).toHaveCount(0);
  await expect(page.getByText('Aucune citation QH-8 reconnaissable disponible',{exact:false})).toBeVisible();
  await page.getByText('Identité et détails canoniques',{exact:true}).click();
  await expect(page.locator('.json-value').filter({hasText:'Bibliography, not a QH-8 locator'}).first()).toBeVisible();
  await expect(page.locator('.assignments .json-value').filter({hasText:'opaque_attribute'})).toBeVisible();
});
test('Bob cannot retrieve Alice understanding by direct URL or direct scoped REST', async ({page}) => {
  await open(page,'bob');
  await expect(page.getByRole('alert')).toContainText('introuvable ou inaccessible');
  await expect(page.getByRole('heading',{name:'Compréhension du contexte'})).toHaveCount(0);
  // Reuse Bob's actual bearer in memory only; never write/print it.
  let token:string|undefined;
  page.on('request', r => { if (r.url().includes('/api/context-spaces')) token=r.headers()['authorization']; });
  await page.getByRole('button',{name:'Réessayer',exact:true}).click();
  await expect.poll(() => !!token).toBe(true);
  const status = await page.evaluate(async ({scope,authorization}) => {
    const r=await fetch('/api/context-spaces/query',{method:'POST',headers:{'Content-Type':'application/json',Authorization:authorization!},body:JSON.stringify({context_ids:[scope],view:'history',text:'pilot'})}); return r.status;
  },{scope:expected.scope,authorization:token});
  expect(status).toBe(404);
});
test('late historical responses cannot relabel proposals as confirmed-current (request delay)',async({page})=>{
  await open(page);
  await search(page,'Propositions','decision',true);
  let release:()=>void=()=>{};
  const gate=new Promise<void>(resolve=>{release=resolve;});
  let waiting=false;
  await page.route('**/api/context-spaces/query',async route=>{
    if(route.request().postDataJSON().view==='history') {waiting=true; await gate;}
    await route.continue();
  });
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await expect.poll(()=>waiting).toBe(true);
  await page.getByRole('button',{name:'Confirmé',exact:true}).click();
  await expect(page.locator('.state-confirmed')).toHaveCount(1);
  const old=page.waitForResponse(r=>r.url().endsWith('/api/context-spaces/query') && r.request().postDataJSON().view==='history');
  release();await(await old).finished();
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  await expect(page.locator('.state-confirmed')).toHaveCount(1);
  await expect(page.locator('.state-proposed')).toHaveCount(0);
  await expect(page.locator('.state-rejected')).toHaveCount(0);
});
