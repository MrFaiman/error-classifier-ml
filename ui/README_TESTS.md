# UI E2E Testing Guide

## Overview

End-to-end tests using Puppeteer for the error classification UI.

## Test Structure

```
tests/
├── setup.js              # Test configuration and utilities
├── jest.config.js        # Jest configuration
├── jest.setup.js         # Jest setup hooks
├── search.test.js        # Search page tests
├── navigation.test.js    # Navigation tests
├── status.test.js        # Status page tests
├── docs.test.js          # Manage docs tests
└── dataset.test.js       # Dataset management tests
```

## Prerequisites

### Install Dependencies

```bash
npm install --save-dev puppeteer jest
```

### Start Services

Before running tests, ensure both services are running:

```bash
# Terminal 1: Start API server
cd ../core
python3 src/server.py

# Terminal 2: Start UI dev server
cd ui
npm run dev
```

## Running Tests

### Run all tests

```bash
npm test
```

### Run specific test file

```bash
npm test -- search.test.js
```

### Run with visible browser

```bash
HEADLESS=false npm test
```

### Run in slow motion (for debugging)

```bash
SLOW_MO=100 npm test
```

### Run with custom URLs

```bash
TEST_BASE_URL=http://localhost:3000 TEST_API_URL=http://localhost:8080 npm test
```

## Test Coverage

### Search Page (search.test.js)
- ✅ Load page successfully
- ✅ Submit search query and display results
- ✅ Display response time after search
- ✅ Validate empty search query
- ✅ Switch search engines
- ✅ Toggle multi-search mode
- ✅ Handle API errors gracefully
- ✅ Open correction dialog

### Navigation (navigation.test.js)
- ✅ Navigate to all pages (search, dataset, docs, status)
- ✅ Highlight active navigation item
- ✅ Maintain navigation on page refresh

### Status Page (status.test.js)
- ✅ Load status page successfully
- ✅ Display system health status
- ✅ Display cache statistics
- ✅ Display search engine information
- ✅ Handle status API errors gracefully
- ✅ Refresh status data

### Manage Docs (docs.test.js)
- ✅ Load manage docs page successfully
- ✅ Display documentation list
- ✅ Open create document dialog
- ✅ Search/filter documentation
- ✅ Display documentation by service
- ✅ View document details
- ✅ Handle docs API errors

### Dataset Management (dataset.test.js)
- ✅ Load manage dataset page successfully
- ✅ Display dataset statistics
- ✅ Add new dataset entries
- ✅ Display dataset entries in table
- ✅ Edit dataset entries
- ✅ Delete dataset entries
- ✅ Validate dataset entry fields

## Configuration

### Environment Variables

Create `.env.test` file:

```bash
TEST_BASE_URL=http://localhost:5173
TEST_API_URL=http://localhost:3100
HEADLESS=true
SLOW_MO=0
```

### Test Selectors

Tests use data-testid attributes for stable element selection. Add to components:

```jsx
<button data-testid="search-button">Search</button>
<div data-testid="classification-result">...</div>
```

## Debugging

### Take screenshots on failure

Screenshots are automatically saved to `screenshots/` directory on test failures.

### Run with browser visible

```bash
HEADLESS=false npm test
```

### Add breakpoints

```javascript
test('my test', async () => {
  await page.goto(TEST_CONFIG.baseUrl);
  debugger; // Add debugger statement
  await page.click('button');
});
```

Run with:
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

### Console logs

View browser console in tests:

```javascript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

## Writing New Tests

### Basic Test Structure

```javascript
import puppeteer from 'puppeteer';
import { TEST_CONFIG, SELECTORS } from './setup.js';

describe('My Feature', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: TEST_CONFIG.headless,
      slowMo: TEST_CONFIG.slowMo,
    });
  });

  afterAll(async () => {
    await browser.close();
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.goto(TEST_CONFIG.baseUrl);
  });

  afterEach(async () => {
    await page.close();
  });

  test('should do something', async () => {
    await page.waitForSelector('button');
    await page.click('button');
    
    const text = await page.$eval('.result', el => el.textContent);
    expect(text).toContain('expected');
  });
});
```

### Useful Puppeteer Commands

```javascript
// Navigation
await page.goto(url);
await page.reload();
await page.goBack();
await page.goForward();

// Selectors
await page.waitForSelector('.my-class');
await page.click('button');
await page.type('input', 'text');
await page.$('div'); // querySelector
await page.$$('div'); // querySelectorAll

// Evaluation
const text = await page.$eval('.class', el => el.textContent);
const data = await page.evaluate(() => window.myData);

// Screenshots
await page.screenshot({ path: 'screenshot.png' });

// Network
await page.setRequestInterception(true);
page.on('request', req => req.continue());
page.on('response', res => console.log(res.url()));
```

## Best Practices

1. **Use data-testid attributes** for stable selectors
2. **Wait for elements** before interacting (waitForSelector)
3. **Handle async operations** properly (await all promises)
4. **Take screenshots on failure** for debugging
5. **Keep tests isolated** (no shared state between tests)
6. **Test user flows** not implementation details
7. **Mock API responses** for consistent test data
8. **Clean up resources** (close pages/browsers)

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: npm ci
      - name: Start services
        run: |
          cd core && python3 src/server.py &
          cd ui && npm run dev &
      - name: Run tests
        run: npm test
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: screenshots/
```

## Troubleshooting

### Tests timing out

- Increase timeout in jest.config.js
- Add `await page.waitForTimeout(1000)` after navigation
- Check if services are running

### Elements not found

- Verify selectors match actual DOM
- Use `await page.waitForSelector()` before interaction
- Check if element is visible: `await element.isIntersectingViewport()`

### API errors

- Ensure backend server is running on correct port
- Check CORS configuration
- Verify API endpoints in api.js

### Browser not launching

- Install Chrome/Chromium: `npx puppeteer browsers install chrome`
- Use `args: ['--no-sandbox']` on CI/Linux

## Performance Tips

- Reuse browser instance across tests
- Use `page.waitForSelector()` instead of `page.waitForTimeout()`
- Run tests in parallel with jest workers
- Mock API responses to avoid network delays
