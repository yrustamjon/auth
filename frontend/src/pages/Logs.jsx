import { useEffect, useState } from 'react';
import { Search, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import Table from '../components/Table';
import Badge from '../components/Badge';
import { getLogs } from '../api/admin';

const S = {
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' },
  right: { display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#cbd5e1', fontSize: '0.875rem', width: '176px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' },
};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const load = async () => {
    setLoading(true);
    try {
      const res = await getLogs();
      const data = Array.isArray(res.data) ? res.data : (res.data?.logs ?? []);
      setLogs(data); setFiltered(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(logs.filter(l => {
      const matchSearch =
        (l.username || l.user_fio || '').toLowerCase().includes(q) ||
        (l.device_pc_id || l.device || '').toLowerCase().includes(q) ||
        (l.ip_address || '').toLowerCase().includes(q);
      const matchStatus =
        statusFilter === 'all' ||
        (statusFilter === 'success' && l.success) ||
        (statusFilter === 'failed' && !l.success);
      return matchSearch && matchStatus;
    }));
  }, [search, statusFilter, logs]);

  const successCount = logs.filter(l => l.success).length;
  const failCount = logs.filter(l => !l.success).length;

  const filterOptions = [
    { value: 'all', label: 'Barchasi' },
    { value: 'success', label: 'OK' },
    { value: 'failed', label: 'Rad' },
  ];

  const columns = [
    { key: 'id', label: '#', render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span> },
    {
      key: 'username', label: 'Foydalanuvchi',
      render: (v, row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'white', flexShrink: 0, background: row.success ? 'linear-gradient(135deg,#059669,#10b981)' : 'linear-gradient(135deg,#dc2626,#ef4444)' }}>
            {((row.user_fio || v || '?')[0] || '?').toUpperCase()}
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0' }}>{v || row.user_fio || "Noma'lum"}</p>
            {row.user_fio && v && <p style={{ fontSize: '0.75rem', color: '#475569' }}>{row.user_fio}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'device_pc_id', label: 'Qurilma',
      render: (v, row) => <span style={{ fontFamily: 'monospace', fontSize: '0.875rem', color: '#94a3b8' }}>{v || row.device || '—'}</span>,
    },
    {
      key: 'ip_address', label: 'IP',
      render: v => v
        ? <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '6px' }}>{v}</span>
        : <span style={{ color: '#334155' }}>—</span>,
    },
    {
      key: 'success', label: 'Natija',
      render: v => v
        ? <Badge variant="success" dot>Muvaffaqiyatli</Badge>
        : <Badge variant="danger" dot>Rad etildi</Badge>,
    },
    {
      key: 'timestamp', label: 'Vaqt',
      render: (v, row) => {
        const ts = v || row.created_at;
        return ts
          ? <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(ts).toLocaleString('uz')}</span>
          : <span style={{ color: '#334155' }}>—</span>;
      },
    },
  ];

  return (
    <div className="page-container">
      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.025em' }}>Kirish loglari</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta yozuv</p>
        </div>
        <div style={S.right}>
          {/* Counters */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)' }}>
            <CheckCircle size={13} style={{ color: '#34d399' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 500, color: '#34d399' }}>{successCount} muvaffaqiyatli</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)' }}>
            <XCircle size={13} style={{ color: '#f87171' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 500, color: '#f87171' }}>{failCount} rad etildi</span>
          </div>

          {/* Filter tabs */}
          <div style={{ display: 'flex', gap: '2px', padding: '4px', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
            {filterOptions.map(({ value, label }) => (
              <button key={value} onClick={() => setStatusFilter(value)} style={{
                padding: '0.375rem 0.75rem', borderRadius: '8px', fontSize: '0.75rem', fontWeight: 500,
                border: statusFilter === value ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                background: statusFilter === value ? 'rgba(99,102,241,0.2)' : 'transparent',
                color: statusFilter === value ? '#818cf8' : '#64748b', cursor: 'pointer', transition: 'all 0.2s',
              }}>
                {label}
              </button>
            ))}
          </div>

          {/* Search */}
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" placeholder="User, qurilma, IP..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>

          {/* Refresh */}
          <button onClick={load} style={{ padding: '0.5rem', borderRadius: '0.75rem', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.04)', color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            title="Yangilash">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error} />
      </div>
    </div>
  );
}
