import { test, expect } from '@playwright/test';
test('downloads links to actual agent installer and marks unreleased OS',async({page})=>{
 await page.route('**/api/downloads/',r=>r.fulfill({json:{releases:[{platform:'windows',version:'1.0.3',available:true,prerelease:true,filename:'BioGuard_Setup_v1.0.3.exe',size:60825007,sha256:'75d22d7e',download_url:'/api/downloads/windows/'},{platform:'macos',version:'0.0.0',available:false},{platform:'linux',version:'0.0.0',available:false}]}}));
 await page.goto('/downloads');
 const download=page.getByRole('link',{name:'Windows uchun yuklab olish'});
 await expect(download).toHaveAttribute('href','/api/downloads/windows/');
 await expect(page.getByText('BioGuard_Setup_v1.0.3.exe')).toBeVisible();
 await expect(page.getByText('Hali chiqarilmagan',{exact:true})).toHaveCount(2);
 await expect(page.getByRole('link',{name:'Paketni olish'})).toHaveCount(0);
});
