import { test, expect } from '@playwright/test';

test.describe('Frontend Smoke Test', () => {
  test('Главная страница доступна и содержит relink', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await expect(page).toHaveTitle(/relink/i);
    await expect(page.locator('body')).toBeVisible();
  });
}); 