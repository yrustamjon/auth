import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Search, Fingerprint } from 'lucide-react';
import Table from '../components/Table';
import { activeFilter } from '../components/table-filters';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import BiometricModal from '../components/BiometricModal';
import { getUsers, createUser, updateUser, deleteUser, getRoles } from '../api/admin';
import { useAdminToast } from '../contexts/toast';

const emptyForm = { fio: '', lavozim: '', username: '', role_id: '', status: true };

const S = {
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' },
  right: { display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', maxWidth: '100%' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: '#ffffff', border: '1px solid #e7ecf3' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#46566e', fontSize: '0.875rem', width: '176px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: '#ffffff', border: '1px solid #e7ecf3' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
};

export default function Users() {
  const toast = useAdminToast();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [bioTarget, setBioTarget] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [uRes, rRes] = await Promise.all([getUsers(), getRoles()]);
      const uData = Array.isArray(uRes.data) ? uRes.data : (uRes.data?.users ?? []);
      const rData = Array.isArray(rRes.data) ? rRes.data : (rRes.data?.roles ?? []);
      setUsers(uData); setFiltered(uData); setRoles(rData);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(users.filter(u =>
      (u.username || '').toLowerCase().includes(q) ||
      (u.fio || '').toLowerCase().includes(q) ||
      (u.lavozim || '').toLowerCase().includes(q)
    ));
  }, [search, users]);

  const openCreate = () => { setForm(emptyForm); setModal({ mode: 'create' }); };
  const openEdit = (row) => {
    setForm({
      fio: row.fio || '',
      lavozim: row.lavozim || '',
      username: row.username || '',
      role_id: row.role?.id ?? '',
      status: row.status !== false,
    });
    setModal({ mode: 'edit', data: row });
  };

  const handleSave = async () => {
    if (!form.fio.trim() || !form.username.trim() || !form.lavozim.trim() || !form.role_id) { toast('Ism, login, lavozim va rolni kiriting', 'error'); return; }
    setSaving(true);
    try {
      const payload = {
        fio: form.fio,
        lavozim: form.lavozim,
        username: form.username,
        role_id: form.role_id ? parseInt(form.role_id) : null,
        status: form.status,
      };
      if (modal.mode === 'create') {
        await createUser(payload);
        toast("Foydalanuvchi qo'shildi", 'success');
      } else {
        await updateUser(modal.data.id, payload);
        toast('Foydalanuvchi yangilandi', 'success');
      }
      setModal(null); load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato yuz berdi', 'error'); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await deleteUser(deleteTarget.id);
      toast("O'chirildi", 'success'); setDeleteTarget(null); load();
    } catch { toast("O'chirishda xato", 'error'); }
  };

  const f = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const columns = [
    { key: 'id', label: '#', render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span> },
    {
      key: 'fio', label: 'FIO / Login',
      render: (v, row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'white', flexShrink: 0, background: '#2563eb' }}>
            {(v || row.username || '?')[0].toUpperCase()}
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--ink)', margin: 0 }}>{v}</p>
            <p style={{ fontSize: '0.72rem', color: '#475569', margin: '1px 0 0' }}>{row.username}</p>
          </div>
        </div>
      ),
    },
    { key: 'lavozim', label: 'Lavozim', render: v => <span style={{ fontSize: '0.875rem', color: '#738096' }}>{v || '—'}</span> },
    {
      key: 'role', label: 'Rol',
      render: v => {
        const name = typeof v === 'object' ? v?.name : roles.find(r => r.id === v)?.name;
        return name ? <Badge variant="indigo">{name}</Badge> : <span style={{ color: '#334155' }}>—</span>;
      },
    },
    {
      key: 'has_face', label: 'Yuz',
      render: v => <Badge variant={v ? 'success' : 'default'} dot={!!v}>{v ? 'Bor' : '—'}</Badge>,
    },
    {
      key: 'has_fingerprint', label: 'Barmoq',
      render: v => <Badge variant={v ? 'success' : 'default'} dot={!!v}>{v ? 'Bor' : '—'}</Badge>,
    },
    {
      key: 'status', label: 'Holat',
      render: v => <Badge variant={v !== false ? 'success' : 'danger'} dot>{v !== false ? 'Faol' : 'Nofaol'}</Badge>,
    },
  ];

  return (
    <div className="page-container">
      {bioTarget && (
        <BiometricModal
          user={bioTarget}
          onClose={() => setBioTarget(null)}
          onRefresh={load}
          toast={toast}
        />
      )}

      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.025em' }}>Foydalanuvchilar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta foydalanuvchi</p>
        </div>
        <div style={S.right}>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" aria-label="Qidirish" placeholder="Qidirish..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={openCreate} className="btn-primary">
            <Plus size={16} /> Qo'shish
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error}
          filters={[activeFilter('status'), { key: 'role', label: 'Rol', getValue: row => row.role?.id, options: roles.map(role => ({ value: role.id, label: role.name })) }]}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button onClick={() => setBioTarget(row)} style={S.actionBtn} title="Biometrik"
                onMouseEnter={e => { e.currentTarget.style.color = '#2563eb'; e.currentTarget.style.background = 'rgba(139,92,246,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Fingerprint size={14} />
              </button>
              <button aria-label="Tahrirlash" onClick={() => openEdit(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#2563eb'; e.currentTarget.style.background = 'rgba(99,102,241,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Pencil size={14} />
              </button>
              <button aria-label="O‘chirish" onClick={() => setDeleteTarget(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#cf4650'; e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Trash2 size={14} />
              </button>
            </div>
          )}
        />
      </div>

      {/* Create / Edit Modal */}
      <Modal isOpen={!!modal} onClose={() => setModal(null)}
        title={modal?.mode === 'create' ? "Yangi foydalanuvchi" : 'Tahrirlash'}
        footer={
          <>
            <button onClick={() => setModal(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? 'Saqlanmoqda...' : modal?.mode === 'create' ? "Qo'shish" : 'Yangilash'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            { label: 'FIO *', key: 'fio', type: 'text', ph: 'Ism Familiya' },
            { label: 'Lavozim *', key: 'lavozim', type: 'text', ph: 'Masalan: Buxgalter' },
            { label: 'Login *', key: 'username', type: 'text', ph: 'login_nomi' },
          ].map(({ label, key, type, ph }) => (
            <div key={key}>
              <label htmlFor={"field-"+key} style={S.label}>{label}</label>
              <input id={"field-"+key} type={type} placeholder={ph} value={form[key]}
                onChange={e => f(key)(e.target.value)} className="input-field" />
            </div>
          ))}
          <div>
            <label htmlFor="user-role" style={S.label}>Rol</label>
            <select id="user-role" value={form.role_id} onChange={e => f('role_id')(e.target.value)} className="input-field">
              <option value="">— Tanlang —</option>
              {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          {modal?.mode === 'edit' && <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input type="checkbox" id="status_u" checked={form.status}
              onChange={e => f('status')(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: '#2563eb' }} />
            <label htmlFor="status_u" style={{ fontSize: '0.875rem', color: '#738096', cursor: 'pointer' }}>Faol holat</label>
          </div>}
        </div>
      </Modal>

      {/* Delete Confirm */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="O'chirishni tasdiqlash"
        footer={
          <>
            <button onClick={() => setDeleteTarget(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleDelete} className="btn-danger">O'chirish</button>
          </>
        }
      >
        <p style={{ fontSize: '0.875rem', color: '#738096' }}>
          <span style={{ color: 'var(--ink)', fontWeight: 600 }}>"{deleteTarget?.fio}"</span> ni o'chirishni tasdiqlaysizmi?
        </p>
      </Modal>
    </div>
  );
}
