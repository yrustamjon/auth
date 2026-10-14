import { test, expect } from '@playwright/test';

async function usersPage(page) {
  const users = Array.from({ length: 23 }, (_, i) => ({
    id: i + 1, fio: `Xodim ${i + 1}`, username: `user${i + 1}`, lavozim: 'Dasturchi',
    status: i < 12, role: { id: i % 2 + 1, name: i % 2 ? 'Rahbar' : 'Xodim' },
  }));
  await page.route(url => url.pathname.startsWith('/api/'), route => {
    const path = new URL(route.request().url()).pathname;
    const json = path === '/api/session/'
      ? { authenticated: true, panel: 'admin', user: { id: 1, username: 'admin' }, organization_id: 1, organizations: [{ id: 1, name: 'Ofis' }] }
      : path === '/api/users/' ? { users }
      : path === '/api/roles' ? [{ id: 1, name: 'Xodim' }, { id: 2, name: 'Rahbar' }] : [];
    return route.fulfill({ json });
  });
  await page.goto('/users');
}

test('table pages through all records and search resets to the first page', async ({ page }) => {
  await usersPage(page);
  await expect(page.locator('tbody tr')).toHaveCount(10);
  await page.screenshot({ path: 'artifacts/pagination-desktop.png', fullPage: true });
  await expect(page.getByRole('button', { name: 'Oldingi' })).toBeDisabled();
  await page.getByRole('button', { name: 'Keyingi' }).click();
  await expect(page.locator('tbody tr').first()).toContainText('Xodim 11');
  await page.getByRole('button', { name: 'Keyingi' }).click();
  await expect(page.locator('tbody tr')).toHaveCount(3);
  await expect(page.getByRole('button', { name: 'Keyingi' })).toBeDisabled();
  await page.getByLabel('Qidirish', { exact: true }).fill('Xodim 1');
  await expect(page.locator('tbody tr')).toHaveCount(10);
  await expect(page.locator('tbody tr').first()).toContainText('Xodim 1');
  await expect(page.getByRole('button', { name: 'Oldingi' })).toBeDisabled();
  await page.getByLabel('Qidirish', { exact: true }).fill('');
  await page.getByRole('button', { name: '3-sahifa' }).click();
  await expect(page.locator('tbody tr')).toHaveCount(3);
  await page.getByLabel('Sahifadagi yozuvlar soni').selectOption('25');
  await expect(page.locator('tbody tr')).toHaveCount(23);
  await expect(page.getByRole('button', { name: 'Oldingi' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Keyingi' })).toBeDisabled();
});

test('status and role filters combine before pagination and can recover from empty results', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await usersPage(page);
  await page.getByRole('button', { name: 'Keyingi' }).click();
  await page.getByLabel('Holat filtri').selectOption('false');
  await expect(page.locator('tbody tr')).toHaveCount(10);
  await expect(page.locator('tbody tr').first()).toContainText('Xodim 13');
  await expect(page.getByRole('button', { name: 'Oldingi' })).toBeDisabled();
  await page.getByLabel('Rol filtri').selectOption('2');
  await expect(page.locator('tbody tr')).toHaveCount(5);
  await page.screenshot({ path: 'artifacts/pagination-active-mobile.png', fullPage: true });
  await expect(page.locator('tbody tr').first()).toContainText('Xodim 14');
  await page.getByLabel('Qidirish', { exact: true }).fill('Xodim 1');
  await expect(page.locator('tbody tr')).toHaveCount(3);
  await page.getByLabel('Qidirish', { exact: true }).fill('Xodim 13');
  await expect(page.locator('tbody tr')).toHaveCount(0);
  await expect(page.getByLabel('Rol filtri')).toBeVisible();
  await page.getByRole('button', { name: 'Filtrlarni tozalash' }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'artifacts/pagination-filters-mobile.png', fullPage: true });
});
