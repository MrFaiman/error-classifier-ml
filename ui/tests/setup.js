/**
 * Test Setup and Utilities
 */

export const TEST_CONFIG = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:5173',
  apiUrl: process.env.TEST_API_URL || 'http://localhost:3100',
  timeout: 30000,
  slowMo: process.env.SLOW_MO ? parseInt(process.env.SLOW_MO) : 0,
  headless: process.env.HEADLESS !== 'false',
};

export const SELECTORS = {
  // Navigation
  navHome: '[data-testid="nav-home"]',
  navSearch: '[data-testid="nav-search"]',
  navDataset: '[data-testid="nav-dataset"]',
  navDocs: '[data-testid="nav-docs"]',
  navStatus: '[data-testid="nav-status"]',
  
  // Search Page
  searchInput: 'textarea[name="error_message"]',
  searchButton: 'button[type="submit"]',
  engineSelect: 'div[role="combobox"]',
  multiSearchCheckbox: 'input[type="checkbox"]',
  
  // Results
  resultCard: '[data-testid="classification-result"]',
  documentationPreview: '[data-testid="documentation-preview"]',
  responseTimeChip: '[data-testid="response-time"]',
  correctionButton: '[data-testid="correction-button"]',
  
  // Manage Docs Page
  docsTable: 'table',
  createDocButton: '[data-testid="create-doc-button"]',
  editDocButton: '[data-testid="edit-doc-button"]',
  deleteDocButton: '[data-testid="delete-doc-button"]',
  
  // Status Page
  statusCard: '[data-testid="status-card"]',
  healthIndicator: '[data-testid="health-indicator"]',
  engineComparisonTable: '[data-testid="engine-comparison-table"]',
};

/**
 * Wait for API response
 */
export async function waitForApiResponse(page, url) {
  return page.waitForResponse(
    response => response.url().includes(url) && response.status() === 200,
    { timeout: TEST_CONFIG.timeout }
  );
}

/**
 * Wait for navigation to complete
 */
export async function waitForNavigation(page, url) {
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0' }),
    page.goto(url),
  ]);
}

/**
 * Take screenshot on failure
 */
export async function screenshotOnFailure(page, testName) {
  const filename = `screenshots/${testName.replace(/\s+/g, '-')}-${Date.now()}.png`;
  await page.screenshot({ path: filename, fullPage: true });
  console.log(`Screenshot saved: ${filename}`);
}

/**
 * Clear browser storage
 */
export async function clearStorage(page) {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Mock API response
 */
export async function mockApiResponse(page, endpoint, response) {
  await page.setRequestInterception(true);
  page.on('request', request => {
    if (request.url().includes(endpoint)) {
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    } else {
      request.continue();
    }
  });
}
