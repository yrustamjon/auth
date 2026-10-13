import { test, expect } from '@playwright/test';
test.beforeEach(async({page})=>{
 await page.route(url=>url.pathname==='/api/session/',r=>r.fulfill({json:{authenticated:false,panel:null,organizations:[]}}));
});
test('personal registration requires helper PC and sends its session',async({page})=>{
 await page.route('**/api/devices/browser-enrollment/session/',r=>r.fulfill({status:201,json:{session_id:'owned-pc',status:'pending',identity_ready:false,scan_token:'secret',expires_at:'2026-10-10T12:00:00Z'}}));
 await page.route('**/api/devices/browser-enrollment/session/owned-pc/',r=>r.fulfill({json:{session_id:'owned-pc',status:'pending',identity_ready:true,hostname:'My PC',expires_at:'2026-10-10T12:00:00Z'}}));
 let submitted;
 await page.route('**/api/register/',async r=>{submitted=r.request().postDataJSON();await r.fulfill({status:201,json:{redirect:'/dashboard'}});});
 await page.goto('/?register=personal');
 await expect(page.getByRole('dialog')).toBeVisible();
 await expect(page.getByRole('button',{name:'Davom etish',exact:true})).toBeVisible();
 await page.getByLabel('To‘liq ism').fill('Test Owner');
 await page.getByLabel('Yangi login').fill('new-owner');
 await page.getByLabel('Yangi parol').fill('Strong!Password729');
 await page.getByRole('button',{name:'Davom etish',exact:true}).click();
 await expect(page.getByRole('button',{name:'Hisob yaratish',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Yangi ulanishni boshlash'}).click();
 await expect(page.getByRole('button',{name:'Hisob yaratish',exact:true})).toBeEnabled({timeout:7000});
 await page.getByRole('button',{name:'Hisob yaratish',exact:true}).click();
 await expect.poll(()=>submitted?.enrollment_session_id).toBe('owned-pc');
 expect(submitted.kind).toBe('personal');
});
test('company registration shows review waiting state',async({page})=>{
 await page.route('**/api/register/',r=>r.fulfill({status:201,json:{redirect:'/registration/status'}}));
 await page.route('**/api/registration/status/',r=>r.fulfill({json:{name:'Example Co',kind:'company',status:'pending',active:false}}));
 await page.goto('/?register=company');
 await page.getByLabel('To‘liq ism').fill('Company Owner');
 await page.getByLabel('Yangi login').fill('company-owner');
 await page.getByLabel('Yangi parol').fill('Strong!Password729');
 await page.getByLabel('Kompaniya nomi',{exact:true}).fill('Example Co');
 await page.getByRole('button',{name:'Ariza yuborish'}).click();
 await expect(page).toHaveURL(/\/registration\/status$/);
 await expect(page.getByRole('heading',{name:'Tasdiqlash kutilmoqda'})).toBeVisible();
});
test('system review queue submits an explicit decision',async({page})=>{
 await page.route('**/api/session/',r=>r.fulfill({json:{authenticated:true,panel:'superadmin',user:{username:'system'},organizations:[]}}));
 let action;
 await page.route('**/api/registration/applications/',r=>r.fulfill({json:{applications:[{id:7,name:'Example Co',owner:'owner',status:'pending',created_at:'2026-10-10T10:00:00Z'}]}}));
 await page.route('**/api/registration/7/decision/',async r=>{action=r.request().postDataJSON().action;await r.fulfill({json:{status:'approved'}});});
 await page.goto('/system/applications');
 await page.getByRole('button',{name:'Tasdiqlash',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByRole('dialog').getByRole('button',{name:'Tasdiqlash',exact:true}).click();
 await expect.poll(()=>action).toBe('approve');
});
