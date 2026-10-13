import { test, expect } from '@playwright/test';

test('company admin obtains activation token on demand from profile', async ({ page }) => {
  await page.route('**/api/session/', r => r.fulfill({ json: { authenticated: true, panel: 'admin', user: { id: 1, username: 'owner' }, organization_id: 9, organizations: [{ id: 9, name: 'Company A' }], workspace: { kind: 'company', status: 'approved', active: true } } }));
  await page.route('**/api/profile/', r => r.fulfill({ json: { username: 'owner', account_type: 'admin', organizations: [{ id: 9, name: 'Company A' }], current_organization: { id: 9, name: 'Company A' } } }));
  let requests = 0;
  await page.route('**/api/token/', r => { requests++; return r.fulfill({ json: { token: 'company-activation-secret', expires_at: '2027-01-01T12:00:00Z' } }); });
  await page.goto('/profile');
  await expect(page.getByRole('button', { name: 'Agent aktivatsiya tokenini olish' })).toBeVisible();
  expect(requests).toBe(0);
  await page.getByRole('button', { name: 'Agent aktivatsiya tokenini olish' }).click();
  await expect(page.getByLabel('Agent aktivatsiya tokeni', { exact: true })).toHaveValue('company-activation-secret');
  await expect(page.getByRole('button', { name: 'Tokenni nusxalash' })).toBeVisible();
  expect(requests).toBe(1);
  expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain('company-activation-secret');
  await page.getByRole('button', { name: 'Tokenni yashirish' }).click();
  await expect(page.getByLabel('Agent aktivatsiya tokeni', { exact: true })).toHaveCount(0);
});
