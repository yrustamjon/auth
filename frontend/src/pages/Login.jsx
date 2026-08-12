import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Shield, Lock, User, Zap } from 'lucide-react';
import { adminLogin } from '../api/auth';

export default function Login() {
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
      await adminLogin(form.username, form.password);
      navigate('/dashboard');
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
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.4) 0%, transparent 60%), linear-gradient(160deg, #0a0a14 0%, #13132a 50%, #1a0f2e 100%)',
      }}
    >
      {/* Dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(99,102,241,0.12) 1px, transparent 0)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(circle, #8b5cf6, transparent)' }} />

      <div className="relative w-full max-w-md animate-scale-in">
        {/* Card */}
        <div
          className="rounded-3xl p-8"
          style={{
            background: 'rgba(255,255,255,0.97)',
            boxShadow: '0 32px 64px rgba(0,0,0,0.45)',
          }}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 8px 24px rgba(99,102,241,0.4)' }}>
              <Zap size={26} color="white" fill="white" />
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase mb-3"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', boxShadow: '0 4px 14px rgba(99,102,241,0.4)' }}>
              <Shield size={11} />
              Admin Panel
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight" style={{ color: '#0f172a', letterSpacing: '-0.03em' }}>
              Xush kelibsiz!
            </h1>
            <p className="text-sm mt-1" style={{ color: '#64748b' }}>
              Tizimga kirish uchun ma'lumot kiriting
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl text-sm font-medium"
              style={{ background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div className="flex rounded-xl overflow-hidden"
              style={{ border: '1.5px solid #e2e8f0', transition: 'all 0.2s' }}
              onFocus={(e) => e.currentTarget.style.borderColor = '#6366f1'}
              onBlur={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
            >
              <div className="flex items-center justify-center px-3.5"
                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                <User size={16} color="white" />
              </div>
              <input
                type="text"
                placeholder="Foydalanuvchi nomi"
                value={form.username}
                onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
                required
                autoFocus
                className="flex-1 px-4 py-3 text-sm outline-none"
                style={{ background: 'white', color: '#0f172a' }}
              />
            </div>

            {/* Password */}
            <div className="flex rounded-xl overflow-hidden"
              style={{ border: '1.5px solid #e2e8f0', transition: 'all 0.2s' }}
              onFocus={(e) => e.currentTarget.style.borderColor = '#6366f1'}
              onBlur={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
            >
              <div className="flex items-center justify-center px-3.5"
                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
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

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl text-sm font-bold text-white uppercase tracking-wide transition-all duration-200"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                boxShadow: '0 4px 14px rgba(99,102,241,0.4)',
                opacity: loading ? 0.7 : 1,
                transform: loading ? 'none' : undefined,
              }}
            >
              {loading ? 'Kirish...' : 'Tizimga kirish'}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-5 text-center" style={{ borderTop: '1px solid #f1f5f9' }}>
            <p className="text-xs mb-2" style={{ color: '#64748b' }}>
              Super admin huquqiga egamisiz?
            </p>
            <Link to="/system/login" className="text-sm font-semibold"
              style={{ color: '#6366f1' }}>
              System Login →
            </Link>
          </div>

          <div className="flex items-center justify-center gap-2 mt-4"
            style={{ color: '#94a3b8', fontSize: '0.72rem' }}>
            <Shield size={12} style={{ color: '#6366f1' }} />
            <span>Xavfsiz ulanish | SSL sertifikatlangan</span>
          </div>
        </div>
      </div>
    </div>
  );
}
