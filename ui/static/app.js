/* ============================
   B2C Leads Pro — Dashboard JS
   ============================ */

const API = '';
let currentPage = 'dashboard';
let selectedLocations = [];
let leadsPage = 1;
let pollTimer = null;

/* ---- BUILT-IN CITY LIST (fallback when DB is empty) ---- */
const CITIES = [
  {city:'New York',country:'United States',country_code:'US'},
  {city:'Los Angeles',country:'United States',country_code:'US'},
  {city:'Chicago',country:'United States',country_code:'US'},
  {city:'Houston',country:'United States',country_code:'US'},
  {city:'Phoenix',country:'United States',country_code:'US'},
  {city:'Philadelphia',country:'United States',country_code:'US'},
  {city:'San Antonio',country:'United States',country_code:'US'},
  {city:'San Diego',country:'United States',country_code:'US'},
  {city:'Dallas',country:'United States',country_code:'US'},
  {city:'San Jose',country:'United States',country_code:'US'},
  {city:'Austin',country:'United States',country_code:'US'},
  {city:'Jacksonville',country:'United States',country_code:'US'},
  {city:'Fort Worth',country:'United States',country_code:'US'},
  {city:'Columbus',country:'United States',country_code:'US'},
  {city:'Charlotte',country:'United States',country_code:'US'},
  {city:'Indianapolis',country:'United States',country_code:'US'},
  {city:'San Francisco',country:'United States',country_code:'US'},
  {city:'Seattle',country:'United States',country_code:'US'},
  {city:'Denver',country:'United States',country_code:'US'},
  {city:'Nashville',country:'United States',country_code:'US'},
  {city:'Oklahoma City',country:'United States',country_code:'US'},
  {city:'El Paso',country:'United States',country_code:'US'},
  {city:'Las Vegas',country:'United States',country_code:'US'},
  {city:'Louisville',country:'United States',country_code:'US'},
  {city:'Baltimore',country:'United States',country_code:'US'},
  {city:'Milwaukee',country:'United States',country_code:'US'},
  {city:'Albuquerque',country:'United States',country_code:'US'},
  {city:'Tucson',country:'United States',country_code:'US'},
  {city:'Fresno',country:'United States',country_code:'US'},
  {city:'Sacramento',country:'United States',country_code:'US'},
  {city:'Mesa',country:'United States',country_code:'US'},
  {city:'Kansas City',country:'United States',country_code:'US'},
  {city:'Atlanta',country:'United States',country_code:'US'},
  {city:'Omaha',country:'United States',country_code:'US'},
  {city:'Colorado Springs',country:'United States',country_code:'US'},
  {city:'Raleigh',country:'United States',country_code:'US'},
  {city:'Miami',country:'United States',country_code:'US'},
  {city:'Long Beach',country:'United States',country_code:'US'},
  {city:'Virginia Beach',country:'United States',country_code:'US'},
  {city:'Minneapolis',country:'United States',country_code:'US'},
  {city:'Tampa',country:'United States',country_code:'US'},
  {city:'New Orleans',country:'United States',country_code:'US'},
  {city:'Arlington',country:'United States',country_code:'US'},
  {city:'Bakersfield',country:'United States',country_code:'US'},
  {city:'Honolulu',country:'United States',country_code:'US'},
  {city:'Anaheim',country:'United States',country_code:'US'},
  {city:'Aurora',country:'United States',country_code:'US'},
  {city:'Santa Ana',country:'United States',country_code:'US'},
  {city:'Corpus Christi',country:'United States',country_code:'US'},
  {city:'Riverside',country:'United States',country_code:'US'},
  {city:'Portland',country:'United States',country_code:'US'},
  {city:'Pittsburgh',country:'United States',country_code:'US'},
  {city:'Boston',country:'United States',country_code:'US'},
  {city:'Detroit',country:'United States',country_code:'US'},
  {city:'Orlando',country:'United States',country_code:'US'},
  {city:'Cleveland',country:'United States',country_code:'US'},
  {city:'Cincinnati',country:'United States',country_code:'US'},
  {city:'St. Louis',country:'United States',country_code:'US'},
  {city:'London',country:'United Kingdom',country_code:'GB'},
  {city:'Manchester',country:'United Kingdom',country_code:'GB'},
  {city:'Birmingham',country:'United Kingdom',country_code:'GB'},
  {city:'Glasgow',country:'United Kingdom',country_code:'GB'},
  {city:'Leeds',country:'United Kingdom',country_code:'GB'},
  {city:'Liverpool',country:'United Kingdom',country_code:'GB'},
  {city:'Toronto',country:'Canada',country_code:'CA'},
  {city:'Vancouver',country:'Canada',country_code:'CA'},
  {city:'Montreal',country:'Canada',country_code:'CA'},
  {city:'Calgary',country:'Canada',country_code:'CA'},
  {city:'Ottawa',country:'Canada',country_code:'CA'},
  {city:'Sydney',country:'Australia',country_code:'AU'},
  {city:'Melbourne',country:'Australia',country_code:'AU'},
  {city:'Brisbane',country:'Australia',country_code:'AU'},
  {city:'Perth',country:'Australia',country_code:'AU'},
  {city:'Adelaide',country:'Australia',country_code:'AU'},
  {city:'Dublin',country:'Ireland',country_code:'IE'},
  {city:'Auckland',country:'New Zealand',country_code:'NZ'},
  {city:'Berlin',country:'Germany',country_code:'DE'},
  {city:'Munich',country:'Germany',country_code:'DE'},
  {city:'Hamburg',country:'Germany',country_code:'DE'},
  {city:'Paris',country:'France',country_code:'FR'},
  {city:'Lyon',country:'France',country_code:'FR'},
  {city:'Madrid',country:'Spain',country_code:'ES'},
  {city:'Barcelona',country:'Spain',country_code:'ES'},
  {city:'Rome',country:'Italy',country_code:'IT'},
  {city:'Milan',country:'Italy',country_code:'IT'},
  {city:'Amsterdam',country:'Netherlands',country_code:'NL'},
  {city:'Brussels',country:'Belgium',country_code:'BE'},
  {city:'Zurich',country:'Switzerland',country_code:'CH'},
  {city:'Stockholm',country:'Sweden',country_code:'SE'},
  {city:'Oslo',country:'Norway',country_code:'NO'},
  {city:'Copenhagen',country:'Denmark',country_code:'DK'},
  {city:'Helsinki',country:'Finland',country_code:'FI'},
  {city:'Warsaw',country:'Poland',country_code:'PL'},
  {city:'Prague',country:'Czech Republic',country_code:'CZ'},
  {city:'Vienna',country:'Austria',country_code:'AT'},
  {city:'Lisbon',country:'Portugal',country_code:'PT'},
  {city:'Mexico City',country:'Mexico',country_code:'MX'},
  {city:'Guadalajara',country:'Mexico',country_code:'MX'},
  {city:'Monterrey',country:'Mexico',country_code:'MX'},
  {city:'Sao Paulo',country:'Brazil',country_code:'BR'},
  {city:'Rio de Janeiro',country:'Brazil',country_code:'BR'},
  {city:'Buenos Aires',country:'Argentina',country_code:'AR'},
  {city:'Bogota',country:'Colombia',country_code:'CO'},
  {city:'Santiago',country:'Chile',country_code:'CL'},
  {city:'Lima',country:'Peru',country_code:'PE'},
  {city:'Dubai',country:'UAE',country_code:'AE'},
  {city:'Abu Dhabi',country:'UAE',country_code:'AE'},
  {city:'Riyadh',country:'Saudi Arabia',country_code:'SA'},
  {city:'Doha',country:'Qatar',country_code:'QA'},
  {city:'Kuwait City',country:'Kuwait',country_code:'KW'},
  {city:'Tel Aviv',country:'Israel',country_code:'IL'},
  {city:'Istanbul',country:'Turkey',country_code:'TR'},
  {city:'Ankara',country:'Turkey',country_code:'TR'},
  {city:'Cairo',country:'Egypt',country_code:'EG'},
  {city:'Lagos',country:'Nigeria',country_code:'NG'},
  {city:'Nairobi',country:'Kenya',country_code:'KE'},
  {city:'Johannesburg',country:'South Africa',country_code:'ZA'},
  {city:'Cape Town',country:'South Africa',country_code:'ZA'},
  {city:'Mumbai',country:'India',country_code:'IN'},
  {city:'Delhi',country:'India',country_code:'IN'},
  {city:'Bangalore',country:'India',country_code:'IN'},
  {city:'Hyderabad',country:'India',country_code:'IN'},
  {city:'Chennai',country:'India',country_code:'IN'},
  {city:'Pune',country:'India',country_code:'IN'},
  {city:'Tokyo',country:'Japan',country_code:'JP'},
  {city:'Osaka',country:'Japan',country_code:'JP'},
  {city:'Beijing',country:'China',country_code:'CN'},
  {city:'Shanghai',country:'China',country_code:'CN'},
  {city:'Shenzhen',country:'China',country_code:'CN'},
  {city:'Hong Kong',country:'Hong Kong',country_code:'HK'},
  {city:'Singapore',country:'Singapore',country_code:'SG'},
  {city:'Seoul',country:'South Korea',country_code:'KR'},
  {city:'Kuala Lumpur',country:'Malaysia',country_code:'MY'},
  {city:'Jakarta',country:'Indonesia',country_code:'ID'},
  {city:'Bangkok',country:'Thailand',country_code:'TH'},
  {city:'Manila',country:'Philippines',country_code:'PH'},
  {city:'Ho Chi Minh City',country:'Vietnam',country_code:'VN'},
];

function searchCities(q) {
  const lq = q.toLowerCase();
  return CITIES.filter(c =>
    c.city.toLowerCase().includes(lq) ||
    c.country.toLowerCase().includes(lq) ||
    c.country_code.toLowerCase().includes(lq)
  ).slice(0, 12);
}

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
  const p = isNaN(pct) ? 0 : Math.min(100, Math.max(0, pct));
  return `<div class="progress-wrap"><div class="progress-bar" style="width:${p}%"></div></div>`;
}

// Compute progress % from pages_scraped / pages_discovered
function jobProgress(j) {
  if (!j.pages_discovered || j.pages_discovered === 0) {
    return j.status === 'done' ? 100 : 0;
  }
  return Math.round((j.pages_scraped / j.pages_discovered) * 100);
}

// Short UUID display
function shortId(id) {
  return id ? String(id).slice(0, 8) : '—';
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
    const [jobsData, proxiesData, queues] = await Promise.all([
      api('/api/jobs/'),
      api('/api/proxies/'),
      api('/api/queues/').catch(() => null),
    ]);

    // Total emails found across all jobs
    const totalLeads = jobsData.reduce((s, j) => s + (j.emails_found || 0), 0);
    const verifiedLeads = jobsData.reduce((s, j) => s + (j.emails_verified || 0), 0);
    document.getElementById('kpi-total-leads').textContent = num(totalLeads);
    document.getElementById('kpi-verified').textContent = num(verifiedLeads);

    const running = jobsData.filter(j => j.status === 'running' || j.status === 'pending').length;
    document.getElementById('kpi-active-jobs').textContent = num(running);

    const active = proxiesData.filter(p => p.is_active).length;
    document.getElementById('kpi-proxies').textContent = num(active);

    if (queues && !queues.error) {
      const d = queues.discovery_queue ?? queues.discovery ?? '—';
      const s = queues.scrape_queue   ?? queues.scrape   ?? '—';
      const v = queues.verify_queue   ?? queues.verify   ?? '—';
      document.getElementById('kpi-queue').textContent = `D:${d} S:${s} V:${v}`;
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
  if (!jobs || !jobs.length) {
    tbody.innerHTML = `<tr><td colspan="${compact?7:9}" class="empty">No jobs yet. Launch one from New Job.</td></tr>`;
    return;
  }
  tbody.innerHTML = jobs.map(j => {
    const pct      = jobProgress(j);
    const keywords = compact ? '' : `<td>${(j.keywords || []).join(', ') || '—'}</td>`;
    const started  = compact ? '' : `<td>${fmtDate(j.started_at)}</td>`;
    const finished = compact ? '' : `<td>${fmtDate(j.finished_at)}</td>`;
    const jid      = String(j.id);
    return `<tr>
      <td><span style="font-family:var(--font-mono);color:var(--color-text-muted)" title="${jid}">#${shortId(jid)}</span></td>
      <td>${statusBadge(j.status)}</td>
      <td>${j.location_id ? shortId(String(j.location_id)) : '—'}</td>
      ${keywords}
      <td>${progressBar(pct)}<span style="color:var(--color-text-muted);margin-left:4px">${pct}%</span></td>
      <td>${num(j.emails_found)}</td>
      <td>${num(j.pages_scraped)}</td>
      ${started}${finished}
      <td><button class="btn btn-sm btn-ghost" onclick="viewJobLeads('${jid}')">Leads</button></td>
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
  if (q.length < 1) { dd.classList.remove('open'); return; }

  const local = searchCities(q);
  renderDropdown(dd, [], q, local);

  if (q.length >= 2) {
    searchDebounce = setTimeout(async () => {
      try {
        const dbResults = await api(`/api/locations/search?q=${encodeURIComponent(q)}`);
        const dbCities = new Set(dbResults.map(r => (r.city || r.country).toLowerCase()));
        const extra = local.filter(c => !dbCities.has(c.city.toLowerCase()));
        renderDropdown(dd, dbResults, q, extra);
      } catch(e) { /* keep local */ }
    }, 300);
  }
}

function renderDropdown(dd, dbResults, q, localFallback = []) {
  let html = '';

  html += dbResults.map(r =>
    `<div class="dropdown-item" onclick="addLocation(${JSON.stringify(r.id)},'${(r.city||r.country).replace(/'/g,"\\'")}','${r.country_code}')">
      ${r.city ? r.city + ', ' : ''}${r.country} <span style="color:var(--color-text-faint)">${r.country_code}</span>
    </div>`
  ).join('');

  html += localFallback.map(c =>
    `<div class="dropdown-item" onclick="createAndAddLocation('${c.city.replace(/'/g,"\\'")}','${c.country.replace(/'/g,"\\'")}','${c.country_code}')">
      ${c.city}, ${c.country} <span style="color:var(--color-text-faint)">${c.country_code}</span>
    </div>`
  ).join('');

  if (!dbResults.length && !localFallback.length) {
    html += `<div class="dropdown-item" style="color:var(--color-primary)" onclick="createAndAddLocation('${q.replace(/'/g,"\\'")}','','')">
      ➕ Add "${q}"
    </div>`;
  }

  if (html) {
    dd.innerHTML = html;
    dd.classList.add('open');
  } else {
    dd.classList.remove('open');
  }
}

async function createAndAddLocation(city, country, cc) {
  try {
    const loc = await api('/api/locations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, country: country || city, country_code: cc || 'XX', raw_input: city }),
    });
    addLocation(loc.id, loc.city || loc.country, loc.country_code || cc || 'XX');
  } catch(e) {
    try {
      const results = await api(`/api/locations/search?q=${encodeURIComponent(city)}`);
      if (results.length) addLocation(results[0].id, results[0].city || results[0].country, results[0].country_code);
    } catch(e2) { console.error('createAndAddLocation failed', e2); }
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
    `<span class="location-tag">${l.city} <span style="opacity:.6">${l.cc}</span><button onclick="removeLocation(${JSON.stringify(l.id)})" title="Remove">×</button></span>`
  ).join('');
}

document.addEventListener('click', e => {
  if (!e.target.closest('.location-search-wrap'))
    document.getElementById('location-dropdown').classList.remove('open');
});

/* ---- SUBMIT JOB ----
   Backend JobCreate expects: location_id (UUID), keywords (list), source_types (list), proxy_mode (str)
   We use the FIRST selected location as location_id; niches become keywords.
---- */
async function submitJob() {
  const msg = document.getElementById('job-submit-msg');
  if (!selectedLocations.length) {
    msg.textContent = 'Please add at least one location.';
    msg.className = 'form-msg error'; return;
  }
  const nichesRaw = document.getElementById('job-niches').value;
  const keywords  = nichesRaw.split(',').map(s => s.trim()).filter(Boolean);

  // Backend only supports single location_id — use first selected
  const payload = {
    location_id:  selectedLocations[0].id,
    keywords:     keywords.length ? keywords : null,
    source_types: null,
    proxy_mode:   'rotating_residential',
  };

  try {
    const job = await api('/api/jobs/', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    msg.textContent = `✓ Job #${shortId(String(job.id))} launched!`;
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
    if (!data.results || !data.results.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty">No leads found. Run a job first.</td></tr>';
    } else {
      tbody.innerHTML = data.results.map(l => `<tr>
        <td style="font-family:var(--font-mono);color:var(--color-primary)">${l.email}</td>
        <td>${l.full_name || '—'}</td>
        <td>${l.city || '—'}</td>
        <td>${l.country_code || '—'}</td>
        <td>${l.niche || '—'}</td>
        <td><strong>${l.score ?? '—'}</strong></td>
        <td>${l.is_verified
          ? '<span class="badge badge-done">✓ Yes</span>'
          : '<span class="badge badge-failed">— No</span>'}</td>
        <td style="color:var(--color-text-muted);font-size:.7rem">${l.source_domain || '—'}</td>
        <td><span style="color:var(--color-text-muted)">${shortId(String(l.job_id || ''))}</span></td>
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
        <button class="btn btn-sm btn-ghost" onclick="checkProxy('${p.id}')">Check</button>
        <button class="btn btn-sm btn-danger" onclick="deleteProxy('${p.id}')">✕</button>
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

/* ---- INIT ---- */
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  pollTimer = setInterval(loadDashboard, 6000);
});
