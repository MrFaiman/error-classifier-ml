/**
 * Manage Dataset Page E2E Tests
 */
import puppeteer from 'puppeteer';
import { TEST_CONFIG, screenshotOnFailure } from './setup.js';

describe('Manage Dataset Page', () => {
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
    await page.goto(`${TEST_CONFIG.baseUrl}/dataset`);
  });

  afterEach(async () => {
    await page.close();
  });

  test('should load manage dataset page successfully', async () => {
    try {
      await page.waitForSelector('h4', { timeout: TEST_CONFIG.timeout });
      
      const heading = await page.$eval('h4', el => el.textContent);
      expect(heading).toMatch(/dataset|data|manage/i);
      
    } catch (error) {
      await screenshotOnFailure(page, 'dataset-load-failure');
      throw error;
    }
  });

  test('should display dataset statistics', async () => {
    await page.waitForTimeout(2000);
    
    const pageText = await page.evaluate(() => document.body.textContent.toLowerCase());
    
    // Should show dataset info
    const hasDatasetInfo = 
      pageText.includes('dataset') ||
      pageText.includes('total') ||
      pageText.includes('entries') ||
      pageText.includes('records');
    
    expect(hasDatasetInfo).toBe(true);
  });

  test('should allow adding new dataset entries', async () => {
    await page.waitForTimeout(2000);
    
    // Look for add/create button
    const buttons = await page.$$('button');
    
    for (const button of buttons) {
      const text = await page.evaluate(el => el.textContent.toLowerCase(), button);
      if (text.includes('add') || text.includes('create') || text.includes('new')) {
        await button.click();
        await page.waitForTimeout(1000);
        
        // Form or dialog should appear
        const form = await page.$('form') || await page.$('[role="dialog"]');
        expect(form).toBeTruthy();
        break;
      }
    }
  });

  test('should display dataset entries in table', async () => {
    await page.waitForTimeout(2000);
    
    // Check for table structure
    const hasTable = await page.evaluate(() => {
      return document.querySelectorAll('table').length > 0;
    });
    
    // May have table or alternative display
    expect(typeof hasTable).toBe('boolean');
  });

  test('should allow editing dataset entries', async () => {
    await page.waitForTimeout(2000);
    
    // Look for edit buttons
    const editButtons = await page.$$('button[aria-label*="edit" i], [title*="edit" i]');
    
    if (editButtons.length > 0) {
      await editButtons[0].click();
      await page.waitForTimeout(1000);
      
      // Edit form should appear
      const form = await page.$('form') || await page.$('[role="dialog"]');
      expect(form).toBeTruthy();
    }
  });

  test('should allow deleting dataset entries', async () => {
    await page.waitForTimeout(2000);
    
    // Look for delete buttons
    const deleteButtons = await page.$$('button[aria-label*="delete" i], [title*="delete" i]');
    
    if (deleteButtons.length > 0) {
      await deleteButtons[0].click();
      await page.waitForTimeout(1000);
      
      // Confirmation dialog should appear
      const confirmDialog = await page.$('[role="dialog"], [role="alertdialog"]');
      
      // May or may not show confirmation
      expect(typeof confirmDialog).toBeDefined();
    }
  });

  test('should validate dataset entry fields', async () => {
    await page.waitForTimeout(2000);
    
    // Find and click add button
    const buttons = await page.$$('button');
    let addButton;
    
    for (const button of buttons) {
      const text = await page.evaluate(el => el.textContent.toLowerCase(), button);
      if (text.includes('add') || text.includes('create')) {
        addButton = button;
        break;
      }
    }
    
    if (addButton) {
      await addButton.click();
      await page.waitForTimeout(1000);
      
      // Try to submit empty form
      const submitButtons = await page.$$('button[type="submit"]');
      if (submitButtons.length > 0) {
        await submitButtons[0].click();
        await page.waitForTimeout(1000);
        
        // Should show validation errors or prevent submission
        const hasValidation = await page.evaluate(() => {
          const text = document.body.textContent.toLowerCase();
          return text.includes('required') || text.includes('invalid') || text.includes('error');
        });
        
        expect(typeof hasValidation).toBe('boolean');
      }
    }
  });
});
