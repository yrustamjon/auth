import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getSession } from '../api/auth';
import { loginDestination } from '../api/contracts';
import { ShieldCheck, ArrowRight, Monitor, Fingerprint, QrCode, Download, Check, BookOpen } from 'lucide-react';
import Modal from '../components/Modal';
import LoginForm from '../components/LoginForm';
import RegistrationForm from '../components/RegistrationForm';
import DownloadCatalog from '../components/DownloadCatalog';

const features = [
  [Monitor, 'Qurilmalarni ulang', 'Kompyuterda ulanish sessiyasini yarating, yordamchi paketni yuklang va qurilmani QR orqali tasdiqlashga yuboring.'],
  [Fingerprint, 'Biometrik tasdiqlash', 'Yuz ma’lumotlari va telefon orqali biometrik ro‘yxatdan o‘tish oqimlarini bitta tizimda boshqaring.'],
  [ShieldCheck, 'Jamoani boshqaring', 'Administrator panelida foydalanuvchilar, rollar, qurilmalar va kirish tarixini boshqaring.'],
];
export default function ProductSite({ section='home', loginPanel }) {
  const location=useLocation(), navigate=useNavigate();
  const [session,setSession]=useState(null);
  const [sessionLoading,setSessionLoading]=useState(true);
  useEffect(()=>{
    let alive=true;
    getSession().then(r=>{if(alive)setSession(r.data);}).catch(()=>{}).finally(()=>{if(alive)setSessionLoading(false);});
    return ()=>{alive=false;};
  },[]);
  const workspaceDestination=session?.panel==='admin' && session.workspace && (session.workspace.status!=='approved'||!session.workspace.active)
    ? '/registration/status' : loginDestination(session?.panel,null,session?.workspace?.kind);
  const query=new URLSearchParams(location.search);
  const panel=loginPanel || query.get('login');
  const registration=query.get('register');
  function openLogin(){ navigate('/?login=admin', {state:{from:location.state?.from}}); }
  return <div className="product-site">
    <header className="product-header"><Link to="/" className="brand"><span className="brand-mark"><ShieldCheck size={24}/></span><span>AD<span className="brand-accent">Auth</span></span></Link><nav aria-label="Mahsulot navigatsiyasi"><Link to="/product">Mahsulot</Link><Link to="/downloads">Yuklab olish</Link><Link to="/guide">Qo‘llanma</Link><Link to="/device/scan">PC uchun QR</Link></nav>{!sessionLoading && (session?.authenticated ? <Link className="btn-primary" to={workspaceDestination}>Ish maydonim</Link> : <><button className="btn-secondary" onClick={openLogin}>Kirish</button><Link className="btn-primary" to="/?register=personal">Boshlash</Link></>)}</header>
    <main>
      <section className="product-hero"><div><div className="eyebrow">QURILMALAR VA KIRISHNI BOSHQARISH</div><h1>Jamoangiz uchun<br/><span>yagona kirish nuqtasi.</span></h1><p>ADAuth — hisoblar, kompyuterlar va biometrik tasdiqlashni bir joyga jamlaydigan platforma. Mahsulot bilan tanishing yoki kompyuteringizni ulashdan boshlang.</p><div className="product-actions"><Link className="btn-primary" to="/downloads"><Download size={18}/>Yuklab olish</Link><Link className="btn-secondary" to="/device/scan"><QrCode size={18}/>PC uchun QR yaratish</Link></div><div className="product-note"><Check size={16}/>Mahsulot bilan tanishish va QR yaratish uchun hisob kerak emas.</div></div><div className="product-preview" aria-label="ADAuth imkoniyatlari"><div className="preview-heading"><span className="brand-mark"><ShieldCheck size={24}/></span><div><strong>ADAuth workspace</strong><small>Qurilmadan boshqaruvgacha</small></div></div>{features.map(([Icon,title,description],i)=><div className="preview-step" key={title}><span><Icon size={22}/></span><div><small>0{i+1}</small><strong>{title}</strong><p>{description}</p></div></div>)}</div></section>
      {section==='downloads' ? <DownloadCatalog/>
      : section==='guide' ? <section className="product-section"><div className="eyebrow">BOSHLASH QO‘LLANMASI</div><h2>Uch qadamda ulaning.</h2><div className="product-grid">{['Kompyuterda “PC uchun QR” sahifasini oching va ulanishni boshlang.','Tizimingizni tanlang, yordamchi paketni yuklang va ishga tushiring.','Kompyuter aniqlangach, administrator QR kodni skanerlab qurilmani tasdiqlaydi.'].map((text,i)=><article key={text}><span className="guide-number">0{i+1}</span><h3>{['Sessiya yarating','Paketni ishga tushiring','Tasdiqlating'][i]}</h3><p>{text}</p></article>)}</div><Link className="btn-primary" to="/device/scan">Ulanishni boshlash <ArrowRight size={16}/></Link></section>
      : <section className="product-section"><div className="eyebrow">BIR PLATFORMA. ANIQ BOSHQARUV.</div><h2>Har bir kirish — nazorat ostida.</h2><div className="product-grid">{features.map(([Icon,title,text])=><article key={title}><Icon size={28}/><h3>{title}</h3><p>{text}</p></article>)}</div><Link className="product-guide-link" to="/guide"><BookOpen size={18}/>Boshlash qo‘llanmasini o‘qish <ArrowRight size={16}/></Link></section>}
      <section className="product-cta"><div><h2>Kompyuteringizni ulashga tayyormisiz?</h2><p>Ulanish sessiyasini hoziroq oching. Qurilmani administrator keyin tasdiqlaydi.</p></div><Link className="btn-primary" to="/device/scan">QR yaratish <ArrowRight size={18}/></Link></section>
    </main><footer className="product-footer"><strong>ADAuth</strong><span>Qurilmalar va kirishni boshqarish platformasi</span><Link to="/guide">Qo‘llanma</Link></footer>
    <Modal size="lg" isOpen={registration==='personal'||registration==='company'} onClose={()=>navigate('/',{replace:true})} title="Ro‘yxatdan o‘tish"><RegistrationForm key={registration} initialKind={registration}/></Modal>
    <Modal isOpen={panel==='admin'||panel==='superadmin'} onClose={()=>navigate('/',{replace:true})} title={panel==='superadmin'?'Tizimga kirish':'Hisobga kirish'}><LoginForm panel={panel==='superadmin'?'superadmin':'admin'} embedded/></Modal>
  </div>;
}
