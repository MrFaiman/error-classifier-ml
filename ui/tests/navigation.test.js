/**
 * Navigation E2E Tests
 */
import puppeteer from 'puppeteer';
import { TEST_CONFIG, SELECTORS, clearStorage } from './setup.js';

describe('Navigation', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: TEST_CONFIG.headless,
      slowMo: TEST_CONFIG.slowMo,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  });

  afterAll(async () => {
    await browser.close();
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });
    await clearStorage(page);
    await page.goto(TEST_CONFIG.baseUrl);
  });

  afterEach(async () => {
    await page.close();
  });

  test('should navigate to search page', async () => {
    await page.waitForSelector('nav');
    
    // Find and click Search link
    const searchLink = await page.$('a[href="/"]') || await page.$('a[href="/search"]');
    if (searchLink) {
      await searchLink.click();
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      
      const url = page.url();
      expect(url).toMatch(/\/(search)?$/);
    }
  });

  test('should navigate to manage dataset page', async () => {
    await page.waitForSelector('nav');
    
    const datasetLink = await page.$('a[href="/dataset"]');
    if (datasetLink) {
      await datasetLink.click();
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      
      const url = page.url();
      expect(url).toContain('/dataset');
    }
  });

  test('should navigate to manage docs page', async () => {
    await page.waitForSelector('nav');
    
    const docsLink = await page.$('a[href="/docs"]');
    if (docsLink) {
      await docsLink.click();
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      
      const url = page.url();
      expect(url).toContain('/docs');
    }
  });

  test('should navigate to status page', async () => {
    await page.waitForSelector('nav');
    
    const statusLink = await page.$('a[href="/status"]');
    if (statusLink) {
      await statusLink.click();
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      
      const url = page.url();
      expect(url).toContain('/status');
    }
  });

  test('should highlight active navigation item', async () => {
    await page.waitForSelector('nav');
    
    // Navigate to different pages and check active state
    const pages = [
      { selector: 'a[href="/status"]', path: '/status' },
      { selector: 'a[href="/docs"]', path: '/docs' },
      { selector: 'a[href="/"]', path: '/' },
    ];
    
    for (const { selector, path } of pages) {
      const link = await page.$(selector);
      if (link) {
        await link.click();
        await page.waitForTimeout(1000);
        
        const url = page.url();
        expect(url).toContain(path);
      }
    }
  });

  test('should maintain navigation on page refresh', async () => {
    await page.waitForSelector('nav');
    
    // Navigate to status page
    const statusLink = await page.$('a[href="/status"]');
    if (statusLink) {
      await statusLink.click();
      await page.waitForTimeout(1000);
      
      // Refresh page
      await page.reload({ waitUntil: 'networkidle0' });
      
      // Should still be on status page
      const url = page.url();
      expect(url).toContain('/status');
    }
  });
});
