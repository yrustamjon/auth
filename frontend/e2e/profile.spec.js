import { test, expect } from '@playwright/test';

for (const [kind, panel, path] of [['personal', 'admin', '/personal/profile'], ['company', 'admin', '/profile'], ['company', 'superadmin', '/system/profile']]) {
  for (const width of [390, 1440]) test(`profile and password change for ${path} at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.route('**/api/session/', r => r.fulfill({ json: { authenticated: true, panel, user: { id: 1, username: 'owner' }, organizations: [{ id: 9, name: 'Test workspace' }], organization_id: 9, workspace: { kind, status: 'approved', active: true } } }));
    await page.route('**/api/profile/', r => r.fulfill({ json: { username: 'owner', account_type: panel === 'superadmin' ? 'superadmin' : kind === 'personal' ? 'personal' : 'admin', created_at: '2026-10-01T10:00:00Z', organizations: [{ id: 9, name: 'Test workspace' }] } }));
    let changes = 0;
    await page.route('**/api/profile/password/', r => {
      changes++;
      expect(r.request().postDataJSON()).toEqual({ current_password: 'Old-password829!', new_password: 'New-password937!', confirm_password: 'New-password937!' });
      return r.fulfill({ json: { detail: 'Parol yangilandi.' } });
    });
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1, name: 'Profil', exact: true })).toBeVisible();
    await expect(page.getByText('owner', { exact: true }).last()).toBeVisible();
    await page.getByLabel('Joriy parol', { exact: true }).fill('Old-password829!');
    await page.getByLabel('Yangi parol', { exact: true }).fill('New-password937!');
    await page.getByLabel('Yangi parolni tasdiqlang', { exact: true }).fill('New-password937!');
    await page.getByRole('button', { name: 'Parolni yangilash', exact: true }).click();
    await expect(page.getByRole('status')).toHaveText('Parol yangilandi.');
    await expect(page.getByLabel('Joriy parol', { exact: true })).toHaveValue('');
    expect(changes).toBe(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `artifacts/profile-${panel}-${kind}-${width}.png`, fullPage: true });
    if (width === 390) await page.getByRole('button', { name: 'Menyuni ochish' }).click();
    await expect(page.locator('.app-sidebar').getByRole('link', { name: 'Profil', exact: true })).toHaveAttribute('href', path);
  });
}
