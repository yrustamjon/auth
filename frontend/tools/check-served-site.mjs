import { chromium, expect } from '@playwright/test';
const browser=await chromium.launch({channel:'chrome',headless:true});
try {
 const page=await browser.newPage({extraHTTPHeaders:{'ngrok-skip-browser-warning':'true'}});
 const origin=process.env.SITE_CHECK_URL||'http://127.0.0.1:8000';
 await page.goto(origin+'/');
 await expect(page.getByRole('heading',{name:/yagona kirish nuqtasi/})).toBeVisible();
 await page.getByRole('button',{name:'Kirish',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.keyboard.press('Escape');
 await page.goto(origin+'/downloads');
 await expect(page.getByRole('link',{name:'Windows uchun yuklab olish'})).toHaveAttribute('href','/api/downloads/windows/');
 await page.screenshot({path:'artifacts/django-served-frontend.png',fullPage:true});
 await page.goto(origin+'/personal/computer');
 await expect(page.getByRole('dialog')).toBeVisible();
 console.log('Django-served homepage, login modal, installer catalog and protected deep link passed.');
} finally {await browser.close();}
