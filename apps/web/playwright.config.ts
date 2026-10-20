import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testIgnore: process.env.QH12_GRAPH_OUTAGE === '1' ? ['**/readiness.browser.spec.ts','**/enrichment.browser.spec.ts','**/maquette.browser.spec.ts','**/layout.spec.ts','**/v2.browser.spec.ts','**/provider-session.browser.spec.ts','**/ux.browser.spec.ts','**/chat.browser.spec.ts','**/browse.browser.spec.ts','**/browser.spec.ts','**/contracts.spec.ts','**/understanding.spec.ts','**/understanding.browser.spec.ts'] :
    process.env.QH12_BROWSER_TEST === '1' ? ['**/graph-outage.spec.ts'] : ['**/readiness.browser.spec.ts','**/enrichment.browser.spec.ts','**/maquette.browser.spec.ts','**/v2.browser.spec.ts','**/provider-session.browser.spec.ts','**/ux.browser.spec.ts','**/chat.browser.spec.ts','**/browse.browser.spec.ts','**/understanding.browser.spec.ts','**/graph-outage.spec.ts'], fullyParallel: false, workers: 1, retries: 0,
  timeout: 30000, expect: { timeout: 10000 },
  outputDir: process.env.QH_BROWSER_OUTPUT || '/tmp/qh11-browser-results',
  reporter: [['list']],
  use: { baseURL: 'http://localhost:5173', browserName: 'chromium',
    trace: 'off', video: 'off', screenshot: 'off' },
  webServer: process.env.QH_BROWSER_EXTERNAL_SERVER === '1' ? undefined : { command: 'npm run dev -- --mode test', env:{VITE_QH_OFFLINE_TESTS:'1'}, url: 'http://localhost:5173', reuseExistingServer: false, stdout: 'ignore', stderr: 'pipe' }
});
