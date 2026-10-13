import { useEffect, useState } from 'react';
import { UserRound, KeyRound } from 'lucide-react';
import { getAccountProfile, changeAccountPassword } from '../api/auth';
import ActivationTokenCard from '../components/ActivationTokenCard';

const accountNames = { personal: 'Shaxsiy hisob', admin: 'Administrator', superadmin: 'Superadministrator' };
const emptyPasswords = { current_password: '', new_password: '', confirm_password: '' };

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [passwords, setPasswords] = useState(emptyPasswords);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let alive = true;
    getAccountProfile().then(r => { if (alive) setProfile(r.data); })
      .catch(() => { if (alive) setLoadError('Profilni yuklab bo‘lmadi. Qayta urinib ko‘ring.'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setError(''); setSuccess('');
    if (passwords.new_password !== passwords.confirm_password) {
      setError('Yangi parollar mos kelmadi.'); return;
    }
    setBusy(true);
    try {
      const response = await changeAccountPassword(passwords);
      setPasswords(emptyPasswords); setSuccess(response.data.detail);
    } catch (failure) {
      setError(failure.response?.data?.detail || 'Parolni yangilab bo‘lmadi. Qayta urinib ko‘ring.');
    } finally { setBusy(false); }
  }

  if (loading) return <div className="empty-state" role="status">Profil yuklanmoqda...</div>;
  if (!profile) return <div className="panel"><p className="alert-error" role="alert">{loadError}</p><button className="btn-secondary mt-4" onClick={() => window.location.reload()}>Qayta urinish</button></div>;
  return <div className="profile-page">
    {profile.account_type === 'admin' && <ActivationTokenCard key={profile.current_organization?.id} organization={profile.current_organization} />}
    <section className="panel profile-account">
      <div className="profile-card-heading"><span className="profile-card-icon"><UserRound size={20} /></span><div><h2>Hisob ma’lumotlari</h2><p>Profilingiz va biriktirilgan tashkilotlar</p></div></div>
      <dl className="profile-details">
        <div><dt>Login</dt><dd>{profile.username}</dd></div>
        <div><dt>Hisob turi</dt><dd>{accountNames[profile.account_type] || profile.account_type}</dd></div>
        <div><dt>Yaratilgan sana</dt><dd>{profile.created_at ? new Date(profile.created_at).toLocaleDateString('uz-UZ') : 'Ma’lumot yo‘q'}</dd></div>
        <div className="profile-organizations"><dt>Tashkilotlar</dt><dd>{profile.organizations.length ? profile.organizations.map(org => <span className="profile-org" key={org.id}>{org.name}</span>) : 'Tashkilot biriktirilmagan'}</dd></div>
      </dl>
    </section>
    <section className="panel profile-password">
      <div className="profile-card-heading"><span className="profile-card-icon"><KeyRound size={20} /></span><div><h2>Parolni almashtirish</h2><p>Hisobingiz xavfsizligini boshqaring</p></div></div>
      <p className="profile-hint">Kamida 8 belgili, taxmin qilish qiyin bo‘lgan parol tanlang.</p>
      <form className="field-stack" onSubmit={submit}>
        {[
          ['current_password', 'Joriy parol', 'current-password'],
          ['new_password', 'Yangi parol', 'new-password'],
          ['confirm_password', 'Yangi parolni tasdiqlang', 'new-password'],
        ].map(([name, label, autoComplete]) => <label key={name} htmlFor={name}>{label}<input id={name} name={name} className="input-field" type="password" autoComplete={autoComplete} required disabled={busy} value={passwords[name]} onChange={event => { setPasswords(old => ({ ...old, [name]: event.target.value })); setSuccess(''); }} /></label>)}
        {error && <div className="alert-error" role="alert">{error}</div>}
        {success && <p role="status">{success}</p>}
        <button className="btn-primary" type="submit" disabled={busy}>{busy ? 'Yangilanmoqda...' : 'Parolni yangilash'}</button>
      </form>
    </section>
  </div>;
}
