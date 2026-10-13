import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Monitor, Download } from 'lucide-react';
import client from '../api/client';
import { errorMessage } from '../api/contracts';
const names={windows:'Windows',macos:'macOS',linux:'Linux'};
export default function DownloadCatalog(){
 const [rows,setRows]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 useEffect(()=>{let alive=true;client.get('/api/downloads/').then(r=>{if(alive)setRows(r.data.releases);}).catch(e=>{if(alive)setError(errorMessage(e));}).finally(()=>{if(alive)setLoading(false);});return()=>{alive=false;};},[]);
 return <section className="product-section"><div className="eyebrow">AGENTNI YUKLAB OLISH</div><h2>ADAuth’ni kompyuteringizga o‘rnating.</h2><p>Operatsion tizimingizga mos mahsulot paketini yuklab oling. O‘rnatish uchun ish maydoningizning aktivatsiya tokeni kerak bo‘ladi.</p>{error&&<div className="alert-error" role="alert">{error}</div>}{loading?<p role="status">Versiyalar yuklanmoqda...</p>:<div className="product-grid">{rows.map(row=><article key={row.platform}><Monitor size={28}/><h3>{names[row.platform]}</h3>{row.available?<><p><strong>v{row.version}</strong> · {(row.size/1024/1024).toFixed(1)} MB</p><p className="download-filename">{row.filename}</p>{row.prerelease&&<p>Sinov versiyasi. SIMULATE va EXIT tugmalari yoqilgan; tizimga kirishni majburiy bloklash hali mavjud emas.</p>}<a className="btn-primary" href={row.download_url}><Download size={16}/>{names[row.platform]} uchun yuklab olish</a><details className="mt-5"><summary>SHA-256</summary><code className="download-hash">{row.sha256}</code></details></>:<><p>Hali chiqarilmagan</p><button className="btn-secondary" disabled>Hozircha mavjud emas</button></>}</article>)}</div>}<p className="product-note">Shaxsiy hisobda PC ro‘yxatdan o‘tish davomida ulanadi. Kompaniya qurilmasini uning administratori tasdiqlaydi.</p><div className="product-actions"><Link className="btn-secondary" to="/?register=personal">Shaxsiy hisob yaratish</Link><Link className="btn-secondary" to="/?register=company">Kompaniya uchun ariza</Link></div></section>;
}
