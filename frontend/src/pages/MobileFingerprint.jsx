import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Fingerprint, Camera, ShieldCheck, CheckCircle, ArrowRight } from 'lucide-react';
import client from '../api/client';
import { getSession } from '../api/auth';
import { errorMessage } from '../api/contracts';
function decode(value){const raw=value.replace(/-/g,'+').replace(/_/g,'/');return Uint8Array.from(atob(raw+'='.repeat((4-raw.length%4)%4)),c=>c.charCodeAt(0));}
function encode(value){return btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');}
export default function MobileFingerprint(){
 const {sessionId}=useParams();const [options,setOptions]=useState(null);const [step,setStep]=useState('loading');const [error,setError]=useState('');const [busy,setBusy]=useState(false);const video=useRef(null);const stream=useRef(null);const mounted=useRef(true);
 useEffect(()=>{mounted.current=true;let alive=true;getSession().then(()=>client.get('/api/fingerprint/phone/options/'+sessionId+'/')).then(r=>{if(alive){setOptions(r.data);setStep('ready');}}).catch(e=>{if(alive){setError(errorMessage(e));setStep('error');}});return()=>{alive=false;mounted.current=false;stream.current?.getTracks().forEach(t=>t.stop());};},[sessionId]);
 function stop(){stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;}
 async function startCamera(){
  setError('');setBusy(true);
  try{
   if(!window.isSecureContext)throw new Error('Kamera va biometrik tekshiruv uchun HTTPS kerak.');
   if(options.origin!==window.location.origin)throw new Error('Ushbu sahifani serverning PUBLIC_SITE_URL manzilida oching: '+options.origin);
   if(!navigator.credentials?.create)throw new Error('Bu brauzer biometrik tasdiqlashni qo‘llamaydi.');
   const media=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'user'},width:{ideal:720},height:{ideal:960}}});
   if(!mounted.current){media.getTracks().forEach(t=>t.stop());return;}
   stream.current=media;video.current.srcObject=media;await video.current.play();if(!mounted.current){media.getTracks().forEach(t=>t.stop());return;}setStep('camera');
  }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
 }
 async function face(){
  setBusy(true);setError('');
  try{
   const el=video.current;if(!el.videoWidth)throw new Error('Kamera hali tayyor emas. Qayta urinib ko‘ring.');
   const canvas=document.createElement('canvas');const cropWidth=Math.min(el.videoWidth,el.videoHeight*3/4);const cropHeight=cropWidth*4/3;canvas.width=600;canvas.height=800;canvas.getContext('2d').drawImage(el,(el.videoWidth-cropWidth)/2,(el.videoHeight-cropHeight)/2,cropWidth,cropHeight,0,0,600,800);
   const r=await client.post('/api/face/phone/check/',{session_id:sessionId,image:canvas.toDataURL('image/jpeg',.85).split(',')[1]});
   if(r.data.status!=='verified')throw new Error(r.data.status==='not_found'?'Yuz ma’lumoti mavjud emas. Administrator bilan bog‘laning.':'Yuz mos kelmadi. Qayta urinib ko‘ring.');
   stop();setStep('finger');
  }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
 }
 async function fingerprint(){
  setBusy(true);setError('');
  try{
   const credential=await navigator.credentials.create({publicKey:{challenge:decode(options.challenge),rp:{name:'ADAuth',id:options.rp_id},user:{id:decode(options.user_id),name:options.username,displayName:options.username},pubKeyCredParams:[{type:'public-key',alg:-7}],authenticatorSelection:{userVerification:'required'},timeout:60000}});
   if(!credential)throw new Error('Biometrik tasdiqlash bekor qilindi.');
   await client.post('/api/fingerprint/phone/submit/',{session_id:sessionId,rawId:encode(credential.rawId),clientDataJSON:encode(credential.response.clientDataJSON),attestationObject:encode(credential.response.attestationObject)});
   if(mounted.current)setStep('done');
  }catch(e){if(mounted.current)setError(errorMessage(e));}finally{if(mounted.current)setBusy(false);}
 }
 return <div className="public-page mobile-biometric-page"><section className="public-card mobile-biometric-card"><div className="stat-icon">{step==='done'?<CheckCircle size={25}/>:<ShieldCheck size={25}/>}</div><div className="eyebrow mt-5">SHAXSNI TASDIQLASH</div><h1>{step==='done'?'Muvaffaqiyatli saqlandi':'Biometrik tasdiqlash'}</h1><p>{step==='done'?'Biometrik ma’lumot saqlandi. Ushbu oynani yopishingiz mumkin.':'Avval yuzingizni, keyin qurilmangizdagi biometrik sensor orqali shaxsingizni tasdiqlang.'}</p>{error&&<div className="alert-error" role="alert">{error}</div>}{step==='loading'&&<p role="status">Sessiya tekshirilmoqda...</p>}<div className="mobile-face-camera" style={{display:step==='camera'?'block':'none'}}><video ref={video} autoPlay muted playsInline aria-label="Old kamera"/><div className="mobile-face-guide" aria-hidden="true"/></div>{step==='camera'&&<p className="mobile-face-hint">Yuzingizni ramka ichiga joylashtiring.</p>}{step==='ready'&&<><div className="quick-action"><Camera size={22}/><div><strong>1. Yuzni tekshirish</strong><small>Yuzingiz kamerada aniq ko‘rinsin</small></div></div><div className="quick-action"><Fingerprint size={22}/><div><strong>2. Biometrik tasdiqlash</strong><small>Qurilmangizdagi sensor yoki xavfsizlik kaliti</small></div></div><button className="btn-primary mt-6" disabled={busy} onClick={startCamera}>Tekshiruvni boshlash<ArrowRight size={16}/></button></>}{step==='camera'&&<button className="btn-primary mt-5" disabled={busy} onClick={face}>{busy?'Tekshirilmoqda...':'Yuzni tasdiqlash'}</button>}{step==='finger'&&<button className="btn-primary mt-5" disabled={busy} onClick={fingerprint}><Fingerprint size={18}/>{busy?'Tasdiqlash kutilmoqda...':'Biometrik sensor bilan tasdiqlash'}</button>}</section></div>;
}

