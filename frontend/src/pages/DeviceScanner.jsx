import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Camera, QrCode, ArrowRight } from 'lucide-react';
import { readEnrollmentToken } from '../api/enrollment-state';
export default function DeviceScanner() {
 const navigate=useNavigate();const [value,setValue]=useState('');const [error,setError]=useState('');const [scanning,setScanning]=useState(false);const video=useRef(null);const stream=useRef(null);const timer=useRef(null);
 const stop=()=>{clearTimeout(timer.current);stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;setScanning(false);};
 useEffect(()=>()=>{clearTimeout(timer.current);stream.current?.getTracks().forEach(t=>t.stop());},[]);
 function open(text){try{const token=readEnrollmentToken(text,window.location.origin);stop();navigate('/device-enroll/'+token);}catch(e){setError(e.message);}}
 async function camera(){
  setError('');
  if(!window.isSecureContext){setError('Kamera uchun sahifani HTTPS orqali oching. QR havolani qo‘lda ham kiritishingiz mumkin.');return;}
  if(!('BarcodeDetector' in window)){setError('Bu brauzer kamera skanerini qo‘llamaydi. Telefon kamerasi bilan QR kodni oching yoki havolani quyida kiriting.');return;}
  try{
   const detector=new window.BarcodeDetector({formats:['qr_code']});stream.current=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});video.current.srcObject=stream.current;await video.current.play();setScanning(true);
   async function scan(){if(!stream.current)return;try{const codes=await detector.detect(video.current);if(codes.length){open(codes[0].rawValue);if(!stream.current)return;}}catch{}timer.current=setTimeout(scan,400);}
   scan();
  }catch(e){stop();setError(e.message || 'Kamerani ochib bo‘lmadi.');}
 }
 return <div className="page-container"><div className="page-intro"><div><div className="eyebrow">QURILMANI ULASH</div><h2>QR kodni skanerlang</h2><p>Kompyuterdagi QR kodni telefon yoki kamera orqali oching.</p></div><Link className="btn-secondary" to="/devices">Qurilmalarga qaytish</Link></div><div className="panel" style={{maxWidth:650}}><div className="panel-heading"><div><h3>Yangi qurilma</h3><p>Kompyuterda ro‘yxatdan o‘tkazish sahifasini oching.</p></div><QrCode size={24} className="text-blue-600"/></div><Link to="/device/scan" target="_blank" className="quick-action"><QrCode size={20}/><div><strong>Kompyuterda ulanishni boshlash</strong><small>Yordamchi paket va QR kod</small></div><ArrowRight size={18}/></Link><video ref={video} muted playsInline className="scan-video mt-5" style={{display:scanning?'block':'none'}}/>{error&&<div role="alert" className="alert-error mt-5">{error}</div>}<div className="public-actions"><button className="btn-primary" onClick={scanning?stop:camera}><Camera size={16}/>{scanning?'Kamerani to‘xtatish':'Kamera bilan skanerlash'}</button></div><form className="field-stack mt-6" onSubmit={e=>{e.preventDefault();open(value.trim());}}><label>QR havola<input type="url" className="input-field mt-2" placeholder={window.location.origin+'/device-enroll/...'} value={value} onChange={e=>setValue(e.target.value)} required/></label><button className="btn-secondary" type="submit">Tasdiqlash sahifasini ochish<ArrowRight size={16}/></button></form></div></div>;
}

