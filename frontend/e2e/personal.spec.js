import { test, expect } from '@playwright/test';
const profile={user:{id:12,fio:'Test Owner',username:'owner',has_face:false,has_fingerprint:false},devices:[{id:3,pc_id:'MY-PC',platform:'windows',location:'Shaxsiy kompyuter',enrollment_status:'browser_approved',is_active:false}],logs:[]};
async function personal(page,hasFace=false){
 await page.route('**/api/session/',r=>r.fulfill({json:{authenticated:true,panel:'admin',user:{id:1,username:'owner'},organizations:[{id:9,name:'Shaxsiy'}],organization_id:9,workspace:{kind:'personal',status:'approved',active:true}}}));
 await page.route('**/api/personal/',r=>r.fulfill({json:{...profile,user:{...profile.user,has_face:hasFace}}}));
 await page.route('**/api/downloads/',r=>r.fulfill({json:{releases:[{platform:'windows',available:true,version:'1.0.3',download_url:'/api/downloads/windows/'}]}}));
 await page.route('**/api/users/12/biometric-status/',r=>r.fulfill({json:{has_face:hasFace,has_fingerprint:false}}));
 await page.route('**/api/users/12/fingerprint/',r=>r.fulfill({json:[]}));
}
for(const width of [1440,390])test('personal menu and onboarding fit '+width,async({page})=>{
 await page.setViewportSize({width,height:950});await personal(page);
 await page.goto('/dashboard');await expect(page).toHaveURL(/\/personal\/computer$/);
 if(width===390)await page.getByRole('button',{name:'Menyuni ochish'}).click();
 await expect(page.getByRole('link',{name:'Mening kompyuterim',exact:true}).first()).toBeVisible();
 await expect(page.locator('.app-sidebar').getByRole('link',{name:'Foydalanuvchilar',exact:true})).toHaveCount(0);
 await expect(page.locator('.app-sidebar').getByRole('link',{name:'Rollar va ruxsatlar'})).toHaveCount(0);
 if(width===390)await page.keyboard.press('Escape');
 await expect(page.getByRole('button',{name:'Aktivatsiya tokenini olish'})).toBeDisabled();
 await page.screenshot({path:`artifacts/personal-computer-${width}.png`,fullPage:true});
 await page.getByRole('link',{name:'Biometrikani sozlash',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Biometrikam',exact:true,level:1})).toBeVisible();
 await page.getByRole('button',{name:'Biometrikani sozlash',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:`artifacts/personal-${width}.png`,fullPage:true});
 await page.goto('/roles');await expect(page).toHaveURL(/\/personal\/computer$/);
});
test('personal activation token is loaded on demand and not persisted',async({page})=>{
 await personal(page,true);let requests=0;
 await page.route('**/api/token/',r=>{requests++;return r.fulfill({json:{token:'test-activation-token',expires_at:'2027-01-01T12:00:00Z'}});});
 await page.goto('/personal/computer');
 await expect(page.getByRole('link',{name:'Agentni yuklab olish',exact:true})).toHaveAttribute('href','/api/downloads/windows/');
 expect(requests).toBe(0);
 await page.getByRole('button',{name:'Aktivatsiya tokenini olish'}).click();
 await expect(page.getByLabel('Aktivatsiya tokeni',{exact:true})).toHaveValue('test-activation-token');
 expect(requests).toBe(1);
 const stored=await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}));expect(stored).not.toContain('test-activation-token');
 await page.getByRole('link',{name:'Kirish tarixim',exact:true}).first().click();
 await expect(page.getByRole('heading',{name:'Kirish tarixim',exact:true,level:1})).toBeVisible();
 await page.goto('/personal/computer');await expect(page.getByLabel('Aktivatsiya tokeni',{exact:true})).toHaveCount(0);
});
