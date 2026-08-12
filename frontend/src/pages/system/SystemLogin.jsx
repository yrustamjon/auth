import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Zap, Lock, User, Shield } from 'lucide-react';
import { systemLogin } from '../../api/auth';

export default function SystemLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await systemLogin(form.username, form.password);
      navigate('/system/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || "Username yoki parol noto'g'ri");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(139,92,246,0.45) 0%, transparent 60%), linear-gradient(160deg, #07071a 0%, #0d0b2e 50%, #150e3a 100%)',
      }}
    >
      {/* Dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(139,92,246,0.14) 1px, transparent 0)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(circle, #7c3aed, transparent)' }} />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(circle, #a78bfa, transparent)' }} />

      <div className="relative w-full max-w-md animate-scale-in">
        <div
          className="rounded-3xl p-8"
          style={{
            background: 'rgba(255,255,255,0.97)',
            boxShadow: '0 32px 64px rgba(0,0,0,0.55), 0 0 0 1px rgba(139,92,246,0.15)',
          }}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)', boxShadow: '0 8px 24px rgba(124,58,237,0.45)' }}>
              <Zap size={26} color="white" fill="white" />
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase mb-3"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)', color: 'white', boxShadow: '0 4px 14px rgba(124,58,237,0.4)' }}>
              <Shield size={11} />
              Super Admin
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight" style={{ color: '#0f172a', letterSpacing: '-0.03em' }}>
              System Login
            </h1>
            <p className="text-sm mt-1" style={{ color: '#64748b' }}>
              Superadmin tizimga kirish
            </p>
          </div>

          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl text-sm font-medium"
              style={{ background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex rounded-xl overflow-hidden"
              style={{ border: '1.5px solid #e2e8f0', transition: 'all 0.2s' }}
              onFocus={e => e.currentTarget.style.borderColor = '#7c3aed'}
              onBlur={e => e.currentTarget.style.borderColor = '#e2e8f0'}
            >
              <div className="flex items-center justify-center px-3.5"
                style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}>
                <User size={16} color="white" />
              </div>
              <input
                type="text"
                placeholder="Superadmin login"
                value={form.username}
                onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
                required
                autoFocus
                className="flex-1 px-4 py-3 text-sm outline-none"
                style={{ background: 'white', color: '#0f172a' }}
              />
            </div>

            <div className="flex rounded-xl overflow-hidden"
              style={{ border: '1.5px solid #e2e8f0', transition: 'all 0.2s' }}
              onFocus={e => e.currentTarget.style.borderColor = '#7c3aed'}
              onBlur={e => e.currentTarget.style.borderColor = '#e2e8f0'}
            >
              <div className="flex items-center justify-center px-3.5"
                style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}>
                <Lock size={16} color="white" />
              </div>
              <input
                type={showPw ? 'text' : 'password'}
                placeholder="Parol"
                value={form.password}
                onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                required
                className="flex-1 px-4 py-3 text-sm outline-none"
                style={{ background: 'white', color: '#0f172a' }}
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                className="px-3.5 flex items-center"
                style={{ background: 'white', color: '#94a3b8' }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl text-sm font-bold text-white uppercase tracking-wide transition-all duration-200"
              style={{
                background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
                boxShadow: '0 4px 14px rgba(124,58,237,0.4)',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Kirish...' : 'Tizimga kirish'}
            </button>
          </form>

          <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', textAlign: 'center', borderTop: '1px solid #f1f5f9' }}>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem' }}>Oddiy admin panelga kirmoqchimisiz?</p>
            <Link to="/login" style={{ fontSize: '0.875rem', fontWeight: 600, color: '#7c3aed', textDecoration: 'none' }}>
              Admin Login →
            </Link>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem', color: '#94a3b8', fontSize: '0.72rem' }}>
            <Shield size={12} style={{ color: '#7c3aed' }} />
            <span>Yuqori darajali kirish huquqi talab etiladi</span>
          </div>
        </div>
      </div>
    </div>
  );
}
