/* Optional browser metadata; server observations remain authoritative. */
window.auditClientInfo=function(){
  const nav=navigator, hints=nav.userAgentData;
  return {user_agent:nav.userAgent,platform:hints?.platform||nav.platform,language:nav.language,
    timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,mobile:hints?.mobile??/Android|iPhone|iPad/i.test(nav.userAgent),
    browser:hints?.brands?.map(b=>b.brand+' '+b.version).join(', ')||nav.userAgent,
    screen:{width:screen.width,height:screen.height,color_depth:screen.colorDepth,pixel_ratio:window.devicePixelRatio},
    viewport:{width:window.innerWidth,height:window.innerHeight}};
};
