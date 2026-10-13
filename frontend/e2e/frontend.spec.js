import { test, expect } from '@playwright/test';
const orgs=[{id:1,name:'Toshkent universiteti',slug:'tashkent',active:true,admin_count:2,created_at:'2026-10-01T10:00:00Z'},{id:2,name:'Raqamli texnologiyalar markazi',slug:'digital',active:false,admin_count:1,created_at:'2026-09-25T10:00:00Z'}];
const users=[{id:1,fio:'Aziz Karimov',username:'aziz',lavozim:'Dasturchi',role:{id:1,name:'Xodim'},status:true,has_face:true,has_fingerprint:false}];
const roles=[{id:1,name:'Xodim',is_active:true,created_at:'2026-09-25'}];
const devices=[{id:1,pc_id:'DESKTOP-TECH-01',license:'WIN-001',location:'Toshkent, 2-qavat',platform:'windows',is_active:true,enrollment_status:'agent_enrolled',last_seen:'2026-10-10T09:10:00Z'},{id:2,pc_id:'MAC-STUDIO-02',location:'Dizayn bo‘limi',platform:'macos',is_active:false,enrollment_status:'browser_approved'}];
const logs=[{id:1,user_fio:'Aziz Karimov',device_pc_id:'DESKTOP-TECH-01',timestamp:'2026-10-10T09:10:00Z',success:true},{id:2,user_fio:'Dilshod Aliyev',device_pc_id:'OFFICE-PC-03',timestamp:'2026-10-10T08:40:00Z',success:false}];
async function api(page,panel='admin'){
 await page.route(url => url.pathname.startsWith('/api/'),async route=>{
  const url=new URL(route.request().url());let data={ok:true};
  if(url.pathname==='/api/session/')data={authenticated:panel!==null,panel,user:panel?{id:1,username:'admin'}:null,organization_id:1,organizations:[{id:1,name:orgs[0].name}]};
  else if(url.pathname==='/api/users/')data={users};
  else if(url.pathname==='/api/roles')data=roles;
  else if(url.pathname==='/api/devices')data=devices;
  else if(url.pathname==='/api/access-logs')data={logs};
  else if(url.pathname==='/api/organizations/')data=orgs;
  else if(url.pathname==='/api/system/admins/')data=[{id:1,username:'admin',organization:['Toshkent universiteti'],superadmin:false,locked:false,failed_attempts:0,created_at:'2026-10-01'}];
  else if(url.pathname.includes('biometric-status'))data={has_face:true};
  else if(url.pathname.includes('/fingerprint/'))data=[];
  await route.fulfill({json:data});
 });
}
test('login renders, toggles password and retains incorrect-password error',async({page})=>{
 await api(page,null);
 await page.route('**/api/admin/login',r=>r.fulfill({status:401,json:{detail:'Password incorrect'}}));
 await page.goto('/login');
 await page.getByLabel('Foydalanuvchi nomi',{exact:true}).fill('admin');
 await page.getByLabel('Parol',{exact:true}).fill('wrong');
 await page.getByRole('button',{name:'Parolni ko‘rsatish'}).click();
 await expect(page.locator('#password')).toHaveAttribute('type','text');
 await page.getByRole('button',{name:'Hisobga kirish'}).click();
 await expect(page.getByRole('alert')).toContainText('Password incorrect');
 await expect(page).toHaveURL(/\/?\?login=admin$/);
 await page.screenshot({path:'artifacts/login-desktop.png',fullPage:true});
});
test('anonymous admin route redirects and wrong-panel access stays separated',async({page})=>{
 await api(page,null);await page.goto('/users');await expect(page).toHaveURL(/\/?\?login=admin$/);
 await api(page,'admin');await page.goto('/system/admins');await expect(page).toHaveURL(/\/dashboard$/);
});
for(const width of [1440,390]){
 for(const panel of ['admin','superadmin']){
  test(panel+' pages and modals fit '+width+'px',async({page})=>{
   await page.setViewportSize({width,height:1000});await api(page,panel);
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   const paths=panel==='admin'?['/dashboard','/users','/roles','/devices','/logs']:['/system/dashboard','/system/organizations','/system/admins'];
   for(const path of paths){
    await page.goto(path);await expect(page.locator('.app-header')).toBeVisible();
    await expect(page.locator('.page-container')).toBeVisible();
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    if(path.endsWith('dashboard'))await page.screenshot({path:'artifacts/'+panel+'-dashboard-'+width+'.png',fullPage:true});
   }
   if(width===390){await page.getByRole('button',{name:'Menyuni ochish'}).click();await expect(page.locator('.app-sidebar')).toHaveClass(/is-open/);await page.keyboard.press('Escape');await expect(page.locator('.app-sidebar')).not.toHaveClass(/is-open/);}
   await page.goto(panel==='admin'?'/users':'/system/organizations');
   await page.getByRole('button',{name:/Qo'shish|qo'shish/}).first().click();
   await expect(page.getByRole('dialog')).toBeVisible();
   await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
   expect(errors).toEqual([]);
  });
 }
}
test('partial dashboard failure is unavailable rather than zero',async({page})=>{
 await api(page);await page.route('**/api/devices',r=>r.fulfill({status:500,json:{detail:'offline'}}));await page.goto('/dashboard');
 await expect(page.locator('.stat-card').nth(2)).toContainText('—');
 await expect(page.locator('.stat-card').nth(2)).toContainText('Yuklab bo‘lmadi');
});
test('QR approval reaches terminal state and displays real device identity',async({page})=>{
 await api(page);
 const enrollment={session_id:'session-1',status:'pending',identity_ready:true,hostname:'OFFICE-PC',device_id:'machine-1',display_code:'123456',platform:'windows',identifiers:{machine_guid:'machine-1'},location:'Unknown'};
 await page.route('**/api/devices/browser-enrollment/claim/',r=>r.fulfill({json:{enrollment,organization:orgs[0]}}));
 await page.route('**/api/devices/browser-enrollment/session/session-1/approve/',r=>r.fulfill({json:{...enrollment,status:'approved'}}));
 await page.goto('/device-enroll/abcdefghijklmnopqrstuv');
 await expect(page.getByText('123456',{exact:true})).toBeVisible();
 await page.getByLabel('Joylashuv').fill('Ofis 1');await page.getByRole('button',{name:'Tasdiqlash',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('Qurilma tasdiqlandi');
 await expect(page.getByRole('button',{name:'Tasdiqlash',exact:true})).toHaveCount(0);
});
test('phone and QR public pages render on mobile',async({page})=>{
 await page.setViewportSize({width:390,height:844});await api(page,null);
 await page.route('**/api/fingerprint/phone/options/**',r=>r.fulfill({json:{challenge:'eHh4',rp_id:'127.0.0.1',origin:'http://127.0.0.1:5173',user_id:'MQ',username:'aziz'}}));
 await page.goto('/mobile/fingerprint/1/');await expect(page.getByRole('button',{name:'Tekshiruvni boshlash'})).toBeVisible();
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.goto('/device/scan');await expect(page.getByRole('button',{name:'Yangi ulanishni boshlash'})).toBeVisible();
});


test('administrator API failure stays an error instead of false empty result',async({page})=>{
 await api(page,'superadmin');await page.route('**/api/system/admins/',r=>r.fulfill({status:500,json:{detail:'offline'}}));await page.goto('/system/admins');
 await expect(page.getByRole('alert')).toContainText('Administratorlarni yuklab bo‘lmadi');
});
test('organization attachment is guarded while backend toggle is pending',async({page})=>{
 await api(page,'superadmin');await page.goto('/system/admins');await page.getByRole('button',{name:'Tahrirlash'}).first().click();await page.getByRole('button',{name:'Tashkilotlar',exact:true}).click();
 await page.locator('select').last().selectOption('2');
 let release;const gate=new Promise(resolve=>release=resolve);let calls=0;
 await page.route('**/api/system/admins/1/?organization_id=2',async r=>{calls++;await gate;await r.fulfill({json:{ok:true}});});
 const button=page.getByRole('button',{name:'Biriktirish',exact:true});await button.click();await expect(button).toBeDisabled();expect(calls).toBe(1);release();
});
test('user creation exposes only supported status settings',async({page})=>{
 await api(page);await page.goto('/users');await page.getByRole('button',{name:"Qo'shish",exact:true}).click();
 await expect(page.getByRole('dialog').getByLabel('Faol holat')).toHaveCount(0);
});
