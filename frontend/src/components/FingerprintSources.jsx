import {useState} from 'react';
import {Fingerprint,Keyboard,Smartphone,Plug,Plus,Trash2,X} from 'lucide-react';

const sources=[{key:'manual',label:'Manual',Icon:Keyboard},{key:'phone',label:'Phone',Icon:Smartphone},{key:'scanner',label:'Scanner',Icon:Fingerprint},{key:'external',label:'External',Icon:Plug}];
export default function FingerprintSources({records,busy,hasFace,phonePane,onStart,onReset,onRemove}){
 const [selected,setSelected]=useState(null),[adding,setAdding]=useState(false);
 const source=sources.find(s=>s.key===selected);
 const rows=records.filter(r=>r.source===selected);
 function select(key){onReset();setAdding(false);setSelected(key);}
 function close(){onReset();setAdding(false);}
 return <div className="biometric-template">
 <div className="fp-summary" role="status">{records.length?`Jami ${records.length} ta barmoq izi template mavjud`:"Barmoq izi yo‘q — manba tanlang va qo‘shing"}</div>
 <div className="fp-cards-grid">{sources.map(({key,label,Icon})=>{
 const entries=records.filter(r=>r.source===key);
 const latest=entries.map(r=>r.created_at).filter(Boolean).sort().at(-1);
 return <div key={key} className={'fp-card'+(selected===key?' fp-card--active':'')}><div className="fp-card-header"><div className={'fp-card-icon '+key}><Icon size={16}/></div><span className="fp-card-name">{label}</span><span className={'fp-badge '+(entries.length?'yes':'no')}>{entries.length?'✓ Mavjud':'— Mavjud emas'}</span></div><div className="fp-card-meta">{entries.length>0&&<span>{entries.length} ta template</span>}{latest&&<span>Added: {latest.slice(0,10)}</span>}</div><button className="fp-card-btn open" aria-label={label+' — Ochish'} disabled={busy} onClick={()=>select(key)}>Ochish</button></div>;
 })}</div>
 {source&&<section className="fp-manager visible"><div className="fp-manager-head"><div className={'fp-card-icon '+selected}><source.Icon size={16}/></div><span className="fp-manager-title">{source.label} — Barmoq izlari</span><button className="fp-manager-close" aria-label="Manbani yopish" disabled={busy} onClick={()=>select(null)}><X size={16}/></button></div><div className="fp-manager-body">
 {adding&&(selected==='phone'?<>{phonePane(close)}</>:<div className="fp-add-form"><div className="fp-add-form-title">{selected==='manual'?'Yangi Manual Template':selected==='scanner'?"USB Scanner orqali qo‘shish":'External Integration'}</div>
 {selected==='manual'?<><div className="fp-field-row"><label className="fp-field">Template nomi *<input type="text" placeholder="Masalan: O‘ng bosh barmoq"/></label><label className="fp-field">Fingerprint template *<input type="text" className="mono" placeholder="Template qiymatini kiriting..."/></label></div><p>Manual template saqlash hozircha mavjud emas.</p></>:selected==='scanner'?<div className="fp-scanner-area"><Fingerprint size={28}/><p className="fp-scanner-label">USB skaner ulanishi hali sozlanmagan.</p><button className="fp-scanner-btn" disabled>Scannerni ulash</button></div>:<div className="fp-external-area"><Plug size={28}/><div className="fp-external-label">Bu manba kelajakda avtomatik tarzda ulanadi.</div></div>}
 <div className="fp-form-actions"><button className="fp-form-cancel" onClick={close}>{selected==='manual'?'Bekor':'Yopish'}</button>{selected==='manual'&&<button className="fp-form-save" disabled>Saqlash</button>}</div></div>)}
 <div className="fp-add-row"><span>{rows.length?`${rows.length} ta template`:"Hali template yo‘q"}</span><button className="fp-btn-add-new" disabled={busy||(selected==='phone'&&!hasFace)} onClick={()=>{if(adding){close();return;}setAdding(true);if(selected==='phone')onStart();}}><Plus size={14}/>Template qo‘shish</button></div>
 {selected==='phone'&&!hasFace&&<p>Avval Yuz bo‘limida yuz ma’lumotingizni saqlang.</p>}
 <div className="fp-list">{rows.length?rows.map(record=><div className="fp-item" key={record.id}><div className="fp-item-icon"><Fingerprint size={18}/></div><div className="fp-item-info"><div className="fp-item-name">{record.template_name||'Template #'+record.id}</div><div className="fp-item-date">{record.created_at?new Date(record.created_at).toLocaleDateString('uz-UZ'):'Saqlangan ma’lumot'}</div></div><button className="fp-item-btn del" aria-label="Biometrik ma’lumotni o‘chirish" disabled={busy} onClick={()=>onRemove(record.id)}><Trash2 size={15}/></button></div>):<div className="fp-list-empty"><Fingerprint size={24}/>Bu manba uchun hali template qo‘shilmagan</div>}</div>
 </div></section>}
 </div>;
}
