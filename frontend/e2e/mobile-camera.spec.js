import {test,expect} from '@playwright/test';
for(const width of [390,360])test('phone camera uses portrait preview and matching capture '+width,async({page})=>{
 await page.setViewportSize({width,height:800});
 await page.addInitScript(()=>{
  navigator.mediaDevices.getUserMedia=async()=>{const canvas=document.createElement('canvas');canvas.width=1280;canvas.height=720;const ctx=canvas.getContext('2d');ctx.fillStyle='#789';ctx.fillRect(0,0,1280,720);return canvas.captureStream(10);};
 });
 await page.route('**/api/session/',r=>r.fulfill({json:{authenticated:false}}));
 await page.route('**/api/fingerprint/phone/options/**',r=>r.fulfill({json:{challenge:'eHh4',rp_id:'127.0.0.1',origin:'http://127.0.0.1:5173',user_id:'MQ',username:'owner'}}));
 let dimensions;
 await page.route('**/api/face/phone/check/',async r=>{const data=r.request().postDataJSON();dimensions=await page.evaluate(async image=>{const img=new Image();img.src='data:image/jpeg;base64,'+image;await img.decode();return [img.width,img.height];},data.image);await r.fulfill({json:{status:'verified'}});});
 await page.goto('/mobile/fingerprint/test/');
 await page.getByRole('button',{name:'Tekshiruvni boshlash'}).click();
 const camera=page.locator('.mobile-face-camera');await expect(camera).toBeVisible();
 const box=await camera.boundingBox();expect(box.width/box.height).toBeCloseTo(.75,2);
 await expect(page.getByRole('button',{name:'Yuzni tasdiqlash'})).toBeInViewport();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:`artifacts/mobile-camera-${width}.png`,fullPage:true});
 await page.getByRole('button',{name:'Yuzni tasdiqlash'}).click();
 await expect(page.getByRole('button',{name:'Biometrik sensor bilan tasdiqlash'})).toBeVisible();
 expect(dimensions).toEqual([600,800]);
});
