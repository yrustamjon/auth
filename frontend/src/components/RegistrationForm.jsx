import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Monitor, Building2, ArrowRight, ArrowLeft, Check } from 'lucide-react';
import { getSession, registerAccount } from '../api/auth';
import { errorMessage } from '../api/contracts';
import DeviceScan from '../pages/DeviceScan';

export default function RegistrationForm({ initialKind='personal' }) {
 const [kind,setKind]=useState(initialKind),[step,setStep]=useState(1);
 const [fio,setFio]=useState(''),[username,setUsername]=useState(''),[password,setPassword]=useState('');
 const [company,setCompany]=useState(''),[enrollmentId,setEnrollmentId]=useState(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');const navigate=useNavigate();
 function choose(value){setKind(value);setStep(1);setError('');}
 async function createAccount(){if(busy||(kind==='personal'&&!enrollmentId))return;setBusy(true);setError('');try{
  await getSession();const r=await registerAccount({kind,fio:fio.trim(),username:username.trim(),password,
   ...(kind==='company'?{company_name:company.trim()}:{enrollment_session_id:enrollmentId})});
  navigate(r.data.redirect==='/registration/status'?'/registration/status':kind==='personal'?'/personal/biometrics':'/dashboard',{replace:true});
 }catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 function submit(e){e.preventDefault();if(kind==='personal'){setError('');setStep(2);}else createAccount();}
 return <div className="registration-form"><div className="product-actions"><button className={kind==='personal'?'btn-primary':'btn-secondary'} disabled={busy} onClick={()=>choose('personal')}><Monitor size={16}/>Shaxsiy foydalanish</button><button className={kind==='company'?'btn-primary':'btn-secondary'} disabled={busy} onClick={()=>choose('company')}><Building2 size={16}/>Kompaniya</button></div>
 {kind==='personal'&&<ol className="onboarding-steps" aria-label="Ro‘yxatdan o‘tish bosqichlari"><li className={step===1?'current':'complete'}><span>{step===1?'1':<Check size={14}/>}</span>Hisob ma’lumotlari</li><li className={step===2?'current':''}><span>2</span>PC’ni aniqlash</li></ol>}
 {error&&<div role="alert" className="alert-error mb-4">{error}</div>}
 <form onSubmit={submit} className="field-stack" hidden={kind==='personal'&&step===2}>
 <h3>{kind==='personal'?'Avval hisob ma’lumotlarini kiriting':'Kompaniya uchun ariza'}</h3>
 <label htmlFor="register-name">To‘liq ism<input id="register-name" className="input-field" value={fio} onChange={e=>setFio(e.target.value)} autoComplete="name" maxLength={255} required disabled={busy}/></label>
 <label htmlFor="register-login">Yangi login<input id="register-login" className="input-field" value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" maxLength={150} required disabled={busy}/></label>
 <label htmlFor="register-password">Yangi parol<input id="register-password" type="password" className="input-field" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="new-password" minLength={8} maxLength={128} required disabled={busy}/></label>
 {kind==='company'&&<><label htmlFor="register-company">Kompaniya nomi<input id="register-company" className="input-field" value={company} onChange={e=>setCompany(e.target.value)} maxLength={255} required disabled={busy}/></label><p className="product-note">Kompaniyangiz platforma jamoasi tasdiqlaganidan keyin faol bo‘ladi. Qurilmalarni kompaniya administratori tasdiqlaydi.</p></>}
 <button className="btn-primary" disabled={busy}>{busy?'Yuborilmoqda...':kind==='company'?'Ariza yuborish':'Davom etish'}<ArrowRight size={16}/></button></form>
 <div hidden={kind!=='personal'||step!==2}><p className="product-note">{fio}, hisob yaratishdan oldin shu kompyuterni aniqlaymiz. Yordamchi dastur faqat qurilma ma’lumotlarini yuboradi.</p><DeviceScan embedded onIdentity={setEnrollmentId}/><div className="public-actions"><button className="btn-secondary" disabled={busy} onClick={()=>setStep(1)}><ArrowLeft size={16}/>Orqaga</button><button className="btn-primary" disabled={busy||!enrollmentId} onClick={createAccount}>{busy?'Yaratilmoqda...':'Hisob yaratish'}<ArrowRight size={16}/></button></div><p className="product-note">Keyingi qadam: biometrikani sozlash. Kompaniya tasdig‘ini kutishingiz shart emas.</p></div>
 </div>;
}
