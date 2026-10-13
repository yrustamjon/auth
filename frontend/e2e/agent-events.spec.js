import {test,expect} from '@playwright/test';
for(const width of [1440,390])test('agent alerts and pause permission fit '+width,async({page})=>{
 await page.setViewportSize({width,height:900});
 let permission;
 const event={id:1,kind:'connection_lost',title:'Agent bilan aloqa yo‘qoldi — sabab aniqlanmagan',severity:'warning',timestamp:new Date().toISOString(),device_pc_id:'PC-T',ip_address:'192.0.2.10',details:{last_heartbeat:'2026-10-13T10:00:00Z'}};
 await page.route(url=>url.pathname.startsWith('/api/'),async r=>{
  const path=new URL(r.request().url()).pathname;
  if(path.endsWith('/pause-permission/')){permission=r.request().postDataJSON();return r.fulfill({json:{pause_until:new Date().toISOString()}});}
  return r.fulfill({json:path==='/api/session/'?{authenticated:true,panel:'admin',user:{username:'admin'},organizations:[]}:path==='/api/agent-events/'?{events:[event],devices:[{id:1,pc_id:'PC-T'}]}:[]});
 });
 await page.goto('/agent-events');
 await expect(page.getByRole('status')).toContainText('PC-T');
 await page.getByRole('button',{name:'Hodisa #1 tafsilotlari'}).click();
 await expect(page.getByRole('dialog')).toContainText('192.0.2.10');
 await page.keyboard.press('Escape');
 await page.getByText('Tanaffusga ruxsat yozish',{exact:true}).click();
 await page.getByRole('combobox',{name:'Qurilma',exact:true}).selectOption('1');
 await page.getByLabel('Sabab',{exact:true}).fill('Texnik xizmat');
 await page.getByRole('button',{name:'Ruxsatni saqlash'}).click();
 await expect(page.getByText('Ruxsat hodisa tarixiga yozildi.')).toBeVisible();
 expect(permission).toEqual({minutes:15,reason:'Texnik xizmat'});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});
