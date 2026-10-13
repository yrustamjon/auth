import { test, expect } from '@playwright/test';

async function mock(page, getDevice) {
 await page.route('**/api/session/', r=>r.fulfill({json:{authenticated:true,panel:'admin',user:{id:1,username:'owner'},organizations:[{id:9,name:'Shaxsiy'}],organization_id:9,workspace:{kind:'personal',status:'approved',active:true}}}));
 await page.route('**/api/personal/', r=>r.fulfill({json:{user:{id:12,fio:'Owner',username:'owner',has_face:true,has_fingerprint:false},devices:[getDevice()],logs:[]}}));
 await page.route('**/api/downloads/', r=>r.fulfill({json:{releases:[{platform:'windows',available:true,download_url:'/api/downloads/windows/'}]}}));
}
const active={id:3,pc_id:'MY-PC',platform:'windows',location:'Uy',enrollment_status:'agent_enrolled',is_active:true,removal_state:'active'};

test('activated device shows management instead of activation instructions',async({page})=>{
 await mock(page,()=>active);await page.goto('/personal/computer');
 await expect(page.getByRole('heading',{name:'Kompyuteringiz foydalanishga tayyor'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Aktivatsiya tokenini olish'})).toHaveCount(0);
 await expect(page.getByRole('heading',{name:'Agentni yuklash va aktivatsiya qilish'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'O‘chirish kodini olish'})).toBeVisible();
});
test('poll sees activation and clears visible token',async({page})=>{
 let installed=false;
 await mock(page,()=>installed?active:{...active,enrollment_status:'manual_registered',is_active:false});
 await page.route('**/api/token/',r=>r.fulfill({json:{token:'temporary-token',expires_at:'2027-01-01T00:00:00Z'}}));
 await page.goto('/personal/computer');await page.getByRole('button',{name:'Aktivatsiya tokenini olish'}).click();
 await expect(page.getByLabel('Aktivatsiya tokeni',{exact:true})).toHaveValue('temporary-token');
 installed=true;
 await expect(page.getByRole('heading',{name:'Kompyuteringiz foydalanishga tayyor'})).toBeVisible({timeout:10000});
 await expect(page.getByLabel('Aktivatsiya tokeni',{exact:true})).toHaveCount(0);
});
test('pending removal blocks activation and code issuance',async({page})=>{
 await mock(page,()=>({...active,is_active:false,removal_state:'removal_pending'}));
 await page.goto('/personal/computer');
 await expect(page.getByRole('heading',{name:'O‘chirish yakunlanishi kutilmoqda'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Aktivatsiya tokenini olish'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'O‘chirish kodini olish'})).toHaveCount(0);
});

test('fingerprint addition shows a local QR and expires for retry',async({page})=>{
 await mock(page,()=>active);
 await page.route('**/api/users/12/biometric-status/',r=>r.fulfill({json:{has_face:true,has_fingerprint:false}}));
 await page.route('**/api/users/12/fingerprint/',r=>r.fulfill({json:[]}));
 await page.route('**/api/fingerprint/phone/start/',r=>r.fulfill({json:{session_id:'test-session',expires_in:2,status:'pending'}}));
 await page.goto('/personal/biometrics');
 await page.getByRole('button',{name:'Biometrikani sozlash',exact:true}).click();
 await page.getByRole('button',{name:'Barmoq izi',exact:true}).click();
 await page.getByRole('button',{name:'Phone — Ochish'}).click();
 await page.getByRole('button',{name:'Template qo‘shish'}).click();
 await expect(page.getByAltText('Barmoq izi qo‘shish uchun QR kod')).toHaveAttribute('src',/^data:image\/png;base64,/);
 await page.getByText('Telefon uchun havola',{exact:true}).click();
 await expect(page.getByLabel('Telefon tasdiqlash havolasi')).toHaveValue('http://127.0.0.1:5173/mobile/fingerprint/test-session/');
 await expect(page.getByText('Sessiya muddati tugadi. QR ni yangilang.',{exact:true})).toBeVisible({timeout:5000});
 await expect(page.getByRole('button',{name:'QR ni yangilash'})).toBeEnabled();
 await expect(page.getByAltText('Barmoq izi qo‘shish uchun QR kod')).toHaveCount(0);
});

test('legacy fingerprint source cards show separate forms on mobile',async({page})=>{
 await page.setViewportSize({width:390,height:900});
 await mock(page,()=>active);
 await page.route('**/api/users/12/biometric-status/',r=>r.fulfill({json:{has_face:true,has_fingerprint:true}}));
 await page.route('**/api/users/12/fingerprint/',r=>r.fulfill({json:[{id:5,source:'phone',created_at:'2026-10-11T12:00:00Z'}]}));
 await page.goto('/personal/biometrics');
 await page.getByRole('button',{name:'Biometrikani sozlash',exact:true}).click();
 await page.getByRole('button',{name:'Barmoq izi',exact:true}).click();
 for(const source of ['Manual','Phone','Scanner','External'])await expect(page.getByRole('button',{name:source+' — Ochish'})).toBeVisible();
 await page.getByRole('button',{name:'Phone — Ochish'}).click();
 await expect(page.getByText('Template #5',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Manual — Ochish'}).click();
 await expect(page.getByText('Template #5',{exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Template qo‘shish'}).click();
 await expect(page.getByText('Yangi Manual Template',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Saqlash',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Scanner — Ochish'}).click();
 await page.getByRole('button',{name:'Template qo‘shish'}).click();
 await expect(page.getByRole('button',{name:'Scannerni ulash'})).toBeDisabled();
 await page.getByRole('button',{name:'External — Ochish'}).click();
 await page.getByRole('button',{name:'Template qo‘shish'}).click();
 await expect(page.getByText('External Integration',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});
