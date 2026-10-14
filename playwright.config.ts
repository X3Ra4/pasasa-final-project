import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', timeout: 60000, fullyParallel: false, workers: 1,
  use: { baseURL: 'http://127.0.0.1:8093', viewport: { width: 390, height: 844 },
    channel: process.env.CI ? undefined : 'chrome', screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  outputDir: '.work/playwright',
  webServer: { command: 'node tools/serve.mjs', url: 'http://127.0.0.1:8093', reuseExistingServer: !process.env.CI },
});
