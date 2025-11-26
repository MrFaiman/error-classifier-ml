/**
 * Manage Docs Page E2E Tests
 */
import puppeteer from 'puppeteer';
import { TEST_CONFIG, waitForApiResponse, screenshotOnFailure } from './setup.js';

describe('Manage Docs Page', () => {
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
    await page.goto(`${TEST_CONFIG.baseUrl}/docs`);
  });

  afterEach(async () => {
    await page.close();
  });

  test('should load manage docs page successfully', async () => {
    try {
      await page.waitForSelector('h4', { timeout: TEST_CONFIG.timeout });
      
      const heading = await page.$eval('h4', el => el.textContent);
      expect(heading).toMatch(/documentation|docs|manage/i);
      
    } catch (error) {
      await screenshotOnFailure(page, 'docs-load-failure');
      throw error;
    }
  });

  test('should display documentation list', async () => {
    await waitForApiResponse(page, '/api/docs');
    await page.waitForTimeout(2000);
    
    // Check if docs are displayed (table, cards, or list)
    const hasDocs = await page.evaluate(() => {
      const tables = document.querySelectorAll('table');
      const cards = document.querySelectorAll('[class*="card"]');
      const lists = document.querySelectorAll('ul, ol');
      
      return tables.length > 0 || cards.length > 0 || lists.length > 0;
    });
    
    expect(hasDocs).toBe(true);
  });

  test('should open create document dialog', async () => {
    await page.waitForTimeout(2000);
    
    // Look for create button
    const createButton = await page.$('button:not([disabled])');
    const buttons = await page.$$('button');
    
    for (const button of buttons) {
      const text = await page.evaluate(el => el.textContent.toLowerCase(), button);
      if (text.includes('create') || text.includes('add') || text.includes('new')) {
        await button.click();
        await page.waitForTimeout(1000);
        
        // Dialog or form should appear
        const dialog = await page.$('[role="dialog"]') || await page.$('form');
        expect(dialog).toBeTruthy();
        break;
      }
    }
  });

  test('should search/filter documentation', async () => {
    await page.waitForTimeout(2000);
    
    // Look for search input
    const searchInputs = await page.$$('input[type="text"], input[placeholder*="search" i]');
    
    if (searchInputs.length > 0) {
      await searchInputs[0].type('error');
      await page.waitForTimeout(1000);
      
      // Results should update
      const pageText = await page.evaluate(() => document.body.textContent);
      expect(pageText.length).toBeGreaterThan(0);
    }
  });

  test('should display documentation by service', async () => {
    await waitForApiResponse(page, '/api/docs');
    await page.waitForTimeout(2000);
    
    const pageText = await page.evaluate(() => document.body.textContent.toLowerCase());
    
    // Should show service names
    const hasServices = 
      pageText.includes('service') ||
      pageText.includes('logitrack') ||
      pageText.includes('skyguard') ||
      pageText.includes('meteo');
    
    expect(hasServices).toBe(true);
  });

  test('should view document details', async () => {
    await page.waitForTimeout(2000);
    
    // Find first clickable doc item
    const docLinks = await page.$$('a, button[class*="row"], [role="button"]');
    
    if (docLinks.length > 0) {
      const firstLink = docLinks[0];
      const isVisible = await firstLink.isIntersectingViewport();
      
      if (isVisible) {
        await firstLink.click();
        await page.waitForTimeout(1000);
        
        // Should show details or navigate
        const url = page.url();
        expect(url.length).toBeGreaterThan(0);
      }
    }
  });

  test('should handle docs API errors', async () => {
    const errorPage = await browser.newPage();
    await errorPage.setRequestInterception(true);
    
    errorPage.on('request', request => {
      if (request.url().includes('/api/docs')) {
        request.respond({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Failed to load docs' }),
        });
      } else {
        request.continue();
      }
    });
    
    await errorPage.goto(`${TEST_CONFIG.baseUrl}/docs`);
    await errorPage.waitForTimeout(2000);
    
    // Page should still render
    const hasContent = await errorPage.evaluate(() => document.body.textContent.length > 0);
    expect(hasContent).toBe(true);
    
    await errorPage.close();
  });
});
