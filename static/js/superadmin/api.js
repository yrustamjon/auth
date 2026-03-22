// ============================================================
// api.js — Shared utilities for all superadmin pages
// ============================================================

const API_BASE_URL = 'https://sibilantly-penanceless-young.ngrok-free.dev';

// ===== CSRF =====
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        for (let cookie of document.cookie.split(';')) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== AUTH FETCH =====
async function fetchWithAuth(url, options = {}) {
    const fetchOptions = {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    const response = await fetch(`${API_BASE_URL}${url}`, fetchOptions);

    if (response.status === 401) {
        sessionStorage.removeItem('isAuthenticated');
        localStorage.removeItem('isAuthenticated');
        window.location.href = '/system/login/';
        throw new Error('Session expired. Please login again.');
    }

    return response;
}

// ===== LOADING SPINNER =====
function showLoading() {
    let el = document.getElementById('globalSpinner');
    if (!el) {
        el = document.createElement('div');
        el.id = 'globalSpinner';
        el.style.cssText = `
            position:fixed;inset:0;background:rgba(24,24,27,.3);
            display:flex;align-items:center;justify-content:center;z-index:9999;
        `;
        el.innerHTML = `<div style="
            width:38px;height:38px;border-radius:50%;
            border:3px solid #e4e4e7;border-top-color:#6366f1;
            animation:_spin .65s linear infinite;
        "></div>`;
        const style = document.createElement('style');
        style.textContent = '@keyframes _spin{to{transform:rotate(360deg)}}';
        document.head.appendChild(style);
        document.body.appendChild(el);
    }
    el.style.display = 'flex';
}

function hideLoading() {
    const el = document.getElementById('globalSpinner');
    if (el) el.style.display = 'none';
}

// ===== TOAST =====
function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;
            display:flex;flex-direction:column;gap:.45rem;
        `;
        const style = document.createElement('style');
        style.textContent = `
            @keyframes _toastIn {
                from { opacity:0; transform:translateX(16px); }
                to   { opacity:1; transform:translateX(0); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(container);
    }

    const colors = { success:'#10b981', danger:'#f43f5e', warning:'#f59e0b', info:'#6366f1' };
    const icons  = { success:'fa-check-circle', danger:'fa-exclamation-circle', warning:'fa-triangle-exclamation', info:'fa-info-circle' };
    const color  = colors[type] || colors.info;
    const icon   = icons[type]  || icons.info;

    const el = document.createElement('div');
    el.style.cssText = `
        background:#fff;border-radius:10px;padding:.7rem 1rem;
        box-shadow:0 8px 28px rgba(0,0,0,.12);
        border-left:4px solid ${color};
        display:flex;align-items:center;gap:.6rem;
        font-size:.87rem;min-width:230px;max-width:320px;
        animation:_toastIn .22s ease;
    `;
    el.innerHTML = `
        <i class="fas ${icon}" style="color:${color};font-size:.95rem;flex-shrink:0;"></i>
        <span style="flex:1;color:#18181b;">${message}</span>
        <button onclick="this.parentElement.remove()"
            style="background:none;border:none;cursor:pointer;color:#a1a1aa;font-size:1.1rem;padding:0;line-height:1;">×</button>
    `;
    container.appendChild(el);
    setTimeout(() => el.remove(), 3500);
}

// ===== CONFIRM MODAL =====
function showConfirmation(title, message, onConfirm, dangerBtn = true) {
    const existing = document.getElementById('_confirmOverlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = '_confirmOverlay';
    overlay.style.cssText = `
        position:fixed;inset:0;background:rgba(24,24,27,.5);
        z-index:9998;display:flex;align-items:center;justify-content:center;padding:1rem;
    `;

    const btnColor = dangerBtn
        ? 'background:linear-gradient(135deg,#f43f5e,#e11d48);color:#fff;'
        : 'background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;';

    overlay.innerHTML = `
        <div style="background:#fff;border-radius:14px;padding:2rem;max-width:400px;width:100%;
                    box-shadow:0 20px 60px rgba(0,0,0,.18);animation:_toastIn .2s ease;">
            <h4 style="font-size:1rem;font-weight:700;color:#18181b;margin:0 0 .5rem;">${title}</h4>
            <p style="color:#71717a;font-size:.88rem;margin:0 0 1.5rem;">${message}</p>
            <div style="display:flex;gap:.75rem;justify-content:flex-end;">
                <button id="_confirmCancel" style="
                    padding:.48rem 1.1rem;border:1.5px solid #e4e4e7;
                    border-radius:7px;background:#fff;cursor:pointer;
                    font-size:.86rem;font-weight:600;color:#18181b;">
                    Cancel
                </button>
                <button id="_confirmOk" style="
                    padding:.48rem 1.1rem;border:none;border-radius:7px;
                    ${btnColor}cursor:pointer;font-size:.86rem;font-weight:600;">
                    Confirm
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    overlay.querySelector('#_confirmCancel').onclick = () => overlay.remove();
    overlay.querySelector('#_confirmOk').onclick = () => { overlay.remove(); onConfirm(); };
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
}

// ===== MODAL HELPERS =====
function openModal(id, html) {
    let overlay = document.getElementById(id);
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = id;
        overlay.style.cssText = `
            position:fixed;inset:0;background:rgba(24,24,27,.5);
            z-index:2000;display:flex;align-items:center;justify-content:center;padding:1rem;
        `;
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
        <div style="background:#fff;border-radius:16px;padding:2rem;width:100%;
                    max-width:480px;max-height:90vh;overflow-y:auto;
                    box-shadow:0 20px 60px rgba(0,0,0,.16);animation:_toastIn .2s ease;">
            ${html}
        </div>
    `;
    overlay.style.display = 'flex';
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(id); });
    return overlay;
}

function openModalWide(id, html) {
    let overlay = document.getElementById(id);
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = id;
        overlay.style.cssText = `
            position:fixed;inset:0;background:rgba(24,24,27,.5);
            z-index:2000;display:flex;align-items:center;justify-content:center;padding:1rem;
        `;
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
        <div style="background:#fff;border-radius:16px;padding:2rem;width:100%;
                    max-width:720px;max-height:90vh;overflow-y:auto;
                    box-shadow:0 20px 60px rgba(0,0,0,.16);animation:_toastIn .2s ease;">
            ${html}
        </div>
    `;
    overlay.style.display = 'flex';
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(id); });
    return overlay;
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

// ===== FORM BUILDER HELPERS =====
function modalHeader(title, modalId) {
    return `
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:1.4rem;padding-bottom:1rem;border-bottom:1px solid #e4e4e7;">
            <h3 style="font-size:1rem;font-weight:700;color:#18181b;margin:0;">${title}</h3>
            <button onclick="closeModal('${modalId}')"
                style="background:none;border:none;font-size:1.4rem;cursor:pointer;
                       color:#a1a1aa;line-height:1;padding:0 .2rem;">×</button>
        </div>
    `;
}

function formGroup(label, inputHtml) {
    return `
        <div style="margin-bottom:1rem;">
            <label style="display:block;font-size:.81rem;font-weight:600;
                          color:#18181b;margin-bottom:.35rem;">${label}</label>
            ${inputHtml}
        </div>
    `;
}

const inputCls = `style="width:100%;padding:.6rem .85rem;border:1.5px solid #e4e4e7;
    border-radius:7px;font-size:.88rem;color:#18181b;background:#fff;outline:none;
    transition:border-color .18s;"
    onfocus="this.style.borderColor='#6366f1'"
    onblur="this.style.borderColor='#e4e4e7'"`;

// ===== FORMAT DATE =====
function formatDate(dateString) {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
    });
}

// ===== SYSTEM LOGOUT =====
async function System_Logout() {
    try {
        await fetchWithAuth('/api/system/logout', {
            method: 'POST',
            credentials: 'include',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
    } catch (e) {
        console.error('Logout error:', e);
    }
    sessionStorage.removeItem('isAuthenticated');
    localStorage.removeItem('isAuthenticated');
}

async function logout() {
    showConfirmation('Logout', 'Are you sure you want to logout?', async () => {
        await System_Logout();
        console.log('Logged out successfully');
        showToast('Logged out successfully');
        setTimeout(() => window.location.href = '/system/login/', 800);
    });
}