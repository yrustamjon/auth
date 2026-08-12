import { useEffect, useState } from 'react';
import { Building2, UserCog, TrendingUp, Activity, CheckCircle, AlertCircle } from 'lucide-react';
import { getOrganizations, getSystemAdmins } from '../../api/superadmin';

function StatCard({ icon, title, value, subtitle, color }) {
  const colors = {
    violet: { bg: 'rgba(139,92,246,0.1)', border: 'rgba(139,92,246,0.2)', text: '#a78bfa', glow: 'rgba(139,92,246,0.3)' },
    purple: { bg: 'rgba(168,85,247,0.1)', border: 'rgba(168,85,247,0.2)', text: '#c084fc', glow: 'rgba(168,85,247,0.3)' },
    indigo: { bg: 'rgba(99,102,241,0.1)', border: 'rgba(99,102,241,0.2)', text: '#818cf8', glow: 'rgba(99,102,241,0.3)' },
    fuchsia: { bg: 'rgba(217,70,239,0.1)', border: 'rgba(217,70,239,0.2)', text: '#e879f9', glow: 'rgba(217,70,239,0.3)' },
  };
  const c = colors[color] || colors.violet;

  return (
    <div className="rounded-2xl p-5 transition-all hover:translate-y-[-2px]"
      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="flex items-start justify-between">
        <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: c.bg, border: `1px solid ${c.border}`, boxShadow: `0 0 20px ${c.glow}` }}>
          <span style={{ color: c.text }}>{icon}</span>
        </div>
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-slate-100 tracking-tight">{value}</p>
        <p className="text-sm font-medium text-slate-400 mt-0.5">{title}</p>
        {subtitle && <p className="text-xs text-slate-600 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

const services = [
  { label: 'System API', status: true },
  { label: 'Auth Service', status: true },
  { label: 'Database', status: true },
  { label: 'Org Manager', status: true },
];

export default function SystemDashboard() {
  const [stats, setStats] = useState({ orgs: 0, admins: 0 });
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([getOrganizations(), getSystemAdmins()])
      .then(([o, a]) => {
        const orgData = o.status === 'fulfilled'
          ? (Array.isArray(o.value.data) ? o.value.data : o.value.data?.organizations ?? [])
          : [];
        const adminData = a.status === 'fulfilled'
          ? (Array.isArray(a.value.data) ? a.value.data : a.value.data?.admins ?? [])
          : [];
        setStats({ orgs: orgData.length, admins: adminData.length });
        setOrgs(orgData.slice(0, 6));
      })
      .finally(() => setLoading(false));
  }, []);

  const activeOrgs = orgs.filter(o => o.is_active !== false).length;

  const cards = [
    { icon: <Building2 size={20} />, title: 'Tashkilotlar', value: loading ? '...' : stats.orgs, subtitle: `${activeOrgs} faol`, color: 'violet' },
    { icon: <UserCog size={20} />, title: 'System Adminlar', value: loading ? '...' : stats.admins, subtitle: 'Barcha adminlar', color: 'purple' },
    { icon: <Activity size={20} />, title: 'Faol sessiyalar', value: loading ? '...' : '—', subtitle: 'Real-time', color: 'indigo' },
    { icon: <TrendingUp size={20} />, title: 'So\'rovlar bugun', value: loading ? '...' : '—', subtitle: 'API calls', color: 'fuchsia' },
  ];

  return (
    <div className="page-container">
      <div>
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">System Dashboard</h2>
        <p className="text-sm text-slate-500 mt-0.5">Tizim holati va umumiy statistika</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map((c, i) => <StatCard key={i} {...c} />)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent orgs */}
        <div className="lg:col-span-2 rounded-2xl p-5"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">So'nggi tashkilotlar</h3>
              <p className="text-xs text-slate-600">Oxirgi qo'shilganlar</p>
            </div>
            <Building2 size={16} className="text-slate-600" />
          </div>
          {loading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-12 rounded-xl animate-pulse" style={{ background: 'rgba(255,255,255,0.04)' }} />
              ))}
            </div>
          ) : orgs.length === 0 ? (
            <p className="text-sm text-slate-600 py-8 text-center">Hozircha tashkilotlar yo'q</p>
          ) : (
            orgs.map((org, i) => (
              <div key={org.id ?? i} className="flex items-center gap-3 py-3"
                style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white shrink-0"
                  style={{ background: 'linear-gradient(135deg,#8b5cf6,#a78bfa)' }}>
                  {(org.name || '?')[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-300 truncate">{org.name || '—'}</p>
                  <p className="text-xs text-slate-600 truncate">{org.domain || org.email || '—'}</p>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${org.is_active !== false ? 'text-emerald-400' : 'text-red-400'}`}
                  style={{ background: org.is_active !== false ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)' }}>
                  {org.is_active !== false ? 'Faol' : 'Nofaol'}
                </span>
              </div>
            ))
          )}
        </div>

        {/* System status */}
        <div className="rounded-2xl p-5"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} style={{ color: '#a78bfa' }} />
            <h3 className="text-sm font-semibold text-slate-200">Tizim holati</h3>
          </div>
          {services.map(s => (
            <div key={s.label} className="flex items-center justify-between py-2.5"
              style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div className="flex items-center gap-2">
                {s.status
                  ? <CheckCircle size={13} className="text-emerald-400" />
                  : <AlertCircle size={13} className="text-red-400" />}
                <span className="text-sm text-slate-400">{s.label}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full"
                  style={{ background: s.status ? '#10b981' : '#ef4444', boxShadow: `0 0 6px ${s.status ? '#10b981' : '#ef4444'}` }} />
                <span className={`text-xs font-medium ${s.status ? 'text-emerald-400' : 'text-red-400'}`}>
                  {s.status ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          ))}
          <div className="mt-4 p-3 rounded-xl" style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)' }}>
            <p className="text-xs text-slate-500">Barcha xizmatlar</p>
            <p className="text-sm font-semibold mt-0.5" style={{ color: '#a78bfa' }}>Ishlayapti ✓</p>
          </div>
        </div>
      </div>
    </div>
  );
}
