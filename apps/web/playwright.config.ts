import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testIgnore: process.env.QH12_GRAPH_OUTAGE === '1' ? ['**/browser.spec.ts','**/contracts.spec.ts','**/understanding.spec.ts','**/understanding.browser.spec.ts'] :
    process.env.QH12_BROWSER_TEST === '1' ? ['**/graph-outage.spec.ts'] : ['**/understanding.browser.spec.ts','**/graph-outage.spec.ts'], fullyParallel: false, workers: 1, retries: 0,
  timeout: 30000, expect: { timeout: 10000 },
  outputDir: process.env.QH_BROWSER_OUTPUT || '/tmp/qh11-browser-results',
  reporter: [['list']],
  use: { baseURL: 'http://localhost:5173', browserName: 'chromium',
    trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: 'npm run dev', url: 'http://localhost:5173', reuseExistingServer: false, stdout: 'ignore', stderr: 'pipe' }
});
