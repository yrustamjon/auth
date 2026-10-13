import { test, expect } from '@playwright/test';
for(const width of [1440,390])test('access log details include cause and similarity at '+width,async({page})=>{
 await page.setViewportSize({width,height:900});
 await page.route(url=>url.pathname.startsWith('/api/'),r=>{
  const path=new URL(r.request().url()).pathname;
  return r.fulfill({json:path==='/api/session/'?{authenticated:true,panel:'admin',user:{username:'admin'},organizations:[]}:path==='/api/access-logs'?{logs:[
   {id:11,user_fio:'Ali Valiyev',device_pc_id:'PC-11',success:false,timestamp:'2026-10-13T10:00:00Z',cause:'Yuz tanilmadi (similarity=0.6500)',similarity:0.65,ip_address:'192.0.2.20',source:'mobile_web',device_snapshot:{pc_id:'PC-11',platform:'windows',identifiers:{machine_guid:'machine-11'}},request_context:{user_agent:'Mobile browser',client:{timezone:'Asia/Tashkent',screen:{width:390,height:844}},initiator:{ip_address:'192.0.2.10'}}},
   {id:12,user_fio:'Ali Valiyev',device_pc_id:'PC-11',success:true,timestamp:'2026-10-13T11:00:00Z',cause:'Yuz tasdiqlandi',similarity:null},
  ]}:[]});
 });
 await page.goto('/logs');
 await page.getByRole('row').filter({has:page.getByRole('button',{name:'Log #11 tafsilotlari'})}).getByText('PC-11').click();
 const modal=page.getByRole('dialog');
 await expect(modal).toContainText('Ali Valiyev');
 await expect(modal).toContainText('PC-11');
 await expect(modal).toContainText('Yuz tanilmadi');
 await expect(modal).toContainText('65.00%');
 await expect(modal).toContainText('192.0.2.20');
 await expect(modal).toContainText('192.0.2.10');
 await expect(modal).toContainText('machine-11');
 await expect(modal).toContainText('Asia/Tashkent');
 expect(await modal.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await modal.evaluate(async el=>{await Promise.all(el.getAnimations().map(animation=>animation.finished));});
 await page.screenshot({path:`artifacts/log-details-${width}.png`});
 await page.keyboard.press('Escape');
 await expect(modal).toHaveCount(0);
 await page.getByRole('button',{name:'Log #12 tafsilotlari'}).click();
 await expect(modal).toContainText('Saqlanmagan');
});
