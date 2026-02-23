// ============================================================
// organizations.js — Organizations Page  (requires api.js)
// ============================================================

// ===== API CALLS =====

async function apiFetchOrganizations() {
    const res = await fetchWithAuth('/api/organizations/');
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiFetchOrgDetail(id) {
    const res = await fetchWithAuth(`/api/organizations/${id}/`);
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiFetchOrgAdmins(orgId) {
    const res = await fetchWithAuth(`/api/system/admins/?organization_id=${orgId}`);
    if (!res.ok) return [];
    return res.json();
}

async function apiFetchAllAdmins() {
    const res = await fetchWithAuth('/api/system/admins/');
    if (!res.ok) return [];
    return res.json();
}

async function apiCreateOrganization(data) {
    const res = await fetchWithAuth('/api/organizations/', {
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

async function apiUpdateOrganization(id, data) {
    const res = await fetchWithAuth(`/api/organizations/${id}/`, {
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

async function apiDeleteOrganization(id) {
    const res = await fetchWithAuth(`/api/organizations/${id}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok && res.status !== 204) throw new Error(res.status);
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

async function apiAttachAdminToOrg(adminId, orgId) {
    const res = await fetchWithAuth(`/api/system/admins/${adminId}/?organization_id=${orgId}`, {
        method: 'PATCH',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
        body: JSON.stringify({ organization_id: orgId })
    });
    if (!res.ok) throw new Error(res.status);
    return res.json();
}

async function apiDeleteAdminOrg(adminId, orgId) {
    const res = await fetchWithAuth(`/api/system/admins/${adminId}/?organization_id=${orgId}`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    if (!res.ok && res.status !== 204) throw new Error(res.status);
}

// ===== DESIGN TOKENS =====
const C = {
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
const GRAD       = `linear-gradient(135deg, ${C.primary}, ${C.primary2})`;
const GRAD_VIVID = `linear-gradient(135deg, ${C.indigo}, ${C.violet})`;

// ===== SHARED TABLE STYLES =====
const TH = `style="
    padding:11px 16px;text-align:left;font-size:10.5px;font-weight:700;
    text-transform:uppercase;letter-spacing:.07em;color:${C.primary};
    border-bottom:2px solid ${C.border};background:${C.bg};white-space:nowrap;"`;

const TD = `style="
    padding:13px 16px;border-bottom:1px solid #f3f4f6;
    color:${C.text};vertical-align:middle;font-size:13.5px;"`;

// ===== UI HELPERS =====

function formatDate(val) {
    if (!val) return '—';
    const d = new Date(val);
    return isNaN(d) ? val : d.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit', year:'numeric' });
}

function badge(text, type) {
    const map = {
        active:   { bg:'#d1fae5', color:'#065f46', dot:'#10b981' },
        inactive: { bg:'#fee2e2', color:'#991b1b', dot:'#ef4444' },
        super:    { bg:'#ede9fe', color:'#5b21b6', dot:'#8b5cf6' },
        normal:   { bg:'#f3f4f6', color:'#4b5563', dot:'#9ca3af' },
    };
    const s = map[type] || map.normal;
    return `<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px 3px 7px;
        background:${s.bg};color:${s.color};border-radius:20px;font-size:11.5px;font-weight:600;">
        <span style="width:6px;height:6px;border-radius:50%;background:${s.dot};flex-shrink:0;"></span>
        ${text}</span>`;
}

function iconBtn(icon, title, onclick, variant = 'default') {
    const v = {
        default: `background:${C.white};border:1.5px solid ${C.border};color:${C.muted};`,
        primary: `background:#eff6ff;border:1.5px solid #bfdbfe;color:${C.primary};`,
        danger:  `background:#fff1f2;border:1.5px solid #fecdd3;color:#f43f5e;`,
        success: `background:#f0fdf4;border:1.5px solid #bbf7d0;color:#16a34a;`,
        warning: `background:#fffbeb;border:1.5px solid #fde68a;color:#d97706;`,
    };
    return `<button title="${title}" onclick="${onclick}" style="${v[variant]||v.default}
        padding:6px 10px;border-radius:7px;cursor:pointer;font-size:12.5px;line-height:1;
        transition:transform .15s,box-shadow .15s;"
        onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 4px 10px rgba(0,0,0,.1)'"
        onmouseout="this.style.transform='';this.style.boxShadow=''">
        <i class="${icon}"></i></button>`;
}

function avatar(letter, size = 34, radius = 9) {
    return `<div style="width:${size}px;height:${size}px;border-radius:${radius}px;flex-shrink:0;
        background:${GRAD_VIVID};display:flex;align-items:center;justify-content:center;
        color:#fff;font-weight:800;font-size:${Math.round(size*0.38)}px;
        box-shadow:0 2px 8px rgba(99,102,241,.3);">${letter}</div>`;
}

// ===== RENDER =====
async function renderOrganizations() {
    const container = document.getElementById('page-content');
    if (!container) return;

    showLoading();
    let orgs = [];
    try {
        orgs = await apiFetchOrganizations();
    } catch (err) {
        showToast('Failed to load organizations: ' + err.message, 'danger');
    } finally {
        hideLoading();
    }

    const total    = orgs.length;
    const activeC  = orgs.filter(o => o.active).length;
    const adminSum = orgs.reduce((s, o) => s + (o.admin_count ?? 0), 0);

    const statCards = [
        { icon:'fas fa-sitemap',      label:'Total Orgs',  val:total,         color:C.primary  },
        { icon:'fas fa-circle-check', label:'Active',      val:activeC,       color:C.success  },
        { icon:'fas fa-ban',          label:'Inactive',    val:total-activeC, color:C.danger   },
        { icon:'fas fa-users',        label:'Total Admins',val:adminSum,      color:C.violet   },
    ].map(s => `
        <div style="flex:1;min-width:140px;background:${C.white};border-radius:14px;
            padding:18px 20px;border:1.5px solid ${C.border};
            display:flex;align-items:center;gap:14px;
            box-shadow:0 2px 8px rgba(0,0,0,.04);
            transition:transform .2s,box-shadow .2s;cursor:default;"
            onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 10px 28px rgba(0,0,0,.09)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 2px 8px rgba(0,0,0,.04)'">
            <div style="width:44px;height:44px;border-radius:11px;background:${s.color}15;
                display:flex;align-items:center;justify-content:center;font-size:18px;color:${s.color};flex-shrink:0;">
                <i class="${s.icon}"></i></div>
            <div>
                <div style="font-size:24px;font-weight:800;color:${C.text};line-height:1;">${s.val}</div>
                <div style="font-size:11px;color:${C.muted};font-weight:600;margin-top:2px;">${s.label}</div>
            </div>
        </div>`).join('');

    const rows = total
        ? orgs.map((o, i) => `
            <tr style="transition:background .12s;animation:rowIn .3s ease both;animation-delay:${i*0.05}s;"
                onmouseover="this.style.background='${C.bg}'" onmouseout="this.style.background=''">
                <td ${TD}>
                    <div style="display:flex;align-items:center;gap:11px;">
                        ${avatar(o.name[0].toUpperCase())}
                        <strong style="color:${C.text};font-size:13.5px;">${o.name}</strong>
                    </div>
                </td>
                <td ${TD}>
                    <code style="background:#f1f5f9;padding:3px 9px;border-radius:6px;
                        font-size:11.5px;color:${C.muted};border:1px solid #e2e8f0;">${o.slug}</code>
                </td>
                <td ${TD}>${badge(o.active ? 'Active' : 'Inactive', o.active ? 'active' : 'inactive')}</td>
                <td ${TD} style="text-align:center;">
                    <span style="display:inline-flex;align-items:center;justify-content:center;
                        width:28px;height:28px;border-radius:50%;
                        background:${C.primary}15;color:${C.primary};font-size:12px;font-weight:700;">
                        ${o.admin_count ?? 0}
                    </span>
                </td>
                <td ${TD} style="color:${C.muted};font-size:12.5px;">
                    <i class="fas fa-calendar-alt" style="margin-right:5px;opacity:.45;"></i>${formatDate(o.created_at)}
                </td>
                <td ${TD}>
                    <div style="display:flex;gap:5px;align-items:center;flex-wrap:nowrap;">
                        ${iconBtn('fas fa-eye',  'View',  `viewOrganization(${o.id})`,  'primary')}
                        ${iconBtn('fas fa-pen',  'Edit',  `editOrganization(${o.id})`,  'default')}
                        ${iconBtn(
                            o.active ? 'fas fa-ban' : 'fas fa-circle-check',
                            o.active ? 'Disable' : 'Enable',
                            `toggleOrgStatus(${o.id}, ${o.active})`,
                            o.active ? 'warning' : 'success'
                        )}
                        ${iconBtn('fas fa-trash','Delete',`deleteOrganization(${o.id},'${o.name.replace(/'/g,"\\'")}')`, 'danger')}
                    </div>
                </td>
            </tr>`).join('')
        : `<tr><td colspan="6" style="text-align:center;padding:3rem;color:${C.muted};font-size:13px;">
                <i class="fas fa-building" style="font-size:2.2rem;opacity:.15;display:block;margin-bottom:10px;"></i>
                No organizations found</td></tr>`;

    container.innerHTML = `
        <style>
            @keyframes rowIn { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
            @keyframes pageIn{ from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
            @keyframes modalIn{ from{opacity:0;transform:scale(.94) translateY(8px)} to{opacity:1;transform:scale(1) translateY(0)} }
        </style>

        <div style="padding:2rem;animation:pageIn .4s ease both;">

            <!-- Header -->
            <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;">
                <div>
                    <h2 style="margin:0 0 3px;font-size:20px;font-weight:800;color:${C.text};
                        display:flex;align-items:center;gap:10px;">
                        <span style="width:38px;height:38px;border-radius:10px;background:${GRAD};
                            display:inline-flex;align-items:center;justify-content:center;
                            box-shadow:0 4px 14px rgba(78,115,223,.35);">
                            <i class="fas fa-building" style="color:#fff;font-size:15px;"></i>
                        </span>
                        Organizations
                    </h2>
                    <p style="margin:0;font-size:12.5px;color:${C.muted};">
                        Manage system organizations and their administrators
                    </p>
                </div>
                <button onclick="openCreateOrgModal()"
                    style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;
                        background:${GRAD};color:#fff;border:none;border-radius:10px;
                        font-size:13px;font-weight:700;cursor:pointer;
                        box-shadow:0 4px 14px rgba(78,115,223,.35);
                        transition:transform .18s,box-shadow .18s;"
                    onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 22px rgba(78,115,223,.45)'"
                    onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(78,115,223,.35)'">
                    <i class="fas fa-plus"></i> Create Organization
                </button>
            </div>

            <!-- Stat cards -->
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:1.5rem;">${statCards}</div>

            <!-- Table card -->
            <div style="background:${C.white};border-radius:16px;border:1.5px solid ${C.border};
                box-shadow:0 4px 20px rgba(0,0,0,.05);overflow:hidden;">

                <!-- Card toolbar -->
                <div style="padding:14px 20px;border-bottom:1.5px solid ${C.border};background:${C.bg};
                    display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                    <span style="font-size:13px;font-weight:700;color:${C.text};display:flex;align-items:center;gap:8px;">
                        <i class="fas fa-table-list" style="color:${C.primary};"></i>
                        All Organizations
                        <span style="background:${C.primary}15;color:${C.primary};
                            border-radius:20px;padding:1px 9px;font-size:11px;font-weight:700;">${total}</span>
                    </span>
                    <div style="position:relative;">
                        <i class="fas fa-search" style="position:absolute;left:11px;top:50%;
                            transform:translateY(-50%);color:${C.muted};font-size:12px;pointer-events:none;"></i>
                        <input type="text" id="orgSearch" placeholder="Search..."
                            onkeyup="filterOrganizations()"
                            style="padding:8px 14px 8px 33px;border:1.5px solid ${C.border};
                                border-radius:9px;font-size:13px;color:${C.text};background:${C.white};
                                outline:none;width:220px;transition:border-color .2s,box-shadow .2s;"
                            onfocus="this.style.borderColor='${C.primary}';this.style.boxShadow='0 0 0 3px ${C.primary}18'"
                            onblur="this.style.borderColor='${C.border}';this.style.boxShadow='none'">
                    </div>
                </div>

                <!-- Table -->
                <div style="overflow-x:auto;">
                    <table id="orgsTable" style="width:100%;border-collapse:collapse;">
                        <thead><tr>
                            <th ${TH}>Organization</th>
                            <th ${TH}>Slug</th>
                            <th ${TH}>Status</th>
                            <th ${TH} style="padding:11px 16px;text-align:center;">Admins</th>
                            <th ${TH}>Created</th>
                            <th ${TH}>Actions</th>
                        </tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>

                <!-- Footer -->
                <div style="padding:11px 20px;border-top:1px solid ${C.border};background:${C.bg};
                    font-size:11.5px;color:${C.muted};display:flex;justify-content:space-between;">
                    <span><i class="fas fa-info-circle" style="margin-right:4px;"></i>${total} organization(s) total</span>
                    <span id="orgFilterCount"></span>
                </div>
            </div>
        </div>`;
}

window.filterOrganizations = function () {
    const term = document.getElementById('orgSearch')?.value.toLowerCase() || '';
    let visible = 0;
    document.querySelectorAll('#orgsTable tbody tr').forEach(row => {
        const show = row.textContent.toLowerCase().includes(term);
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    const fc = document.getElementById('orgFilterCount');
    if (fc) fc.textContent = term ? `Showing ${visible} result(s)` : '';
};

// ===== MODAL ENGINE =====
function orgOpenModal(id, html, wide = false) {
    let overlay = document.getElementById(id);
    if (!overlay) { overlay = document.createElement('div'); overlay.id = id; document.body.appendChild(overlay); }
    overlay.style.cssText = `position:fixed;inset:0;background:rgba(10,10,20,.6);
        backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;
        justify-content:center;padding:16px;box-sizing:border-box;`;
    overlay.innerHTML = `
        <div style="background:${C.white};border-radius:18px;padding:28px;
            width:100%;max-width:${wide?'700px':'475px'};max-height:90vh;overflow-y:auto;
            box-shadow:0 30px 80px rgba(0,0,0,.25);animation:modalIn .25s cubic-bezier(.34,1.3,.64,1) both;">
            ${html}
        </div>`;
    overlay.addEventListener('click', e => { if (e.target === overlay) orgCloseModal(id); });
}
function orgCloseModal(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }

function orgModalHeader(title, id, icon = 'fas fa-building') {
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:40px;height:40px;border-radius:11px;background:${GRAD};
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 4px 12px rgba(78,115,223,.3);">
                <i class="${icon}" style="color:#fff;font-size:15px;"></i></div>
            <h3 style="margin:0;font-size:15.5px;font-weight:800;color:${C.text};">${title}</h3>
        </div>
        <button onclick="orgCloseModal('${id}')"
            style="width:30px;height:30px;border-radius:8px;background:${C.bg};
                border:1px solid ${C.border};cursor:pointer;color:${C.muted};
                font-size:18px;display:flex;align-items:center;justify-content:center;
                transition:background .15s,color .15s;"
            onmouseover="this.style.background='#fee2e2';this.style.color='#ef4444'"
            onmouseout="this.style.background='${C.bg}';this.style.color='${C.muted}'">×</button>
    </div>`;
}

function orgFormGroup(label, inputHtml) {
    return `<div style="margin-bottom:15px;">
        <label style="display:block;font-size:11px;font-weight:700;color:${C.muted};
            text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">${label}</label>
        ${inputHtml}</div>`;
}

const orgInput = (id, type = 'text', val = '', placeholder = '') => `
    <input type="${type}" id="${id}" value="${val}" placeholder="${placeholder}"
        style="width:100%;padding:10px 13px;border:1.5px solid ${C.border};border-radius:9px;
            font-size:13.5px;color:${C.text};background:${C.white};outline:none;box-sizing:border-box;
            transition:border-color .18s,box-shadow .18s;"
        onfocus="this.style.borderColor='${C.primary}';this.style.boxShadow='0 0 0 3px ${C.primary}18'"
        onblur="this.style.borderColor='${C.border}';this.style.boxShadow='none'">`;

function orgCheckbox(id, label, checked = false) {
    return `<label style="display:flex;align-items:center;gap:10px;cursor:pointer;
            font-size:13px;font-weight:600;color:${C.text};padding:10px 13px;
            border:1.5px solid ${C.border};border-radius:9px;margin-bottom:16px;
            transition:border-color .15s,background .15s;"
            onmouseover="this.style.borderColor='${C.primary}';this.style.background='#f0f4ff'"
            onmouseout="this.style.borderColor='${C.border}';this.style.background=''">
        <input type="checkbox" id="${id}" ${checked?'checked':''} style="width:16px;height:16px;accent-color:${C.primary};cursor:pointer;">
        ${label}</label>`;
}

function orgFooterBtns(cancelId, confirmFn, confirmLabel = 'Save', icon = 'fas fa-check') {
    return `<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:22px;
            padding-top:16px;border-top:1px solid ${C.border};">
        <button onclick="orgCloseModal('${cancelId}')"
            style="padding:9px 20px;border:1.5px solid ${C.border};border-radius:9px;
                background:${C.white};cursor:pointer;font-size:13px;font-weight:600;color:${C.muted};
                transition:border-color .15s,color .15s;"
            onmouseover="this.style.borderColor='${C.text}';this.style.color='${C.text}'"
            onmouseout="this.style.borderColor='${C.border}';this.style.color='${C.muted}'">Cancel</button>
        <button onclick="${confirmFn}"
            style="padding:9px 20px;border:none;border-radius:9px;background:${GRAD};
                color:#fff;cursor:pointer;font-size:13px;font-weight:700;
                display:flex;align-items:center;gap:7px;
                box-shadow:0 4px 14px rgba(78,115,223,.3);transition:transform .15s,box-shadow .15s;"
            onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 8px 20px rgba(78,115,223,.4)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(78,115,223,.3)'">
            <i class="${icon}"></i> ${confirmLabel}</button>
    </div>`;
}

// ===== CREATE ORG =====
window.openCreateOrgModal = function () {
    orgOpenModal('createOrgModal', `
        ${orgModalHeader('Create Organization', 'createOrgModal', 'fas fa-plus')}
        ${orgFormGroup('Organization Name *', orgInput('orgName', 'text', '', 'e.g. TechCorp Solutions'))}
        ${orgFormGroup('Slug *', orgInput('orgSlug', 'text', '', 'e.g. techcorp'))}
        ${orgCheckbox('orgActive', 'Active', true)}
        ${orgFooterBtns('createOrgModal', 'createOrganization()', 'Create', 'fas fa-plus')}`);
};

window.createOrganization = async function () {
    const name = document.getElementById('orgName').value.trim();
    const slug = document.getElementById('orgSlug').value.trim();
    const active = document.getElementById('orgActive').checked;
    if (!name || !slug) { showToast('Please fill all required fields', 'danger'); return; }
    try {
        showLoading();
        await apiCreateOrganization({ name, slug, active });
        orgCloseModal('createOrgModal');
        showToast('Organization created successfully');
        renderOrganizations();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== EDIT ORG =====
window.editOrganization = async function (id) {
    showLoading();
    let org;
    try { org = await apiFetchOrgDetail(id); }
    catch (e) { showToast('Failed to load organization', 'danger'); return; }
    finally { hideLoading(); }

    orgOpenModal('editOrgModal', `
        ${orgModalHeader('Edit Organization', 'editOrgModal', 'fas fa-pen')}
        <input type="hidden" id="editOrgId" value="${org.id}">
        ${orgFormGroup('Organization Name *', orgInput('editOrgName', 'text', org.name))}
        ${orgFormGroup('Slug *', orgInput('editOrgSlug', 'text', org.slug))}
        ${orgCheckbox('editOrgActive', 'Active', org.active)}
        ${orgFooterBtns('editOrgModal', 'updateOrganization()', 'Save Changes', 'fas fa-floppy-disk')}`);
};

window.updateOrganization = async function () {
    const id = document.getElementById('editOrgId').value;
    const name = document.getElementById('editOrgName').value.trim();
    const slug = document.getElementById('editOrgSlug').value.trim();
    const active = document.getElementById('editOrgActive').checked;
    if (!name || !slug) { showToast('Please fill all required fields', 'danger'); return; }
    try {
        showLoading();
        await apiUpdateOrganization(id, { name, slug, active });
        orgCloseModal('editOrgModal');
        showToast('Organization updated successfully');
        renderOrganizations();
    } catch (err) { showToast('Error: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== TOGGLE STATUS =====
window.toggleOrgStatus = function (id, currentActive) {
    if (!confirm(`${currentActive ? 'Disable' : 'Enable'} this organization?`)) return;
    apiUpdateOrganization(id, { active: !currentActive })
        .then(() => { showToast(`Organization ${currentActive ? 'disabled' : 'enabled'}`); renderOrganizations(); })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== DELETE ORG =====
window.deleteOrganization = function (id, name) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    apiDeleteOrganization(id)
        .then(() => { showToast('Organization deleted'); renderOrganizations(); })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
};

// ===== VIEW ORG =====
window.viewOrganization = async function (orgId) {
    showLoading();
    let org, admins;
    try {
        [org, admins] = await Promise.all([apiFetchOrgDetail(orgId), apiFetchOrgAdmins(orgId)]);
    } catch (e) { showToast('Failed to load data', 'danger'); return; }
    finally { hideLoading(); }

    const adminRows = admins.length
        ? admins.map(a => `
            <tr onmouseover="this.style.background='${C.bg}'" onmouseout="this.style.background=''">
                <td ${TD}>
                    <div style="display:flex;align-items:center;gap:9px;">
                        ${avatar(a.username[0].toUpperCase(), 30, 8)}
                        <strong style="font-size:13px;">${a.username}</strong>
                    </div>
                </td>
                <td ${TD}>${badge(a.superadmin ? 'Yes' : 'No', a.superadmin ? 'super' : 'normal')}</td>
                <td ${TD}>${badge(a.locked ? 'Locked' : 'Active', a.locked ? 'inactive' : 'active')}</td>
                <td ${TD} style="text-align:center;">
                    <span style="display:inline-flex;align-items:center;justify-content:center;
                        width:24px;height:24px;border-radius:50%;font-size:11px;font-weight:700;
                        background:${(a.failed_attempts??0)>3?'#fee2e2':'#f3f4f6'};
                        color:${(a.failed_attempts??0)>3?'#dc2626':C.muted};">
                        ${a.failed_attempts ?? 0}</span>
                </td>
                <td ${TD}>${iconBtn('fas fa-unlink','Remove from org',`removeAdminFromOrg(${a.id},${orgId})`,'danger')}</td>
            </tr>`).join('')
        : `<tr><td colspan="5" style="text-align:center;padding:2.5rem;color:${C.muted};font-size:13px;">
                <i class="fas fa-user-slash" style="font-size:2rem;opacity:.15;display:block;margin-bottom:8px;"></i>
                No admins in this organization</td></tr>`;

    orgOpenModal('viewOrgModal', `
        ${orgModalHeader(org.name, 'viewOrgModal', 'fas fa-building')}

        <!-- Info grid -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;
            background:${C.bg};border-radius:12px;padding:16px;
            border:1px solid ${C.border};margin-bottom:20px;">
            ${[
                ['Name',    `<strong style="font-size:13.5px;color:${C.text};">${org.name}</strong>`],
                ['Slug',    `<code style="background:#e2e8f0;padding:2px 8px;border-radius:5px;font-size:11.5px;color:${C.muted};">${org.slug}</code>`],
                ['Status',  badge(org.active ? 'Active' : 'Inactive', org.active ? 'active' : 'inactive')],
                ['Created', `<span style="font-size:12.5px;color:${C.muted};">${formatDate(org.created_at)}</span>`],
            ].map(([k,v]) => `<div>
                <div style="font-size:10px;font-weight:700;color:${C.muted};text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px;">${k}</div>
                ${v}</div>`).join('')}
        </div>

        <!-- Admins section header -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:700;color:${C.text};display:flex;align-items:center;gap:8px;">
                <i class="fas fa-users" style="color:${C.primary};"></i>
                Admins
                <span style="background:${C.primary}15;color:${C.primary};
                    border-radius:20px;padding:1px 9px;font-size:11px;font-weight:700;">${admins.length}</span>
            </div>
            <button onclick="openAttachAdminModal(${orgId})"
                style="display:inline-flex;align-items:center;gap:6px;
                    padding:7px 14px;border:none;border-radius:8px;background:${GRAD};
                    color:#fff;font-size:12px;font-weight:700;cursor:pointer;
                    box-shadow:0 3px 10px rgba(78,115,223,.3);transition:transform .15s;"
                onmouseover="this.style.transform='translateY(-1px)'"
                onmouseout="this.style.transform=''">
                <i class="fas fa-user-plus"></i> Admin qo'shish
            </button>
        </div>

        <!-- Admins table -->
        <div style="border-radius:10px;border:1px solid ${C.border};overflow:hidden;">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="background:${C.bg};">
                    <th ${TH}>Username</th>
                    <th ${TH}>Super Admin</th>
                    <th ${TH}>Status</th>
                    <th ${TH} style="padding:11px 16px;text-align:center;">Failed</th>
                    <th ${TH}>Actions</th>
                </tr></thead>
                <tbody>${adminRows}</tbody>
            </table>
        </div>
    `, true);
};

// ===== ATTACH ADMIN =====
window.openAttachAdminModal = async function (orgId) {
    showLoading();
    let allAdmins = [];
    try { allAdmins = await apiFetchAllAdmins(); }
    catch (e) { showToast('Could not load admins', 'danger'); return; }
    finally { hideLoading(); }

    const orgAdmins   = await apiFetchOrgAdmins(orgId).catch(() => []);
    const attachedIds = new Set(orgAdmins.map(a => a.id));
    const available   = allAdmins.filter(a => !attachedIds.has(a.id));

    const listHtml = available.length
        ? available.map(a => {
            const orgsStr = Array.isArray(a.organization) && a.organization.length
                ? a.organization.join(', ') : 'Biriktirilmagan';
            return `
            <div onclick="selectAdminToAttach(this, ${a.id})"
                style="display:flex;align-items:center;gap:11px;padding:10px 13px;
                    border:1.5px solid ${C.border};border-radius:10px;cursor:pointer;
                    margin-bottom:7px;transition:border-color .15s,background .15s;"
                onmouseover="if(!this.dataset.selected){this.style.borderColor='${C.primary}';this.style.background='#f0f4ff'}"
                onmouseout="if(!this.dataset.selected){this.style.borderColor='${C.border}';this.style.background=''}">
                ${avatar(a.username[0].toUpperCase(), 36, 9)}
                <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:700;color:${C.text};">${a.username}</div>
                    <div style="font-size:11px;color:${C.muted};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        ${a.superadmin ? '⭐ Super Admin' : '👤 Admin'} · ${orgsStr}
                    </div>
                </div>
                <i class="fas fa-circle-check" data-check style="color:${C.primary};font-size:16px;display:none;flex-shrink:0;"></i>
            </div>`;
        }).join('')
        : `<div style="text-align:center;color:${C.muted};padding:2rem;font-size:13px;">
            <i class="fas fa-users-slash" style="font-size:1.8rem;opacity:.15;display:block;margin-bottom:8px;"></i>
            Barcha adminlar allaqachon bu tashkilotda</div>`;

    orgOpenModal('attachAdminModal', `
        ${orgModalHeader("Admin qo'shish", 'attachAdminModal', 'fas fa-user-plus')}
        <input type="hidden" id="attachTargetOrgId" value="${orgId}">
        <input type="hidden" id="selectedAdminId" value="">

        <!-- Tabs -->
        <div style="display:flex;border-bottom:2px solid ${C.border};margin-bottom:18px;">
            <button id="tabExisting" onclick="switchAttachTab('existing')"
                style="padding:8px 16px;border:none;background:none;cursor:pointer;
                    font-size:12.5px;font-weight:700;color:${C.primary};
                    border-bottom:2.5px solid ${C.primary};margin-bottom:-2px;transition:color .15s;">
                <i class="fas fa-users" style="margin-right:5px;"></i>Mavjuddan tanlash
            </button>
            <button id="tabNew" onclick="switchAttachTab('new')"
                style="padding:8px 16px;border:none;background:none;cursor:pointer;
                    font-size:12.5px;font-weight:700;color:${C.muted};
                    border-bottom:2.5px solid transparent;margin-bottom:-2px;transition:color .15s;">
                <i class="fas fa-user-plus" style="margin-right:5px;"></i>Yangi yaratish
            </button>
        </div>

        <!-- Pane: Existing -->
        <div id="paneExisting">
            <div style="max-height:290px;overflow-y:auto;padding-right:2px;">${listHtml}</div>
            ${orgFooterBtns('attachAdminModal', 'confirmAttachAdmin()', 'Biriktirish', 'fas fa-link')}
        </div>

        <!-- Pane: New -->
        <div id="paneNew" style="display:none;">
            ${orgFormGroup('Username *', orgInput('newAdminUsername', 'text', '', 'e.g. john.doe'))}
            ${orgFormGroup('Password *', orgInput('newAdminPassword', 'password', '', '••••••••'))}
            ${orgCheckbox('newAdminSuper', '⭐ Super Admin', false)}
            ${orgFooterBtns('attachAdminModal', 'createAndAttachAdmin()', 'Yaratish va biriktirish', 'fas fa-user-plus')}
        </div>
    `);
};

window.switchAttachTab = function (tab) {
    const isEx = tab === 'existing';
    document.getElementById('paneExisting').style.display = isEx ? '' : 'none';
    document.getElementById('paneNew').style.display      = isEx ? 'none' : '';
    const tE = document.getElementById('tabExisting');
    const tN = document.getElementById('tabNew');
    tE.style.color             = isEx ? C.primary : C.muted;
    tE.style.borderBottomColor = isEx ? C.primary : 'transparent';
    tN.style.color             = isEx ? C.muted   : C.primary;
    tN.style.borderBottomColor = isEx ? 'transparent' : C.primary;
};

window.selectAdminToAttach = function (el, adminId) {
    document.querySelectorAll('#attachAdminModal [data-selected]').forEach(item => {
        delete item.dataset.selected;
        item.style.borderColor = C.border;
        item.style.background  = '';
        const ic = item.querySelector('[data-check]');
        if (ic) ic.style.display = 'none';
    });
    el.dataset.selected  = '1';
    el.style.borderColor = C.primary;
    el.style.background  = '#f0f4ff';
    const ic = el.querySelector('[data-check]');
    if (ic) ic.style.display = '';
    document.getElementById('selectedAdminId').value = adminId;
};

window.confirmAttachAdmin = async function () {
    const adminId = document.getElementById('selectedAdminId')?.value;
    const orgId   = document.getElementById('attachTargetOrgId')?.value;
    if (!adminId) { showToast('Admin tanlang', 'danger'); return; }
    try {
        showLoading();
        await apiAttachAdminToOrg(parseInt(adminId), parseInt(orgId));
        orgCloseModal('attachAdminModal');
        showToast('Admin tashkilotga biriktirildi');
        viewOrganization(parseInt(orgId));
    } catch (err) { showToast('Xato: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

window.createAndAttachAdmin = async function () {
    const orgId    = document.getElementById('attachTargetOrgId')?.value;
    const username = document.getElementById('newAdminUsername')?.value.trim();
    const password = document.getElementById('newAdminPassword')?.value;
    const isSup    = document.getElementById('newAdminSuper')?.checked;
    if (!username || !password) { showToast('Username va password kiriting', 'danger'); return; }
    try {
        showLoading();
        await apiCreateAdmin({ username, password, organization_id: parseInt(orgId), is_superuser: isSup });
        orgCloseModal('attachAdminModal');
        showToast('Admin yaratildi va biriktirildi');
        viewOrganization(parseInt(orgId));
    } catch (err) { showToast('Xato: ' + err.message, 'danger'); }
    finally { hideLoading(); }
};

// ===== REMOVE ADMIN FROM ORG =====
window.removeAdminFromOrg = function (adminId, orgId) {
    if (!confirm('Bu adminni tashkilotdan chiqarishni xohlaysizmi?')) return;
    apiDeleteAdminOrg(adminId, orgId)
        .then(() => { showToast('Admin tashkilotdan chiqarildi'); viewOrganization(orgId); })
        .catch(err => showToast('Xato: ' + err.message, 'danger'));
};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    renderOrganizations();
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', e => { e.preventDefault(); logout(); });
});