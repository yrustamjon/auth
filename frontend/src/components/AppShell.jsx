import { useEffect, useRef, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Fingerprint, LayoutDashboard, Users, ShieldCheck, Monitor, ScrollText, Building2, UserCog, UserRound, Menu, X, LogOut, ChevronDown, ArrowUpRight } from 'lucide-react';
import { adminLogout, systemLogout, getSession, switchOrganization } from '../api/auth';
import client from '../api/client';

const adminItems = [
  ['/dashboard', 'Umumiy ko‘rinish', LayoutDashboard], ['/users', 'Foydalanuvchilar', Users],
  ['/roles', 'Rollar va ruxsatlar', ShieldCheck], ['/devices', 'Qurilmalar', Monitor], ['/logs', 'Kirish tarixi', ScrollText],
  ['/profile', 'Profil', UserRound],
  ['/agent-events','Agent hodisalari',ScrollText],
];
const personalItems = [
 ['/personal/computer','Mening kompyuterim',Monitor], ['/personal/biometrics','Biometrikam',Fingerprint], ['/personal/history','Kirish tarixim',ScrollText],
 ['/personal/profile', 'Profil', UserRound],
 ['/personal/agent-events','Agent hodisalari',ScrollText],
];
const systemItems = [
  ['/system/dashboard', 'Umumiy ko‘rinish', LayoutDashboard], ['/system/organizations', 'Tashkilotlar', Building2], ['/system/admins', 'Administratorlar', UserCog], ['/system/applications', 'Kompaniya arizalari', Building2],
  ['/system/profile', 'Profil', UserRound],
];
export default function AppShell({ panel = 'admin', children }) {
  const [open, setOpen] = useState(false);
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 767px)').matches);
  const sidebarRef = useRef(null);
  const menuRef = useRef(null);
  const [session, setSession] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [agentAlerts,setAgentAlerts]=useState([]);
  const location = useLocation();
  const navigate = useNavigate();
  const personal = panel==='admin' && session?.workspace?.kind==='personal';
  const items = panel === 'superadmin' ? systemItems : personal ? personalItems : adminItems;
  const title = items.find(([path]) => location.pathname.startsWith(path))?.[1] || 'Qurilmani tasdiqlash';
  useEffect(()=>{if(panel!=='admin')return;let alive=true;async function poll(){try{const r=await client.get('/api/agent-events/');if(alive)setAgentAlerts((Array.isArray(r.data?.events)?r.data.events:[]).filter(e=>e.severity==='warning'&&Date.now()-new Date(e.timestamp).getTime()<86400000));}catch{/* The event page exposes failures without interrupting other pages. */}}poll();const timer=setInterval(poll,30000);return()=>{alive=false;clearInterval(timer);};},[panel]);
  useEffect(() => { let alive = true; getSession().then(r => { if (alive) setSession(r.data); }).catch(() => {}); return () => { alive = false; }; }, []);
  useEffect(() => { setOpen(false); }, [location.pathname]);
  useEffect(() => {
    const media = window.matchMedia('(max-width: 767px)');
    const change = () => { setMobile(media.matches); setOpen(false); };
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, []);
  useEffect(() => {
    if (!open) return;
    const menuButton = menuRef.current;
    sidebarRef.current?.querySelector('a')?.focus();
    const close = e => {
      if (e.key === 'Escape') setOpen(false);
      if (e.key === 'Tab') {
        const links = [...sidebarRef.current.querySelectorAll('a, button')];
        const first = links[0], last = links[links.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', close);
    return () => { document.removeEventListener('keydown', close); menuButton?.focus(); };
  }, [open]);
  async function logout() {
    setBusy(true); setError('');
    try { await (panel === 'superadmin' ? systemLogout() : adminLogout()); navigate(panel === 'superadmin' ? '/system/login' : '/login', { replace: true }); }
    catch { setError('Chiqishda xato. Qayta urinib ko‘ring.'); setBusy(false); }
  }
  async function selectOrg(event) {
    setBusy(true); setError('');
    try { await switchOrganization(Number(event.target.value)); window.location.reload(); }
    catch { setError('Tashkilotni almashtirib bo‘lmadi.'); setBusy(false); }
  }
  return (
    <div className="app-shell">
      {open && <button className="sidebar-backdrop" aria-label="Menyuni yopish" onClick={() => setOpen(false)} />}
      <aside ref={sidebarRef} inert={mobile && !open} className={`app-sidebar${open ? ' is-open' : ''}`} aria-label="Asosiy navigatsiya">
        <NavLink to={panel === 'superadmin' ? '/system/dashboard' : personal ? '/personal/computer' : '/dashboard'} className="brand"><span className="brand-mark"><ShieldCheck size={24} /></span><span>AD<span className="brand-accent">Auth</span><small>Kirishni boshqarish</small></span></NavLink>
        <div className="workspace-card"><span className="workspace-icon">{panel === 'superadmin' ? <Building2 size={18} /> : <ShieldCheck size={18} />}</span><div><strong>{panel === 'superadmin' ? 'Tizim boshqaruvi' : personal ? 'Shaxsiy ish maydoni' : 'Ish maydoni'}</strong><small>{panel === 'superadmin' ? 'Superadministrator' : personal ? 'Shaxsiy foydalanish' : 'Administrator paneli'}</small></div><ChevronDown size={14} /></div>
        <p className="nav-caption">BOSHQARUV</p>
        <nav>{items.map(([path, label, Icon]) => <NavLink key={path} to={path} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><Icon size={19} /><span>{label}</span></NavLink>)}</nav>
        <div className="sidebar-footer"><div className="sidebar-note"><ShieldCheck size={22} /><strong>Barchasi nazorat ostida</strong><p>Hisoblar, qurilmalar va kirishlar — bitta ish maydonida.</p><NavLink to={panel === 'superadmin' ? '/system/admins' : personal ? '/personal/history' : '/logs'}>Boshqaruvga o‘tish <ArrowUpRight size={14} /></NavLink></div><p className="sidebar-version">ADAuth <span>Management workspace</span></p></div>
      </aside>
      <div className="app-content" inert={mobile && open}>
        <header className="app-header"><div className="header-title"><button ref={menuRef} className="icon-button mobile-menu" aria-label="Menyuni ochish" aria-expanded={open} onClick={() => setOpen(v => !v)}>{open ? <X size={20} /> : <Menu size={20} />}</button><div><span className="breadcrumb">Ish maydoni <span>/</span> {title}</span><h1>{title}</h1></div></div><div className="header-account">
          {panel === 'admin' && session?.organizations?.length > 1 && <select className="organization-select" aria-label="Joriy tashkilot" value={session.organization_id || ''} onChange={selectOrg} disabled={busy}>{session.organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}</select>}
          <NavLink to={panel === 'superadmin' ? '/system/profile' : personal ? '/personal/profile' : '/profile'} className="avatar" title="Profilni ochish" aria-label="Profilni ochish">{(session?.user?.username || 'A').slice(0, 2).toUpperCase()}</NavLink><div className="account-copy"><strong>{session?.user?.username || 'Hisob'}</strong><small>{panel === 'superadmin' ? 'Superadministrator' : personal ? 'Shaxsiy hisob' : 'Administrator'}</small></div><button className="icon-button" title="Hisobdan chiqish" aria-label="Hisobdan chiqish" disabled={busy} onClick={logout}><LogOut size={18} /></button>
        </div></header>
        {error && <div className="alert-error" role="alert">{error}</div>}
        {agentAlerts.length>0&&<div className="alert-error" role="status">So‘nggi 24 soatdagi hodisa — {agentAlerts[0].device_pc_id}: {agentAlerts[0].title}. <NavLink to={personal?'/personal/agent-events':'/agent-events'} className="text-link">{agentAlerts.length} ta ogohlantirishni ko‘rish</NavLink></div>}
        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}

