// ============================================================
// admins.js — Admin Users Page  (requires api.js + base styles)
// ============================================================

// ===== API CALLS =====

async function apiFetchAdmins() {
    const res = await fetchWithAuth('/api/system/admins/');
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiFetchOrganizations() {
    const res = await fetchWithAuth('/api/organizations/');
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiCreateAdmin(data) {
    const res = await fetchWithAuth('/api/system/admins/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || res.status);
    }
    return res.json();
}

async function apiToggleLock(id, locked) {
    const res = await fetchWithAuth(`/api/system/admins/${id}/`, {
        method: 'PATCH',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify({ locked })
    });
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiResetAttempts(id) {
    const res = await fetchWithAuth(`/api/system/admins/${id}/reset-attempts/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok) throw new Error(res.status);
}

async function apiPatchAdmin(id, data) {
    const res = await fetchWithAuth(`/api/system/admins/${id}/`, {
        method: 'PATCH',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || res.status);
    }
    return res.json();
}

async function apiAttachAdminToOrg(adminId, orgId) {
    const res = await fetchWithAuth(`/api/system/admins/${adminId}/?organization_id=${orgId}`, {
        method: 'PATCH',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify({ organization_id: orgId })
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || res.status);
    }
    return res.json();
}

async function apiForceLogout(id) {
    const res = await fetchWithAuth(`/api/system/admins/${id}/force-logout/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok) throw new Error(res.status);
}

async function apiDeleteAdmin(id) {
    const res = await fetchWithAuth(`/api/system/admins/${id}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok && res.status !== 204) throw new Error(res.status);
}

async function apiRemoveAdminFromOrg(adminId, orgId) {
    const res = await fetchWithAuth(`/api/system/admins/${adminId}/?organization_id=${orgId}`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok && res.status !== 204) throw new Error(res.status);
}

// ===== DESIGN TOKENS (organizations.js bilan bir xil) =====
const AC = {
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
const AGRAD  = `linear-gradient(135deg, ${AC.primary}, ${AC.primary2})`;
const AGVIVID= `linear-gradient(135deg, ${AC.indigo}, ${AC.violet})`;

// ===== UI HELPERS =====
function aFormatDate(val) {
    if (!val) return '—';
    const d = new Date(val);
    return isNaN(d) ? val : d.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit', year:'numeric' });
}

function aBadge(text, type) {
    const map = {
        active:   { bg:'#d1fae5', color:'#065f46', dot:'#10b981' },
        inactive: { bg:'#fee2e2', color:'#991b1b', dot:'#ef4444' },
        super:    { bg:'#ede9fe', color:'#5b21b6', dot:'#8b5cf6' },
        normal:   { bg:'#f3f4f6', color:'#4b5563', dot:'#9ca3af' },
        warn:     { bg:'#fef3c7', color:'#92400e', dot:'#f59e0b' },
    };
    const s = map[type] || map.normal;
    return `<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px 3px 7px;
        background:${s.bg};color:${s.color};border-radius:20px;font-size:11.5px;font-weight:600;">
        <span style="width:6px;height:6px;border-radius:50%;background:${s.dot};flex-shrink:0;"></span>
        ${text}</span>`;
}

function aIconBtn(icon, title, onclick, variant = 'default') {
    const v = {
        default: `background:${AC.white};border:1.5px solid ${AC.border};color:${AC.muted};`,
        primary: `background:#eff6ff;border:1.5px solid #bfdbfe;color:${AC.primary};`,
        danger:  `background:#fff1f2;border:1.5px solid #fecdd3;color:#f43f5e;`,
        success: `background:#f0fdf4;border:1.5px solid #bbf7d0;color:#16a34a;`,
        warning: `background:#fffbeb;border:1.5px solid #fde68a;color:#d97706;`,
        info:    `background:#f0f9ff;border:1.5px solid #bae6fd;color:#0369a1;`,
    };
    return `<button title="${title}" onclick="${onclick}" style="${v[variant]||v.default}
        padding:6px 10px;border-radius:7px;cursor:pointer;font-size:12.5px;line-height:1;
        transition:transform .15s,box-shadow .15s;"
        onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 4px 10px rgba(0,0,0,.1)'"
        onmouseout="this.style.transform='';this.style.boxShadow=''">
        <i class="${icon}"></i></button>`;
}

function aAvatar(letter, size = 34, radius = 9) {
    return `<div style="width:${size}px;height:${size}px;border-radius:${radius}px;flex-shrink:0;
        background:${AGVIVID};display:flex;align-items:center;justify-content:center;
        color:#fff;font-weight:800;font-size:${Math.round(size*0.38)}px;
        box-shadow:0 2px 8px rgba(99,102,241,.3);">${letter}</div>`;
}

// ===== MODAL ENGINE (admins.js o'z modal tizimi) =====
function aOpenModal(id, html, wide = false) {
    let overlay = document.getElementById(id);
    if (!overlay) { overlay = document.createElement('div'); overlay.id = id; document.body.appendChild(overlay); }
    overlay.style.cssText = `position:fixed;inset:0;background:rgba(10,10,20,.6);
        backdrop-filter:blur(4px);z-index:10000;display:flex;align-items:center;
        justify-content:center;padding:16px;box-sizing:border-box;`;
    overlay.innerHTML = `
        <div style="background:${AC.white};border-radius:18px;padding:28px;
            width:100%;max-width:${wide?'680px':'475px'};max-height:90vh;overflow-y:auto;
            box-shadow:0 30px 80px rgba(0,0,0,.25);animation:aModalIn .25s cubic-bezier(.34,1.3,.64,1) both;">
            ${html}
        </div>
        <style>@keyframes aModalIn{from{opacity:0;transform:scale(.93) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}</style>`;
    overlay.addEventListener('click', e => { if (e.target === overlay) aCloseModal(id); });
}
function aCloseModal(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }

function aModalHeader(title, id, icon = 'fas fa-user-shield') {
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:40px;height:40px;border-radius:11px;background:${AGRAD};
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 4px 12px rgba(78,115,223,.3);">
                <i class="${icon}" style="color:#fff;font-size:15px;"></i></div>
            <h3 style="margin:0;font-size:15.5px;font-weight:800;color:${AC.text};">${title}</h3>
        </div>
        <button onclick="aCloseModal('${id}')"
            style="width:30px;height:30px;border-radius:8px;background:${AC.bg};
                border:1px solid ${AC.border};cursor:pointer;color:${AC.muted};
                font-size:18px;display:flex;align-items:center;justify-content:center;
                transition:background .15s,color .15s;"
            onmouseover="this.style.background='#fee2e2';this.style.color='#ef4444'"
            onmouseout="this.style.background='${AC.bg}';this.style.color='${AC.muted}'">×</button>
    </div>`;
}

function aFormGroup(label, inputHtml) {
    return `<div style="margin-bottom:15px;">
        <label style="display:block;font-size:11px;font-weight:700;color:${AC.muted};
            text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">${label}</label>
        ${inputHtml}</div>`;
}

const aInput = (id, type = 'text', val = '', placeholder = '') => `
    <input type="${type}" id="${id}" value="${val}" placeholder="${placeholder}"
        style="width:100%;padding:10px 13px;border:1.5px solid ${AC.border};border-radius:9px;
            font-size:13.5px;color:${AC.text};background:${AC.white};outline:none;box-sizing:border-box;
            transition:border-color .18s,box-shadow .18s;"
        onfocus="this.style.borderColor='${AC.primary}';this.style.boxShadow='0 0 0 3px ${AC.primary}18'"
        onblur="this.style.borderColor='${AC.border}';this.style.boxShadow='none'">`;

function aCheckbox(id, label, checked = false) {
    return `<label style="display:flex;align-items:center;gap:10px;cursor:pointer;
            font-size:13px;font-weight:600;color:${AC.text};padding:10px 13px;
            border:1.5px solid ${AC.border};border-radius:9px;margin-bottom:16px;
            transition:border-color .15s,background .15s;"
            onmouseover="this.style.borderColor='${AC.primary}';this.style.background='#f0f4ff'"
            onmouseout="this.style.borderColor='${AC.border}';this.style.background=''">
        <input type="checkbox" id="${id}" ${checked?'checked':''} style="width:16px;height:16px;accent-color:${AC.primary};cursor:pointer;">
        ${label}</label>`;
}

function aFooterBtns(cancelId, confirmFn, confirmLabel = 'Save', icon = 'fas fa-check') {
    return `<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:22px;
            padding-top:16px;border-top:1px solid ${AC.border};">
        <button onclick="aCloseModal('${cancelId}')"
            style="padding:9px 20px;border:1.5px solid ${AC.border};border-radius:9px;
                background:${AC.white};cursor:pointer;font-size:13px;font-weight:600;color:${AC.muted};
                transition:border-color .15s,color .15s;"
            onmouseover="this.style.borderColor='${AC.text}';this.style.color='${AC.text}'"
            onmouseout="this.style.borderColor='${AC.border}';this.style.color='${AC.muted}'">Cancel</button>
        <button onclick="${confirmFn}"
            style="padding:9px 20px;border:none;border-radius:9px;background:${AGRAD};
                color:#fff;cursor:pointer;font-size:13px;font-weight:700;
                display:flex;align-items:center;gap:7px;
                box-shadow:0 4px 14px rgba(78,115,223,.3);transition:transform .15s,box-shadow .15s;"
            onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 8px 20px rgba(78,115,223,.4)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(78,115,223,.3)'">
            <i class="${icon}"></i> ${confirmLabel}</button>
    </div>`;
}

// ===== TABLE STYLES =====
const ATH = `style="padding:11px 16px;text-align:left;font-size:10.5px;font-weight:700;
    text-transform:uppercase;letter-spacing:.07em;color:${AC.primary};
    border-bottom:2px solid ${AC.border};background:${AC.bg};white-space:nowrap;"`;

const ATD = `style="padding:13px 16px;border-bottom:1px solid #f3f4f6;
    color:${AC.text};vertical-align:middle;font-size:13.5px;"`;

// ===== RENDER =====
async function renderAdmins() {
    const container = document.getElementById('admins-container') || document.getElementById('page-content');
    if (!container) return;

    showLoading();
    let admins = [];
    try {
        admins = await apiFetchAdmins();
    } catch (err) {
        showToast('Failed to load admins: ' + err.message, 'danger');
    } finally {
        hideLoading();
    }

    const total  = admins.length;
    const locked = admins.filter(a => a.locked).length;
    const supers = admins.filter(a => a.superadmin || a.is_superuser).length;
    const atRisk = admins.filter(a => (a.failed_attempts ?? 0) > 3).length;

    const statCards = [
        { icon:'fas fa-users',                label:'Total Admins',     val:total,   color:AC.primary },
        { icon:'fas fa-crown',                label:'Super Admins',     val:supers,  color:AC.violet  },
        { icon:'fas fa-lock',                 label:'Locked',           val:locked,  color:AC.danger  },
        { icon:'fas fa-triangle-exclamation', label:'High Risk',        val:atRisk,  color:AC.warning },
    ].map(s => `
        <div style="flex:1;min-width:140px;background:${AC.white};border-radius:14px;
            padding:18px 20px;border:1.5px solid ${AC.border};
            display:flex;align-items:center;gap:14px;
            box-shadow:0 2px 8px rgba(0,0,0,.04);
            transition:transform .2s,box-shadow .2s;cursor:default;"
            onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 10px 28px rgba(0,0,0,.09)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 2px 8px rgba(0,0,0,.04)'">
            <div style="width:44px;height:44px;border-radius:11px;background:${s.color}18;
                display:flex;align-items:center;justify-content:center;font-size:18px;color:${s.color};flex-shrink:0;">
                <i class="${s.icon}"></i></div>
            <div>
                <div style="font-size:24px;font-weight:800;color:${AC.text};line-height:1;">${s.val}</div>
                <div style="font-size:11px;color:${AC.muted};font-weight:600;margin-top:2px;">${s.label}</div>
            </div>
        </div>`).join('');

    const rows = admins.length
        ? admins.map((a, idx) => {
            const locked     = a.locked ?? false;
            const superAdmin = a.superadmin ?? a.is_superuser ?? false;
            const failed     = a.failed_attempts ?? 0;
            const orgList    = Array.isArray(a.organization)
                ? (a.organization.join(', ') || '—')
                : (a.organization ?? '—');

            const failedType = failed > 3 ? 'inactive' : failed > 0 ? 'warn' : 'active';
            const failedText = failed > 3 ? `${failed} ⚠` : `${failed}`;

            return `
            <tr style="transition:background .12s;animation:aRowIn .3s ease both;animation-delay:${idx*0.04}s;"
                onmouseover="this.style.background='${AC.bg}'" onmouseout="this.style.background=''">
                <td ${ATD}>
                    <div style="display:flex;align-items:center;gap:11px;">
                        ${aAvatar((a.username||'?')[0].toUpperCase())}
                        <strong style="color:${AC.text};font-size:13.5px;">${a.username}</strong>
                    </div>
                </td>
                <td ${ATD}>
                    <span style="font-size:12.5px;color:${AC.muted};">
                        ${orgList !== '—'
                            ? `<i class="fas fa-building" style="margin-right:4px;opacity:.5;"></i>${orgList}`
                            : `<span style="opacity:.4;">—</span>`}
                    </span>
                </td>
                <td ${ATD}>${aBadge(superAdmin ? 'Yes' : 'No', superAdmin ? 'super' : 'normal')}</td>
                <td ${ATD}>${aBadge(locked ? 'Locked' : 'Active', locked ? 'inactive' : 'active')}</td>
                <td ${ATD}>${aBadge(failedText, failedType)}</td>
                <td ${ATD}>
                    <div style="display:flex;gap:5px;align-items:center;flex-wrap:nowrap;">
                        ${aIconBtn('fas fa-pen',          'Edit Admin',           `editAdmin(${a.id},'${a.username}',${superAdmin})`,  'primary')}
                        ${aIconBtn(locked?'fas fa-lock-open':'fas fa-lock',
                                   locked?'Unlock':'Lock',
                                   `toggleAdminLock(${a.id},${locked})`,
                                   locked?'success':'warning')}
                        ${aIconBtn('fas fa-rotate-left',  'Reset Attempts',       `resetAttempts(${a.id})`,               'default')}
                        ${aIconBtn('fas fa-link',         'Attach to Org',        `attachAdminToOrg(${a.id},'${a.username}')`, 'info')}
                        ${aIconBtn('fas fa-sign-out-alt', 'Force Logout',         `forceLogout(${a.id},'${a.username}')`, 'default')}
                        ${aIconBtn('fas fa-trash',        'Delete',               `deleteAdmin(${a.id},'${a.username}')`, 'danger')}
                    </div>
                </td>
            </tr>`;
        }).join('')
        : `<tr><td colspan="6" style="text-align:center;padding:3rem;color:${AC.muted};font-size:13px;">
                <i class="fas fa-user-slash" style="font-size:2.2rem;opacity:.15;display:block;margin-bottom:10px;"></i>
                No admins found</td></tr>`;

    container.innerHTML = `
        <style>
            @keyframes aRowIn { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
            @keyframes aPageIn{ from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
        </style>

        <div style="padding:2rem;animation:aPageIn .4s ease both;">

            <!-- Header -->
            <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;">
                <div>
                    <h2 style="margin:0 0 3px;font-size:20px;font-weight:800;color:${AC.text};
                        display:flex;align-items:center;gap:10px;">
                        <span style="width:38px;height:38px;border-radius:10px;background:${AGRAD};
                            display:inline-flex;align-items:center;justify-content:center;
                            box-shadow:0 4px 14px rgba(78,115,223,.35);">
                            <i class="fas fa-user-shield" style="color:#fff;font-size:15px;"></i>
                        </span>
                        Admin Users
                    </h2>
                    <p style="margin:0;font-size:12.5px;color:${AC.muted};">
                        Manage system administrator accounts and permissions
                    </p>
                </div>
                <button onclick="openCreateAdminModal()"
                    style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;
                        background:${AGRAD};color:#fff;border:none;border-radius:10px;
                        font-size:13px;font-weight:700;cursor:pointer;
                        box-shadow:0 4px 14px rgba(78,115,223,.35);
                        transition:transform .18s,box-shadow .18s;"
                    onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 22px rgba(78,115,223,.45)'"
                    onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(78,115,223,.35)'">
                    <i class="fas fa-plus"></i> Create Admin
                </button>
            </div>

            <!-- Stat cards -->
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:1.5rem;">${statCards}</div>

            <!-- Table card -->
            <div style="background:${AC.white};border-radius:16px;border:1.5px solid ${AC.border};
                box-shadow:0 4px 20px rgba(0,0,0,.05);overflow:hidden;">

                <!-- Toolbar -->
                <div style="padding:14px 20px;border-bottom:1.5px solid ${AC.border};background:${AC.bg};
                    display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                    <span style="font-size:13px;font-weight:700;color:${AC.text};display:flex;align-items:center;gap:8px;">
                        <i class="fas fa-table-list" style="color:${AC.primary};"></i>
                        All Administrators
                        <span style="background:${AC.primary}15;color:${AC.primary};
                            border-radius:20px;padding:1px 9px;font-size:11px;font-weight:700;">${total}</span>
                    </span>
                    <div style="position:relative;">
                        <i class="fas fa-search" style="position:absolute;left:11px;top:50%;
                            transform:translateY(-50%);color:${AC.muted};font-size:12px;pointer-events:none;"></i>
                        <input type="text" id="adminSearch" placeholder="Search admins..."
                            onkeyup="filterAdmins()"
                            style="padding:8px 14px 8px 33px;border:1.5px solid ${AC.border};
                                border-radius:9px;font-size:13px;color:${AC.text};background:${AC.white};
                                outline:none;width:220px;transition:border-color .2s,box-shadow .2s;"
                            onfocus="this.style.borderColor='${AC.primary}';this.style.boxShadow='0 0 0 3px ${AC.primary}18'"
                            onblur="this.style.borderColor='${AC.border}';this.style.boxShadow='none'">
                    </div>
                </div>

                <!-- Table -->
                <div style="overflow-x:auto;">
                    <table id="adminsTable" style="width:100%;border-collapse:collapse;">
                        <thead><tr>
                            <th ${ATH}>Username</th>
                            <th ${ATH}>Organization</th>
                            <th ${ATH}>Super Admin</th>
                            <th ${ATH}>Status</th>
                            <th ${ATH}>Failed</th>
                            <th ${ATH}>Actions</th>
                        </tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>

                <!-- Footer -->
                <div style="padding:11px 20px;border-top:1px solid ${AC.border};background:${AC.bg};
                    font-size:11.5px;color:${AC.muted};display:flex;justify-content:space-between;">
                    <span><i class="fas fa-info-circle" style="margin-right:4px;"></i>${total} admin(s) total</span>
                    <span id="aFilterCount"></span>
                </div>
            </div>
        </div>`;
}

// ===== FILTER =====
window.filterAdmins = function () {
    const term = document.getElementById('adminSearch')?.value.toLowerCase() || '';
    let visible = 0;
    document.querySelectorAll('#adminsTable tbody tr').forEach(row => {
        const show = row.textContent.toLowerCase().includes(term);
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    const fc = document.getElementById('aFilterCount');
    if (fc) fc.textContent = term ? `Showing ${visible} result(s)` : '';
};

// ===== CREATE ADMIN =====
window.openCreateAdminModal = async function () {
    showLoading();
    let orgs = [];
    try { orgs = await apiFetchOrganizations(); }
    catch (e) { showToast('Could not load organizations', 'danger'); }
    finally { hideLoading(); }

    const opts = orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');

    aOpenModal('aCreateModal', `
        ${aModalHeader('Create New Admin', 'aCreateModal', 'fas fa-user-plus')}
        ${aFormGroup('Username *', aInput('cAdminUsername','text','','e.g. john.doe'))}
        ${aFormGroup('Password *', `
            <div style="position:relative;">
                ${aInput('cAdminPassword','password','','••••••••')}
                <button onclick="aTogglePass('cAdminPassword',this)"
                    style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                        background:none;border:none;color:${AC.muted};cursor:pointer;font-size:14px;">
                    <i class="fas fa-eye"></i></button>
            </div>`)}
        ${aFormGroup('Organization *', `
            <select id="cAdminOrg" style="width:100%;padding:10px 13px;border:1.5px solid ${AC.border};
                border-radius:9px;font-size:13.5px;color:${AC.text};background:${AC.white};
                outline:none;box-sizing:border-box;"
                onfocus="this.style.borderColor='${AC.primary}'"
                onblur="this.style.borderColor='${AC.border}'">
                <option value="">Select organization…</option>${opts}
            </select>`)}
        ${aCheckbox('cAdminSuper','⭐ Super Admin',false)}
        ${aFooterBtns('aCreateModal','createAdmin()','Create','fas fa-user-plus')}
    `);
};

window.aTogglePass = function(inputId, btn) {
    const inp = document.getElementById(inputId);
    if (!inp) return;
    const isPass = inp.type === 'password';
    inp.type = isPass ? 'text' : 'password';
    btn.innerHTML = `<i class="fas fa-${isPass?'eye-slash':'eye'}"></i>`;
};

window.createAdmin = async function () {
    const username   = document.getElementById('cAdminUsername')?.value.trim();
    const password   = document.getElementById('cAdminPassword')?.value;
    const orgId      = document.getElementById('cAdminOrg')?.value;
    const superAdmin = document.getElementById('cAdminSuper')?.checked;
    if (!username || !password || !orgId) { showToast('Please fill all required fields', 'danger'); return; }
    try {
        showLoading();
        await apiCreateAdmin({ username, password, organization_id: parseInt(orgId), is_superuser: superAdmin });
        aCloseModal('aCreateModal');
        showToast('Admin created successfully');
        renderAdmins();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== EDIT ADMIN =====
// Uch tabli: Asosiy ma'lumot | Parol | Tashkilot
window.editAdmin = async function (id, username, isSuperadmin) {
    showLoading();
    let orgs = [], admins = [];
    try {
        [orgs, admins] = await Promise.all([apiFetchOrganizations(), apiFetchAdmins()]);
    } catch (e) { showToast('Could not load data', 'danger'); return; }
    finally { hideLoading(); }

    const adminData   = admins.find(a => a.id === id) || {};
    const currentOrgs = Array.isArray(adminData.organization) ? adminData.organization : [];

    const orgRows = currentOrgs.length
        ? currentOrgs.map(orgName => {
            const orgObj = orgs.find(o => o.name === orgName);
            const orgId  = orgObj ? orgObj.id : null;
            return `<div style="display:flex;align-items:center;justify-content:space-between;
                padding:9px 13px;border:1.5px solid ${AC.border};border-radius:9px;margin-bottom:7px;">
                <span style="font-size:13px;font-weight:600;color:${AC.text};display:flex;align-items:center;gap:8px;">
                    <i class="fas fa-building" style="color:${AC.primary};opacity:.7;"></i>${orgName}
                </span>
                ${orgId ? `<button onclick="removeFromOrg(${id},${orgId})" title="Remove"
                    style="background:#fff1f2;border:1.5px solid #fecdd3;color:#f43f5e;
                        padding:4px 9px;border-radius:6px;cursor:pointer;font-size:12px;
                        transition:opacity .15s;"
                    onmouseover="this.style.opacity='.7'" onmouseout="this.style.opacity='1'">
                    <i class="fas fa-unlink"></i></button>` : ''}
            </div>`;
        }).join('')
        : `<div style="text-align:center;color:${AC.muted};padding:1rem;font-size:12.5px;opacity:.7;">
               No organizations attached</div>`;

    aOpenModal('aEditModal', `
        ${aModalHeader(`Edit: ${username}`, 'aEditModal', 'fas fa-pen')}
        <input type="hidden" id="eAdminId" value="${id}">

        <!-- Tabs -->
        <div style="display:flex;border-bottom:2px solid ${AC.border};margin-bottom:18px;">
            ${['info','password','orgs'].map((tab, i) => {
                const labels = ['fas fa-user|Info','fas fa-key|Password','fas fa-building|Organizations'];
                const [icon, label] = labels[i].split('|');
                return `<button id="eTab_${tab}" onclick="switchEditTab('${tab}')"
                    style="padding:8px 14px;border:none;background:none;cursor:pointer;
                        font-size:12px;font-weight:700;
                        color:${i===0?AC.primary:AC.muted};
                        border-bottom:2.5px solid ${i===0?AC.primary:'transparent'};
                        margin-bottom:-2px;transition:color .15s;display:flex;align-items:center;gap:5px;">
                    <i class="${icon}"></i> ${label}</button>`;
            }).join('')}
        </div>

        <!-- Tab: Info -->
        <div id="ePane_info">
            ${aFormGroup('Username *', aInput('eUsername','text',username,''))}
            ${aCheckbox('eSuperAdmin','⭐ Super Admin', isSuperadmin)}
            ${aFooterBtns('aEditModal','saveAdminInfo()','Save Info','fas fa-floppy-disk')}
        </div>

        <!-- Tab: Password -->
        <div id="ePane_password" style="display:none;">
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                padding:12px 14px;margin-bottom:16px;font-size:12.5px;color:#92400e;">
                <i class="fas fa-triangle-exclamation" style="margin-right:5px;"></i>
                Yangi parol kiritilsa admin sessiyasi bekor bo'ladi.
            </div>
            ${aFormGroup('New Password *', `
                <div style="position:relative;">
                    ${aInput('eNewPassword','password','','New password')}
                    <button onclick="aTogglePass('eNewPassword',this)"
                        style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                            background:none;border:none;color:${AC.muted};cursor:pointer;font-size:14px;">
                        <i class="fas fa-eye"></i></button>
                </div>`)}
            ${aFormGroup('Confirm Password *', `
                <div style="position:relative;">
                    ${aInput('eConfirmPassword','password','','Repeat password')}
                    <button onclick="aTogglePass('eConfirmPassword',this)"
                        style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                            background:none;border:none;color:${AC.muted};cursor:pointer;font-size:14px;">
                        <i class="fas fa-eye"></i></button>
                </div>`)}
            ${aFooterBtns('aEditModal','saveAdminPassword()','Change Password','fas fa-key')}
        </div>

        <!-- Tab: Organizations -->
        <div id="ePane_orgs" style="display:none;">
            <div style="margin-bottom:14px;">
                <div style="font-size:11px;font-weight:700;color:${AC.muted};text-transform:uppercase;
                    letter-spacing:.05em;margin-bottom:10px;">Current Organizations</div>
                <div id="eOrgList">${orgRows}</div>
            </div>
            <!-- Org qo'shish -->
            <div style="border-top:1px solid ${AC.border};padding-top:14px;margin-top:6px;">
                <div style="font-size:11px;font-weight:700;color:${AC.muted};text-transform:uppercase;
                    letter-spacing:.05em;margin-bottom:10px;">Add to Organization</div>
                <div style="display:flex;gap:8px;align-items:center;">
                    <select id="eAddOrgSelect" style="flex:1;padding:9px 12px;
                        border:1.5px solid ${AC.border};border-radius:9px;font-size:13px;
                        color:${AC.text};background:${AC.white};outline:none;"
                        onfocus="this.style.borderColor='${AC.primary}'"
                        onblur="this.style.borderColor='${AC.border}'">
                        <option value="">Select organization…</option>
                        ${orgs.filter(o => !currentOrgs.includes(o.name)).map(o =>
                            `<option value="${o.id}">${o.name}</option>`).join('')}
                    </select>
                    <button onclick="addOrgToAdmin(${id})"
                        style="padding:9px 16px;border:none;border-radius:9px;background:${AGRAD};
                            color:#fff;font-size:12.5px;font-weight:700;cursor:pointer;white-space:nowrap;
                            box-shadow:0 3px 10px rgba(78,115,223,.3);transition:transform .15s;"
                        onmouseover="this.style.transform='translateY(-1px)'"
                        onmouseout="this.style.transform=''">
                        <i class="fas fa-link" style="margin-right:5px;"></i>Biriktirish
                    </button>
                </div>
            </div>
            <div style="display:flex;justify-content:flex-end;margin-top:20px;padding-top:16px;border-top:1px solid ${AC.border};">
                <button onclick="aCloseModal('aEditModal')"
                    style="padding:9px 20px;border:1.5px solid ${AC.border};border-radius:9px;
                        background:${AC.white};cursor:pointer;font-size:13px;font-weight:600;color:${AC.muted};">
                    Close</button>
            </div>
        </div>
    `);
};

window.switchEditTab = function (tab) {
    ['info','password','orgs'].forEach(t => {
        const pane = document.getElementById(`ePane_${t}`);
        const btn  = document.getElementById(`eTab_${t}`);
        if (!pane || !btn) return;
        const active = t === tab;
        pane.style.display         = active ? '' : 'none';
        btn.style.color             = active ? AC.primary : AC.muted;
        btn.style.borderBottomColor = active ? AC.primary : 'transparent';
    });
};

window.saveAdminInfo = async function () {
    const id       = document.getElementById('eAdminId')?.value;
    const username = document.getElementById('eUsername')?.value.trim();
    const isSuper  = document.getElementById('eSuperAdmin')?.checked;
    if (!username) { showToast('Username kiritilishi shart', 'danger'); return; }
    try {
        showLoading();
        await apiPatchAdmin(parseInt(id), { username, is_superuser: isSuper });
        aCloseModal('aEditModal');
        showToast('Admin info updated');
        renderAdmins();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

window.saveAdminPassword = async function () {
    const id      = document.getElementById('eAdminId')?.value;
    const newPass = document.getElementById('eNewPassword')?.value;
    const confirm = document.getElementById('eConfirmPassword')?.value;
    if (!newPass) { showToast('Yangi parol kiriting', 'danger'); return; }
    if (newPass !== confirm) { showToast('Parollar mos kelmayapti', 'danger'); return; }
    try {
        showLoading();
        await apiPatchAdmin(parseInt(id), { password: newPass });
        aCloseModal('aEditModal');
        showToast('Password changed successfully');
        renderAdmins();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

window.addOrgToAdmin = async function (adminId) {
    const orgId = document.getElementById('eAddOrgSelect')?.value;
    if (!orgId) { showToast('Tashkilot tanlang', 'danger'); return; }
    try {
        showLoading();
        await apiAttachAdminToOrg(adminId, parseInt(orgId));
        showToast('Tashkilotga biriktirildi');
        // Refresh current admin data and reopen edit modal
        const admins = await apiFetchAdmins();
        const a = admins.find(x => x.id === adminId);
        if (a) { aCloseModal('aEditModal'); editAdmin(a.id, a.username, a.superadmin ?? false); }
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

window.removeFromOrg = async function (adminId, orgId) {
    if (!confirm('Bu adminni tashkilotdan chiqarishni xohlaysizmi?')) return;
    try {
        showLoading();
        await apiRemoveAdminFromOrg(adminId, orgId);
        showToast('Admin tashkilotdan chiqarildi');
        const admins = await apiFetchAdmins();
        const a = admins.find(x => x.id === adminId);
        if (a) { aCloseModal('aEditModal'); editAdmin(a.id, a.username, a.superadmin ?? false); }
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== ATTACH ADMIN TO ORG (quick, from table row) =====
window.attachAdminToOrg = async function (adminId, username) {
    showLoading();
    let orgs = [], admins = [];
    try {
        [orgs, admins] = await Promise.all([apiFetchOrganizations(), apiFetchAdmins()]);
    } catch (e) { showToast('Could not load data', 'danger'); return; }
    finally { hideLoading(); }

    const adminData   = admins.find(a => a.id === adminId) || {};
    const currentOrgs = Array.isArray(adminData.organization) ? adminData.organization : [];
    const available   = orgs.filter(o => !currentOrgs.includes(o.name));

    const listHtml = available.length
        ? available.map(o => `
            <div onclick="selectOrgForAdmin(this, ${o.id})"
                style="display:flex;align-items:center;gap:11px;padding:10px 13px;
                    border:1.5px solid ${AC.border};border-radius:10px;cursor:pointer;
                    margin-bottom:7px;transition:border-color .15s,background .15s;"
                onmouseover="if(!this.dataset.selected){this.style.borderColor='${AC.primary}';this.style.background='#f0f4ff'}"
                onmouseout="if(!this.dataset.selected){this.style.borderColor='${AC.border}';this.style.background=''}">
                <div style="width:34px;height:34px;border-radius:9px;flex-shrink:0;
                    background:${AGRAD};display:flex;align-items:center;justify-content:center;
                    color:#fff;font-weight:700;font-size:13px;">
                    ${o.name[0].toUpperCase()}</div>
                <div>
                    <div style="font-size:13px;font-weight:700;color:${AC.text};">${o.name}</div>
                    <div style="font-size:11px;color:${AC.muted};">
                        <code style="background:#f1f5f9;padding:1px 6px;border-radius:4px;">${o.slug}</code>
                    </div>
                </div>
                <i class="fas fa-circle-check" data-check style="color:${AC.primary};font-size:16px;display:none;margin-left:auto;"></i>
            </div>`).join('')
        : `<div style="text-align:center;color:${AC.muted};padding:2rem;font-size:13px;">
               <i class="fas fa-check-circle" style="font-size:1.8rem;opacity:.2;display:block;margin-bottom:8px;"></i>
               Admin barcha tashkilotlarga biriktirilgan</div>`;

    aOpenModal('aAttachOrgModal', `
        ${aModalHeader(`${username} — Org biriktirish`, 'aAttachOrgModal', 'fas fa-link')}
        <input type="hidden" id="attachQuickAdminId" value="${adminId}">
        <input type="hidden" id="attachQuickOrgId" value="">

        <div style="max-height:320px;overflow-y:auto;padding-right:2px;margin-bottom:4px;">
            ${listHtml}
        </div>
        ${aFooterBtns('aAttachOrgModal','confirmQuickAttach()','Biriktirish','fas fa-link')}
    `);
};

window.selectOrgForAdmin = function (el, orgId) {
    document.querySelectorAll('#aAttachOrgModal [data-selected]').forEach(item => {
        delete item.dataset.selected;
        item.style.borderColor = AC.border;
        item.style.background  = '';
        const ic = item.querySelector('[data-check]');
        if (ic) ic.style.display = 'none';
    });
    el.dataset.selected  = '1';
    el.style.borderColor = AC.primary;
    el.style.background  = '#f0f4ff';
    const ic = el.querySelector('[data-check]');
    if (ic) ic.style.display = '';
    document.getElementById('attachQuickOrgId').value = orgId;
};

window.confirmQuickAttach = async function () {
    const adminId = document.getElementById('attachQuickAdminId')?.value;
    const orgId   = document.getElementById('attachQuickOrgId')?.value;
    if (!orgId) { showToast('Tashkilot tanlang', 'danger'); return; }
    try {
        showLoading();
        await apiAttachAdminToOrg(parseInt(adminId), parseInt(orgId));
        aCloseModal('aAttachOrgModal');
        showToast('Admin tashkilotga biriktirildi');
        renderAdmins();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== TOGGLE LOCK =====
window.toggleAdminLock = function (id, currentLocked) {
    if (!confirm(`${currentLocked ? 'Unlock' : 'Lock'} this admin?`)) return;
    apiPatchAdmin(id, { locked: !currentLocked })
        .then(() => { showToast(`Admin ${currentLocked ? 'unlocked' : 'locked'}`); renderAdmins(); })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== RESET ATTEMPTS =====
window.resetAttempts = function (id) {
    if (!confirm('Reset failed login attempts for this admin?')) return;
    apiResetAttempts(id)
        .then(() => { showToast('Failed attempts reset'); renderAdmins(); })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== FORCE LOGOUT =====
window.forceLogout = function (id, username) {
    if (!confirm(`Force logout ${username} from all sessions?`)) return;
    apiForceLogout(id)
        .then(() => showToast(`${username} logged out from all sessions`))
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== DELETE ADMIN =====
window.deleteAdmin = function (id, username) {
    if (!confirm(`Delete "${username}"? This cannot be undone.`)) return;
    apiDeleteAdmin(id)
        .then(() => { showToast('Admin deleted'); renderAdmins(); })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== TOAST FALLBACK =====
if (typeof showToast === 'undefined') {
    window.showToast = function(msg, type = 'success') {
        console[type === 'danger' ? 'error' : 'log']('[Toast]', msg);
    };
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    renderAdmins();
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', e => { e.preventDefault(); logout(); });
});