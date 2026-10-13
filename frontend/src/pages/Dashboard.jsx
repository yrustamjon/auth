import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, ShieldCheck, Monitor, ScrollText, CalendarDays, ArrowUpRight, Plus, Check, X, Fingerprint } from 'lucide-react';
import StatCard from '../components/StatCard';
import Badge from '../components/Badge';
import { getUsers, getRoles, getDevices, getLogs } from '../api/admin';
import { readCollection, readMetric } from '../api/contracts';
export default function Dashboard() {
  const [state,setState]=useState({loading:true,results:[],logs:[],devices:[]});
  useEffect(()=>{let alive=true; Promise.allSettled([getUsers(),getRoles(),getDevices(),getLogs()]).then(results=>{
    let logs=[],devices=[];
    try { if(results[3].status==='fulfilled') logs=readCollection(results[3].value.data,'logs'); } catch {}
    try { if(results[2].status==='fulfilled') devices=readCollection(results[2].value.data); } catch {}
    if(alive) setState({loading:false,results,logs,devices});
  }); return ()=>{alive=false;};},[]);
  const metrics=state.results.map((r,i)=>readMetric(r,['users',undefined,undefined,'logs'][i]));
  const cards=[['Foydalanuvchilar',Users,'Jamoangizdagi hisoblar'],['Rollar',ShieldCheck,'Kirish ruxsatlari'],['Qurilmalar',Monitor,'Ro‘yxatdagi qurilmalar'],['Kirishlar',ScrollText,'Qayd etilgan kirishlar']];
  const active=state.devices.filter(d=>d.is_active && d.enrollment_status!=='browser_approved').length;
  const pending=state.devices.filter(d=>d.enrollment_status==='browser_approved').length;
  return <div className="page-container"><div className="page-intro"><div><div className="eyebrow">BOSHQARUV PANELI</div><h2>Ish maydoningizga xush kelibsiz</h2><p>Jamoa, qurilmalar va kirishlar haqida muhim ma’lumotlar.</p></div><div className="date-pill"><CalendarDays size={15}/>{new Date().toLocaleDateString('uz-UZ',{day:'numeric',month:'long',year:'numeric'})}</div></div>
    <div className="stats-grid">{cards.map(([title,Icon,subtitle],i)=><StatCard key={title} title={title} icon={<Icon size={19}/>} value={state.loading?'…':metrics[i]?.value} subtitle={metrics[i]?.error?'Yuklab bo‘lmadi':subtitle}/>)}</div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-heading"><div><h3>Oxirgi kirishlar</h3><p>Ish maydonidagi so‘nggi faoliyat</p></div><Link to="/logs" className="text-link">Barchasi<ArrowUpRight size={13}/></Link></div>
      {state.loading?<div className="empty-state">Yuklanmoqda...</div>:metrics[3]?.error?<div className="alert-error">Kirish tarixini yuklab bo‘lmadi.</div>:!state.logs.length?<div className="empty-state"><ScrollText size={26}/><strong>Hozircha kirishlar yo‘q</strong></div>:state.logs.slice(0,6).map(log=><div key={log.id} className="activity-row"><span className={`activity-icon${log.success?'':' danger'}`}>{log.success?<Check size={16}/>:<X size={16}/>}</span><div className="activity-main"><strong>{log.user_fio || 'Noma’lum foydalanuvchi'}</strong><small>{log.device_pc_id || 'Qurilma ko‘rsatilmagan'}</small></div><Badge variant={log.success?'success':'danger'} dot>{log.success?'Ruxsat berildi':'Rad etildi'}</Badge><time className="activity-time">{new Date(log.timestamp).toLocaleTimeString('uz-UZ',{hour:'2-digit',minute:'2-digit'})}</time></div>)}
    </section><div className="flex flex-col gap-5"><section className="panel"><div className="panel-heading"><div><h3>Tezkor amallar</h3><p>Kundalik ishlar uchun qisqa yo‘l</p></div></div><Link to="/users" className="quick-action"><Users size={19}/><div><strong>Foydalanuvchilar</strong><small>Hisoblar va biometrik ma’lumotlar</small></div><ArrowUpRight size={15}/></Link><Link to="/devices/scan-qr/" className="quick-action"><Monitor size={19}/><div><strong>Qurilmani ulash</strong><small>QR orqali ro‘yxatdan o‘tkazish</small></div><ArrowUpRight size={15}/></Link><Link to="/roles" className="quick-action"><ShieldCheck size={19}/><div><strong>Ruxsatlarni boshqarish</strong><small>Jamoa rollarini sozlash</small></div><ArrowUpRight size={15}/></Link></section><section className="panel"><div className="panel-heading"><div><h3>Qurilmalar holati</h3><p>Joriy ro‘yxat asosida</p></div><Monitor size={17} className="text-slate-400"/></div>{metrics[2]?.error?<div className="alert-error">Qurilmalar yuklanmadi.</div>:<><div className="device-summary"><strong>{state.loading?'…':active}</strong><span>Faol qurilmalar</span><Badge variant="success" dot>Faol</Badge></div><div className="device-summary"><strong>{state.loading?'…':pending}</strong><span>Agent ulanishi kutilmoqda</span></div></>}</section></div></div>
    <section className="dashboard-banner"><Fingerprint size={35}/><div><h3>Hisoblar va biometrik ma’lumotlarni boshqaring</h3><p>Yuz va barmoq izi orqali tasdiqlash sozlamalari foydalanuvchi kartasida.</p></div><Link className="btn-primary" to="/users"><Plus size={15}/>Foydalanuvchilar</Link></section>
  </div>;
}
