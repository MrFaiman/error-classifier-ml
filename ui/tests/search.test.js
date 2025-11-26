/**
 * Search Page E2E Tests
 */
import puppeteer from 'puppeteer';
import { TEST_CONFIG, SELECTORS, waitForApiResponse, screenshotOnFailure, clearStorage } from './setup.js';

describe('Search Page', () => {
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

  test('should load search page successfully', async () => {
    await page.waitForSelector(SELECTORS.searchInput, { timeout: TEST_CONFIG.timeout });
    
    const title = await page.title();
    expect(title).toContain('Error Classifier');
    
    const searchInput = await page.$(SELECTORS.searchInput);
    expect(searchInput).toBeTruthy();
  });

  test('should submit search query and display results', async () => {
    try {
      // Enter search query
      await page.waitForSelector(SELECTORS.searchInput);
      await page.type(SELECTORS.searchInput, 'sensor malfunction error');
      
      // Click search button
      const responsePromise = waitForApiResponse(page, '/api/classify');
      await page.click(SELECTORS.searchButton);
      await responsePromise;
      
      // Wait for results
      await page.waitForSelector(SELECTORS.resultCard, { timeout: 10000 });
      
      // Verify result is displayed
      const resultCard = await page.$(SELECTORS.resultCard);
      expect(resultCard).toBeTruthy();
      
      // Verify documentation preview
      const docPreview = await page.$(SELECTORS.documentationPreview);
      expect(docPreview).toBeTruthy();
      
    } catch (error) {
      await screenshotOnFailure(page, 'search-submit-failure');
      throw error;
    }
  });

  test('should display response time after search', async () => {
    await page.waitForSelector(SELECTORS.searchInput);
    await page.type(SELECTORS.searchInput, 'test error');
    
    const responsePromise = waitForApiResponse(page, '/api/classify');
    await page.click(SELECTORS.searchButton);
    await responsePromise;
    
    await page.waitForSelector(SELECTORS.resultCard);
    
    // Check for response time chip
    const responseTimeChip = await page.$(SELECTORS.responseTimeChip);
    expect(responseTimeChip).toBeTruthy();
    
    const responseTimeText = await page.$eval(
      SELECTORS.responseTimeChip,
      el => el.textContent
    );
    expect(responseTimeText).toMatch(/\d+ms/);
  });

  test('should validate empty search query', async () => {
    await page.waitForSelector(SELECTORS.searchButton);
    
    // Try to submit without entering text
    await page.click(SELECTORS.searchButton);
    
    // Should show validation message or prevent submission
    await page.waitForTimeout(1000);
    
    // Result should not appear
    const resultCard = await page.$(SELECTORS.resultCard);
    expect(resultCard).toBeFalsy();
  });

  test('should switch search engines', async () => {
    await page.waitForSelector(SELECTORS.engineSelect);
    
    // Click engine selector
    await page.click(SELECTORS.engineSelect);
    await page.waitForTimeout(500);
    
    // Select different engine (if options available)
    const options = await page.$$('li[role="option"]');
    if (options.length > 1) {
      await options[1].click();
      await page.waitForTimeout(500);
    }
  });

  test('should toggle multi-search mode', async () => {
    await page.waitForSelector(SELECTORS.multiSearchCheckbox);
    
    // Get initial state
    const initialChecked = await page.$eval(
      SELECTORS.multiSearchCheckbox,
      el => el.checked
    );
    
    // Toggle checkbox
    await page.click(SELECTORS.multiSearchCheckbox);
    await page.waitForTimeout(300);
    
    // Verify state changed
    const newChecked = await page.$eval(
      SELECTORS.multiSearchCheckbox,
      el => el.checked
    );
    expect(newChecked).toBe(!initialChecked);
  });

  test('should handle API errors gracefully', async () => {
    // Navigate to search page
    await page.waitForSelector(SELECTORS.searchInput);
    
    // Intercept API call and return error
    await page.setRequestInterception(true);
    page.on('request', request => {
      if (request.url().includes('/api/classify')) {
        request.respond({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      } else {
        request.continue();
      }
    });
    
    // Submit search
    await page.type(SELECTORS.searchInput, 'test error');
    await page.click(SELECTORS.searchButton);
    
    // Should show error message
    await page.waitForTimeout(2000);
    
    // Result should not appear
    const resultCard = await page.$(SELECTORS.resultCard);
    expect(resultCard).toBeFalsy();
  });

  test('should open correction dialog', async () => {
    await page.waitForSelector(SELECTORS.searchInput);
    await page.type(SELECTORS.searchInput, 'sensor error');
    
    const responsePromise = waitForApiResponse(page, '/api/classify');
    await page.click(SELECTORS.searchButton);
    await responsePromise;
    
    await page.waitForSelector(SELECTORS.resultCard);
    
    // Click correction button if available
    const correctionButton = await page.$(SELECTORS.correctionButton);
    if (correctionButton) {
      await correctionButton.click();
      await page.waitForTimeout(500);
      
      // Dialog should appear
      const dialog = await page.$('[role="dialog"]');
      expect(dialog).toBeTruthy();
    }
  });
});
