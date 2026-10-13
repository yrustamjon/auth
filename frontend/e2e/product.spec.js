import { test, expect } from '@playwright/test';
for(const [name,panel,workspace,destination] of [
 ['personal','admin',{kind:'personal',status:'approved',active:true},'/personal/computer'],
 ['company','admin',{kind:'company',status:'approved',active:true},'/dashboard'],
 ['superadmin','superadmin',null,'/system/dashboard'],
 ['pending','admin',{kind:'company',status:'pending',active:false},'/registration/status'],
]) test('signed-in product navigation: '+name,async({page})=>{
 await page.route('**/api/session/',r=>r.fulfill({json:{authenticated:true,panel,workspace,user:{id:1,username:'owner'},organizations:[]}}));
 for(const path of ['/','/product','/downloads','/guide']){
  await page.goto(path);
  const header=page.locator('.product-header');
  await expect(header.getByRole('link',{name:'Ish maydonim',exact:true})).toHaveAttribute('href',destination);
  await expect(header.getByRole('link',{name:'Boshlash',exact:true})).toHaveCount(0);
  await expect(header.getByRole('button',{name:'Kirish',exact:true})).toHaveCount(0);
 }
});
for(const width of [1440,390]) test('public product site and login modal at '+width,async({page})=>{
 await page.setViewportSize({width,height:900});
 await page.route(url=>url.pathname==='/api/session/',r=>r.fulfill({json:{authenticated:false,panel:null,user:null,organizations:[]}}));
 await page.goto('/');
 await expect(page.getByRole('heading',{name:/yagona kirish nuqtasi/})).toBeVisible();
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button',{name:'Kirish',exact:true}).click();
 await expect(page).toHaveURL(/\/?\?login=admin$/);
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByLabel('Foydalanuvchi nomi',{exact:true}).fill('admin');
 await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog')).toHaveCount(0);
 for(const path of ['/product','/downloads','/guide']){
  await page.goto(path);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 }
 await page.goto('/downloads');
 await page.getByRole('link',{name:'PC uchun QR',exact:true}).click();
 await expect(page).toHaveURL(/\/device\/scan$/);
 await expect(page.getByRole('button',{name:'Yangi ulanishni boshlash'})).toBeVisible();
 await page.route('**/api/devices/browser-enrollment/session/',r=>r.fulfill({status:201,json:{session_id:'public-session',status:'pending',identity_ready:false,scan_token:'browser-secret',expires_at:'2026-10-10T12:00:00Z'}}));
 await page.getByRole('button',{name:'Yangi ulanishni boshlash'}).click();
 await expect(page.getByRole('button',{name:'Yordamchi paketni yuklash'})).toBeVisible();
 await expect(page).toHaveURL(/\/device\/scan$/);
 await page.goto('/');
 await page.screenshot({path:`artifacts/product-${width}.png`,fullPage:true});
});
