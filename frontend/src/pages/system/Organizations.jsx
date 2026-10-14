import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Search, Eye, Ban, CheckCircle, LogOut, UserPlus } from 'lucide-react';
import Table from '../../components/Table';
import { activeFilter } from '../../components/table-filters';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import {
  getOrganizations, getOrganization, createOrganization, updateOrganization, deleteOrganization,
  getOrgAdmins, getSystemAdmins, forceLogoutAdmin, attachAdminToOrg,
} from '../../api/superadmin';
import { useSystemToast } from '../../contexts/toast';

const emptyForm = { name: '', slug: '', active: true };

const S = {
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(135px,1fr))', gap: '1rem', marginBottom: '1.5rem' },
  statCard: { borderRadius: '1rem', padding: '1.25rem 1.5rem', background: '#ffffff', border: '1px solid #e7ecf3', display: 'flex', flexDirection: 'column', gap: '0.5rem' },
  statLabel: { fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' },
  statValue: { fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)', lineHeight: 1 },
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' },
  right: { display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', maxWidth: '100%' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: '#ffffff', border: '1px solid #e7ecf3' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#46566e', fontSize: '0.875rem', width: '192px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: '#ffffff', border: '1px solid #e7ecf3' },
  addBtn: { display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1rem', borderRadius: '0.75rem', fontSize: '0.875rem', fontWeight: 600, color: 'white', border: 'none', cursor: 'pointer', background: '#2563eb', boxShadow: '0 3px 7px #2563eb18' },
  saveBtn: { display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1rem', borderRadius: '0.75rem', fontSize: '0.875rem', fontWeight: 600, color: 'white', border: 'none', cursor: 'pointer', background: '#2563eb' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', transition: 'all 0.2s', display: 'flex', alignItems: 'center' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
  detailRow: { display: 'flex', gap: '0.5rem', marginBottom: '0.375rem', fontSize: '0.875rem' },
  detailKey: { color: '#64748b', minWidth: '100px' },
  detailVal: { color: 'var(--ink)', fontWeight: 500 },
  sectionHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid #e7ecf3' },
};

function StatCard({ label, value, color }) {
  return (
    <div style={S.statCard}>
      <span style={S.statLabel}>{label}</span>
      <span style={{ ...S.statValue, color: color || 'var(--ink)' }}>{value}</span>
    </div>
  );
}

export default function Organizations() {
  const toast = useSystemToast();
  const [orgs, setOrgs] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Detail modal state
  const [detailOrg, setDetailOrg] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [orgAdmins, setOrgAdmins] = useState([]);
  const [allAdmins, setAllAdmins] = useState([]);
  const [attachModal, setAttachModal] = useState(false);
  const [attachAdminId, setAttachAdminId] = useState('');
  const [attaching, setAttaching] = useState(false);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await getOrganizations();
      const data = Array.isArray(res.data) ? res.data : (res.data?.organizations ?? []);
      setOrgs(data);
      setFiltered(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(orgs.filter(o =>
      (o.name || '').toLowerCase().includes(q) ||
      (o.slug || '').toLowerCase().includes(q)
    ));
  }, [search, orgs]);

  // Stats
  const totalOrgs = orgs.length;
  const activeOrgs = orgs.filter(o => o.active !== false).length;
  const inactiveOrgs = totalOrgs - activeOrgs;
  const totalAdmins = orgs.reduce((s, o) => s + (o.admin_count || 0), 0);

  const openCreate = () => { setForm(emptyForm); setModal({ mode: 'create' }); };
  const openEdit = (row) => {
    setForm({ name: row.name || '', slug: row.slug || '', active: row.active !== false });
    setModal({ mode: 'edit', data: row });
  };

  const openDetail = async (row) => {
    setDetailOrg(row);
    setDetailLoading(true);
    try {
      const [detailRes, adminsRes, allRes] = await Promise.all([
        getOrganization(row.id),
        getOrgAdmins(row.id),
        getSystemAdmins(),
      ]);
      setDetailOrg(detailRes.data);
      const adminsData = Array.isArray(adminsRes.data) ? adminsRes.data : (adminsRes.data?.admins ?? []);
      setOrgAdmins(adminsData);
      const allData = Array.isArray(allRes.data) ? allRes.data : (allRes.data?.admins ?? []);
      setAllAdmins(allData);
    } catch { toast('Tafsilotlarni yuklashda xato', 'error'); }
    finally { setDetailLoading(false); }
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.slug.trim()) { toast('Nom va slugni kiriting', 'error'); return; }
    setSaving(true);
    try {
      if (modal.mode === 'create') {
        await createOrganization({ name: form.name, slug: form.slug });
        toast("Tashkilot qo'shildi", 'success');
      } else {
        await updateOrganization(modal.data.id, { name: form.name, slug: form.slug, active: form.active });
        toast('Tashkilot yangilandi', 'success');
      }
      setModal(null);
      load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato yuz berdi', 'error'); }
    finally { setSaving(false); }
  };

  const handleToggleActive = async (row) => {
    try {
      await updateOrganization(row.id, { active: !row.active });
      toast(row.active ? 'Noaktiv qilindi' : 'Aktiv qilindi', 'success');
      load();
    } catch { toast('Xato yuz berdi', 'error'); }
  };

  const handleDelete = async () => {
    try {
      await deleteOrganization(deleteTarget.id);
      toast("O'chirildi", 'success');
      setDeleteTarget(null);
      load();
    } catch { toast("O'chirishda xato", 'error'); }
  };

  const handleForceLogout = async (admin) => {
    try {
      await forceLogoutAdmin(admin.id);
      toast(`${admin.username} tizimdan chiqarildi`, 'success');
      const res = await getOrgAdmins(detailOrg.id);
      setOrgAdmins(Array.isArray(res.data) ? res.data : (res.data?.admins ?? []));
    } catch { toast('Xato yuz berdi', 'error'); }
  };

  const handleAttach = async () => {
    if (!attachAdminId) return;
    setAttaching(true);
    try {
      await attachAdminToOrg(attachAdminId, detailOrg.id);
      toast("Admin qo'shildi", 'success');
      setAttachModal(false);
      setAttachAdminId('');
      const res = await getOrgAdmins(detailOrg.id);
      setOrgAdmins(Array.isArray(res.data) ? res.data : (res.data?.admins ?? []));
    } catch { toast('Xato yuz berdi', 'error'); }
    finally { setAttaching(false); }
  };

  const f = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const columns = [
    {
      key: 'id', label: '#',
      render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span>,
    },
    {
      key: 'name', label: 'Tashkilot',
      render: v => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'white', flexShrink: 0, background: '#2563eb' }}>
            {(v || '?')[0].toUpperCase()}
          </div>
          <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--ink)' }}>{v}</span>
        </div>
      ),
    },
    {
      key: 'slug', label: 'Slug',
      render: v => v
        ? <span style={{ fontSize: '0.8rem', color: '#738096', fontFamily: 'monospace', background: '#f5f7fb', padding: '2px 8px', borderRadius: '6px' }}>{v}</span>
        : <span style={{ color: '#334155' }}>—</span>,
    },
    {
      key: 'active', label: 'Holat',
      render: v => <Badge variant={v !== false ? 'success' : 'danger'} dot>{v !== false ? 'Faol' : 'Nofaol'}</Badge>,
    },
    {
      key: 'admin_count', label: 'Adminlar',
      render: v => (
        <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700, color: '#2563eb', background: '#edf3ff' }}>
          {v ?? 0}
        </span>
      ),
    },
    {
      key: 'created_at', label: 'Yaratilgan',
      render: v => v
        ? <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(v).toLocaleDateString('uz')}</span>
        : <span style={{ color: '#334155' }}>—</span>,
    },
  ];

  return (
    <div className="page-container">
      {/* Stat cards */}
      <div style={S.statGrid}>
        <StatCard label="Jami tashkilotlar" value={totalOrgs} />
        <StatCard label="Faol" value={activeOrgs} color="#4ade80" />
        <StatCard label="Nofaol" value={inactiveOrgs} color="#cf4650" />
        <StatCard label="Jami adminlar" value={totalAdmins} color="#2563eb" />
      </div>

      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.025em' }}>Tashkilotlar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta tashkilot</p>
        </div>
        <div style={S.right}>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" placeholder="Nom yoki slug..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={openCreate} style={S.addBtn}><Plus size={16} /> Qo'shish</button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error} filters={[activeFilter('active')]}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <button title="Ko'rish" onClick={() => openDetail(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#38bdf8'; e.currentTarget.style.background = 'rgba(56,189,248,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Eye size={14} />
              </button>
              <button title="Tahrirlash" onClick={() => openEdit(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#2563eb'; e.currentTarget.style.background = 'rgba(139,92,246,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Pencil size={14} />
              </button>
              <button title={row.active !== false ? 'Noaktiv qilish' : 'Aktiv qilish'} onClick={() => handleToggleActive(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = row.active !== false ? '#fb923c' : '#4ade80'; e.currentTarget.style.background = row.active !== false ? 'rgba(251,146,60,0.1)' : 'rgba(74,222,128,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                {row.active !== false ? <Ban size={14} /> : <CheckCircle size={14} />}
              </button>
              <button title="O'chirish" onClick={() => setDeleteTarget(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#cf4650'; e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Trash2 size={14} />
              </button>
            </div>
          )}
        />
      </div>

      {/* Create / Edit modal */}
      <Modal isOpen={!!modal} onClose={() => setModal(null)}
        title={modal?.mode === 'create' ? "Yangi tashkilot" : 'Tashkilotni tahrirlash'}
        footer={
          <>
            <button onClick={() => setModal(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleSave} disabled={saving} style={S.saveBtn}>
              {saving ? 'Saqlanmoqda...' : modal?.mode === 'create' ? "Qo'shish" : 'Yangilash'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="org-name" style={S.label}>Nomi *</label>
            <input type="text" id="org-name" aria-label="Nomi *" placeholder="Tashkilot nomi" value={form.name}
              onChange={e => f('name')(e.target.value)} className="input-field" />
          </div>
          <div>
            <label htmlFor="org-slug" style={S.label}>Slug</label>
            <input type="text" id="org-slug" aria-label="Slug" placeholder="tashkilot-slug" value={form.slug}
              onChange={e => f('slug')(e.target.value)} className="input-field" />
          </div>
          {modal?.mode === 'edit' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input type="checkbox" id="org_active" checked={form.active}
                onChange={e => f('active')(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#2563eb' }} />
              <label htmlFor="org_active" style={{ fontSize: '0.875rem', color: '#738096', cursor: 'pointer' }}>Faol holat</label>
            </div>
          )}
        </div>
      </Modal>

      {/* Detail modal */}
      <Modal isOpen={!!detailOrg} onClose={() => setDetailOrg(null)} title="Tashkilot tafsilotlari" size="lg">
        {detailLoading ? (
          <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Yuklanmoqda...</p>
        ) : detailOrg && (
          <>
            {/* Org info */}
            <div style={{ background: '#ffffff', borderRadius: '0.75rem', padding: '1rem 1.25rem', marginBottom: '1.5rem', border: '1px solid #e7ecf3' }}>
              <div style={S.detailRow}><span style={S.detailKey}>Nomi:</span><span style={S.detailVal}>{detailOrg.name}</span></div>
              <div style={S.detailRow}><span style={S.detailKey}>Slug:</span><span style={{ ...S.detailVal, fontFamily: 'monospace', color: '#738096' }}>{detailOrg.slug || '—'}</span></div>
              <div style={S.detailRow}><span style={S.detailKey}>Holat:</span><Badge variant={detailOrg.active !== false ? 'success' : 'danger'} dot>{detailOrg.active !== false ? 'Faol' : 'Nofaol'}</Badge></div>
              <div style={S.detailRow}><span style={S.detailKey}>Yaratilgan:</span><span style={{ ...S.detailVal, color: '#64748b' }}>{detailOrg.created_at ? new Date(detailOrg.created_at).toLocaleString('uz') : '—'}</span></div>
            </div>

            {/* Admins section */}
            <div style={S.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--ink)' }}>Adminlar</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#2563eb', background: '#edf3ff' }}>
                  {orgAdmins.length}
                </span>
              </div>
              <button onClick={() => setAttachModal(true)} style={{ ...S.saveBtn, fontSize: '0.8rem', padding: '0.4rem 0.75rem', gap: '0.375rem' }}>
                <UserPlus size={13} /> Admin qo'shish
              </button>
            </div>

            {orgAdmins.length === 0 ? (
              <p style={{ color: '#475569', fontSize: '0.875rem', textAlign: 'center', padding: '1.5rem' }}>Adminlar yo'q</p>
            ) : (
              <div style={{ background: '#f8fafc', borderRadius: '0.75rem', overflow: 'hidden', border: '1px solid #f5f7fb' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #e7ecf3' }}>
                      {['Username', 'Super admin', 'Holat', 'Muvaffaqiyatsiz', 'Harakatlar'].map(h => (
                        <th key={h} style={{ padding: '0.625rem 0.875rem', textAlign: 'left', color: '#475569', fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {orgAdmins.map(a => (
                      <tr key={a.id} style={{ borderBottom: '1px solid #ffffff' }}>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--ink)', fontWeight: 500 }}>{a.username}</td>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <Badge variant={a.is_superadmin ? 'success' : 'default'} dot>{a.is_superadmin ? 'Ha' : 'Yo\'q'}</Badge>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <Badge variant={a.is_active !== false ? 'success' : 'danger'} dot>{a.is_active !== false ? 'Faol' : 'Nofaol'}</Badge>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem', color: a.failed_attempts > 0 ? '#cf4650' : '#475569' }}>
                          {a.failed_attempts ?? 0}
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <button onClick={() => handleForceLogout(a)} title="Tizimdan chiqarish"
                            style={{ ...S.actionBtn, color: '#fb923c' }}
                            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(251,146,60,0.1)'; }}
                            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                            <LogOut size={13} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Modal>

      {/* Attach admin modal */}
      <Modal isOpen={attachModal} onClose={() => { setAttachModal(false); setAttachAdminId(''); }} title="Admin qo'shish"
        footer={
          <>
            <button onClick={() => { setAttachModal(false); setAttachAdminId(''); }} className="btn-secondary">Bekor</button>
            <button onClick={handleAttach} disabled={attaching || !attachAdminId} style={S.saveBtn}>
              {attaching ? 'Qo\'shilmoqda...' : "Qo'shish"}
            </button>
          </>
        }
      >
        <div>
          <label style={S.label}>Admin tanlang</label>
          <select value={attachAdminId} onChange={e => setAttachAdminId(e.target.value)} className="input-field">
            <option value="">— Tanlang —</option>
            {allAdmins
              .filter(a => !orgAdmins.find(oa => oa.id === a.id))
              .map(a => (
                <option key={a.id} value={a.id}>{a.username}</option>
              ))}
          </select>
        </div>
      </Modal>

      {/* Delete confirm modal */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="O'chirishni tasdiqlash"
        footer={
          <>
            <button onClick={() => setDeleteTarget(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleDelete} className="btn-danger">O'chirish</button>
          </>
        }
      >
        <p style={{ fontSize: '0.875rem', color: '#738096' }}>
          <span style={{ color: 'var(--ink)', fontWeight: 600 }}>"{deleteTarget?.name}"</span> tashkilotini o'chirasizmi?
        </p>
      </Modal>
    </div>
  );
}
