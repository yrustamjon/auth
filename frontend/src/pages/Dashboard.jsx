import { useEffect, useState } from 'react';
import { Users, Shield, Monitor, FileText, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import StatCard from '../components/StatCard';
import Badge from '../components/Badge';
import { getUsers, getRoles, getDevices, getLogs } from '../api/admin';

function RecentLog({ log }) {
  const time = new Date(log.timestamp || log.created_at || Date.now())
    .toLocaleTimeString('uz', { hour: '2-digit', minute: '2-digit' });
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <div style={{
        width: '32px', height: '32px', borderRadius: '10px', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: log.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
      }}>
        {log.success
          ? <CheckCircle size={15} style={{ color: '#34d399' }} />
          : <XCircle size={15} style={{ color: '#f87171' }} />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {log.user_fio || log.username || "Noma'lum"}
        </p>
        <p style={{ fontSize: '0.75rem', color: '#475569', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {log.device_pc_id || log.device || '—'}
        </p>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <Badge variant={log.success ? 'success' : 'danger'} dot>
          {log.success ? 'OK' : 'Rad'}
        </Badge>
        <p style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.25rem' }}>{time}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({ users: 0, roles: 0, devices: 0, logs: 0 });
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([getUsers(), getRoles(), getDevices(), getLogs()])
      .then(([u, r, d, l]) => {
        const users = u.status === 'fulfilled' ? (Array.isArray(u.value.data) ? u.value.data : u.value.data?.users ?? []) : [];
        const roles = r.status === 'fulfilled' ? (Array.isArray(r.value.data) ? r.value.data : r.value.data?.roles ?? []) : [];
        const devices = d.status === 'fulfilled' ? (Array.isArray(d.value.data) ? d.value.data : []) : [];
        const logs = l.status === 'fulfilled' ? (Array.isArray(l.value.data) ? l.value.data : l.value.data?.logs ?? []) : [];
        setStats({ users: users.length, roles: roles.length, devices: devices.length, logs: logs.length });
        setRecentLogs(logs.slice(0, 8));
      })
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    { icon: <Users size={20} />, title: 'Foydalanuvchilar', value: loading ? '...' : stats.users, subtitle: 'Jami admin userlar', trend: 12, color: 'indigo' },
    { icon: <Shield size={20} />, title: 'Rollar', value: loading ? '...' : stats.roles, subtitle: 'Faol rollar', color: 'violet' },
    { icon: <Monitor size={20} />, title: 'Qurilmalar', value: loading ? '...' : stats.devices, subtitle: "Ro'yxatdagi qurilmalar", trend: -3, color: 'blue' },
    { icon: <FileText size={20} />, title: 'Kirish loglari', value: loading ? '...' : stats.logs, subtitle: 'Jami yozuvlar', trend: 8, color: 'emerald' },
  ];

  return (
    <div className="page-container">
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.025em' }}>Dashboard</h2>
        <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>Tizim holati va statistika</p>
      </div>

      {/* Stats grid */}
      <div className="stats-grid">
        {cards.map((c, i) => <StatCard key={i} {...c} />)}
      </div>

      {/* Bottom grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {/* Recent logs — span 2 */}
        <div style={{
          gridColumn: 'span 2', borderRadius: '1rem', padding: '1.25rem',
          background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>So'nggi kirish loglari</h3>
              <p style={{ fontSize: '0.75rem', color: '#475569' }}>Real-time monitoring</p>
            </div>
            <Clock size={16} style={{ color: '#475569' }} />
          </div>
          {recentLogs.length === 0 && !loading ? (
            <p style={{ fontSize: '0.875rem', color: '#475569', padding: '2rem 0', textAlign: 'center' }}>Hozircha loglar yo'q</p>
          ) : (
            recentLogs.map((log, i) => <RecentLog key={log.id ?? i} log={log} />)
          )}
        </div>

        {/* System status */}
        <div style={{
          borderRadius: '1rem', padding: '1.25rem',
          background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <TrendingUp size={16} style={{ color: '#818cf8' }} />
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>Tizim holati</h3>
          </div>
          {[
            { label: 'API Server', status: true },
            { label: 'Database', status: true },
            { label: 'Auth Service', status: true },
            { label: 'Log Service', status: true },
          ].map(s => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.625rem 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{s.label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981', display: 'inline-block' }} />
                <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 500 }}>Online</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
