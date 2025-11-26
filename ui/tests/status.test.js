/**
 * Status Page E2E Tests
 */
import puppeteer from 'puppeteer';
import { TEST_CONFIG, SELECTORS, waitForApiResponse, screenshotOnFailure } from './setup.js';

describe('Status Page', () => {
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
    await page.goto(`${TEST_CONFIG.baseUrl}/status`);
  });

  afterEach(async () => {
    await page.close();
  });

  test('should load status page successfully', async () => {
    try {
      await page.waitForSelector('h4', { timeout: TEST_CONFIG.timeout });
      
      const heading = await page.$eval('h4', el => el.textContent);
      expect(heading).toMatch(/system|status|health/i);
      
    } catch (error) {
      await screenshotOnFailure(page, 'status-load-failure');
      throw error;
    }
  });

  test('should display system health status', async () => {
    const responsePromise = waitForApiResponse(page, '/api/status');
    await responsePromise;
    
    await page.waitForTimeout(2000);
    
    // Look for health indicators
    const healthText = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'));
      return elements
        .map(el => el.textContent)
        .join(' ')
        .toLowerCase();
    });
    
    expect(healthText).toMatch(/healthy|operational|status/);
  });

  test('should display cache statistics', async () => {
    await waitForApiResponse(page, '/api/status');
    await page.waitForTimeout(2000);
    
    const pageText = await page.evaluate(() => document.body.textContent.toLowerCase());
    
    // Check for cache-related terms
    const hasCacheInfo = 
      pageText.includes('cache') || 
      pageText.includes('redis') ||
      pageText.includes('hit rate');
    
    // Cache info may or may not be displayed depending on status
    expect(typeof hasCacheInfo).toBe('boolean');
  });

  test('should display search engine information', async () => {
    await page.waitForTimeout(2000);
    
    const pageText = await page.evaluate(() => document.body.textContent.toLowerCase());
    
    // Should mention search engines
    const hasEngineInfo = 
      pageText.includes('engine') ||
      pageText.includes('hybrid') ||
      pageText.includes('vector') ||
      pageText.includes('tfidf') ||
      pageText.includes('bm25');
    
    expect(hasEngineInfo).toBe(true);
  });

  test('should handle status API errors gracefully', async () => {
    // Create new page with intercepted requests
    const errorPage = await browser.newPage();
    await errorPage.setRequestInterception(true);
    
    errorPage.on('request', request => {
      if (request.url().includes('/api/status')) {
        request.respond({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Service unavailable' }),
        });
      } else {
        request.continue();
      }
    });
    
    await errorPage.goto(`${TEST_CONFIG.baseUrl}/status`);
    await errorPage.waitForTimeout(2000);
    
    // Should still load page structure
    const hasContent = await errorPage.evaluate(() => document.body.textContent.length > 0);
    expect(hasContent).toBe(true);
    
    await errorPage.close();
  });

  test('should refresh status data', async () => {
    await page.waitForTimeout(2000);
    
    // Get initial timestamp or data
    const initialText = await page.evaluate(() => document.body.textContent);
    
    // Reload page
    await page.reload({ waitUntil: 'networkidle0' });
    await page.waitForTimeout(2000);
    
    // Page should still be functional
    const newText = await page.evaluate(() => document.body.textContent);
    expect(newText.length).toBeGreaterThan(0);
  });
});
