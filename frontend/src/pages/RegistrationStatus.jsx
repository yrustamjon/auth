import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Clock, ShieldCheck } from 'lucide-react';
import { getRegistrationStatus, adminLogout } from '../api/auth';
import { errorMessage } from '../api/contracts';
export default function RegistrationStatus(){
 const [data,setData]=useState(null),[error,setError]=useState('');const navigate=useNavigate();
 useEffect(()=>{let alive=true,timer;async function poll(){try{const r=await getRegistrationStatus();if(!alive)return;setData(r.data);setError('');if(r.data.status==='approved'&&r.data.active){navigate('/dashboard',{replace:true});return;}if(r.data.status==='pending'||(r.data.status==='approved'&&!r.data.active))timer=setTimeout(poll,5000);}catch(e){if(!alive)return;if(e.response?.status===401){navigate('/?login=admin',{replace:true});return;}setError(errorMessage(e));timer=setTimeout(poll,8000);}}poll();return()=>{alive=false;clearTimeout(timer);};},[navigate]);
 async function logout(){try{await adminLogout();navigate('/');}catch(e){setError(errorMessage(e));}}
 return <div className="public-page"><section className="public-card"><ShieldCheck size={30}/><div className="eyebrow mt-5">KOMPANIYA ARIZASI</div><h1>{data?.status==='rejected'?'Ariza rad etildi':'Tasdiqlash kutilmoqda'}</h1>{error&&<div role="alert" className="alert-error">{error}</div>}<h3>{data?.name}</h3><p>{data?.status==='rejected'?'Platforma jamoasi arizangizni rad etdi.':data?.status==='approved'?'Ish maydoni hozir faol emas.':'Arizangiz qabul qilindi. Platforma jamoasi ko‘rib chiqmoqda. Tasdiqlangach, boshqaruv paneli ochiladi.'}</p>{data?.note&&<div className="panel">{data.note}</div>}<p className="product-note"><Clock size={16}/>Holat avtomatik tekshiriladi.</p><div className="public-actions"><Link to="/" className="btn-secondary">Bosh sahifa</Link><button className="btn-secondary" onClick={logout}>Hisobdan chiqish</button></div></section></div>;
}
