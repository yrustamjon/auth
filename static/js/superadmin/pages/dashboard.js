// ============================================================
// dashboard.js — System Dashboard Page  (requires api.js)
// ============================================================

// ===== API CALLS =====

async function apiFetchOrgs() {
    const res = await fetchWithAuth('/api/organizations/');
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiFetchAdmins() {
    const res = await fetchWithAuth('/api/system/admins/');
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

// async function apiFetchRecentLogins() {
//     const res = await fetchWithAuth('/api/system/dashboard/recent-logins/');
//     if (!res.ok) throw new Error(res.status);
//     return res.json();
// }

// async function apiFetchRecentOrgs() {
//     const res = await fetchWithAuth('/api/system/dashboard/recent-organizations/');
//     if (!res.ok) throw new Error(res.status);
//     return res.json();
// }

// ===== DESIGN TOKENS (barcha page lar bilan bir xil) =====
const DC = {
    primary:  '#4e73df',
    primary2: '#224abe',
    indigo:   '#6366f1',
    violet:   '#8b5cf6',
    success:  '#10b981',
    danger:   '#ef4444',
    warning:  '#f59e0b',
    text:     '#1e1e2e',
    muted:    '#6b7280',
    border:   '#e5e7eb',
    bg:       '#f9fafb',
    white:    '#ffffff',
};
const DGRAD  = `linear-gradient(135deg, ${DC.primary}, ${DC.primary2})`;
const DGVIVID= `linear-gradient(135deg, ${DC.indigo}, ${DC.violet})`;

// ===== HELPERS =====
function dFormatDate(val) {
    if (!val) return '—';
    const d = new Date(val);
    if (isNaN(d)) return val;
    return d.toLocaleDateString('en-RU', { day:'2-digit', month:'2-digit', year:'numeric' });
}

function dFormatTime(val) {
    if (!val) return '—';
    const d = new Date(val);
    if (isNaN(d)) return val;
        return d.toLocaleString('en-RU', {
                        day:'2-digit', month:'2-digit', year:'numeric',
                    hour:'2-digit', minute:'2-digit'
    });
}

function dBadge(text, type) {
    const map = {
        success:  { bg:'#d1fae5', color:'#065f46', dot:'#10b981' },
        failed:   { bg:'#fee2e2', color:'#991b1b', dot:'#ef4444' },
        locked:   { bg:'#fef3c7', color:'#92400e', dot:'#f59e0b' },
        active:   { bg:'#d1fae5', color:'#065f46', dot:'#10b981' },
        inactive: { bg:'#fee2e2', color:'#991b1b', dot:'#ef4444' },
        normal:   { bg:'#f3f4f6', color:'#4b5563', dot:'#9ca3af' },
    };
    const s = map[type] || map.normal;
    return `<span style="display:inline-flex;align-items:center;gap:5px;
        padding:3px 10px 3px 7px;background:${s.bg};color:${s.color};
        border-radius:20px;font-size:11.5px;font-weight:600;white-space:nowrap;">
        <span style="width:6px;height:6px;border-radius:50%;background:${s.dot};flex-shrink:0;"></span>
        ${text}</span>`;
}

function dAvatar(letter, size = 32, radius = 8, grad = DGVIVID) {
    return `<div style="width:${size}px;height:${size}px;border-radius:${radius}px;flex-shrink:0;
        background:${grad};display:flex;align-items:center;justify-content:center;
        color:#fff;font-weight:800;font-size:${Math.round(size*0.38)}px;
        box-shadow:0 2px 6px rgba(99,102,241,.25);">${letter}</div>`;
}

const DTH = `style="padding:11px 16px;text-align:left;font-size:10.5px;font-weight:700;
    text-transform:uppercase;letter-spacing:.07em;color:${DC.primary};
    border-bottom:2px solid ${DC.border};background:${DC.bg};white-space:nowrap;"`;

const DTD = `style="padding:12px 16px;border-bottom:1px solid #f3f4f6;
    color:${DC.text};vertical-align:middle;font-size:13.5px;"`;

// ===== RENDER =====
async function renderDashboard() {
    const container = document.getElementById('page-content');
    if (!container) return;

    showLoading();
    let admins = [], orgs=[],recentLogins = [], recentOrgs = [];
    try {
        [admins,orgs,] = await Promise.all([
            apiFetchAdmins(),
            apiFetchOrgs(),
            // apiFetchRecentLogins(),
            // apiFetchRecentOrgs()
        ]);
    } catch (err) {
        showToast('Failed to load dashboard: ' + err.message, 'danger');
    } finally {
        hideLoading();
    }
    console.log('Admins:', admins);

    // ===== STAT CARDS =====
    const statDefs = [
        { icon:'fas fa-building',             color:DC.indigo,   label:'Organizations',  val: orgs.length ?? 0 },
        { icon:'fas fa-user-shield',          color:DC.violet,   label:'Total Admins',   val: admins.length ?? 0 },
        { icon:'fas fa-user-check',           color:DC.success,  label:'Active Admins',  val: admins.filter(a => a.is_active === true).length ?? 0 },
        { icon:'fas fa-user-lock',            color:DC.danger,   label:'Locked Admins',  val: admins.filter(a => a.locked === true).length ?? 0 },
    ];

    const statCards = statDefs.map((s, i) => `
        <div style="flex:1;min-width:160px;background:${DC.white};border-radius:16px;
            padding:22px 20px;border:1.5px solid ${DC.border};
            border-top:3px solid ${s.color};
            box-shadow:0 2px 8px rgba(0,0,0,.04);
            display:flex;flex-direction:column;align-items:center;text-align:center;
            transition:transform .2s,box-shadow .2s;cursor:default;
            animation:dCardIn .4s ease both;animation-delay:${i*0.08}s;"
            onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 12px 32px rgba(0,0,0,.1)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 2px 8px rgba(0,0,0,.04)'">
            <div style="width:50px;height:50px;border-radius:14px;
                background:${s.color}15;
                display:flex;align-items:center;justify-content:center;
                font-size:20px;color:${s.color};margin-bottom:14px;
                box-shadow:0 2px 8px ${s.color}25;">
                <i class="${s.icon}"></i>
            </div>
            <div style="font-size:32px;font-weight:900;color:${s.color};line-height:1;margin-bottom:6px;">
                ${s.val}
            </div>
            <div style="font-size:11px;font-weight:700;color:${DC.muted};
                text-transform:uppercase;letter-spacing:.06em;">${s.label}</div>
        </div>`).join('');

    // ===== RECENT LOGINS =====
    const loginRows = recentLogins.length
        ? recentLogins.map((l, i) => {
            const statusType = l.status === 'success' ? 'success'
                             : l.status === 'locked'  ? 'locked'
                             : 'failed';
            const username = l.username || '—';
            const org = l.organization_name ?? l.organization ?? '—';
            const time = dFormatTime(l.login_time ?? l.loginTime);
            return `
            <tr style="transition:background .12s;animation:dRowIn .3s ease both;animation-delay:${i*0.04}s;"
                onmouseover="this.style.background='${DC.bg}'"
                onmouseout="this.style.background=''">
                <td ${DTD}>
                    <div style="display:flex;align-items:center;gap:9px;">
                        ${dAvatar(username[0].toUpperCase())}
                        <strong style="font-size:13px;">${username}</strong>
                    </div>
                </td>
                <td ${DTD}>
                    <span style="font-size:12.5px;color:${DC.muted};display:flex;align-items:center;gap:5px;">
                        <i class="fas fa-building" style="opacity:.4;font-size:11px;"></i>${org}
                    </span>
                </td>
                <td ${DTD} style="color:${DC.muted};font-size:12.5px;white-space:nowrap;">
                    <i class="fas fa-clock" style="margin-right:5px;opacity:.4;"></i>${time}
                </td>
                <td ${DTD}>${dBadge(l.status, statusType)}</td>
            </tr>`;
        }).join('')
        : `<tr><td colspan="4" style="text-align:center;padding:2.5rem;color:${DC.muted};font-size:13px;">
                <i class="fas fa-clock" style="font-size:2rem;opacity:.15;display:block;margin-bottom:8px;"></i>
                No recent logins</td></tr>`;

    // ===== RECENT ORGS =====
    const orgRows = recentOrgs.length
        ? recentOrgs.map((o, i) => `
            <tr style="transition:background .12s;animation:dRowIn .3s ease both;animation-delay:${i*0.04}s;"
                onmouseover="this.style.background='${DC.bg}'"
                onmouseout="this.style.background=''">
                <td ${DTD}>
                    <div style="display:flex;align-items:center;gap:9px;">
                        ${dAvatar(o.name[0].toUpperCase(), 32, 8, DGRAD)}
                        <div>
                            <strong style="font-size:13px;display:block;">${o.name}</strong>
                            <code style="font-size:11px;color:${DC.muted};background:#f1f5f9;
                                padding:1px 6px;border-radius:4px;">${o.slug ?? ''}</code>
                        </div>
                    </div>
                </td>
                <td ${DTD}>
                    <span style="font-size:12.5px;color:${DC.muted};">
                        ${o.created_by ?? o.createdBy ?? '—'}
                    </span>
                </td>
                <td ${DTD} style="color:${DC.muted};font-size:12.5px;white-space:nowrap;">
                    <i class="fas fa-calendar-alt" style="margin-right:5px;opacity:.4;"></i>
                    ${dFormatDate(o.created_at ?? o.date)}
                </td>
                <td ${DTD}>${dBadge(o.active ? 'Active' : 'Inactive', o.active ? 'active' : 'inactive')}</td>
            </tr>`).join('')
        : `<tr><td colspan="4" style="text-align:center;padding:2.5rem;color:${DC.muted};font-size:13px;">
                <i class="fas fa-building" style="font-size:2rem;opacity:.15;display:block;margin-bottom:8px;"></i>
                No recent organizations</td></tr>`;

    // ===== TABLE CARD BUILDER =====
    function tableCard(title, icon, color, rows, heads, extraBadge = '') {
        const thCells = heads.map(h => `<th ${DTH}>${h}</th>`).join('');
        return `
            <div style="background:${DC.white};border-radius:16px;
                border:1.5px solid ${DC.border};
                box-shadow:0 4px 20px rgba(0,0,0,.05);overflow:hidden;
                display:flex;flex-direction:column;">

                <!-- Card header -->
                <div style="padding:14px 20px;border-bottom:1.5px solid ${DC.border};
                    background:${DC.bg};display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-size:13px;font-weight:700;color:${DC.text};
                        display:flex;align-items:center;gap:9px;">
                        <span style="width:32px;height:32px;border-radius:9px;
                            background:${color}15;
                            display:flex;align-items:center;justify-content:center;
                            font-size:13px;color:${color};">
                            <i class="${icon}"></i>
                        </span>
                        ${title}
                    </span>
                    ${extraBadge}
                </div>

                <!-- Table -->
                <div style="overflow-x:auto;flex:1;">
                    <table style="width:100%;border-collapse:collapse;">
                        <thead><tr>${thCells}</tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>`;
    }

    // ===== QUICK ACTIONS =====
    const quickActions = [
        { icon:'fas fa-user-plus',   label:'Create Admin',        color:DC.primary, onclick:"window.location.href='/system/admins/'" },
        { icon:'fas fa-building',    label:'New Organization',    color:DC.violet,  onclick:"window.location.href='/system/organizations/'" },
        { icon:'fas fa-rotate-left', label:'Reset Attempts',      color:DC.warning, onclick:"window.location.href='/system/admins/'" },
        { icon:'fas fa-shield-halved',label:'Security Overview',  color:DC.success, onclick:"window.location.href='/system/admins/'" },
    ].map(a => `
        <button onclick="${a.onclick}"
            style="display:flex;flex-direction:column;align-items:center;gap:9px;
                padding:18px 12px;background:${DC.white};border:1.5px solid ${DC.border};
                border-radius:13px;cursor:pointer;flex:1;min-width:110px;
                box-shadow:0 2px 6px rgba(0,0,0,.04);
                transition:transform .18s,box-shadow .18s,border-color .18s;"
            onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 10px 24px rgba(0,0,0,.1)';this.style.borderColor='${a.color}'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 2px 6px rgba(0,0,0,.04)';this.style.borderColor='${DC.border}'">
            <div style="width:42px;height:42px;border-radius:12px;background:${a.color}15;
                display:flex;align-items:center;justify-content:center;
                font-size:17px;color:${a.color};">
                <i class="${a.icon}"></i>
            </div>
            <span style="font-size:11.5px;font-weight:700;color:${DC.text};text-align:center;line-height:1.3;">
                ${a.label}
            </span>
        </button>`).join('');

    // ===== ASSEMBLE PAGE =====
    container.innerHTML = `
        <style>
            @keyframes dPageIn  { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
            @keyframes dCardIn  { from{opacity:0;transform:translateY(8px)}  to{opacity:1;transform:translateY(0)} }
            @keyframes dRowIn   { from{opacity:0;transform:translateY(5px)}  to{opacity:1;transform:translateY(0)} }
        </style>

        <div style="padding:2rem;animation:dPageIn .4s ease both;">

            <!-- Header -->
            <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:1.75rem;flex-wrap:wrap;gap:1rem;">
                <div>
                    <h2 style="margin:0 0 3px;font-size:20px;font-weight:800;color:${DC.text};
                        display:flex;align-items:center;gap:10px;">
                        <span style="width:38px;height:38px;border-radius:10px;background:${DGRAD};
                            display:inline-flex;align-items:center;justify-content:center;
                            box-shadow:0 4px 14px rgba(78,115,223,.35);">
                            <i class="fas fa-gauge-high" style="color:#fff;font-size:15px;"></i>
                        </span>
                        Dashboard
                    </h2>
                    <p style="margin:0;font-size:12.5px;color:${DC.muted};">
                        System overview and recent activity
                    </p>
                </div>

                <!-- Live clock -->
                <div style="display:flex;align-items:center;gap:8px;
                    padding:8px 16px;background:${DC.white};border:1.5px solid ${DC.border};
                    border-radius:10px;font-size:12.5px;color:${DC.muted};
                    box-shadow:0 2px 6px rgba(0,0,0,.04);">
                    <i class="fas fa-clock" style="color:${DC.primary};"></i>
                    <span id="dashClock">—</span>
                </div>
            </div>

            <!-- Stat cards -->
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:1.75rem;">
                ${statCards}
            </div>

            <!-- Quick actions -->
            <div style="background:${DC.white};border-radius:16px;border:1.5px solid ${DC.border};
                box-shadow:0 4px 20px rgba(0,0,0,.05);overflow:hidden;margin-bottom:1.75rem;">
                <div style="padding:14px 20px;border-bottom:1.5px solid ${DC.border};background:${DC.bg};">
                    <span style="font-size:13px;font-weight:700;color:${DC.text};
                        display:flex;align-items:center;gap:8px;">
                        <i class="fas fa-bolt" style="color:${DC.warning};"></i>
                        Quick Actions
                    </span>
                </div>
                <div style="padding:16px 20px;display:flex;gap:12px;flex-wrap:wrap;">
                    ${quickActions}
                </div>
            </div>

            <!-- Tables grid -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

                ${tableCard(
                    'Recent Logins',
                    'fas fa-clock-rotate-left',
                    DC.indigo,
                    loginRows,
                    ['User', 'Organization', 'Time', 'Status']
                )}

                ${tableCard(
                    'New Organizations',
                    'fas fa-building-circle-check',
                    DC.violet,
                    orgRows,
                    ['Organization', 'Created By', 'Date', 'Status']
                )}

            </div>
        </div>`;

    // Live clock
    function tickClock() {
        const el = document.getElementById('dashClock');
        if (!el) return;
        const now = new Date();
        el.textContent = now.toLocaleString('ru-RU', {
            weekday:'short', day:'2-digit', month:'2-digit',
            hour:'2-digit', minute:'2-digit', second:'2-digit'
        });
    }
    tickClock();
    setInterval(tickClock, 1000);
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    renderDashboard();
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', e => { e.preventDefault(); logout(); });
});