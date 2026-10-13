import Modal from './Modal';
import './LogDetails.css';
import { CheckCircle, XCircle, UserRound, Monitor, Globe, Network } from 'lucide-react';

const missing='Saqlanmagan';
const labels={id:'ID',pc_id:'PC ID',platform:'Operatsion tizim',location:'Joylashuv',identifiers:'Apparat identifikatorlari',enrollment_status:'Ro‘yxatdan o‘tish holati',attestation_status:'Qurilma tasdig‘i',is_active:'Faollik',last_ip:'Qurilmaning oxirgi IP manzili',registered_at:'Ro‘yxatdan o‘tgan vaqt',enrolled_at:'Agent ulangan vaqt',ip_address:'IP manzili',peer_ip:'Serverga ulangan IP',method:'So‘rov usuli',path:'So‘rov yo‘li',user_agent:'Brauzer / Agent',accept_language:'So‘rov tili',browser_hints:'Brauzer ma’lumotlari',client:'Brauzer taqdim etgan ma’lumotlar',initiator:'Kompyuterdan boshlangan so‘rov',browser:'Brauzer',browser_version:'Brauzer versiyasi',platform_version:'Tizim versiyasi',language:'Til',timezone:'Vaqt zonasi',device_type:'Qurilma turi',mobile:'Mobil qurilma',screen:'Ekran',viewport:'Brauzer oynasi',width:'Kenglik',height:'Balandlik',pixel_ratio:'Piksel nisbati',color_depth:'Rang chuqurligi',brands:'Brauzerlar',machine_guid:'Machine GUID',bios_uuid:'BIOS UUID',platform_uuid:'Platform UUID',serial:'Seriya raqami'};
const statuses={windows:'Windows',linux:'Linux',macos:'macOS',agent_enrolled:'Agent ulangan',browser_approved:'Brauzer orqali tasdiqlangan',manual_registered:'Qo‘lda ro‘yxatdan o‘tgan',not_provided:'Taqdim etilmagan',verified:'Tasdiqlangan'};
function displayValue(key,value){
 if(value===null||value===undefined||value==='')return missing;
 if(typeof value==='boolean')return value?'Ha':'Yo‘q';
 if(key.endsWith('_at')){const date=new Date(value);if(!Number.isNaN(date.getTime()))return date.toLocaleString('uz-UZ');}
 return statuses[value]||String(value);
}
function Fields({data}){
 return <dl className="log-fields">{Object.entries(data||{}).map(([key,value])=><div className={`log-field${value&&typeof value==='object'?' log-field-group':''}`} key={key}><dt>{labels[key]||key}</dt><dd>{value&&typeof value==='object'?<Fields data={value}/>:displayValue(key,value)}</dd></div>)}</dl>;
}
function Section({title,Icon,data}){
 return <section className="log-section"><h4><Icon size={17}/>{title}</h4>{Object.keys(data||{}).length?<Fields data={data}/>:<p className="log-missing">Bu logda ma’lumot saqlanmagan.</p>}</section>;
}
export function similarityText(value){return typeof value==='number'&&Number.isFinite(value)?`${(value*100).toFixed(2)}%`:missing;}
export default function LogDetails({log,onClose}){
 const context=log?.request_context||{};
 const {client,initiator,...request}=context;
 const ResultIcon=log?.success?CheckCircle:XCircle;
 return <Modal isOpen={!!log} onClose={onClose} title={`Log #${log?.id} tafsilotlari`} size="xl">{log&&<div className="log-details">
  <div className={`log-result ${log.success?'is-success':'is-failed'}`}><ResultIcon size={25}/><div><strong>{log.success?'Kirish muvaffaqiyatli':'Kirish rad etildi'}</strong><span>{log.timestamp||log.created_at?new Date(log.timestamp||log.created_at).toLocaleString('uz-UZ'):missing}</span></div></div>
  <div className="log-metrics"><div><span>O‘xshashlik darajasi</span><strong>{similarityText(log.similarity)}</strong></div><div><span>IP manzili</span><strong>{log.ip_address||missing}</strong></div><div><span>Kirish manbasi</span><strong>{({mobile_web:'Telefon brauzeri',desktop_agent:'Kompyuter agenti'})[log.source]||missing}</strong></div></div>
  <div className="log-reason"><span>Sabab</span><p>{log.cause||'Sabab ko‘rsatilmagan.'}</p></div>
  <div className="log-section-grid">
   <Section title="Foydalanuvchi" Icon={UserRound} data={{'Ism':log.user_fio||missing,'Login':log.username||missing}}/>
   <Section title="Kirilgan kompyuter" Icon={Monitor} data={Object.keys(log.device_snapshot||{}).length?log.device_snapshot:{pc_id:log.device_pc_id||missing}}/>
   <Section title="So‘rov ma’lumotlari" Icon={Network} data={request}/>
   <Section title="Brauzer va ekran" Icon={Globe} data={client}/>
   {initiator&&<Section title="Kompyuterdan boshlangan so‘rov" Icon={Monitor} data={initiator}/>}
  </div>
 </div>}</Modal>;
}
