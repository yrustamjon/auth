import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, Eye, EyeOff, ArrowRight, LockKeyhole, Monitor, Check } from 'lucide-react';
import { adminLogin, systemLogin, getSession } from '../api/auth';
import { loginDestination, errorMessage } from '../api/contracts';
export default function LoginForm({ panel='admin', embedded=false }) {
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const [visible,setVisible]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const navigate=useNavigate();
  const location=useLocation();
  useEffect(() => { let alive=true; getSession().then(r => { if(alive && r.data.authenticated) navigate(r.data.panel=== 'admin' && r.data.workspace && (r.data.workspace.status!=='approved'||!r.data.workspace.active) ? '/registration/status' : loginDestination(r.data.panel, new URLSearchParams(location.search).get('next') || location.state?.from, r.data.workspace?.kind),{replace:true}); }).catch(() => {}); return () => {alive=false;}; },[navigate,location.state,location.search]);
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await getSession();
      const response=await (panel==='superadmin' ? systemLogin(username.trim(),password) : adminLogin(username.trim(),password));
      const next=new URLSearchParams(location.search).get('next') || location.state?.from || response.data.redirect;
      navigate(response.data.redirect==='/registration/status' ? '/registration/status' : loginDestination(panel,next),{replace:true});
    } catch(err) { setError(errorMessage(err,'Kirish amalga oshmadi.')); }
    finally {setBusy(false);}
  }
  return <div className={embedded ? "login-page login-embedded" : "login-page"}><section className="login-story"><Link to="/login" className="brand"><span className="brand-mark"><ShieldCheck size={24} /></span><span>AD<span className="brand-accent">Auth</span><small>Kirishni boshqarish</small></span></Link><div className="login-story-content"><div className="eyebrow">SIZNING ISH MAYDONINGIZ</div><h1>Har bir kirish.<br />Har bir qurilma.<br /><span>Barchasi bir joyda.</span></h1><p>Jamoangiz, qurilmalaringiz va kirish ruxsatlarini sodda, tartibli ish maydonida boshqaring.</p><div className="login-art"><div className="login-art-top"><span className="stat-icon"><ShieldCheck size={20} /></span><div><strong>Kirish nazorati</strong><small>Hisoblar va qurilmalar boshqaruvi</small></div></div><div className="login-art-line"><Monitor size={16} /> Qurilmalarni ro‘yxatga olish <span><Check size={12} /></span></div><div className="login-art-line"><LockKeyhole size={16} /> Biometrik tasdiqlash <span><Check size={12} /></span></div></div></div><div className="login-story-footer">ADAuth · Kirishni boshqarish platformasi</div></section><section className="login-form-wrap"><form className="login-form" onSubmit={submit}><div className="eyebrow">{panel==='superadmin' ? 'TIZIM BOSHQARUVI' : 'XUSH KELIBSIZ'}</div><h2>Hisobingizga kiring</h2><p>{panel==='superadmin' ? 'Tashkilotlar va administratorlarni boshqarish uchun tizim hisobidan foydalaning.' : 'Ish maydoningizga kirish uchun login va parolingizni kiriting.'}</p>{error && <div className="alert-error" role="alert">{error}</div>}<div className="login-field"><label htmlFor="username">Foydalanuvchi nomi</label><input id="username" autoComplete="username" className="input-field" placeholder="Loginni kiriting" value={username} onChange={e=>setUsername(e.target.value)} required disabled={busy} /></div><div className="login-field"><label htmlFor="password">Parol</label><div className="password-field"><input id="password" type={visible?'text':'password'} autoComplete="current-password" className="input-field" placeholder="Parolingizni kiriting" value={password} onChange={e=>setPassword(e.target.value)} required disabled={busy} /><button type="button" className="icon-button" aria-label={visible?'Parolni yashirish':'Parolni ko‘rsatish'} onClick={()=>setVisible(v=>!v)}>{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button></div></div><button className="btn-primary login-submit" disabled={busy}>{busy?'Kirilmoqda...':'Hisobga kirish'}<ArrowRight size={16}/></button><Link className="login-switch" to={panel==='superadmin'?'/login':'/system/login'}>{panel==='superadmin'?'Administrator sifatida kirish':'Superadministrator sifatida kirish'}</Link><div className="login-security"><ShieldCheck size={13}/>Sessiya orqali himoyalangan kirish</div></form></section></div>;
}

