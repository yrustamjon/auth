import { test, expect } from '@playwright/test';
test('closed mobile sidebar is removed from keyboard navigation',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.route(url=>url.pathname.startsWith('/api/'),r=>r.fulfill({json:new URL(r.request().url()).pathname==='/api/session/'?{authenticated:true,panel:'admin',user:{username:'admin'},organizations:[]}:[]}));
 await page.goto('/users');
 await expect(page.locator('.app-sidebar')).toHaveAttribute('inert','');
 await page.getByRole('button',{name:'Menyuni ochish'}).click();
 await expect(page.locator('.app-sidebar')).not.toHaveAttribute('inert','');
 await page.keyboard.press('Escape');
 await expect(page.getByRole('button',{name:'Menyuni ochish'})).toBeFocused();
});
