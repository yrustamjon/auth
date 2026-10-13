import { useState } from 'react';
import { Copy, KeyRound } from 'lucide-react';
import { issueRemovalCode } from '../api/admin';
import { errorMessage } from '../api/contracts';

export default function RemovalCodeCard({ device }) {
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  async function issue() {
    if (busy) return;
    setBusy(true); setError(''); setResult(null); setCopied(false);
    try { const response = await issueRemovalCode(device.id); setResult(response.data); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(result.code); setCopied(true); }
    catch { setError('Kodni qo‘lda nusxalang.'); }
  }
  return <div>
    <p><strong>{device.pc_id}</strong> qurilmasida Agentni o‘chirish uchun bir martalik kod yarating.</p>
    <p className="product-note">Kod faqat shu qurilmada 10 daqiqa amal qiladi. Uni yaratishning o‘zi Agentni o‘chirmaydi. Uninstallerda internet talab qilinadi.</p>
    {error && <div role="alert" className="alert-error">{error}</div>}
    <button className="btn-danger" disabled={busy} onClick={issue}><KeyRound size={16}/>{busy ? 'Yaratilmoqda...' : result ? 'Yangi kod yaratish' : 'Kod yaratish'}</button>
    {result && <div className="personal-token">
      <label>Bir martalik o‘chirish kodi<input aria-label="Bir martalik o‘chirish kodi" className="input-field" readOnly value={result.code}/></label>
      <p className="product-note">Muddati: {new Date(result.expires_at).toLocaleString('uz-UZ')}. Yangi kod yaratilsa, avvalgi kod bekor qilinadi.</p>
      <button className="btn-secondary" onClick={copy}><Copy size={16}/>{copied ? 'Nusxalandi' : 'Kodni nusxalash'}</button>
    </div>}
  </div>;
}
