import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Search, Lock, Unlock, RefreshCw, LogOut, Link } from 'lucide-react';
import Table from '../../components/Table';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import {
  getSystemAdmins, createSystemAdmin, updateSystemAdmin, deleteSystemAdmin,
  getOrganizations, forceLogoutAdmin, resetAdminAttempts, toggleAdminLock, attachAdminToOrg,
} from '../../api/superadmin';
import { useSystemToast } from '../../layouts/SystemLayout';

const emptyCreate = { username: '', password: '', organization_id: '', is_superuser: false };

const S = {
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '1rem', marginBottom: '1.5rem' },
  statCard: { borderRadius: '1rem', padding: '1.25rem 1.5rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: '1rem' },
  statIcon: { width: '44px', height: '44px', borderRadius: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: '1.1rem' },
  statLabel: { fontSize: '0.72rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' },
  statValue: { fontSize: '1.6rem', fontWeight: 800, color: '#f1f5f9', lineHeight: 1 },
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' },
  right: { display: 'flex', alignItems: 'center', gap: '0.75rem' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#cbd5e1', fontSize: '0.875rem', width: '176px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' },
  addBtn: { display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1rem', borderRadius: '0.75rem', fontSize: '0.875rem', fontWeight: 600, color: 'white', border: 'none', cursor: 'pointer', background: 'linear-gradient(135deg,#8b5cf6,#a78bfa)', boxShadow: '0 4px 14px rgba(139,92,246,0.35)' },
  saveBtn: { display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1rem', borderRadius: '0.75rem', fontSize: '0.875rem', fontWeight: 600, color: 'white', border: 'none', cursor: 'pointer', background: 'linear-gradient(135deg,#8b5cf6,#a78bfa)' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', transition: 'all 0.2s', display: 'flex', alignItems: 'center' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
  tab: (active) => ({ padding: '0.6rem 1rem', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700, color: active ? '#a78bfa' : '#64748b', borderBottom: `2px solid ${active ? '#8b5cf6' : 'transparent'}`, display: 'flex', alignItems: 'center', gap: '0.375rem', transition: 'all 0.2s' }),
};

function hoverBtn(el, color, bg) {
  el.onmouseenter = () => { el.style.color = color; el.style.background = bg; };
  el.onmouseleave = () => { el.style.color = '#64748b'; el.style.background = 'transparent'; };
}

function StatCard({ icon, label, value, color, bg }) {
  return (
    <div style={S.statCard}>
      <div style={{ ...S.statIcon, background: bg, color }}>{icon}</div>
      <div>
        <div style={S.statValue}>{value}</div>
        <div style={S.statLabel}>{label}</div>
      </div>
    </div>
  );
}

export default function Admins() {
  const toast = useSystemToast();
  const [admins, setAdmins] = useState([]);
  const [orgs, setOrgs] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  // Create modal
  const [createModal, setCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreate);
  const [creating, setCreating] = useState(false);

  // Edit modal
  const [editTarget, setEditTarget] = useState(null);
  const [editTab, setEditTab] = useState('info');
  const [editInfo, setEditInfo] = useState({ username: '', is_superuser: false });
  const [editPass, setEditPass] = useState({ password: '', confirm: '' });
  const [editOrgs, setEditOrgs] = useState([]);
  const [attachOrgId, setAttachOrgId] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete modal
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [aRes, oRes] = await Promise.allSettled([getSystemAdmins(), getOrganizations()]);
      const aData = aRes.status === 'fulfilled' ? (Array.isArray(aRes.value.data) ? aRes.value.data : aRes.value.data?.admins ?? []) : [];
      const oData = oRes.status === 'fulfilled' ? (Array.isArray(oRes.value.data) ? oRes.value.data : oRes.value.data?.organizations ?? []) : [];
      setAdmins(aData); setFiltered(aData); setOrgs(oData);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(admins.filter(a =>
      (a.username || '').toLowerCase().includes(q) ||
      (a.fio || '').toLowerCase().includes(q)
    ));
  }, [search, admins]);

  // Stats
  const totalAdmins = admins.length;
  const superAdmins = admins.filter(a => a.superadmin || a.is_superuser).length;
  const lockedAdmins = admins.filter(a => a.locked).length;
  const highRisk = admins.filter(a => (a.failed_attempts ?? 0) > 3).length;

  const openEdit = (row) => {
    setEditTarget(row);
    setEditTab('info');
    setEditInfo({ username: row.username || '', is_superuser: !!(row.superadmin || row.is_superuser) });
    setEditPass({ password: '', confirm: '' });
    const orgNames = Array.isArray(row.organization) ? row.organization : (row.organization ? [row.organization] : []);
    setEditOrgs(orgNames);
    setAttachOrgId('');
  };

  // Create
  const handleCreate = async () => {
    if (!createForm.username.trim() || !createForm.password || !createForm.organization_id) {
      toast('Barcha majburiy maydonlarni to\'ldiring', 'error'); return;
    }
    setCreating(true);
    try {
      await createSystemAdmin({
        username: createForm.username,
        password: createForm.password,
        organization_id: parseInt(createForm.organization_id),
        is_superuser: createForm.is_superuser,
      });
      toast("Admin qo'shildi", 'success');
      setCreateModal(false);
      setCreateForm(emptyCreate);
      load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato yuz berdi', 'error'); }
    finally { setCreating(false); }
  };

  // Edit — Info tab
  const handleSaveInfo = async () => {
    if (!editInfo.username.trim()) return;
    setSaving(true);
    try {
      await updateSystemAdmin(editTarget.id, { username: editInfo.username, is_superuser: editInfo.is_superuser });
      toast('Admin yangilandi', 'success');
      setEditTarget(null);
      load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato', 'error'); }
    finally { setSaving(false); }
  };

  // Edit — Password tab
  const handleSavePass = async () => {
    if (!editPass.password) { toast('Yangi parol kiriting', 'error'); return; }
    if (editPass.password !== editPass.confirm) { toast('Parollar mos kelmayapti', 'error'); return; }
    setSaving(true);
    try {
      await updateSystemAdmin(editTarget.id, { password: editPass.password });
      toast('Parol o\'zgartirildi', 'success');
      setEditTarget(null);
      load();
    } catch (e) { toast(e.response?.data?.detail || 'Xato', 'error'); }
    finally { setSaving(false); }
  };

  // Edit — Orgs tab: attach
  const handleAttachOrg = async () => {
    if (!attachOrgId) { toast('Tashkilot tanlang', 'error'); return; }
    try {
      await attachAdminToOrg(editTarget.id, parseInt(attachOrgId));
      toast('Biriktirildi', 'success');
      const res = await getSystemAdmins();
      const aData = Array.isArray(res.data) ? res.data : res.data?.admins ?? [];
      const updated = aData.find(a => a.id === editTarget.id);
      if (updated) {
        setEditOrgs(Array.isArray(updated.organization) ? updated.organization : (updated.organization ? [updated.organization] : []));
        setEditTarget(updated);
      }
      setAttachOrgId('');
      setAdmins(aData); setFiltered(aData);
    } catch (e) { toast(e.response?.data?.detail || 'Xato', 'error'); }
  };

  // Row actions
  const handleToggleLock = async (row) => {
    try {
      await toggleAdminLock(row.id, !row.locked);
      toast(row.locked ? 'Qulf ochildi' : 'Qulflandi', 'success');
      load();
    } catch { toast('Xato', 'error'); }
  };

  const handleResetAttempts = async (row) => {
    try {
      await resetAdminAttempts(row.id);
      toast('Urinishlar tiklandi', 'success');
      load();
    } catch { toast('Xato', 'error'); }
  };

  const handleForceLogout = async (row) => {
    try {
      await forceLogoutAdmin(row.id);
      toast(`${row.username} tizimdan chiqarildi`, 'success');
    } catch { toast('Xato', 'error'); }
  };

  const handleDelete = async () => {
    try {
      await deleteSystemAdmin(deleteTarget.id);
      toast("O'chirildi", 'success');
      setDeleteTarget(null);
      load();
    } catch { toast("O'chirishda xato", 'error'); }
  };

  const getOrgName = (row) => {
    const orgVal = row.organization;
    if (!orgVal) return null;
    if (Array.isArray(orgVal)) return orgVal.join(', ') || null;
    if (typeof orgVal === 'object') return orgVal.name;
    const found = orgs.find(o => o.id === orgVal);
    return found?.name ?? String(orgVal);
  };

  const columns = [
    { key: 'id', label: '#', render: v => <span style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{v}</span> },
    {
      key: 'username', label: 'Admin',
      render: (v, row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{ width: '34px', height: '34px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, color: 'white', flexShrink: 0, background: 'linear-gradient(135deg,#8b5cf6,#a78bfa)', boxShadow: '0 2px 8px rgba(139,92,246,0.3)' }}>
            {(v || '?')[0].toUpperCase()}
          </div>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>{v}</span>
        </div>
      ),
    },
    {
      key: 'organization', label: 'Tashkilot',
      render: (_, row) => {
        const name = getOrgName(row);
        return name
          ? <span style={{ fontSize: '0.78rem', fontWeight: 500, padding: '3px 10px', borderRadius: '6px', color: '#c4b5fd', background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)' }}>{name}</span>
          : <span style={{ color: '#334155' }}>—</span>;
      },
    },
    {
      key: 'superadmin', label: 'Super Admin',
      render: (v, row) => {
        const is = v || row.is_superuser;
        return <Badge variant={is ? 'indigo' : 'default'} dot={!!is}>{is ? 'Ha' : "Yo'q"}</Badge>;
      },
    },
    {
      key: 'locked', label: 'Holat',
      render: v => <Badge variant={v ? 'danger' : 'success'} dot>{v ? 'Qulflangan' : 'Faol'}</Badge>,
    },
    {
      key: 'failed_attempts', label: 'Failed',
      render: v => {
        const n = v ?? 0;
        const color = n > 3 ? '#f87171' : n > 0 ? '#fbbf24' : '#34d399';
        return <span style={{ fontWeight: 700, color, fontSize: '0.875rem' }}>{n > 3 ? `${n} ⚠` : n}</span>;
      },
    },
  ];

  // Orgs not yet attached to editTarget
  const unattachedOrgs = orgs.filter(o => !editOrgs.includes(o.name) && !editOrgs.includes(String(o.id)));

  return (
    <div className="page-container">
      {/* Stat cards */}
      <div style={S.statGrid}>
        <StatCard icon="👥" label="Jami adminlar" value={totalAdmins} color="#8b5cf6" bg="rgba(139,92,246,0.12)" />
        <StatCard icon="⭐" label="Super adminlar" value={superAdmins} color="#a78bfa" bg="rgba(167,139,250,0.12)" />
        <StatCard icon="🔒" label="Qulflangan" value={lockedAdmins} color="#f87171" bg="rgba(239,68,68,0.12)" />
        <StatCard icon="⚠️" label="Xavfli (>3 urinish)" value={highRisk} color="#fbbf24" bg="rgba(245,158,11,0.12)" />
      </div>

      <div style={S.pageTop}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.025em' }}>System Adminlar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta admin</p>
        </div>
        <div style={S.right}>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" placeholder="Qidirish..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={() => { setCreateForm(emptyCreate); setCreateModal(true); }} style={S.addBtn}>
            <Plus size={16} /> Qo'shish
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <button title="Tahrirlash" onClick={() => openEdit(row)} style={S.actionBtn}
                ref={el => el && hoverBtn(el, '#a78bfa', 'rgba(139,92,246,0.1)')}>
                <Pencil size={13} />
              </button>
              <button title={row.locked ? 'Qulfni ochish' : 'Qulflash'} onClick={() => handleToggleLock(row)} style={S.actionBtn}
                ref={el => el && hoverBtn(el, row.locked ? '#34d399' : '#fbbf24', row.locked ? 'rgba(52,211,153,0.1)' : 'rgba(251,191,36,0.1)')}>
                {row.locked ? <Unlock size={13} /> : <Lock size={13} />}
              </button>
              <button title="Urinishlarni tiklash" onClick={() => handleResetAttempts(row)} style={S.actionBtn}
                ref={el => el && hoverBtn(el, '#60a5fa', 'rgba(59,130,246,0.1)')}>
                <RefreshCw size={13} />
              </button>
              <button title="Force logout" onClick={() => handleForceLogout(row)} style={S.actionBtn}
                ref={el => el && hoverBtn(el, '#fb923c', 'rgba(251,146,60,0.1)')}>
                <LogOut size={13} />
              </button>
              <button title="O'chirish" onClick={() => setDeleteTarget(row)} style={S.actionBtn}
                ref={el => el && hoverBtn(el, '#f87171', 'rgba(239,68,68,0.1)')}>
                <Trash2 size={13} />
              </button>
            </div>
          )}
        />
      </div>

      {/* Create Modal */}
      <Modal isOpen={createModal} onClose={() => setCreateModal(false)} title="Yangi admin"
        footer={
          <>
            <button onClick={() => setCreateModal(false)} className="btn-secondary">Bekor</button>
            <button onClick={handleCreate} disabled={creating} style={S.saveBtn}>
              {creating ? 'Yaratilmoqda...' : "Qo'shish"}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={S.label}>Username *</label>
            <input type="text" placeholder="login" value={createForm.username}
              onChange={e => setCreateForm(p => ({ ...p, username: e.target.value }))} className="input-field" />
          </div>
          <div>
            <label style={S.label}>Parol *</label>
            <input type="password" placeholder="••••••••" value={createForm.password}
              onChange={e => setCreateForm(p => ({ ...p, password: e.target.value }))} className="input-field" />
          </div>
          <div>
            <label style={S.label}>Tashkilot *</label>
            <select value={createForm.organization_id}
              onChange={e => setCreateForm(p => ({ ...p, organization_id: e.target.value }))} className="input-field">
              <option value="">— Tanlang —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input type="checkbox" id="cSuper" checked={createForm.is_superuser}
              onChange={e => setCreateForm(p => ({ ...p, is_superuser: e.target.checked }))}
              style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }} />
            <label htmlFor="cSuper" style={{ fontSize: '0.875rem', color: '#94a3b8', cursor: 'pointer' }}>⭐ Super Admin</label>
          </div>
        </div>
      </Modal>

      {/* Edit Modal — 3 tabs */}
      <Modal isOpen={!!editTarget} onClose={() => setEditTarget(null)} title={`Tahrirlash: ${editTarget?.username}`}>
        {editTarget && (
          <>
            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)', marginBottom: '1.25rem' }}>
              {[['info', 'Info'], ['password', 'Parol'], ['orgs', 'Tashkilotlar']].map(([key, label]) => (
                <button key={key} onClick={() => setEditTab(key)} style={S.tab(editTab === key)}>{label}</button>
              ))}
            </div>

            {/* Info tab */}
            {editTab === 'info' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={S.label}>Username *</label>
                  <input type="text" value={editInfo.username}
                    onChange={e => setEditInfo(p => ({ ...p, username: e.target.value }))} className="input-field" />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input type="checkbox" id="eSuper" checked={editInfo.is_superuser}
                    onChange={e => setEditInfo(p => ({ ...p, is_superuser: e.target.checked }))}
                    style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }} />
                  <label htmlFor="eSuper" style={{ fontSize: '0.875rem', color: '#94a3b8', cursor: 'pointer' }}>⭐ Super Admin</label>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <button onClick={() => setEditTarget(null)} className="btn-secondary">Bekor</button>
                  <button onClick={handleSaveInfo} disabled={saving} style={S.saveBtn}>
                    {saving ? 'Saqlanmoqda...' : 'Saqlash'}
                  </button>
                </div>
              </div>
            )}

            {/* Password tab */}
            {editTab === 'password' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ padding: '0.75rem 1rem', borderRadius: '0.625rem', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', fontSize: '0.8rem', color: '#fbbf24' }}>
                  ⚠ Yangi parol kiritilsa admin sessiyasi bekor bo'ladi
                </div>
                <div>
                  <label style={S.label}>Yangi parol *</label>
                  <input type="password" placeholder="••••••••" value={editPass.password}
                    onChange={e => setEditPass(p => ({ ...p, password: e.target.value }))} className="input-field" />
                </div>
                <div>
                  <label style={S.label}>Parolni tasdiqlang *</label>
                  <input type="password" placeholder="••••••••" value={editPass.confirm}
                    onChange={e => setEditPass(p => ({ ...p, confirm: e.target.value }))} className="input-field" />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <button onClick={() => setEditTarget(null)} className="btn-secondary">Bekor</button>
                  <button onClick={handleSavePass} disabled={saving} style={S.saveBtn}>
                    {saving ? 'Saqlanmoqda...' : 'Parolni o\'zgartirish'}
                  </button>
                </div>
              </div>
            )}

            {/* Organizations tab */}
            {editTab === 'orgs' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.625rem' }}>Joriy tashkilotlar</p>
                  {editOrgs.length === 0 ? (
                    <p style={{ fontSize: '0.8rem', color: '#475569', textAlign: 'center', padding: '1rem' }}>Tashkilot biriktirilmagan</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {editOrgs.map((name, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.625rem 0.875rem', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '0.625rem', background: 'rgba(255,255,255,0.02)' }}>
                          <span style={{ fontSize: '0.875rem', color: '#e2e8f0', fontWeight: 500 }}>🏢 {name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem' }}>
                  <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.625rem' }}>Tashkilot qo'shish</p>
                  <div style={{ display: 'flex', gap: '0.625rem' }}>
                    <select value={attachOrgId} onChange={e => setAttachOrgId(e.target.value)} className="input-field" style={{ flex: 1 }}>
                      <option value="">— Tanlang —</option>
                      {unattachedOrgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                    </select>
                    <button onClick={handleAttachOrg} style={{ ...S.saveBtn, padding: '0.625rem 1rem', gap: '0.375rem', fontSize: '0.8rem' }}>
                      <Link size={13} /> Biriktirish
                    </button>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <button onClick={() => setEditTarget(null)} className="btn-secondary">Yopish</button>
                </div>
              </div>
            )}
          </>
        )}
      </Modal>

      {/* Delete modal */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="O'chirishni tasdiqlash"
        footer={
          <>
            <button onClick={() => setDeleteTarget(null)} className="btn-secondary">Bekor</button>
            <button onClick={handleDelete} className="btn-danger">O'chirish</button>
          </>
        }
      >
        <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>"{deleteTarget?.username}"</span> adminni o'chirasizmi?
        </p>
      </Modal>
    </div>
  );
}
