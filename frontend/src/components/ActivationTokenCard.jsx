import { useEffect, useState } from 'react';
import { Copy, KeyRound } from 'lucide-react';
import { getToken } from '../api/auth';

export default function ActivationTokenCard({ organization }) {
  const [token, setToken] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  useEffect(() => {
    if (!token) return;
    const remaining = new Date(token.expires_at).getTime() - Date.now();
    if (remaining <= 0) { setToken(null); return; }
    const timer = setTimeout(() => setToken(null), Math.min(remaining, 2147483647));
    return () => clearTimeout(timer);
  }, [token]);

  async function obtain() {
    if (busy) return;
    setBusy(true); setError(''); setNotice(''); setToken(null);
    try { setToken((await getToken()).data); }
    catch (failure) { setError(failure.response?.data?.detail || failure.response?.data?.error || 'Tokenni olib bo‘lmadi. Qayta urinib ko‘ring.'); }
    finally { setBusy(false); }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(token.token); setNotice('Token nusxalandi.'); }
    catch { setError('Nusxalash ishlamadi. Tokenni maydondan qo‘lda nusxalang.'); }
  }
  return <section className="panel profile-activation">
    <div className="profile-card-heading"><span className="profile-card-icon"><KeyRound size={20} /></span><div><h2>Agent aktivatsiya tokeni</h2><p>Kompyuterni kompaniyangizga ulash</p></div></div>
    {organization && <div className="profile-company"><span>Joriy kompaniya</span><strong>{organization.name}</strong></div>}
    <p className="profile-hint">Tokenni Agentni o‘rnatishda kiriting. Qurilma kompaniyaga qo‘shilgan yoki QR orqali tasdiqlangan bo‘lishi kerak. Har bir aktivatsiya uchun token bir marta ishlatiladi.</p>
    <button className="btn-primary mt-4" disabled={busy || !organization} onClick={obtain}>{busy ? 'Token olinmoqda...' : 'Agent aktivatsiya tokenini olish'}</button>
    {error && <div className="alert-error mt-4" role="alert">{error}</div>}
    {token && <div className="personal-token">
      <label htmlFor="company-activation-token">Agent aktivatsiya tokeni<input id="company-activation-token" className="input-field" readOnly value={token.token} /></label>
      <p>Muddati: {new Date(token.expires_at).toLocaleString('uz-UZ')}</p>
      <div className="product-actions"><button className="btn-secondary" onClick={copy}><Copy size={16} />Tokenni nusxalash</button><button className="btn-secondary" onClick={() => { setToken(null); setNotice(''); }}>Tokenni yashirish</button></div>
    </div>}
    {notice && <p role="status">{notice}</p>}
  </section>;
}
