"""Serves the single-page frontend."""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

HTML = b"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>B2C Leads Pro</title>
<style>
  :root {
    --bg: #0f0f0f; --surface: #1a1a1a; --surface2: #222;
    --border: #2e2e2e; --text: #e8e8e8; --muted: #888;
    --primary: #2563eb; --primary-h: #1d4ed8;
    --green: #22c55e; --red: #ef4444; --yellow: #f59e0b;
    --gmaps: #2563eb; --yelp: #e11d48; --yp: #f59e0b; --angi: #f97316;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
  #sidebar { width: 280px; min-width: 280px; background: var(--surface);
             border-right: 1px solid var(--border); display: flex; flex-direction: column;
             padding: 16px; gap: 18px; overflow-y: auto; }
  .logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px; }
  .section-label { font-size: 11px; font-weight: 600; color: var(--muted);
                   text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
  .tags-wrap { display: flex; flex-wrap: wrap; gap: 6px; background: var(--surface2);
               border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px;
               min-height: 40px; cursor: text; }
  .tags-wrap:focus-within { border-color: var(--primary); }
  .tag { display: flex; align-items: center; gap: 4px; background: var(--primary);
         color: #fff; border-radius: 5px; padding: 2px 8px; font-size: 12px; }
  .tag button { background: none; border: none; color: #fff; cursor: pointer; font-size: 14px; line-height: 1; padding: 0; }
  .tags-wrap input { background: none; border: none; outline: none; color: var(--text); font-size: 13px; min-width: 100px; flex: 1; }
  input[type=text], input[type=number] {
    background: var(--surface2); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); font-size: 13px; padding: 8px 10px; width: 100%; outline: none; transition: border .15s;
  }
  input:focus { border-color: var(--primary); }
  .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .field label { font-size: 11px; color: var(--muted); margin-bottom: 4px; display: block; }
  .sources-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .src-btn { display: flex; align-items: center; gap: 8px; padding: 8px 10px;
             border-radius: 8px; border: 1px solid var(--border); background: var(--surface2);
             cursor: pointer; font-size: 13px; color: var(--muted); transition: all .15s; }
  .src-btn .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
  .src-btn.active { border-color: currentColor; color: var(--text); }
  .src-btn.active .dot { background: currentColor; }
  .src-btn[data-src=gmaps].active { color: var(--gmaps); }
  .src-btn[data-src=yelp].active  { color: var(--yelp); }
  .src-btn[data-src=yellowpages].active { color: var(--yp); }
  .src-btn[data-src=angi].active  { color: var(--angi); }
  .btn-launch { background: var(--primary); color: #fff; border: none; border-radius: 10px;
                padding: 12px; font-size: 14px; font-weight: 600; cursor: pointer;
                transition: background .15s; width: 100%; }
  .btn-launch:hover { background: var(--primary-h); }
  .btn-launch:disabled { opacity: .5; cursor: not-allowed; }
  .jobs-list { display: flex; flex-direction: column; gap: 6px; overflow-y: auto; flex: 1; }
  .job-card { padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border);
              background: var(--surface2); cursor: pointer; transition: border .15s; }
  .job-card:hover, .job-card.active { border-color: var(--primary); }
  .job-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  .job-id { font-size: 12px; font-weight: 700; }
  .badge { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 99px; }
  .badge.done    { background: #14532d; color: var(--green); }
  .badge.running { background: #1e3a5f; color: #60a5fa; }
  .badge.error   { background: #450a0a; color: var(--red); }
  .badge.pending { background: #292524; color: var(--yellow); }
  .job-meta { font-size: 11px; color: var(--muted); }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  #top-bar { padding: 16px 20px; border-bottom: 1px solid var(--border);
             display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
  .top-left h2 { font-size: 18px; font-weight: 700; }
  .top-left p  { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .filter-row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
  .filter-btn { padding: 5px 12px; border-radius: 99px; border: 1px solid var(--border);
                background: none; color: var(--muted); font-size: 12px; cursor: pointer; transition: all .15s; }
  .filter-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
  .btn-export { background: var(--green); color: #fff; border: none; border-radius: 8px;
                padding: 7px 14px; font-size: 12px; font-weight: 600; cursor: pointer; }
  #table-wrap { flex: 1; overflow: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { position: sticky; top: 0; background: var(--surface); padding: 10px 14px;
             text-align: left; font-size: 11px; font-weight: 600; color: var(--muted);
             text-transform: uppercase; letter-spacing: .06em; border-bottom: 1px solid var(--border); }
  tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
  tbody tr:hover { background: var(--surface2); }
  td { padding: 9px 14px; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .src-badge { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 99px; }
  .src-badge.gmaps       { background: #1e3a5f; color: #60a5fa; }
  .src-badge.yelp        { background: #450a0a; color: #fca5a5; }
  .src-badge.yellowpages { background: #451a03; color: #fcd34d; }
  .src-badge.angi        { background: #431407; color: #fb923c; }
  .empty { text-align: center; padding: 60px; color: var(--muted); }
  a { color: #60a5fa; text-decoration: none; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<aside id="sidebar">
  <div class="logo">
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
      <rect width="28" height="28" rx="7" fill="#2563eb"/>
      <path d="M7 14h4l3-7 3 14 3-7h4" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    B2C Leads Pro
  </div>
  <div>
    <div class="section-label">Locations</div>
    <div class="tags-wrap" id="loc-wrap" onclick="document.getElementById('loc-input').focus()">
      <input id="loc-input" placeholder="Type city + Enter" autocomplete="off">
    </div>
  </div>
  <div>
    <div class="section-label">Niches <span style="color:#555;font-weight:400">(optional &#x2014; comma separated)</span></div>
    <input type="text" id="niches" placeholder="e.g. plumber, electrician">
  </div>
  <div>
    <div class="section-label">Sources</div>
    <div class="sources-grid">
      <button class="src-btn active" data-src="gmaps"><span class="dot"></span>Google Maps</button>
      <button class="src-btn active" data-src="yelp"><span class="dot"></span>Yelp</button>
      <button class="src-btn active" data-src="yellowpages"><span class="dot"></span>YellowPages</button>
      <button class="src-btn active" data-src="angi"><span class="dot"></span>Angi</button>
    </div>
  </div>
  <div class="row2">
    <div class="field"><label>Max Pages</label><input type="number" id="max-pages" value="10" min="1" max="500"></div>
    <div class="field"><label>Concurrency</label><input type="number" id="concurrency" value="3" min="1" max="20"></div>
  </div>
  <button class="btn-launch" id="btn-launch" onclick="launchJob()">&#x1F680; Launch Job</button>
  <div>
    <div class="section-label">Recent Jobs</div>
    <div class="jobs-list" id="jobs-list"></div>
  </div>
</aside>
<main id="main">
  <div id="top-bar">
    <div class="top-left">
      <h2 id="job-title">No job selected</h2>
      <p id="job-meta"></p>
    </div>
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <div class="filter-row">
        <button class="filter-btn active" data-filter="all" onclick="setFilter('all')">All</button>
        <button class="filter-btn" data-filter="gmaps" onclick="setFilter('gmaps')">gmaps</button>
        <button class="filter-btn" data-filter="yelp" onclick="setFilter('yelp')">yelp</button>
        <button class="filter-btn" data-filter="yellowpages" onclick="setFilter('yellowpages')">yellowpages</button>
        <button class="filter-btn" data-filter="angi" onclick="setFilter('angi')">angi</button>
      </div>
      <button class="btn-export" onclick="exportCSV()">&#x2193; Export CSV</button>
    </div>
  </div>
  <div id="table-wrap">
    <table>
      <thead><tr>
        <th>Source</th><th>Name</th><th>Phone</th><th>Email</th>
        <th>Website</th><th>Address</th><th>Rating</th><th>Category</th>
        <th>Location</th><th>Niche</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="empty" id="empty-msg">Select or launch a job to see leads.</div>
  </div>
</main>
<script>
const API='';
let currentJobId=null,allLeads=[],currentFilter='all',pollTimer=null,locations=[];
const locInput=document.getElementById('loc-input');
const locWrap=document.getElementById('loc-wrap');
locInput.addEventListener('keydown',e=>{
  if((e.key==='Enter'||e.key===',')&&locInput.value.trim()){
    e.preventDefault();addLocation(locInput.value.trim().replace(/,$/,''));locInput.value='';
  }else if(e.key==='Backspace'&&!locInput.value&&locations.length){
    removeLocation(locations[locations.length-1]);
  }
});
function addLocation(city){
  if(!city||locations.includes(city))return;
  locations.push(city);
  const tag=document.createElement('div');tag.className='tag';tag.dataset.city=city;
  tag.innerHTML=`${city} <button onclick="removeLocation('${city}')">&times;</button>`;
  locWrap.insertBefore(tag,locInput);
}
function removeLocation(city){
  locations=locations.filter(l=>l!==city);
  const el=locWrap.querySelector(`[data-city="${CSS.escape(city)}"]`);
  if(el)el.remove();
}
document.querySelectorAll('.src-btn').forEach(btn=>btn.addEventListener('click',()=>btn.classList.toggle('active')));
function getActiveSources(){return[...document.querySelectorAll('.src-btn.active')].map(b=>b.dataset.src);}
async function launchJob(){
  if(!locations.length){alert('Please add at least one location.');return;}
  const sources=getActiveSources();
  if(!sources.length){alert('Select at least one source.');return;}
  const btn=document.getElementById('btn-launch');
  btn.disabled=true;btn.textContent='Launching...';
  try{
    const res=await fetch(`${API}/api/jobs/`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({locations,niches:document.getElementById('niches').value,
        sources:sources.join(','),
        max_pages:parseInt(document.getElementById('max-pages').value)||10,
        concurrency:parseInt(document.getElementById('concurrency').value)||3})
    });
    const job=await res.json();loadJob(job.id);loadJobs();
  }catch(e){alert('Failed: '+e);}
  btn.disabled=false;btn.textContent='\u{1F680} Launch Job';
}
async function loadJob(id){
  clearInterval(pollTimer);currentJobId=id;
  document.querySelectorAll('.job-card').forEach(c=>c.classList.toggle('active',+c.dataset.id===id));
  await fetchLeads(id);
  const job=await(await fetch(`${API}/api/jobs/${id}`)).json();
  if(job.status==='running'||job.status==='pending'){
    pollTimer=setInterval(async()=>{
      await fetchLeads(id);
      const j=await(await fetch(`${API}/api/jobs/${id}`)).json();
      updateJobMeta(j);
      if(j.status!=='running'&&j.status!=='pending')clearInterval(pollTimer);
    },2000);
  }
  updateJobMeta(job);
}
async function fetchLeads(id){
  const r=await fetch(`${API}/api/leads/?job_id=${id}&limit=5000`);
  allLeads=await r.json();renderTable();
}
function updateJobMeta(job){
  const locs=JSON.parse(job.locations||'[]').join(', ');
  document.getElementById('job-title').textContent=locs||`Job #${job.id}`;
  document.getElementById('job-meta').textContent=`${job.leads_found} leads \u00b7 ${job.status} \u00b7 sources: ${job.sources}`;
  loadJobs();
}
async function loadJobs(){
  const jobs=await(await fetch(`${API}/api/jobs/`)).json();
  const list=document.getElementById('jobs-list');list.innerHTML='';
  jobs.slice().reverse().forEach(job=>{
    const locs=JSON.parse(job.locations||'[]').join(', ');
    const div=document.createElement('div');
    div.className='job-card'+(job.id===currentJobId?' active':'');div.dataset.id=job.id;
    div.onclick=()=>loadJob(job.id);
    div.innerHTML=`<div class="job-card-top"><span class="job-id">#${job.id}</span><span class="badge ${job.status}">${job.status.toUpperCase()}</span></div><div class="job-meta">${locs} &middot; ${job.leads_found} leads</div>`;
    list.appendChild(div);
  });
}
function setFilter(f){
  currentFilter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.filter===f));
  renderTable();
}
function renderTable(){
  const rows=currentFilter==='all'?allLeads:allLeads.filter(l=>l.source===currentFilter);
  const tbody=document.getElementById('tbody'),empty=document.getElementById('empty-msg');
  if(!rows.length){
    tbody.innerHTML='';empty.style.display='';
    empty.textContent=allLeads.length?'No leads for this filter.':'No leads yet \u2014 job is running...';
    return;
  }
  empty.style.display='none';
  tbody.innerHTML=rows.map(l=>`<tr>
    <td><span class="src-badge ${l.source}">${l.source}</span></td>
    <td title="${l.name||''}">${l.name||'\u2014'}</td>
    <td>${l.phone||'\u2014'}</td>
    <td>${l.email?`<a href="mailto:${l.email}">${l.email}</a>`:'\u2014'}</td>
    <td>${l.website?`<a href="${l.website}" target="_blank" rel="noopener">link</a>`:'\u2014'}</td>
    <td title="${l.address||''}">${l.address||'\u2014'}</td>
    <td>${l.rating||'\u2014'}</td>
    <td>${l.category||'\u2014'}</td>
    <td>${l.location||'\u2014'}</td>
    <td>${l.niche||'\u2014'}</td>
  </tr>`).join('');
}
function exportCSV(){
  const rows=currentFilter==='all'?allLeads:allLeads.filter(l=>l.source===currentFilter);
  if(!rows.length){alert('No leads to export.');return;}
  const cols=['source','name','phone','email','website','address','rating','category','location','niche'];
  const csv=[cols.join(','),...rows.map(r=>cols.map(c=>'"'+String(r[c]||'').replace(/"/g,'""')+'"').join(','))].join('\n');
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download=`leads_job_${currentJobId}.csv`;a.click();
}
loadJobs();
</script>
</body>
</html>
"""

@router.get("/", response_class=Response)
async def index():
    return Response(content=HTML, media_type="text/html; charset=utf-8")
