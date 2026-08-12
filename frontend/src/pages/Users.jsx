import { useEffect, useState, useRef } from 'react';
import { Plus, Pencil, Trash2, Search, Fingerprint, Camera, RefreshCw, Copy, Check, X } from 'lucide-react';
import Table from '../components/Table';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import {
  getUsers, createUser, updateUser, deleteUser, getRoles,
  getBiometricStatus, uploadFace, deleteFace,
  getFingerprints, deleteFingerprint,
  startFingerprintSession, getFingerprintSessionStatus,
} from '../api/admin';
import { useAdminToast } from '../layouts/AdminLayout';

const emptyForm = { fio: '', lavozim: '', username: '', role_id: '', status: true };

const S = {
  pageTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' },
  right: { display: 'flex', alignItems: 'center', gap: '0.75rem' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' },
  searchInput: { background: 'transparent', border: 'none', outline: 'none', color: '#cbd5e1', fontSize: '0.875rem', width: '176px' },
  tableWrap: { borderRadius: '1rem', overflow: 'hidden', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' },
  actionBtn: { padding: '6px', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center' },
  label: { display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
};

const FP_SOURCES = [
  { key: 'manual',   label: 'Manual',   color: '#818cf8', bg: 'rgba(99,102,241,0.12)'  },
  { key: 'phone',    label: 'Phone',    color: '#60a5fa', bg: 'rgba(59,130,246,0.12)'  },
  { key: 'scanner',  label: 'Scanner',  color: '#34d399', bg: 'rgba(16,185,129,0.12)'  },
  { key: 'external', label: 'External', color: '#fbbf24', bg: 'rgba(245,158,11,0.12)'  },
];

// ─── Biometric Modal ──────────────────────────────────────────────────────────
function BiometricModal({ user, onClose, onRefresh, toast }) {
  const [tab, setTab]           = useState('face');
  const [hasFace, setHasFace]   = useState(false);
  const [faceMode, setFaceMode] = useState('view');
  const [faceFile, setFaceFile] = useState(null);
  const [facePreview, setFacePreview] = useState('');
  const [savingFace, setSavingFace]   = useState(false);
  const [fingerprints, setFingerprints] = useState([]);
  const [activeSource, setActiveSource] = useState(null); // 'manual'|'phone'|'scanner'|'external'
  const [fpSession, setFpSession]     = useState(null);
  const [fpPollStatus, setFpPollStatus] = useState('');
  const [copied, setCopied] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => { loadBio(); return () => stopPoll(); }, []);

  const stopPoll = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const loadBio = async () => {
    try {
      const [sRes, fRes] = await Promise.all([getBiometricStatus(user.id), getFingerprints(user.id)]);
      setHasFace(sRes.data.has_face);
      setFingerprints(Array.isArray(fRes.data) ? fRes.data : []);
    } catch {}
  };

  const reloadFingerprints = async () => {
    try { const r = await getFingerprints(user.id); setFingerprints(Array.isArray(r.data) ? r.data : []); } catch {}
  };

  // ── Face ──
  const handleFileChange = (e) => {
    const file = e.target.files[0]; if (!file) return;
    setFaceFile(file); setFacePreview(URL.createObjectURL(file));
  };
  const handleSaveFace = async () => {
    if (!faceFile) return; setSavingFace(true);
    try {
      await uploadFace(user.id, faceFile);
      toast('Yuz saqlandi!', 'success'); setHasFace(true); setFaceMode('view'); setFaceFile(null); setFacePreview(''); onRefresh();
    } catch (e) { toast(e.response?.data?.error || 'Yuz saqlanmadi', 'error'); }
    finally { setSavingFace(false); }
  };
  const handleDeleteFace = async () => {
    if (!window.confirm("Yuz embeddingini o'chirishni tasdiqlaysizmi?")) return;
    try { await deleteFace(user.id); setHasFace(false); toast("O'chirildi", 'success'); onRefresh(); }
    catch { toast("O'chirishda xato", 'error'); }
  };

  // ── Fingerprint ──
  const handleDeleteFp = async (fpId) => {
    try { await deleteFingerprint(user.id, fpId); await reloadFingerprints(); toast("O'chirildi", 'success'); onRefresh(); }
    catch { toast("O'chirishda xato", 'error'); }
  };
  const handleStartSession = async () => {
    try {
      const res = await startFingerprintSession(user.id);
      const { session_id } = res.data;
      setFpSession({ session_id, url: `http://127.0.0.1:8000/mobile/fingerprint/${session_id}/` });
      setFpPollStatus('pending');
      stopPoll();
      pollRef.current = setInterval(async () => {
        try {
          const sr = await getFingerprintSessionStatus(session_id);
          const st = sr.data.status; setFpPollStatus(st);
          if (st === 'completed') {
            stopPoll(); toast('Barmoq izi muvaffaqiyatli olindi!', 'success');
            await reloadFingerprints(); setFpSession(null); onRefresh();
          } else if (st === 'expired') { stopPoll(); }
        } catch {}
      }, 3000);
    } catch { toast('Sessiya yaratishda xato', 'error'); }
  };
  const copyUrl = () => {
    if (!fpSession) return;
    navigator.clipboard.writeText(fpSession.url); setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  const tabBtn = (t, icon, label) => (
    <button onClick={() => setTab(t)} style={{ padding: '0.6rem 1.25rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', borderBottom: `2px solid ${tab === t ? '#6366f1' : 'transparent'}`, color: tab === t ? '#818cf8' : '#64748b', background: 'transparent', border: 'none', borderBottom: `2px solid ${tab === t ? '#6366f1' : 'transparent'}`, display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
      {icon}{label}
    </button>
  );

  const srcRecords = (key) => fingerprints.filter(f => f.source === key);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <div style={{ background: '#141420', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '1rem', width: '100%', maxWidth: '520px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 24px 60px rgba(0,0,0,0.5)' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.06)', flexShrink: 0 }}>
          <div>
            <p style={{ fontSize: '0.7rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>Biometrik</p>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', margin: '2px 0 0' }}>{user.fio}</h3>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: '8px', width: '32px', height: '32px', cursor: 'pointer', color: '#94a3b8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <X size={16} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '0 1.5rem', flexShrink: 0 }}>
          {tabBtn('face',   <Camera size={14} />,      'Yuz')}
          {tabBtn('finger', <Fingerprint size={14} />, 'Barmoq izi')}
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', padding: '1.25rem 1.5rem', flex: 1 }}>

          {/* ── FACE ── */}
          {tab === 'face' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.75rem 1rem', borderRadius: '0.75rem', background: hasFace ? 'rgba(16,185,129,0.08)' : 'rgba(234,179,8,0.08)', border: `1px solid ${hasFace ? 'rgba(16,185,129,0.2)' : 'rgba(234,179,8,0.2)'}` }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: hasFace ? '#10b981' : '#eab308' }} />
                <span style={{ fontSize: '0.875rem', fontWeight: 500, color: hasFace ? '#34d399' : '#fbbf24' }}>
                  {hasFace ? 'Yuz embeddigi mavjud' : "Yuz embeddigi yo'q"}
                </span>
              </div>

              {hasFace && faceMode === 'view' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <button onClick={() => { setFaceMode('upload'); setFaceFile(null); setFacePreview(''); }}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '0.75rem', border: 'none', background: 'rgba(99,102,241,0.15)', color: '#818cf8', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    <RefreshCw size={15} /> Yuzni Yangilash
                  </button>
                  <button onClick={handleDeleteFace}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '0.75rem', border: 'none', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    <Trash2 size={15} /> Yuz embeddingini o'chirish
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <label style={{ display: 'block', cursor: 'pointer' }}>
                    <div style={{ border: `2px dashed ${faceFile ? '#10b981' : 'rgba(255,255,255,0.12)'}`, borderRadius: '0.75rem', padding: '1.5rem', textAlign: 'center', background: faceFile ? 'rgba(16,185,129,0.05)' : 'rgba(255,255,255,0.02)' }}>
                      {facePreview
                        ? <img src={facePreview} alt="preview" style={{ maxHeight: '140px', maxWidth: '100%', borderRadius: '0.5rem', objectFit: 'cover', margin: '0 auto', display: 'block' }} />
                        : <><Camera size={28} style={{ color: '#475569', marginBottom: '0.5rem', display: 'block', margin: '0 auto 0.5rem' }} />
                          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Rasm tanlash uchun bosing</p>
                          <p style={{ fontSize: '0.75rem', color: '#475569', margin: '0.25rem 0 0' }}>JPG / PNG • Yuz aniq ko'rinsin</p></>}
                    </div>
                    <input type="file" accept="image/*" onChange={handleFileChange} style={{ display: 'none' }} />
                  </label>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {faceMode === 'upload' && (
                      <button onClick={() => { setFaceMode('view'); setFaceFile(null); setFacePreview(''); }}
                        style={{ flex: 1, padding: '0.625rem', borderRadius: '0.75rem', border: '1px solid rgba(255,255,255,0.08)', background: 'transparent', color: '#64748b', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer' }}>
                        Bekor
                      </button>
                    )}
                    <button onClick={handleSaveFace} disabled={!faceFile || savingFace}
                      style={{ flex: 1, padding: '0.625rem', borderRadius: '0.75rem', border: 'none', background: faceFile ? 'linear-gradient(135deg,#6366f1,#8b5cf6)' : 'rgba(255,255,255,0.06)', color: faceFile ? '#fff' : '#475569', fontWeight: 600, fontSize: '0.875rem', cursor: faceFile ? 'pointer' : 'not-allowed', opacity: savingFace ? 0.7 : 1 }}>
                      {savingFace ? 'Saqlanmoqda...' : 'Yuzni Saqlash'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── FINGER ── */}
          {tab === 'finger' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {/* Overall status */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.75rem 1rem', borderRadius: '0.75rem', background: fingerprints.length ? 'rgba(16,185,129,0.08)' : 'rgba(234,179,8,0.08)', border: `1px solid ${fingerprints.length ? 'rgba(16,185,129,0.2)' : 'rgba(234,179,8,0.2)'}` }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: fingerprints.length ? '#10b981' : '#eab308' }} />
                <span style={{ fontSize: '0.875rem', fontWeight: 500, color: fingerprints.length ? '#34d399' : '#fbbf24' }}>
                  {fingerprints.length ? `Jami ${fingerprints.length} ta barmoq izi mavjud` : "Barmoq izi yo'q — manba tanlang"}
                </span>
              </div>

              {/* Source cards grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.625rem' }}>
                {FP_SOURCES.map(src => {
                  const recs = srcRecords(src.key);
                  const isActive = activeSource === src.key;
                  return (
                    <div key={src.key}
                      onClick={() => setActiveSource(isActive ? null : src.key)}
                      style={{ border: `1.5px solid ${isActive ? src.color : 'rgba(255,255,255,0.08)'}`, borderRadius: '0.75rem', padding: '0.875rem', background: isActive ? src.bg : 'rgba(255,255,255,0.02)', cursor: 'pointer', transition: 'all 0.2s', boxShadow: isActive ? `0 0 0 3px ${src.bg}` : 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: src.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          <Fingerprint size={14} style={{ color: src.color }} />
                        </div>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#e2e8f0', flex: 1 }}>{src.label}</span>
                        <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '999px', background: recs.length ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)', color: recs.length ? '#34d399' : '#64748b' }}>
                          {recs.length ? `✓ ${recs.length} ta` : '— Mavjud emas'}
                        </span>
                      </div>
                      <button
                        onClick={e => { e.stopPropagation(); setActiveSource(isActive ? null : src.key); }}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.3rem 0.7rem', borderRadius: '6px', border: 'none', background: isActive ? src.color : 'rgba(255,255,255,0.08)', color: isActive ? '#fff' : '#94a3b8', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}>
                        Ochish
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Source manager panel */}
              {activeSource && (() => {
                const src = FP_SOURCES.find(s => s.key === activeSource);
                const recs = srcRecords(activeSource);
                return (
                  <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '0.75rem', overflow: 'hidden' }}>
                    {/* Panel header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                      <Fingerprint size={14} style={{ color: src.color }} />
                      <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#e2e8f0', flex: 1 }}>{src.label} — Barmoq izlari</span>
                      <button onClick={() => { setActiveSource(null); setFpSession(null); setFpPollStatus(''); stopPoll(); }}
                        style={{ background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: '6px', width: '24px', height: '24px', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <X size={12} />
                      </button>
                    </div>

                    <div style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                      {/* Fingerprint list for this source */}
                      {recs.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.625rem', border: '1.5px dashed rgba(255,255,255,0.08)' }}>
                          <Fingerprint size={20} style={{ color: '#334155', marginBottom: '0.375rem', display: 'block', margin: '0 auto 0.375rem' }} />
                          <p style={{ fontSize: '0.8rem', color: '#475569', margin: 0 }}>Bu manba uchun hali template qo'shilmagan</p>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {recs.map(fp => (
                            <div key={fp.id} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.5rem 0.75rem', borderRadius: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                              <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: src.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <Fingerprint size={13} style={{ color: src.color }} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <p style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', margin: 0 }}>Template #{fp.id}</p>
                                <p style={{ fontSize: '0.7rem', color: '#475569', margin: '1px 0 0' }}>{fp.created_at ? new Date(fp.created_at).toLocaleDateString('uz-UZ') : '—'}</p>
                              </div>
                              <button onClick={() => handleDeleteFp(fp.id)}
                                style={{ padding: '4px', borderRadius: '5px', border: 'none', background: 'rgba(239,68,68,0.1)', color: '#f87171', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                                <Trash2 size={12} />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Action area per source */}
                      {activeSource === 'phone' && !fpSession && (
                        <button onClick={handleStartSession}
                          style={{ width: '100%', padding: '0.5rem', borderRadius: '0.625rem', border: 'none', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                          <Plus size={14} /> Template qo'shish (Phone)
                        </button>
                      )}

                      {activeSource === 'phone' && fpSession && (
                        <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '0.625rem', overflow: 'hidden' }}>
                          <div style={{ padding: '0.625rem 0.75rem', background: 'rgba(255,255,255,0.02)' }}>
                            <p style={{ fontSize: '0.72rem', fontWeight: 600, color: '#64748b', margin: '0 0 0.25rem' }}>Telefonda oching:</p>
                            <p style={{ fontSize: '0.7rem', color: '#475569', margin: 0, wordBreak: 'break-all', fontFamily: 'monospace' }}>{fpSession.url}</p>
                          </div>
                          <div style={{ padding: '0.5rem 0.75rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: 1 }}>
                              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: fpPollStatus === 'completed' ? '#10b981' : fpPollStatus === 'expired' ? '#f87171' : '#f59e0b' }} />
                              <span style={{ fontSize: '0.75rem', color: fpPollStatus === 'completed' ? '#34d399' : fpPollStatus === 'expired' ? '#f87171' : '#fbbf24', fontWeight: 500 }}>
                                {fpPollStatus === 'completed' ? 'Qabul qilindi!' : fpPollStatus === 'expired' ? 'Muddati tugadi' : 'Kutilmoqda...'}
                              </span>
                            </div>
                            <button onClick={copyUrl} style={{ padding: '0.3rem 0.5rem', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.06)', color: copied ? '#34d399' : '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem' }}>
                              {copied ? <Check size={11} /> : <Copy size={11} />}{copied ? 'Nusxalandi' : 'Nusxa'}
                            </button>
                            <button onClick={() => { stopPoll(); setFpSession(null); setFpPollStatus(''); }}
                              style={{ padding: '0.3rem', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.06)', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                              <X size={11} />
                            </button>
                          </div>
                          {fpPollStatus === 'expired' && (
                            <div style={{ padding: '0 0.75rem 0.625rem' }}>
                              <button onClick={() => { setFpSession(null); setFpPollStatus(''); handleStartSession(); }}
                                style={{ width: '100%', padding: '0.4rem', borderRadius: '0.5rem', border: 'none', background: 'rgba(99,102,241,0.15)', color: '#818cf8', fontWeight: 600, fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}>
                                <RefreshCw size={12} /> Yangi sessiya
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {activeSource === 'scanner' && (
                        <div style={{ textAlign: 'center', padding: '0.75rem', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '0.625rem' }}>
                          <p style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 500, margin: 0 }}>USB Scanner ulanishi kutilmoqda...</p>
                          <p style={{ fontSize: '0.72rem', color: '#475569', margin: '0.25rem 0 0' }}>Scanner funksiyasi tez orada qo'shiladi</p>
                        </div>
                      )}

                      {activeSource === 'external' && (
                        <div style={{ textAlign: 'center', padding: '0.75rem', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '0.625rem' }}>
                          <p style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 500, margin: 0 }}>External Integration</p>
                          <p style={{ fontSize: '0.72rem', color: '#475569', margin: '0.25rem 0 0' }}>Bu manba kelajakda avtomatik ulanadi</p>
                        </div>
                      )}

                      {activeSource === 'manual' && (
                        <div style={{ textAlign: 'center', padding: '0.75rem', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: '0.625rem' }}>
                          <p style={{ fontSize: '0.8rem', color: '#818cf8', fontWeight: 500, margin: 0 }}>Manual kiritish</p>
                          <p style={{ fontSize: '0.72rem', color: '#475569', margin: '0.25rem 0 0' }}>Skanerlash qurilmasidan to'g'ridan-to'g'ri olinadi</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
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
    setLoading(true);
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
          <div style={{ width: '32px', height: '32px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'white', flexShrink: 0, background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
            {(v || row.username || '?')[0].toUpperCase()}
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0', margin: 0 }}>{v}</p>
            <p style={{ fontSize: '0.72rem', color: '#475569', margin: '1px 0 0' }}>{row.username}</p>
          </div>
        </div>
      ),
    },
    { key: 'lavozim', label: 'Lavozim', render: v => <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{v || '—'}</span> },
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
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.025em' }}>Foydalanuvchilar</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '2px' }}>{filtered.length} ta foydalanuvchi</p>
        </div>
        <div style={S.right}>
          <div style={S.searchBox}>
            <Search size={14} style={{ color: '#475569' }} />
            <input type="text" placeholder="Qidirish..." value={search}
              onChange={e => setSearch(e.target.value)} style={S.searchInput} />
          </div>
          <button onClick={openCreate} className="btn-primary">
            <Plus size={16} /> Qo'shish
          </button>
        </div>
      </div>

      <div style={S.tableWrap}>
        <Table columns={columns} data={filtered} loading={loading} error={error}
          actions={(row) => (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button onClick={() => setBioTarget(row)} style={S.actionBtn} title="Biometrik"
                onMouseEnter={e => { e.currentTarget.style.color = '#a78bfa'; e.currentTarget.style.background = 'rgba(139,92,246,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Fingerprint size={14} />
              </button>
              <button onClick={() => openEdit(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#818cf8'; e.currentTarget.style.background = 'rgba(99,102,241,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; }}>
                <Pencil size={14} />
              </button>
              <button onClick={() => setDeleteTarget(row)} style={S.actionBtn}
                onMouseEnter={e => { e.currentTarget.style.color = '#f87171'; e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; }}
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
            { label: 'Username *', key: 'username', type: 'text', ph: 'login_nomi' },
          ].map(({ label, key, type, ph }) => (
            <div key={key}>
              <label style={S.label}>{label}</label>
              <input type={type} placeholder={ph} value={form[key]}
                onChange={e => f(key)(e.target.value)} className="input-field" />
            </div>
          ))}
          <div>
            <label style={S.label}>Rol</label>
            <select value={form.role_id} onChange={e => f('role_id')(e.target.value)} className="input-field">
              <option value="">— Tanlang —</option>
              {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input type="checkbox" id="status_u" checked={form.status}
              onChange={e => f('status')(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: '#6366f1' }} />
            <label htmlFor="status_u" style={{ fontSize: '0.875rem', color: '#94a3b8', cursor: 'pointer' }}>Faol holat</label>
          </div>
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
        <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>"{deleteTarget?.fio}"</span> ni o'chirishni tasdiqlaysizmi?
        </p>
      </Modal>
    </div>
  );
}
