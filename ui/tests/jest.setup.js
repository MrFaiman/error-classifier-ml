/**
 * Jest Setup
 */
import { mkdir } from 'fs/promises';
import { join } from 'path';

// Create screenshots directory
beforeAll(async () => {
  try {
    await mkdir(join(process.cwd(), 'screenshots'), { recursive: true });
  } catch (error) {
    // Directory might already exist
  }
});

// Set default timeout
jest.setTimeout(30000);

// Global test utilities
global.sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
