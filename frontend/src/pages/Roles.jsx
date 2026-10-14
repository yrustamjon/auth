import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Search, Shield } from 'lucide-react';
import Table from '../components/Table';
import { activeFilter } from '../components/table-filters';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import { getRoles, createRole, updateRole, deleteRole } from '../api/admin';
import { useAdminToast } from '../contexts/toast';

const S = {
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' },
  right: { display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', maxWidth: '100%' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: '#ffffff', border: '1px solid #e7ecf3' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#46566e', fontSize: '0.875rem', width: '176px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: '#ffffff', border: '1px solid #e7ecf3' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', transition: 'all 0.2s', display: 'flex', alignItems: 'center' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
};

export default function Roles() {
  const toast = useAdminToast();
  const [roles, setRoles] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({ name: '' });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await getRoles();
      const data = Array.isArray(res.data) ? res.data : (res.data?.roles ?? []);
      setRoles(data); setFiltered(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(roles.filter(r => r.name?.toLowerCase().includes(q)));
  }, [search, roles]);

  const openCreate = () => { setForm({ name: '' }); setModal({ mode: 'create' }); };
  const openEdit = (row) => { setForm({ name: row.name }); setModal({ mode: 'edit', data: row }); };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      if (modal.mode === 'create') { await createRole(form); toast("Rol qo'shildi", 'success'); }
      else { await updateRole(modal.data.id, form); toast('Rol yangilandi', 'success'); }
      setModal(null); load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato yuz berdi', 'error'); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await deleteRole(deleteTarget.id);
      toast("Rol o'chirildi", 'success'); setDeleteTarget(null); load();
    } catch { toast("O'chirishda xato", 'error'); }
  };

  const columns = [
    { key: 'id', label: '#', render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span> },
    {
      key: 'name', label: 'Rol nomi',
      render: v => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(99,102,241,0.12)' }}>
            <Shield size={13} style={{ color: '#2563eb' }} />
          </div>
          <span style={{ color: 'var(--ink)', fontWeight: 500 }}>{v}</span>
        </div>
      ),
    },
    {
      key: 'is_active', label: 'Holati',
      render: v => <Badge variant={v !== false ? 'success' : 'danger'} dot>{v !== false ? 'Faol' : 'Nofaol'}</Badge>,
    },
    {
      key: 'created_at', label: 'Yaratilgan',
      render: v => v ? <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(v).toLocaleDateString('uz')}</span> : <span style={{ color: '#334155' }}>—</span>,
    },
  ];

  return (
    <div className="page-container">
      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.025em' }}>Rollar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta rol topildi</p>
        </div>
        <div style={S.right}>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" aria-label="Qidirish" placeholder="Qidirish..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={openCreate} className="btn-primary">
            <Plus size={16} /> Yangi rol
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error} filters={[activeFilter('is_active')]}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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

      <Modal isOpen={!!modal} onClose={() => setModal(null)}
        title={modal?.mode === 'create' ? "Yangi rol qo'shish" : 'Rolni tahrirlash'}
        footer={
          <>
            <button onClick={() => setModal(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? 'Saqlanmoqda...' : modal?.mode === 'create' ? "Qo'shish" : 'Yangilash'}
            </button>
          </>
        }
      >
        <div>
          <label htmlFor="role-name" style={S.label}>Rol nomi *</label>
          <input id="role-name" type="text" placeholder="Masalan: Moderator" value={form.name}
            onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
            className="input-field" autoFocus />
        </div>
      </Modal>

      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Rolni o'chirish"
        footer={
          <>
            <button onClick={() => setDeleteTarget(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleDelete} className="btn-danger">O'chirish</button>
          </>
        }
      >
        <p style={{ fontSize: '0.875rem', color: '#738096' }}>
          <span style={{ color: 'var(--ink)', fontWeight: 600 }}>"{deleteTarget?.name}"</span> rolini o'chirishni tasdiqlaysizmi? Bu amalni qaytarib bo'lmaydi.
        </p>
      </Modal>
    </div>
  );
}
