import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Pencil, Trash2, Search, Monitor } from 'lucide-react';
import Table from '../components/Table';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import RemovalCodeCard from '../components/RemovalCodeCard';
import { getDevices, createDevice, updateDevice } from '../api/admin';
import { useAdminToast } from '../contexts/toast';

const empty = { pc_id: '', location: '', license: '', platform: 'windows', is_active: true };

const S = {
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' },
  right: { display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', maxWidth: '100%' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: '#ffffff', border: '1px solid #e7ecf3' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#46566e', fontSize: '0.875rem', width: '192px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: '#ffffff', border: '1px solid #e7ecf3' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', transition: 'all 0.2s', display: 'flex', alignItems: 'center' },
  formGroup: { display: 'flex', flexDirection: 'column', gap: '1rem' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
};

export default function Devices() {
  const toast = useAdminToast();
  const [devices, setDevices] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await getDevices();
      const data = Array.isArray(res.data) ? res.data : [];
      setDevices(data); setFiltered(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(devices.filter(d =>
      (d.pc_id || '').toLowerCase().includes(q) ||
      (d.location || '').toLowerCase().includes(q)
    ));
  }, [search, devices]);

  const openCreate = () => { setForm(empty); setModal({ mode: 'create' }); };
  const openEdit = (row) => {
    setForm({ pc_id: row.pc_id, location: row.location || '', license: row.license || '', platform: row.platform || 'windows', is_active: row.is_active !== false });
    setModal({ mode: 'edit', data: row });
  };

  const handleSave = async () => {
    if (!form.pc_id.trim() || !form.location.trim() || (form.platform === 'windows' && !form.license.trim())) { toast('PC ID, joylashuv va Windows litsenziyasini kiriting', 'error'); return; }
    setSaving(true);
    try {
      if (modal.mode === 'create') { await createDevice(form); toast("Qurilma qo'shildi", 'success'); }
      else { await updateDevice(modal.data.id, form); toast('Qurilma yangilandi', 'success'); }
      setModal(null); load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato', 'error'); }
    finally { setSaving(false); }
  };



  const f = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const columns = [
    { key: 'id', label: '#', render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span> },
    {
      key: 'pc_id', label: 'PC ID',
      render: v => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.15)' }}>
            <Monitor size={14} style={{ color: '#60a5fa' }} />
          </div>
          <span style={{ color: 'var(--ink)', fontFamily: 'monospace', fontSize: '0.875rem' }}>{v}</span>
        </div>
      ),
    },
    { key: 'location', label: 'Joylashuv', render: v => <span style={{ color: '#738096', fontSize: '0.875rem' }}>{v || '—'}</span> },
    {
      key: 'is_active', label: 'Holat',
      render: (v, row) => row.removal_state === 'removed'
        ? <Badge variant="default">O‘chirilgan</Badge>
        : row.removal_state === 'removal_pending'
        ? <Badge variant="warning">O‘chirish yakunlanmagan</Badge>
        : row.enrollment_status === 'browser_approved'
        ? <Badge variant="warning" dot>Agent kutilmoqda</Badge>
        : <Badge variant={v !== false ? 'success' : 'danger'} dot>{v !== false ? 'Faol' : 'Nofaol'}</Badge>,
    },
    {
      key: 'last_seen', label: "Oxirgi ko'rilgan",
      render: v => v
        ? <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(v).toLocaleString('uz')}</span>
        : <span style={{ color: '#334155' }}>—</span>,
    },
  ];

  return (
    <div className="page-container">
      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.025em' }}>Qurilmalar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta qurilma</p>
        </div>
        <div style={S.right}>
          <Link to="/devices/scan-qr/" className="btn-secondary">QR orqali ulash</Link>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" placeholder="PC ID yoki joylashuv..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={openCreate} className="btn-primary">
            <Plus size={16} /> Qurilma qo'shish
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button aria-label="Tahrirlash" disabled={row.enrollment_status === 'browser_approved'} title={row.enrollment_status === 'browser_approved' ? 'Agent ulanishi kutilmoqda' : 'Tahrirlash'} onClick={() => openEdit(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#2563eb'; e.currentTarget.style.background = 'rgba(99,102,241,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Pencil size={14} />
              </button>
              <button aria-label="O‘chirish" disabled={row.removal_state && row.removal_state !== 'active'} title="O‘chirish kodini yaratish" onClick={() => setDeleteTarget(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#cf4650'; e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Trash2 size={14} />
              </button>
            </div>
          )}
        />
      </div>

      <Modal isOpen={!!modal} onClose={() => setModal(null)}
        title={modal?.mode === 'create' ? "Yangi qurilma" : 'Qurilmani tahrirlash'}
        footer={
          <>
            <button onClick={() => setModal(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? 'Saqlanmoqda...' : modal?.mode === 'create' ? "Qo'shish" : 'Yangilash'}
            </button>
          </>
        }
      >
        <div style={S.formGroup}>
          <label className="text-sm">Operatsion tizim<select className="input-field mt-2" value={form.platform} onChange={e => f('platform')(e.target.value)}><option value="windows">Windows</option><option value="macos">macOS</option><option value="linux">Linux</option></select></label>
          {[
            { label: 'PC ID *', key: 'pc_id', ph: 'DESKTOP-XXXXX' },
            { label: 'Joylashuv *', key: 'location', ph: 'Ofis 1, 3-qavat' },
            { label: 'Litsenziya', key: 'license', ph: 'XXX-XXX-XXX' },
          ].map(({ label, key, ph }) => (
            <div key={key}>
              <label htmlFor={"field-"+key} style={S.label}>{label}</label>
              <input id={"field-"+key} type="text" placeholder={ph} value={form[key]}
                onChange={e => f(key)(e.target.value)} className="input-field" />
            </div>
          ))}
          {modal?.mode === 'edit' && <div style={{ display: 'flex', gap: '1.5rem' }}>
            {[
              { id: 'is_active', label: 'Faol', key: 'is_active' },

            ].map(({ id, label, key }) => (
              <div key={id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input type="checkbox" id={id} checked={form[key]}
                  onChange={e => f(key)(e.target.checked)}
                  style={{ width: '16px', height: '16px', accentColor: '#2563eb' }} />
                <label htmlFor={id} style={{ fontSize: '0.875rem', color: '#738096', cursor: 'pointer' }}>{label}</label>
              </div>
            ))}
          </div>}
        </div>
      </Modal>

      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Agentni o‘chirish kodi"
        footer={
          <>
            <button onClick={() => setDeleteTarget(null)} className="btn-secondary">Bekor</button>

          </>
        }
      >
        {deleteTarget && <RemovalCodeCard key={deleteTarget.id} device={deleteTarget}/>}
      </Modal>
    </div>
  );
}
