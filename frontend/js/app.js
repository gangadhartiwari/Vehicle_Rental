/* =========================================================================
   ROADWAY — API client + helpers (mobile-first)
   ========================================================================= */

const CONFIG = {
  API_BASE: localStorage.getItem('rw_api_base') || 'http://localhost:8000',
  API_PREFIX: '/api/v1',
};

/* Detect path depth so a single nav module works from /index.html and /pages/* */
function pathPrefix() {
  // Pages live in /pages/*. Anything else is at root.
  return location.pathname.includes('/pages/') ? '../' : '';
}

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
    ['rw_access_token', 'rw_refresh_token', 'rw_role', 'rw_user_id'].forEach(k => localStorage.removeItem(k));
  },
  isLoggedIn() { return !!this.accessToken; },
  redirectIfNotRole(role, fallback) {
    fallback = fallback || (pathPrefix() + 'pages/login.html?role=' + role);
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
        <button class="icon-btn" data-modal-close aria-label="Close">✕</button>
      </div>
      <div class="modal-body">${body}</div>
      ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
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
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`;
  return fmtDateShort(d);
}

function statusBadge(status) {
  if (!status) return '';
  const map = {
    AVAILABLE: 'success', BOOKED: 'info', INACTIVE: 'neutral', UNDER_MAINTENANCE: 'warn',
    PENDING: 'neutral', SUBMITTED: 'info', APPROVED: 'success', REJECTED: 'danger',
    PENDING_PAYMENT: 'warn', CONFIRMED: 'info', ONGOING: 'accent', COMPLETED: 'success', CANCELLED: 'danger',
    PAID: 'success', UNPAID: 'warn', REFUNDED: 'neutral', FAILED: 'danger',
  };
  const cls = map[status] || 'neutral';
  return `<span class="badge badge-${cls}">${status.replace(/_/g, ' ').toLowerCase()}</span>`;
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
  return `${CONFIG.API_BASE}/${first.replace(/^\/+/, '')}`;
}

function vehicleIcon(type) {
  return { BIKE: '🏍️', CAR: '🚗', AUTO: '🛺' }[type] || '🚗';
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
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

/* ---------------------------- TOP BAR ---------------------------- */
function renderTopBar(active = '') {
  const p = pathPrefix();
  const isLoggedIn = Auth.isLoggedIn();
  const role = Auth.role;
  const dashHref = role === 'partner' ? p + 'pages/partner-dashboard.html'
    : role === 'admin' ? p + 'pages/admin-dashboard.html'
      : p + 'pages/user-dashboard.html';

  return `
    <header class="topbar">
      <div class="container topbar-inner">
        <a href="${p}index.html" class="brand">
          <span class="brand-mark">R</span>
          <span>Roadway</span>
        </a>
        <ul class="nav-links">
          <li><a href="${p}index.html" class="${active === 'home' ? 'active' : ''}">Home</a></li>
          <li><a href="${p}pages/browse.html" class="${active === 'browse' ? 'active' : ''}">Browse</a></li>
          <li><a href="${p}pages/partner-onboard.html" class="${active === 'partners' ? 'active' : ''}">Partner</a></li>
        </ul>
        <div class="nav-actions">
          ${isLoggedIn
      ? `<a class="btn btn-secondary btn-sm" href="${dashHref}">Dashboard</a>
                 <button class="icon-btn" onclick="logout()" title="Sign out" aria-label="Sign out">⎋</button>`
      : `<a class="btn btn-primary btn-sm" href="${p}pages/login.html?role=user">Sign in</a>`}
        </div>
      </div>
    </header>
  `;
}

/* ---------------------------- BOTTOM NAV (MOBILE) ---------------------------- */
function renderBottomNav(active = '') {
  const p = pathPrefix();
  const role = Auth.role;
  const isLoggedIn = Auth.isLoggedIn();

  const dashHref = role === 'partner' ? p + 'pages/partner-dashboard.html'
    : role === 'admin' ? p + 'pages/admin-dashboard.html'
      : p + 'pages/user-dashboard.html';

  const dashLabel = role === 'partner' ? 'Fleet' : role === 'admin' ? 'Admin' : 'Trips';

  return `
    <nav class="bottom-nav">
      <a href="${p}index.html" class="${active === 'home' ? 'active' : ''}">
        <span class="icon">🏠</span><span>Home</span>
      </a>
      <a href="${p}pages/browse.html" class="${active === 'browse' ? 'active' : ''}">
        <span class="icon">🔎</span><span>Browse</span>
      </a>
      ${isLoggedIn ? `
        <a href="${dashHref}" class="${active === 'dash' ? 'active' : ''}">
          <span class="icon">📋</span><span>${dashLabel}</span>
        </a>
        <a href="#" onclick="logout(); return false;">
          <span class="icon">⎋</span><span>Sign out</span>
        </a>` : `
        <a href="${p}pages/partner-onboard.html" class="${active === 'partners' ? 'active' : ''}">
          <span class="icon">🤝</span><span>Partner</span>
        </a>
        <a href="${p}pages/login.html?role=user" class="${active === 'auth' ? 'active' : ''}">
          <span class="icon">👤</span><span>Sign in</span>
        </a>`}
    </nav>
  `;
}

/* Inject top bar + bottom nav on any page that calls this */
function mountChrome(active = '') {
  const navHost = document.getElementById('nav-host');
  if (navHost) navHost.innerHTML = renderTopBar(active);

  // Bottom nav on all main pages (not auth)
  if (document.body.classList.contains('has-bottom-nav')) {
    const existing = document.querySelector('.bottom-nav');
    if (existing) existing.remove();
    document.body.insertAdjacentHTML('beforeend', renderBottomNav(active));
  }
}

function logout() {
  Auth.clear();
  toast('Signed out');
  setTimeout(() => {
    window.location.href = pathPrefix() + 'index.html';
  }, 400);
}

/* Expose globals */
window.logout = logout;
window.api = api;
window.Auth = Auth;
window.CONFIG = CONFIG;
window.mountChrome = mountChrome;
window.renderTopBar = renderTopBar;
window.renderBottomNav = renderBottomNav;
window.pathPrefix = pathPrefix;
