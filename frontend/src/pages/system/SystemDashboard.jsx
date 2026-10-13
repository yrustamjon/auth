import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, UserCog, ShieldCheck, CalendarDays, ArrowUpRight, Plus } from 'lucide-react';
import StatCard from '../../components/StatCard';
import Badge from '../../components/Badge';
import { getOrganizations, getSystemAdmins } from '../../api/superadmin';
import { readCollection, readMetric } from '../../api/contracts';
export default function SystemDashboard() {
 const [state,setState]=useState({loading:true,results:[],orgs:[],admins:[]});
 useEffect(()=>{let alive=true;Promise.allSettled([getOrganizations(),getSystemAdmins()]).then(results=>{
  let orgs=[],admins=[];
  try {if(results[0].status==='fulfilled')orgs=readCollection(results[0].value.data,'organizations');}catch{}
  try {if(results[1].status==='fulfilled')admins=readCollection(results[1].value.data,'admins');}catch{}
  if(alive)setState({loading:false,results,orgs,admins});
 });return()=>{alive=false;};},[]);
 const metrics=state.results.map(r=>readMetric(r));
 const active=state.orgs.filter(o=>o.active).length;
 const locked=state.admins.filter(a=>a.locked).length;
 return <div className="page-container"><div className="page-intro"><div><div className="eyebrow">TIZIM BOSHQARUVI</div><h2>Tizimingiz haqida umumiy ko‘rinish</h2><p>Tashkilotlar va administratorlarni bitta ish maydonida boshqaring.</p></div><div className="date-pill"><CalendarDays size={15}/>{new Date().toLocaleDateString('uz-UZ',{day:'numeric',month:'long',year:'numeric'})}</div></div><div className="stats-grid"><StatCard icon={<Building2 size={19}/>} title="Tashkilotlar" value={state.loading?'…':metrics[0]?.value} subtitle={metrics[0]?.error?'Yuklab bo‘lmadi':'Barcha tashkilotlar'}/><StatCard icon={<ShieldCheck size={19}/>} title="Faol tashkilotlar" value={state.loading?'…':metrics[0]?.error?null:active} subtitle="Faoliyat yuritayotgan ish maydonlari"/><StatCard icon={<UserCog size={19}/>} title="Administratorlar" value={state.loading?'…':metrics[1]?.value} subtitle={metrics[1]?.error?'Yuklab bo‘lmadi':'Tizimdagi hisoblar'}/><StatCard icon={<ShieldCheck size={19}/>} title="Bloklangan hisoblar" value={state.loading?'…':metrics[1]?.error?null:locked} subtitle="Vaqtincha cheklangan kirishlar"/></div>
 <div className="dashboard-grid"><section className="panel"><div className="panel-heading"><div><h3>Tashkilotlar</h3><p>So‘nggi qo‘shilgan ish maydonlari</p></div><Link to="/system/organizations" className="text-link">Barchasi<ArrowUpRight size={13}/></Link></div>{metrics[0]?.error?<div className="alert-error">Tashkilotlarni yuklab bo‘lmadi.</div>:state.loading?<div className="empty-state">Yuklanmoqda...</div>:!state.orgs.length?<div className="empty-state"><Building2 size={28}/><strong>Hozircha tashkilot yo‘q</strong></div>:[...state.orgs].sort((a,b)=>new Date(b.created_at)-new Date(a.created_at)).slice(0,6).map(org=><Link key={org.id} to="/system/organizations" className="activity-row"><span className="stat-icon"><Building2 size={17}/></span><div className="activity-main"><strong>{org.name}</strong><small>{org.slug} · {org.admin_count ?? 0} administrator</small></div><Badge variant={org.active?'success':'default'} dot>{org.active?'Faol':'Nofaol'}</Badge><ArrowUpRight size={14} className="text-slate-400"/></Link>)}</section><section className="panel"><div className="panel-heading"><div><h3>Tezkor boshqaruv</h3><p>Tizim sozlamalariga o‘tish</p></div></div><Link to="/system/organizations" className="quick-action"><Building2 size={20}/><div><strong>Tashkilotlar</strong><small>Yangi ish maydonini qo‘shish</small></div><Plus size={16}/></Link><Link to="/system/admins" className="quick-action"><UserCog size={20}/><div><strong>Administratorlar</strong><small>Hisob va vakolatlarni boshqarish</small></div><ArrowUpRight size={16}/></Link><div className="sidebar-note mt-6"><ShieldCheck size={24}/><strong>Vakolatlar nazorati</strong><p>Har bir tashkilotga tegishli administratorlarni biriktiring va zarur hollarda kirishni cheklang.</p></div></section></div></div>;
}
