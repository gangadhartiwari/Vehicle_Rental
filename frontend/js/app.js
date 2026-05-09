/* =========================================================================
   ROADWAY — API client + helpers
   ========================================================================= */

const CONFIG = {
  // Set the API base. Defaults to localhost:8000 — change as needed.
  API_BASE: localStorage.getItem('rw_api_base') || 'http://localhost:8000',
  API_PREFIX: '/api/v1',
};

const Auth = {
  get accessToken() { return localStorage.getItem('rw_access_token'); },
  get refreshToken() { return localStorage.getItem('rw_refresh_token'); },
  get role() { return localStorage.getItem('rw_role'); },
  get userId() { return localStorage.getItem('rw_user_id'); },
  set(tokens, role, userId) {
    localStorage.setItem('rw_access_token', tokens.access_token);
    localStorage.setItem('rw_refresh_token', tokens.refresh_token);
    localStorage.setItem('rw_role', role);
    localStorage.setItem('rw_user_id', userId);
  },
  clear() {
    ['rw_access_token','rw_refresh_token','rw_role','rw_user_id'].forEach(k => localStorage.removeItem(k));
  },
  isLoggedIn() { return !!this.accessToken; },
  redirectIfNotRole(role, fallback = '../index.html') {
    if (!this.isLoggedIn() || this.role !== role) {
      window.location.href = fallback;
    }
  },
};

async function api(path, { method = 'GET', body, query, headers = {}, raw = false, isForm = false } = {}) {
  const url = new URL(CONFIG.API_BASE + CONFIG.API_PREFIX + path);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.append(k, v);
    });
  }
  const opts = { method, headers: { ...headers } };
  if (Auth.accessToken) opts.headers.Authorization = `Bearer ${Auth.accessToken}`;
  if (body && !isForm) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body && isForm) {
    opts.body = body; // FormData
  }

  const res = await fetch(url, opts);
  if (raw) return res;

  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }

  if (!res.ok) {
    const err = new Error((data && (data.detail || data.message)) || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

/* ---------------------------- TOAST ---------------------------- */
function toast(message, type = 'default', timeout = 3500) {
  let host = document.querySelector('.toast-host');
  if (!host) {
    host = document.createElement('div');
    host.className = 'toast-host';
    document.body.appendChild(host);
  }
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  host.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 200); }, timeout);
}

/* ---------------------------- MODAL ---------------------------- */
function modal({ title, body, footer, onClose }) {
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
    <div class="modal" role="dialog">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="btn btn-ghost btn-sm" data-modal-close>✕</button>
      </div>
      <div class="modal-body">${body}</div>
      ${footer ? `<div class="modal-footer mt-6 flex gap-3" style="justify-content:flex-end">${footer}</div>` : ''}
    </div>
  `;
  document.body.appendChild(backdrop);
  const close = () => { backdrop.remove(); onClose && onClose(); };
  backdrop.addEventListener('click', e => { if (e.target === backdrop) close(); });
  backdrop.querySelector('[data-modal-close]').onclick = close;
  return { el: backdrop, close };
}

function confirmModal(message, { title = 'Confirm', confirmText = 'Confirm', danger = false } = {}) {
  return new Promise(resolve => {
    const m = modal({
      title,
      body: `<p class="muted">${message}</p>`,
      footer: `
        <button class="btn btn-secondary" data-cancel>Cancel</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-ok>${confirmText}</button>
      `,
    });
    m.el.querySelector('[data-cancel]').onclick = () => { m.close(); resolve(false); };
    m.el.querySelector('[data-ok]').onclick = () => { m.close(); resolve(true); };
  });
}

/* ---------------------------- FORMATTING ---------------------------- */
function fmtMoney(n, currency = 'INR') {
  if (n === null || n === undefined) return '—';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(n);
}

function fmtDate(d) {
  if (!d) return '—';
  const date = new Date(d);
  return date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function fmtDateShort(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function timeAgo(d) {
  if (!d) return '—';
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  if (diff < 2592000) return `${Math.floor(diff/86400)}d ago`;
  return fmtDateShort(d);
}

function statusBadge(status) {
  const map = {
    AVAILABLE: 'success', BOOKED: 'info', INACTIVE: 'neutral', UNDER_MAINTENANCE: 'warn',
    PENDING: 'neutral', SUBMITTED: 'info', APPROVED: 'success', REJECTED: 'danger',
    PENDING_PAYMENT: 'warn', CONFIRMED: 'info', ONGOING: 'accent', COMPLETED: 'success', CANCELLED: 'danger',
    PAID: 'success', UNPAID: 'warn', REFUNDED: 'neutral', FAILED: 'danger',
  };
  const cls = map[status] || 'neutral';
  return `<span class="badge badge-${cls}">${status.replace(/_/g,' ').toLowerCase()}</span>`;
}

function starsHtml(n) {
  const v = Math.round(n || 0);
  return `<span class="stars">${'★'.repeat(v)}${'☆'.repeat(5 - v)}</span>`;
}

function vehicleImageUrl(v) {
  if (!v.images) return null;
  const first = v.images.split(',')[0]?.trim();
  if (!first) return null;
  if (first.startsWith('http')) return first;
  return `${CONFIG.API_BASE}/${first.replace(/^\/+/,'')}`;
}

function vehicleIcon(type) {
  return { BIKE: '🏍️', CAR: '🚗', AUTO: '🛺' }[type] || '🚗';
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function setLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Loading…';
  } else {
    btn.disabled = false;
    if (btn.dataset.originalText) btn.innerHTML = btn.dataset.originalText;
  }
}

/* ---------------------------- NAV BUILDERS ---------------------------- */
function renderTopNav(active = '') {
  const isLoggedIn = Auth.isLoggedIn();
  const role = Auth.role;
  const dashHref = role === 'partner' ? 'pages/partner-dashboard.html'
    : role === 'admin' ? 'pages/admin-dashboard.html'
    : 'pages/user-dashboard.html';
  return `
    <nav class="navbar">
      <div class="container nav-inner">
        <a href="index.html" class="brand">
          <span class="brand-mark">R</span>
          <span>Roadway</span>
        </a>
        <ul class="nav-links">
          <li><a href="index.html" ${active==='home'?'style="color:var(--accent)"':''}>Home</a></li>
          <li><a href="pages/browse.html" ${active==='browse'?'style="color:var(--accent)"':''}>Browse</a></li>
          <li><a href="index.html#how">How it works</a></li>
          <li><a href="pages/partner-onboard.html">Become a partner</a></li>
        </ul>
        <div class="nav-actions">
          ${isLoggedIn
            ? `<a class="btn btn-ghost btn-sm" href="${active.startsWith('dash')?'#':dashHref}">Dashboard</a>
               <button class="btn btn-secondary btn-sm" onclick="logout()">Sign out</button>`
            : `<a class="btn btn-ghost btn-sm" href="pages/login.html?role=partner">Partner</a>
               <a class="btn btn-ghost btn-sm" href="pages/login.html?role=admin">Admin</a>
               <a class="btn btn-primary btn-sm" href="pages/login.html?role=user">Sign in</a>`}
        </div>
      </div>
    </nav>
  `;
}

function logout() {
  Auth.clear();
  toast('Signed out');
  setTimeout(() => { window.location.href = '/index.html'.replace(/^\//, '') || 'index.html'; }, 400);
}

/* Allow logout from anywhere */
window.logout = logout;
window.api = api;
window.Auth = Auth;
window.CONFIG = CONFIG;
