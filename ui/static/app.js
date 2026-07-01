/* ============================
   B2C Leads Pro — Dashboard JS
   ============================ */

const API = '';
let currentPage = 'dashboard';
let selectedLocations = [];
let leadsPage = 1;
let pollTimer = null;

/* ---- NAVIGATION ---- */
function showPage(name, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  if (el) el.classList.add('active');
  currentPage = name;
  clearInterval(pollTimer);
  if (name === 'dashboard') { loadDashboard(); pollTimer = setInterval(loadDashboard, 6000); }
  if (name === 'jobs')      { loadJobs();      pollTimer = setInterval(loadJobs, 4000); }
  if (name === 'leads')     { loadLeads(1); }
  if (name === 'proxies')   { loadProxies(); }
}

/* ---- THEME ---- */
function toggleTheme() {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('theme-icon').innerHTML = next === 'dark'
    ? '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
    : '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
}

/* ---- HELPERS ---- */
async function api(path, opts = {}) {
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function statusBadge(s) {
  return `<span class="badge badge-${s}">${s}</span>`;
}

function progressBar(pct) {
  return `<div class="progress-wrap"><div class="progress-bar" style="width:${pct}%"></div></div>`;
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString(undefined, { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
}

function num(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString();
}

/* ---- DASHBOARD ---- */
async function loadDashboard() {
  try {
    const [leadsData, jobsData, proxiesData, queues] = await Promise.all([
      api('/api/leads/?page=1&page_size=1'),
      api('/api/jobs/'),
      api('/api/proxies/'),
      api('/api/queues/').catch(() => null),
    ]);

    document.getElementById('kpi-total-leads').textContent = num(leadsData.total);

    const vData = await api('/api/leads/?is_verified=true&page=1&page_size=1');
    document.getElementById('kpi-verified').textContent = num(vData.total);

    const running = jobsData.filter(j => j.status === 'running' || j.status === 'pending').length;
    document.getElementById('kpi-active-jobs').textContent = num(running);

    const active = proxiesData.filter(p => p.is_active).length;
    document.getElementById('kpi-proxies').textContent = num(active);

    if (queues && !queues.error) {
      document.getElementById('kpi-queue').textContent =
        `D:${queues.discovery} S:${queues.scrape} V:${queues.verify}`;
    }

    renderJobsTable(jobsData.slice(0, 10), 'dashboard-jobs-body', true);
  } catch(e) {
    console.error('Dashboard error:', e);
  }
}

/* ---- JOBS ---- */
async function loadJobs() {
  try {
    const jobs = await api('/api/jobs/');
    renderJobsTable(jobs, 'jobs-body', false);
  } catch(e) { console.error(e); }
}

function renderJobsTable(jobs, tbodyId, compact) {
  const tbody = document.getElementById(tbodyId);
  if (!jobs.length) {
    tbody.innerHTML = `<tr><td colspan="${compact?8:10}" class="empty">No jobs yet. Launch one from New Job.</td></tr>`;
    return;
  }
  tbody.innerHTML = jobs.map(j => {
    const locs   = (j.location_ids || []).join(', ');
    const niches = compact ? '' : `<td>${(j.niches || []).join(', ') || '—'}</td>`;
    const started  = compact ? '' : `<td>${fmtDate(j.started_at)}</td>`;
    const finished = compact ? '' : `<td>${fmtDate(j.finished_at)}</td>`;
    return `<tr>
      <td><span style="font-family:var(--font-mono);color:var(--color-text-muted)">#${j.id}</span></td>
      <td>${statusBadge(j.status)}</td>
      <td>${locs || '—'}</td>
      ${niches}
      <td>${progressBar(j.progress)}<span style="color:var(--color-text-muted);margin-left:4px">${j.progress}%</span></td>
      <td>${num(j.leads_found)}</td>
      <td>${num(j.pages_crawled)}</td>
      ${started}${finished}
      <td><button class="btn btn-sm btn-ghost" onclick="viewJobLeads(${j.id})">Leads</button></td>
    </tr>`;
  }).join('');
}

function viewJobLeads(jobId) {
  ['filter-country','filter-city','filter-niche','filter-min-score'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('filter-verified').value = '';
  currentJobFilter = jobId;
  showPage('leads', document.querySelector('[data-page="leads"]'));
  loadLeads(1, jobId);
}

/* ---- NEW JOB — LOCATION ---- */
let searchDebounce = null;

async function searchLocations() {
  const q = document.getElementById('location-search').value.trim();
  const dd = document.getElementById('location-dropdown');
  clearTimeout(searchDebounce);
  if (q.length < 2) { dd.classList.remove('open'); return; }
  searchDebounce = setTimeout(async () => {
    try {
      const results = await api(`/api/locations/search?q=${encodeURIComponent(q)}`);
      let html = results.map(r =>
        `<div class="dropdown-item" onclick="addLocation(${r.id},'${(r.city||r.country).replace(/'/g,"\\'")}','${r.country_code}')">${r.city ? r.city + ', ' : ''}${r.country} <span style="color:var(--color-text-faint)">${r.country_code}</span></div>`
      ).join('');
      // Always show a "create" option at the bottom
      html += `<div class="dropdown-item" style="border-top:1px solid var(--color-border);color:var(--color-primary)" onclick="createAndAddLocation('${q.replace(/'/g,"\\'")}')">
        ➕ Add "${q}" as new location
      </div>`;
      dd.innerHTML = html;
      dd.classList.add('open');
    } catch(e) { console.error(e); }
  }, 300);
}

// Allow pressing Enter to instantly create & add the typed location
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('location-search');
  if (input) {
    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const q = input.value.trim();
        if (q.length < 2) return;
        await createAndAddLocation(q);
      }
    });
  }
  loadDashboard();
  pollTimer = setInterval(loadDashboard, 6000);
});

async function createAndAddLocation(name) {
  try {
    // Try to create the location via API; if it already exists API should return it
    const loc = await api('/api/locations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: name, country: name, country_code: 'XX' }),
    });
    addLocation(loc.id, loc.city || loc.country, loc.country_code || 'XX');
  } catch(e) {
    // If POST fails, fall back to searching and picking first result
    try {
      const results = await api(`/api/locations/search?q=${encodeURIComponent(name)}`);
      if (results.length) {
        const r = results[0];
        addLocation(r.id, r.city || r.country, r.country_code);
      } else {
        alert('Could not add location: ' + name + '. The API may need a /api/locations/ POST endpoint.');
      }
    } catch(e2) { console.error(e2); }
  }
  document.getElementById('location-dropdown').classList.remove('open');
  document.getElementById('location-search').value = '';
}

function addLocation(id, city, cc) {
  if (selectedLocations.find(l => l.id === id)) return;
  selectedLocations.push({ id, city, cc });
  renderLocationTags();
  document.getElementById('location-dropdown').classList.remove('open');
  document.getElementById('location-search').value = '';
}

function removeLocation(id) {
  selectedLocations = selectedLocations.filter(l => l.id !== id);
  renderLocationTags();
}

function renderLocationTags() {
  document.getElementById('location-tags').innerHTML = selectedLocations.map(l =>
    `<span class="location-tag">${l.city} ${l.cc}<button onclick="removeLocation(${l.id})" title="Remove">×</button></span>`
  ).join('');
}

document.addEventListener('click', e => {
  if (!e.target.closest('.location-search-wrap'))
    document.getElementById('location-dropdown').classList.remove('open');
});

async function submitJob() {
  const msg = document.getElementById('job-submit-msg');
  if (!selectedLocations.length) {
    msg.textContent = 'Please add at least one location.';
    msg.className = 'form-msg error'; return;
  }
  const payload = {
    location_ids: selectedLocations.map(l => l.id),
    niches: document.getElementById('job-niches').value.split(',').map(s=>s.trim()).filter(Boolean),
    max_pages:   parseInt(document.getElementById('job-max-pages').value)   || 50,
    concurrency: parseInt(document.getElementById('job-concurrency').value) || 5,
  };
  try {
    const job = await api('/api/jobs/', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    msg.textContent = `✓ Job #${job.id} launched — discovery tasks queued!`;
    msg.className = 'form-msg';
    selectedLocations = []; renderLocationTags();
    setTimeout(() => showPage('jobs', document.querySelector('[data-page="jobs"]')), 1500);
  } catch(e) {
    msg.textContent = 'Error: ' + e.message;
    msg.className = 'form-msg error';
  }
}

/* ---- LEADS ---- */
let currentJobFilter = null;
async function loadLeads(page = 1, jobId = null) {
  leadsPage = page;
  if (jobId !== null) currentJobFilter = jobId;
  const params = new URLSearchParams({ page, page_size: 50 });
  const cc    = document.getElementById('filter-country').value.trim();
  const city  = document.getElementById('filter-city').value.trim();
  const niche = document.getElementById('filter-niche').value.trim();
  const ver   = document.getElementById('filter-verified').value;
  const score = document.getElementById('filter-min-score').value;
  if (cc)    params.set('country_code', cc.toUpperCase());
  if (city)  params.set('city', city);
  if (niche) params.set('niche', niche);
  if (ver)   params.set('is_verified', ver);
  if (score) params.set('min_score', score);
  if (currentJobFilter) params.set('job_id', currentJobFilter);

  try {
    const data = await api('/api/leads/?' + params.toString());
    const tbody = document.getElementById('leads-body');
    if (!data.results.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty">No leads found. Try adjusting filters or run a job first.</td></tr>';
    } else {
      tbody.innerHTML = data.results.map(l => `<tr>
        <td style="font-family:var(--font-mono);color:var(--color-primary)">${l.email}</td>
        <td>${l.full_name || '—'}</td>
        <td>${l.city || '—'}</td>
        <td>${l.country_code || '—'}</td>
        <td>${l.niche || '—'}</td>
        <td><strong>${l.score}</strong></td>
        <td>${l.is_verified
          ? '<span class="badge badge-verified">✓ Yes</span>'
          : '<span class="badge badge-unverified">— No</span>'}</td>
        <td style="color:var(--color-text-muted);font-size:.7rem">${l.source_domain || '—'}</td>
        <td><span style="color:var(--color-text-muted)">#${l.job_id || '—'}</span></td>
      </tr>`).join('');
    }
    renderPagination(data.total, page, 50);
  } catch(e) { console.error(e); }
}

function clearFilters() {
  ['filter-country','filter-city','filter-niche','filter-min-score'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('filter-verified').value = '';
  currentJobFilter = null;
  loadLeads(1);
}

function renderPagination(total, page, pageSize) {
  const pages = Math.ceil(total / pageSize);
  const wrap = document.getElementById('leads-pagination');
  if (pages <= 1) { wrap.innerHTML = ''; return; }
  let html = '';
  for (let i = 1; i <= Math.min(pages, 15); i++)
    html += `<button class="page-btn ${i===page?'active':''}" onclick="loadLeads(${i})">${i}</button>`;
  if (pages > 15) html += `<span style="color:var(--color-text-muted);font-size:var(--text-xs)">…${pages} pages</span>`;
  wrap.innerHTML = html;
}

function exportLeads() {
  const params = new URLSearchParams();
  const cc  = document.getElementById('filter-country').value.trim();
  const ver = document.getElementById('filter-verified').value;
  if (cc)  params.set('country_code', cc.toUpperCase());
  if (ver) params.set('is_verified', ver);
  if (currentJobFilter) params.set('job_id', currentJobFilter);
  window.location.href = '/api/leads/export?' + params.toString();
}

/* ---- PROXIES ---- */
async function loadProxies() {
  try {
    const proxies = await api('/api/proxies/');
    const tbody = document.getElementById('proxies-body');
    if (!proxies.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty">No proxies. Add one above.</td></tr>';
      return;
    }
    tbody.innerHTML = proxies.map(p => `<tr>
      <td style="font-family:var(--font-mono)">${p.host}</td>
      <td>${p.port}</td>
      <td>${p.protocol}</td>
      <td>${p.country_code || '—'}</td>
      <td>${p.is_active ? '<span class="badge badge-done">✓ Active</span>' : '<span class="badge badge-failed">✗ Down</span>'}</td>
      <td>${p.latency_ms != null ? p.latency_ms + ' ms' : '—'}</td>
      <td>${p.fail_count}</td>
      <td>${fmtDate(p.last_checked_at)}</td>
      <td style="display:flex;gap:4px">
        <button class="btn btn-sm btn-ghost" onclick="checkProxy(${p.id})">Check</button>
        <button class="btn btn-sm btn-danger" onclick="deleteProxy(${p.id})">✕</button>
      </td>
    </tr>`).join('');
  } catch(e) { console.error(e); }
}

async function addProxy() {
  const msg = document.getElementById('proxy-msg');
  const payload = {
    host:         document.getElementById('proxy-host').value.trim(),
    port:         parseInt(document.getElementById('proxy-port').value),
    protocol:     document.getElementById('proxy-protocol').value,
    username:     document.getElementById('proxy-username').value.trim() || null,
    password:     document.getElementById('proxy-password').value || null,
    country_code: document.getElementById('proxy-country').value.trim().toUpperCase() || null,
  };
  if (!payload.host || !payload.port) {
    msg.textContent = 'Host and port are required.'; msg.className = 'form-msg error'; return;
  }
  try {
    await api('/api/proxies/', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    msg.textContent = '✓ Proxy added.'; msg.className = 'form-msg';
    ['proxy-host','proxy-port','proxy-username','proxy-password','proxy-country'].forEach(id => document.getElementById(id).value = '');
    loadProxies();
  } catch(e) { msg.textContent = 'Error: ' + e.message; msg.className = 'form-msg error'; }
}

async function checkProxy(id) {
  try { await api(`/api/proxies/${id}/check`, {method:'POST'}); loadProxies(); }
  catch(e) { console.error(e); }
}

async function deleteProxy(id) {
  if (!confirm('Delete this proxy?')) return;
  try { await fetch(`/api/proxies/${id}`, {method:'DELETE'}); loadProxies(); }
  catch(e) { console.error(e); }
}
