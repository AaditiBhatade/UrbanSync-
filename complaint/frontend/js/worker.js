// UrbanSync — Field Worker Dashboard & Task Management System

let workerState = {
  profile: null,
  stats: null,
  complaints: [],
  currentFilter: 'ACTIVE',
  searchQuery: ''
};

async function renderWorkerDashboard() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="main-content" style="max-width:1240px; margin:0 auto; padding:2rem 1.5rem;">
      <div style="text-align:center; padding:3rem 0;">
        <div style="font-size:2rem; margin-bottom:1rem;">⏳</div>
        <p style="color:var(--text-muted); font-weight:500;">Loading Field Worker Portal...</p>
      </div>
    </div>
  `;

  try {
    const [profileRes, complaintsRes] = await Promise.all([
      apiFetch("/api/worker/me"),
      apiFetch("/api/worker/complaints?status_filter=ALL")
    ]);

    if (!profileRes || !profileRes.success) {
      throw new Error("Failed to load worker profile.");
    }

    workerState.profile = profileRes.worker;
    workerState.stats = profileRes.stats;
    workerState.complaints = complaintsRes.complaints || [];

    buildWorkerDashboardHTML();
  } catch (err) {
    root.innerHTML = `
      <div class="main-content" style="max-width:800px; margin:4rem auto; text-align:center;">
        <div style="font-size:3rem; margin-bottom:1rem;">⚠️</div>
        <h2 style="color:var(--danger); margin-bottom:0.5rem;">Unable to Load Worker Dashboard</h2>
        <p style="color:var(--text-muted); margin-bottom:1.5rem;">${err.message || "An unexpected error occurred."}</p>
        <button class="btn btn-primary" onclick="navigate('/')">Return Home</button>
      </div>
    `;
  }
}

function buildWorkerDashboardHTML() {
  const root = document.getElementById("app-root");
  const w = workerState.profile;
  const s = workerState.stats;

  const isFree = w.worker_status === true;
  const statusBadgeBg = isFree ? "#ECFDF5" : "#FFFBEB";
  const statusBadgeColor = isFree ? "#065F46" : "#92400E";
  const statusBadgeBorder = isFree ? "#A7F3D0" : "#FDE68A";
  const statusIcon = isFree ? "🟢" : "🟠";
  const statusText = isFree ? "Available (Free)" : "On Task (Busy)";

  // Filter complaints based on currentFilter
  const filteredComplaints = getFilteredWorkerComplaints();

  root.innerHTML = `
    <div class="main-content" style="max-width:1240px; margin:0 auto; padding:1.5rem 1.5rem 4rem;">
      <!-- Breadcrumbs & Live Time -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:0.5rem;">
        <div style="font-size:0.85rem; color:var(--text-muted);">
          <span>Municipal Field Operations</span> &nbsp;›&nbsp; 
          <strong style="color:var(--text-main);">${w.department_name || w.department_code}</strong>
        </div>
        <div style="font-size:0.8rem; color:var(--text-muted); display:flex; align-items:center; gap:0.5rem;">
          <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981;"></span>
          Live Sync Active
        </div>
      </div>

      <!-- Hero Worker Card -->
      <div style="background:linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius:var(--radius-lg); padding:2rem; color:#FFFFFF; margin-bottom:2rem; box-shadow:var(--shadow-md); position:relative; overflow:hidden;">
        <div style="position:absolute; right:-20px; bottom:-20px; font-size:12rem; opacity:0.04; pointer-events:none;">👷</div>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1.5rem; position:relative; z-index:1;">
          <div style="display:flex; align-items:center; gap:1.25rem;">
            <div style="width:72px; height:72px; border-radius:20px; background:linear-gradient(135deg, #2563EB, #06B6D4); display:flex; align-items:center; justify-content:center; font-size:2.4rem; box-shadow:0 8px 16px rgba(37,99,235,0.3); flex-shrink:0;">
              👷‍♂️
            </div>
            <div>
              <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap; margin-bottom:0.25rem;">
                <h1 style="font-size:1.6rem; font-weight:800; color:#FFFFFF; margin:0;">${w.name}</h1>
                <span style="background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.25); color:#F1F5F9; font-size:0.75rem; font-weight:700; padding:0.2rem 0.6rem; border-radius:20px; letter-spacing:0.05em;">
                  ${w.worker_code}
                </span>
              </div>
              <div style="color:#94A3B8; font-size:0.95rem; margin-bottom:0.6rem;">
                ${w.designation} &nbsp;•&nbsp; <span style="color:#38BDF8; font-weight:600;">${w.department_name || w.department_code}</span>
              </div>
              <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap; font-size:0.8rem; color:#CBD5E1;">
                <span>📞 <a href="tel:${w.phone}" style="color:#CBD5E1; text-decoration:none;">${w.phone}</a></span>
                ${w.email ? `<span>✉️ <a href="mailto:${w.email}" style="color:#CBD5E1; text-decoration:none;">${w.email}</a></span>` : ''}
                ${w.skills ? `<span>🛠️ <em style="color:#E2E8F0;">${w.skills}</em></span>` : ''}
              </div>
            </div>
          </div>

          <!-- Availability Status & Duty Toggle -->
          <div style="background:rgba(255,255,255,0.07); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.15); border-radius:var(--radius-md); padding:1rem 1.25rem; display:flex; flex-direction:column; align-items:flex-end; gap:0.75rem; min-width:220px;">
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:#94A3B8; font-weight:600;">
              Operational Status
            </div>
            <div id="worker-status-badge" style="background:${statusBadgeBg}; color:${statusBadgeColor}; border:1px solid ${statusBadgeBorder}; font-size:0.85rem; font-weight:700; padding:0.35rem 0.8rem; border-radius:20px; display:inline-flex; align-items:center; gap:0.4rem;">
              <span>${statusIcon}</span>
              <span id="worker-status-text">${statusText}</span>
            </div>
            <button id="btn-toggle-availability" class="btn btn-sm" style="background:rgba(255,255,255,0.2); color:#FFFFFF; border:1px solid rgba(255,255,255,0.3); font-size:0.8rem; padding:0.4rem 0.8rem; border-radius:var(--radius-sm); width:100%;" onclick="toggleWorkerAvailability()">
              🔄 Toggle Duty Status
            </button>
          </div>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="cards-grid" style="grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:1rem; margin-bottom:2rem;">
        <div class="stat-card" style="background:var(--bg-surface); border-left:4px solid #2563EB; cursor:pointer;" onclick="setWorkerFilter('ALL')">
          <div style="color:var(--text-muted); font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.4rem;">Total Assigned</div>
          <div style="font-size:2rem; font-weight:800; color:var(--text-main);">${s.total_assigned}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">Lifetime dispatched tasks</div>
        </div>

        <div class="stat-card" style="background:var(--bg-surface); border-left:4px solid #EF4444; cursor:pointer;" onclick="setWorkerFilter('ACTIVE')">
          <div style="color:#EF4444; font-size:0.8rem; font-weight:700; text-transform:uppercase; margin-bottom:0.4rem;">Action Required</div>
          <div style="font-size:2rem; font-weight:800; color:#EF4444;">${s.active_tasks}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">Needs work or completion</div>
        </div>

        <div class="stat-card" style="background:var(--bg-surface); border-left:4px solid #F59E0B; cursor:pointer;" onclick="setWorkerFilter('IN_PROGRESS')">
          <div style="color:#D97706; font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.4rem;">In Progress / Ack</div>
          <div style="font-size:2rem; font-weight:800; color:#D97706;">${(s.in_progress_tasks || 0) + (s.acknowledged_tasks || 0)}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">Active repairs underway</div>
        </div>

        <div class="stat-card" style="background:var(--bg-surface); border-left:4px solid #10B981; cursor:pointer;" onclick="setWorkerFilter('RESOLVED')">
          <div style="color:#10B981; font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.4rem;">Successfully Resolved</div>
          <div style="font-size:2rem; font-weight:800; color:#10B981;">${s.resolved_tasks}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">Fixed and verified</div>
        </div>
      </div>

      <!-- Controls: Filter Tabs & Search -->
      <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.25rem; margin-bottom:1.5rem; box-shadow:var(--shadow-sm);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
          <!-- Filter Tabs -->
          <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
            <button class="btn btn-sm ${workerState.currentFilter === 'ACTIVE' ? 'btn-primary' : 'btn-outline'}" onclick="setWorkerFilter('ACTIVE')">
              ⚡ Action Needed (${s.active_tasks})
            </button>
            <button class="btn btn-sm ${workerState.currentFilter === 'ALL' ? 'btn-primary' : 'btn-outline'}" onclick="setWorkerFilter('ALL')">
              📋 All Tasks (${s.total_assigned})
            </button>
            <button class="btn btn-sm ${workerState.currentFilter === 'IN_PROGRESS' ? 'btn-primary' : 'btn-outline'}" onclick="setWorkerFilter('IN_PROGRESS')">
              🚧 In Progress (${s.in_progress_tasks || 0})
            </button>
            <button class="btn btn-sm ${workerState.currentFilter === 'RESOLVED' ? 'btn-primary' : 'btn-outline'}" onclick="setWorkerFilter('RESOLVED')">
              ✅ Resolved (${s.resolved_tasks})
            </button>
          </div>

          <!-- Search Input -->
          <div style="position:relative; min-width:240px;">
            <input type="text" id="worker-search-input" class="form-control" style="font-size:0.85rem; padding-left:2rem; border-radius:20px;" placeholder="Search task ID, title, or area..." value="${workerState.searchQuery}" oninput="handleWorkerSearch(this.value)" />
            <span style="position:absolute; left:10px; top:50%; transform:translateY(-50%); color:var(--text-muted); font-size:0.85rem;">🔍</span>
          </div>
        </div>
      </div>

      <!-- Complaints Queue Section -->
      <div id="worker-complaints-container">
        ${renderWorkerComplaintsGrid(filteredComplaints)}
      </div>
    </div>

    <!-- Status Change Modal Container -->
    <div id="worker-modal-root"></div>
  `;
}

function getFilteredWorkerComplaints() {
  let list = workerState.complaints || [];

  // Filter by status tab
  if (workerState.currentFilter === 'ACTIVE') {
    list = list.filter(c => ['ASSIGNED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'REOPENED', 'PENDING', 'SUBMITTED'].includes(c.status));
  } else if (workerState.currentFilter === 'IN_PROGRESS') {
    list = list.filter(c => ['IN_PROGRESS', 'ACKNOWLEDGED'].includes(c.status));
  } else if (workerState.currentFilter === 'RESOLVED') {
    list = list.filter(c => ['RESOLVED', 'CLOSED'].includes(c.status));
  }

  // Filter by search query
  if (workerState.searchQuery.trim()) {
    const q = workerState.searchQuery.toLowerCase().trim();
    list = list.filter(c => 
      c.complaint_id.toLowerCase().includes(q) ||
      (c.title && c.title.toLowerCase().includes(q)) ||
      (c.description && c.description.toLowerCase().includes(q)) ||
      (c.location && c.location.toLowerCase().includes(q)) ||
      (c.citizen_name && c.citizen_name.toLowerCase().includes(q))
    );
  }

  return list;
}

function setWorkerFilter(filter) {
  workerState.currentFilter = filter;
  buildWorkerDashboardHTML();
}

function handleWorkerSearch(value) {
  workerState.searchQuery = value;
  const filtered = getFilteredWorkerComplaints();
  const container = document.getElementById("worker-complaints-container");
  if (container) {
    container.innerHTML = renderWorkerComplaintsGrid(filtered);
  }
}

function renderWorkerComplaintsGrid(complaints) {
  if (!complaints || complaints.length === 0) {
    return `
      <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:4rem 2rem; text-align:center; box-shadow:var(--shadow-sm);">
        <div style="font-size:3.5rem; margin-bottom:1rem;">🎉</div>
        <h3 style="font-size:1.25rem; color:var(--text-main); margin-bottom:0.5rem;">No Complaints Found</h3>
        <p style="color:var(--text-muted); max-width:450px; margin:0 auto 1.5rem; font-size:0.9rem;">
          ${workerState.currentFilter === 'ACTIVE' 
            ? "You currently have no pending tasks in your queue! Take a breather or check all past tasks."
            : "No complaints match your active filter or search keywords."}
        </p>
        ${workerState.currentFilter !== 'ALL' ? `
          <button class="btn btn-outline btn-sm" onclick="setWorkerFilter('ALL')">View All Assigned Tasks</button>
        ` : ''}
      </div>
    `;
  }

  return `
    <div style="display:flex; flex-direction:column; gap:1.25rem;">
      ${complaints.map(c => renderWorkerComplaintCard(c)).join('')}
    </div>
  `;
}

function renderWorkerComplaintCard(c) {
  const statusStyles = {
    ASSIGNED: { bg: "#EFF6FF", color: "#1D4ED8", border: "#BFDBFE", label: "Assigned" },
    ACKNOWLEDGED: { bg: "#F5F3FF", color: "#6D28D9", border: "#DDD6FE", label: "Acknowledged" },
    IN_PROGRESS: { bg: "#FFFBEB", color: "#B45309", border: "#FDE68A", label: "In Progress" },
    RESOLVED: { bg: "#ECFDF5", color: "#047857", border: "#A7F3D0", label: "Resolved" },
    CLOSED: { bg: "#F8FAFC", color: "#475569", border: "#E2E8F0", label: "Closed" },
    REOPENED: { bg: "#FEF2F2", color: "#B91C1C", border: "#FECACA", label: "Reopened" }
  };

  const priorityStyles = {
    EMERGENCY: { bg: "#7F1D1D", color: "#FFFFFF" },
    HIGH: { bg: "#EF4444", color: "#FFFFFF" },
    MEDIUM: { bg: "#F59E0B", color: "#FFFFFF" },
    LOW: { bg: "#10B981", color: "#FFFFFF" }
  };

  const st = statusStyles[c.status] || { bg: "#F1F5F9", color: "#334155", border: "#CBD5E1", label: c.status };
  const pr = priorityStyles[c.priority] || { bg: "#64748B", color: "#FFFFFF" };

  const isResolvedOrClosed = ['RESOLVED', 'CLOSED'].includes(c.status);

  return `
    <div class="complaint-card" style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:1.5rem; box-shadow:var(--shadow-sm); transition:var(--transition); position:relative;" onmouseenter="this.style.boxShadow='var(--shadow-md)'" onmouseleave="this.style.boxShadow='var(--shadow-sm)'">
      <!-- Top Bar: ID, Status, Priority -->
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.75rem;">
        <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
          <span style="font-size:0.85rem; font-weight:700; color:var(--primary); font-family:monospace; background:rgba(15,23,42,0.06); padding:0.2rem 0.5rem; border-radius:var(--radius-sm);">
            ${c.complaint_id}
          </span>
          <span style="background:${st.bg}; color:${st.color}; border:1px solid ${st.border}; font-size:0.75rem; font-weight:700; padding:0.2rem 0.6rem; border-radius:20px;">
            ${st.label}
          </span>
          <span style="background:${pr.bg}; color:${pr.color}; font-size:0.7rem; font-weight:700; padding:0.15rem 0.5rem; border-radius:4px; text-transform:uppercase;">
            ${c.priority || 'MEDIUM'} Priority
          </span>
          ${c.category ? `
            <span style="background:#F1F5F9; color:#475569; font-size:0.75rem; font-weight:600; padding:0.2rem 0.5rem; border-radius:4px;">
              📁 ${c.category}
            </span>
          ` : ''}
        </div>

        <div style="font-size:0.75rem; color:var(--text-muted);">
          Assigned: ${c.assigned_at ? new Date(c.assigned_at).toLocaleDateString(undefined, {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}) : (c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recent')}
        </div>
      </div>

      <!-- Main Body -->
      <div style="display:flex; justify-content:space-between; gap:1.5rem; flex-wrap:wrap;">
        <div style="flex:1; min-width:280px;">
          <h3 style="font-size:1.15rem; font-weight:700; color:var(--text-main); margin-bottom:0.5rem; line-height:1.35;">
            ${c.title}
          </h3>
          <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem; line-height:1.5;">
            ${c.description}
          </p>

          <!-- Key Meta Items: Location, Citizen Contact -->
          <div style="display:flex; flex-wrap:wrap; gap:1.25rem; font-size:0.85rem; color:var(--text-muted); padding:0.75rem; background:var(--bg-main); border-radius:var(--radius-sm); margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:0.4rem;">
              <span>📍</span>
              <strong style="color:var(--text-main);">${c.location || c.address || 'Mumbai'}</strong>
            </div>
            ${c.citizen_name ? `
              <div style="display:flex; align-items:center; gap:0.4rem;">
                <span>👤</span>
                <span>Citizen: <strong style="color:var(--text-main);">${c.citizen_name}</strong></span>
              </div>
            ` : ''}
            ${c.citizen_phone ? `
              <div style="display:flex; align-items:center; gap:0.4rem;">
                <span>📞</span>
                <a href="tel:${c.citizen_phone}" style="color:var(--accent); font-weight:600; text-decoration:none;">
                  Call ${c.citizen_phone}
                </a>
              </div>
            ` : ''}
          </div>

          ${c.resolution_description ? `
            <div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:0.75rem 1rem; border-radius:var(--radius-sm); font-size:0.85rem; color:#065F46; margin-bottom:1rem;">
              <strong>✓ Resolution Notes:</strong> ${c.resolution_description}
            </div>
          ` : ''}
        </div>

        <!-- Thumbnail Image (if exists) -->
        ${c.image ? `
          <div style="width:120px; height:120px; border-radius:var(--radius-md); overflow:hidden; border:1px solid var(--border); flex-shrink:0; cursor:pointer;" onclick="previewImage('${c.image}')">
            <img src="${c.image}" alt="Site Photo" style="width:100%; height:100%; object-fit:cover; transition:transform 0.2s;" onmouseenter="this.style.transform='scale(1.05)'" onmouseleave="this.style.transform='scale(1)'" />
          </div>
        ` : ''}
      </div>

      <!-- Action Buttons Toolbar -->
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem; padding-top:1rem; border-top:1px solid var(--border); margin-top:0.5rem;">
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
          <!-- Quick Next Status Actions based on State Machine -->
          ${!isResolvedOrClosed ? `
            <button class="btn btn-primary btn-sm" onclick="openWorkerStatusModal('${c.complaint_id}', '${c.status}', '${escapeQuotes(c.title)}')">
              ⚡ Change Status
            </button>
            ${c.status === 'ASSIGNED' ? `
              <button class="btn btn-outline btn-sm" style="border-color:#DDD6FE; color:#6D28D9;" onclick="quickUpdateWorkerStatus('${c.complaint_id}', 'ACKNOWLEDGED')">
                👁️ Acknowledge Assignment
              </button>
            ` : ''}
            ${c.status === 'ACKNOWLEDGED' ? `
              <button class="btn btn-outline btn-sm" style="border-color:#FDE68A; color:#B45309;" onclick="quickUpdateWorkerStatus('${c.complaint_id}', 'IN_PROGRESS')">
                🚧 Begin Repair (In Progress)
              </button>
            ` : ''}
            ${c.status === 'IN_PROGRESS' ? `
              <button class="btn btn-sm" style="background:#10B981; color:#FFFFFF;" onclick="openWorkerStatusModal('${c.complaint_id}', 'IN_PROGRESS', '${escapeQuotes(c.title)}', 'RESOLVED')">
                ✅ Complete & Resolve
              </button>
            ` : ''}
          ` : `
            <span style="font-size:0.85rem; color:#059669; font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;">
              ✓ Task Completed
            </span>
          `}
        </div>

        <div>
          <button class="btn btn-outline btn-sm" onclick="navigate('/worker/complaints/${c.complaint_id}')">
            🔍 View Full Details & Site Map →
          </button>
        </div>
      </div>
    </div>
  `;
}

function escapeQuotes(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// Modal for Changing Status
function openWorkerStatusModal(complaintRef, currentStatus, title, preselectedStatus = null) {
  const modalRoot = document.getElementById("worker-modal-root");
  if (!modalRoot) return;

  const validNext = [];
  if (['ASSIGNED', 'REOPENED'].includes(currentStatus)) {
    validNext.push({ value: 'ACKNOWLEDGED', label: '👁️ Acknowledge Assignment', desc: 'Accept the dispatch task and confirm receipt' });
    validNext.push({ value: 'IN_PROGRESS', label: '🚧 In Progress', desc: 'Arrived on-site and commenced repair work' });
    validNext.push({ value: 'RESOLVED', label: '✅ Mark Resolved', desc: 'Repairs finished and issue addressed' });
  } else if (currentStatus === 'ACKNOWLEDGED') {
    validNext.push({ value: 'IN_PROGRESS', label: '🚧 In Progress', desc: 'Arrived on-site and commenced repair work' });
    validNext.push({ value: 'RESOLVED', label: '✅ Mark Resolved', desc: 'Repairs finished and issue addressed' });
  } else if (currentStatus === 'IN_PROGRESS') {
    validNext.push({ value: 'RESOLVED', label: '✅ Mark Resolved', desc: 'Repairs finished and verified working' });
  }

  const defaultNext = preselectedStatus || (validNext.length > 0 ? validNext[0].value : '');

  modalRoot.innerHTML = `
    <div style="position:fixed; inset:0; background:rgba(15,23,42,0.65); backdrop-filter:blur(4px); z-index:9999; display:flex; align-items:center; justify-content:center; padding:1.5rem;" onclick="if(event.target === this) closeWorkerModal()">
      <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); width:100%; max-width:540px; box-shadow:var(--shadow-lg); overflow:hidden; animation:slideDown 0.2s ease-out;">
        <!-- Modal Header -->
        <div style="padding:1.25rem 1.5rem; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; background:var(--bg-main);">
          <div>
            <h3 style="margin:0; font-size:1.15rem; color:var(--text-main); font-weight:800;">Update Complaint Status</h3>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.2rem;">
              Task Ref: <strong>${complaintRef}</strong>
            </div>
          </div>
          <button style="background:none; border:none; font-size:1.4rem; color:var(--text-muted); cursor:pointer; padding:0.2rem 0.5rem;" onclick="closeWorkerModal()">&times;</button>
        </div>

        <!-- Modal Body -->
        <form onsubmit="handleWorkerStatusSubmit(event, '${complaintRef}')" style="padding:1.5rem;">
          <div style="font-size:0.9rem; font-weight:600; color:var(--text-main); margin-bottom:0.75rem;">
            Current Status: <span class="badge" style="background:#EFF6FF; color:#1D4ED8; padding:0.2rem 0.5rem;">${currentStatus}</span>
          </div>

          <!-- Select New Status -->
          <div class="form-group" style="margin-bottom:1.25rem;">
            <label class="form-label" style="font-weight:700;">Select New Status <span class="req">*</span></label>
            <div style="display:flex; flex-direction:column; gap:0.5rem;">
              ${validNext.map(opt => `
                <label style="display:flex; align-items:flex-start; gap:0.75rem; padding:0.75rem 1rem; border:1px solid var(--border); border-radius:var(--radius-md); cursor:pointer; background:${opt.value === defaultNext ? 'rgba(37,99,235,0.05)' : 'var(--bg-surface)'};" onclick="handleStatusRadioChange('${opt.value}')">
                  <input type="radio" name="modal_new_status" value="${opt.value}" ${opt.value === defaultNext ? 'checked' : ''} style="margin-top:0.25rem;" />
                  <div>
                    <div style="font-weight:700; font-size:0.9rem; color:var(--text-main);">${opt.label}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${opt.desc}</div>
                  </div>
                </label>
              `).join('')}
            </div>
          </div>

          <!-- Resolution Summary (Conditional) -->
          <div id="resolution-desc-container" class="form-group" style="margin-bottom:1.25rem; display:${defaultNext === 'RESOLVED' ? 'block' : 'none'};">
            <label class="form-label" style="font-weight:700; color:#047857;">Resolution Summary / Work Done <span class="req">*</span></label>
            <textarea id="modal-resolution-desc" class="form-control" rows="3" placeholder="Describe work completed (e.g. Pipeline joint welded, sealed with rubber sleeve, water pressure tested and operational)."></textarea>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">
              This description is shown to the citizen and department engineer.
            </div>
          </div>

          <!-- Field Work Notes / Comment -->
          <div class="form-group" style="margin-bottom:1.5rem;">
            <label class="form-label" style="font-weight:700;">Field Work Notes / Comment (Optional)</label>
            <input type="text" id="modal-worker-comment" class="form-control" placeholder="e.g. Arrived on location with replacement parts" />
          </div>

          <!-- Action Buttons -->
          <div style="display:flex; justify-content:flex-end; gap:0.75rem; pt:1rem; border-top:1px solid var(--border); margin-top:1.5rem; padding-top:1rem;">
            <button type="button" class="btn btn-outline" onclick="closeWorkerModal()">Cancel</button>
            <button type="submit" id="btn-submit-status" class="btn btn-primary" style="min-width:130px;">
              Save & Update
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
}

function handleStatusRadioChange(val) {
  const resContainer = document.getElementById("resolution-desc-container");
  if (resContainer) {
    resContainer.style.display = val === 'RESOLVED' ? 'block' : 'none';
  }
}

function closeWorkerModal() {
  const modalRoot = document.getElementById("worker-modal-root");
  if (modalRoot) modalRoot.innerHTML = '';
}

async function handleWorkerStatusSubmit(event, complaintRef) {
  event.preventDefault();
  const btn = document.getElementById("btn-submit-status");
  const selectedRadio = document.querySelector('input[name="modal_new_status"]:checked');
  if (!selectedRadio) {
    showToast("Please choose a new status.", "error");
    return;
  }

  const newStatus = selectedRadio.value;
  const comment = document.getElementById("modal-worker-comment")?.value.trim() || '';
  const resolution_description = document.getElementById("modal-resolution-desc")?.value.trim() || '';

  if (newStatus === 'RESOLVED' && !resolution_description) {
    showToast("Please provide a resolution summary describing the completed work.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Updating...";

  try {
    const res = await apiFetch(`/api/worker/complaints/${complaintRef}/status`, {
      method: "POST",
      body: JSON.stringify({
        status: newStatus,
        comment: comment || `Status updated to ${newStatus}`,
        resolution_description: resolution_description || null
      })
    });

    if (res && res.success) {
      showToast(`Complaint ${complaintRef} updated to ${newStatus}!`, "success");
      closeWorkerModal();
      // Reload dashboard data
      renderWorkerDashboard();
    }
  } catch (err) {
    showToast(err.message || "Failed to update complaint status.", "error");
    btn.disabled = false;
    btn.textContent = "Save & Update";
  }
}

// Quick 1-Click Update helper
async function quickUpdateWorkerStatus(complaintRef, newStatus) {
  const confirmMsg = `Are you sure you want to transition task ${complaintRef} to ${newStatus}?`;
  if (!confirm(confirmMsg)) return;

  try {
    const res = await apiFetch(`/api/worker/complaints/${complaintRef}/status`, {
      method: "POST",
      body: JSON.stringify({
        status: newStatus,
        comment: `Field Worker changed status to ${newStatus}`
      })
    });

    if (res && res.success) {
      showToast(`Task ${complaintRef} transitioned to ${newStatus}!`, "success");
      renderWorkerDashboard();
    }
  } catch (err) {
    showToast(err.message || "Failed to update status", "error");
  }
}

// Worker Self-Toggle Availability
async function toggleWorkerAvailability() {
  const btn = document.getElementById("btn-toggle-availability");
  if (btn) btn.disabled = true;

  try {
    const res = await apiFetch("/api/worker/toggle-status", {
      method: "POST"
    });

    if (res && res.success) {
      showToast(res.message, "success");
      // Update local state and DOM elements
      workerState.profile.worker_status = res.worker_status;

      const isFree = res.worker_status === true;
      const badge = document.getElementById("worker-status-badge");
      const text = document.getElementById("worker-status-text");

      if (badge && text) {
        badge.style.background = isFree ? "#ECFDF5" : "#FFFBEB";
        badge.style.color = isFree ? "#065F46" : "#92400E";
        badge.style.borderColor = isFree ? "#A7F3D0" : "#FDE68A";
        badge.innerHTML = `<span>${isFree ? "🟢" : "🟠"}</span><span>${isFree ? "Available (Free)" : "On Task (Busy)"}</span>`;
      }
    }
  } catch (err) {
    showToast(err.message || "Failed to toggle status", "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Full Detail View for a Complaint
async function renderWorkerComplaintDetail(complaintRef) {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="main-content" style="max-width:1100px; margin:0 auto; padding:2rem 1.5rem;">
      <div style="text-align:center; padding:3rem 0;">
        <div style="font-size:2rem; margin-bottom:1rem;">⏳</div>
        <p style="color:var(--text-muted); font-weight:500;">Loading Task Details...</p>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch(`/api/worker/complaints/${complaintRef}`);
    if (!res || !res.complaint) {
      throw new Error("Complaint not found or not assigned to you.");
    }
    const c = res.complaint;
    buildWorkerComplaintDetailHTML(c);
  } catch (err) {
    root.innerHTML = `
      <div class="main-content" style="max-width:700px; margin:4rem auto; text-align:center;">
        <div style="font-size:3rem; margin-bottom:1rem;">⚠️</div>
        <h2 style="color:var(--danger); margin-bottom:0.5rem;">Access Denied / Not Found</h2>
        <p style="color:var(--text-muted); margin-bottom:1.5rem;">${err.message}</p>
        <button class="btn btn-primary" onclick="navigate('/worker/dashboard')">Back to My Tasks</button>
      </div>
    `;
  }
}

function buildWorkerComplaintDetailHTML(c) {
  const root = document.getElementById("app-root");

  const statusStyles = {
    ASSIGNED: { bg: "#EFF6FF", color: "#1D4ED8", border: "#BFDBFE" },
    ACKNOWLEDGED: { bg: "#F5F3FF", color: "#6D28D9", border: "#DDD6FE" },
    IN_PROGRESS: { bg: "#FFFBEB", color: "#B45309", border: "#FDE68A" },
    RESOLVED: { bg: "#ECFDF5", color: "#047857", border: "#A7F3D0" },
    CLOSED: { bg: "#F8FAFC", color: "#475569", border: "#E2E8F0" },
    REOPENED: { bg: "#FEF2F2", color: "#B91C1C", border: "#FECACA" }
  };
  const st = statusStyles[c.status] || { bg: "#F1F5F9", color: "#334155", border: "#CBD5E1" };

  root.innerHTML = `
    <div class="main-content" style="max-width:1100px; margin:0 auto; padding:1.5rem 1.5rem 4rem;">
      <!-- Top Navigation & Action -->
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom:1.5rem;">
        <button class="btn btn-outline btn-sm" onclick="navigate('/worker/dashboard')">
          ← Back to Assigned Tasks
        </button>
        <div style="display:flex; gap:0.5rem; align-items:center;">
          <span style="background:${st.bg}; color:${st.color}; border:1px solid ${st.border}; font-size:0.8rem; font-weight:700; padding:0.25rem 0.75rem; border-radius:20px;">
            ${c.status}
          </span>
          <span class="badge" style="background:#0F172A; color:#FFFFFF; font-size:0.8rem; padding:0.25rem 0.6rem;">
            ${c.priority} Priority
          </span>
        </div>
      </div>

      <!-- Main Layout: 2 Columns -->
      <div style="display:grid; grid-template-columns:1fr 340px; gap:1.75rem; align-items:start;">
        <!-- Left Column: Details, Map, Photos -->
        <div>
          <!-- Title & Overview Card -->
          <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:2rem; box-shadow:var(--shadow-sm); margin-bottom:1.75rem;">
            <div style="font-size:0.8rem; color:var(--text-muted); font-family:monospace; margin-bottom:0.5rem;">
              REF: ${c.complaint_id} • Category: ${c.category || 'General Civic'}
            </div>
            <h1 style="font-size:1.6rem; font-weight:800; color:var(--text-main); margin-bottom:1rem; line-height:1.3;">
              ${c.title}
            </h1>
            <p style="color:var(--text-main); font-size:0.95rem; line-height:1.6; margin-bottom:1.5rem; white-space:pre-line;">
              ${c.description}
            </p>

            <!-- Metadata Pills -->
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; padding:1rem; background:var(--bg-main); border-radius:var(--radius-md);">
              <div>
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Citizen Contact</div>
                <div style="font-weight:600; color:var(--text-main); font-size:0.9rem; margin-top:0.2rem;">${c.citizen_name || 'Citizen'}</div>
                ${c.citizen_phone ? `
                  <a href="tel:${c.citizen_phone}" style="color:var(--accent); font-size:0.85rem; font-weight:600; text-decoration:none;">
                    📞 ${c.citizen_phone} (Call)
                  </a>
                ` : ''}
              </div>

              <div>
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Location Details</div>
                <div style="font-weight:600; color:var(--text-main); font-size:0.9rem; margin-top:0.2rem;">
                  ${c.address || c.area || 'Mumbai'}
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.city || 'Mumbai'}, ${c.cluster_name || ''}</div>
              </div>

              <div>
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Timeline</div>
                <div style="font-size:0.85rem; color:var(--text-main); margin-top:0.2rem;">
                  Reported: ${c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'}
                </div>
                ${c.resolved_at ? `<div style="font-size:0.85rem; color:#059669; font-weight:600;">Resolved: ${new Date(c.resolved_at).toLocaleDateString()}</div>` : ''}
              </div>
            </div>
          </div>

          <!-- Interactive Leaflet Map for Field Navigation -->
          <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; box-shadow:var(--shadow-sm); margin-bottom:1.75rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
              <h3 style="font-size:1.1rem; font-weight:700; color:var(--text-main); margin:0;">
                📍 Site Location & Coordinates
              </h3>
              ${c.latitude && c.longitude ? `
                <a href="https://www.google.com/maps/search/?api=1&query=${c.latitude},${c.longitude}" target="_blank" class="btn btn-outline btn-sm" style="font-size:0.75rem;">
                  🗺️ Open in Google Maps
                </a>
              ` : ''}
            </div>

            <div id="worker-detail-map" style="width:100%; height:280px; border-radius:var(--radius-md); border:1px solid var(--border); background:#F1F5F9;"></div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.6rem;">
              Coordinates: ${c.latitude || 19.0760}, ${c.longitude || 72.8777} &nbsp;•&nbsp; ${c.address || c.area || 'Mumbai'}
            </div>
          </div>

          <!-- Site Evidence Photos -->
          ${c.images && c.images.length > 0 ? `
            <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; box-shadow:var(--shadow-sm); margin-bottom:1.75rem;">
              <h3 style="font-size:1.1rem; font-weight:700; color:var(--text-main); margin-bottom:1rem;">
                📷 Citizen Site Photos
              </h3>
              <div style="display:flex; gap:1rem; flex-wrap:wrap;">
                ${c.images.map(img => `
                  <div style="width:200px; height:200px; border-radius:var(--radius-md); overflow:hidden; border:1px solid var(--border); cursor:pointer;" onclick="previewImage('${img}')">
                    <img src="${img}" alt="Complaint Photo" style="width:100%; height:100%; object-fit:cover;" />
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Right Column: Quick Status Update Panel & Timeline -->
        <div>
          <!-- Status Transition Control Card -->
          <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; box-shadow:var(--shadow-sm); margin-bottom:1.5rem;">
            <h3 style="font-size:1.1rem; font-weight:800; color:var(--text-main); margin-bottom:0.75rem; display:flex; align-items:center; gap:0.4rem;">
              <span>⚡</span> Update Task Status
            </h3>
            
            ${c.allowed_transitions && c.allowed_transitions.length > 0 ? `
              <form onsubmit="handleDetailStatusUpdate(event, '${c.complaint_id}')">
                <div class="form-group" style="margin-bottom:1rem;">
                  <label class="form-label" style="font-size:0.85rem; font-weight:700;">Transition To:</label>
                  <select id="detail-next-status" class="form-control" onchange="toggleDetailResolutionDesc(this.value)">
                    ${c.allowed_transitions.map(st => `
                      <option value="${st}">${st === 'ACKNOWLEDGED' ? '👁️ Acknowledge Assignment' : (st === 'IN_PROGRESS' ? '🚧 In Progress (On-Ground)' : '✅ Resolved')}</option>
                    `).join('')}
                  </select>
                </div>

                <div id="detail-resolution-box" class="form-group" style="margin-bottom:1rem; display:${c.allowed_transitions[0] === 'RESOLVED' ? 'block' : 'none'};">
                  <label class="form-label" style="font-size:0.85rem; font-weight:700; color:#047857;">Resolution Summary:</label>
                  <textarea id="detail-resolution-text" class="form-control" rows="3" placeholder="Describe actions taken to fix the issue"></textarea>
                </div>

                <div class="form-group" style="margin-bottom:1.25rem;">
                  <label class="form-label" style="font-size:0.85rem; font-weight:700;">Work Notes (Optional):</label>
                  <input type="text" id="detail-work-notes" class="form-control" placeholder="e.g. Arrived on site, valve replaced" />
                </div>

                <button type="submit" id="btn-detail-status-submit" class="btn btn-primary" style="width:100%; padding:0.65rem;">
                  Submit Status Change
                </button>
              </form>
            ` : `
              <div style="background:#ECFDF5; border:1px solid #A7F3D0; color:#065F46; padding:1rem; border-radius:var(--radius-md); font-size:0.85rem; text-align:center;">
                ✓ This complaint is marked as <strong>${c.status}</strong>. No further action required.
              </div>
            `}
          </div>

          <!-- Activity History Log -->
          <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; box-shadow:var(--shadow-sm);">
            <h3 style="font-size:1.05rem; font-weight:800; color:var(--text-main); margin-bottom:1rem;">
              📜 Activity Timeline
            </h3>

            <div style="display:flex; flex-direction:column; gap:1rem; position:relative;">
              ${(c.history || []).map(h => `
                <div style="display:flex; gap:0.75rem; align-items:flex-start;">
                  <div style="width:10px; height:10px; border-radius:50%; background:var(--accent); margin-top:0.35rem; flex-shrink:0;"></div>
                  <div>
                    <div style="font-weight:700; font-size:0.85rem; color:var(--text-main);">
                      ${h.status}
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">
                      ${h.actor_role} &nbsp;•&nbsp; ${new Date(h.timestamp).toLocaleDateString(undefined, {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}
                    </div>
                    ${h.comment ? `
                      <div style="font-size:0.8rem; color:var(--text-main); margin-top:0.25rem; background:var(--bg-main); padding:0.35rem 0.6rem; border-radius:var(--radius-sm);">
                        "${h.comment}"
                      </div>
                    ` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Initialize Map
  setTimeout(() => {
    initWorkerDetailMap(c.latitude || 19.0760, c.longitude || 72.8777, c.title);
  }, 100);
}

function toggleDetailResolutionDesc(val) {
  const box = document.getElementById("detail-resolution-box");
  if (box) {
    box.style.display = val === 'RESOLVED' ? 'block' : 'none';
  }
}

async function handleDetailStatusUpdate(event, complaintRef) {
  event.preventDefault();
  const btn = document.getElementById("btn-detail-status-submit");
  const nextStatus = document.getElementById("detail-next-status").value;
  const resolution_description = document.getElementById("detail-resolution-text")?.value.trim() || '';
  const comment = document.getElementById("detail-work-notes")?.value.trim() || '';

  if (nextStatus === 'RESOLVED' && !resolution_description) {
    showToast("Please provide a resolution summary describing how the issue was fixed.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Updating...";

  try {
    const res = await apiFetch(`/api/worker/complaints/${complaintRef}/status`, {
      method: "POST",
      body: JSON.stringify({
        status: nextStatus,
        comment: comment || `Status updated to ${nextStatus}`,
        resolution_description: resolution_description || null
      })
    });

    if (res && res.success) {
      showToast(`Complaint status successfully updated to ${nextStatus}!`, "success");
      // Reload current detail page
      renderWorkerComplaintDetail(complaintRef);
    }
  } catch (err) {
    showToast(err.message || "Failed to update status", "error");
    btn.disabled = false;
    btn.textContent = "Submit Status Change";
  }
}

function initWorkerDetailMap(lat, lng, title) {
  const el = document.getElementById("worker-detail-map");
  if (!el || typeof L === "undefined") return;

  try {
    const map = L.map('worker-detail-map').setView([lat, lng], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    L.marker([lat, lng])
      .addTo(map)
      .bindPopup(`<strong>${title || 'Task Site'}</strong><br/>Lat: ${lat}, Lng: ${lng}`)
      .openPopup();
  } catch (err) {
    console.warn("Leaflet Map init error:", err);
  }
}

function previewImage(src) {
  const modalRoot = document.getElementById("worker-modal-root") || document.body;
  const overlay = document.createElement("div");
  overlay.style.cssText = "position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:99999; display:flex; align-items:center; justify-content:center; padding:2rem; cursor:pointer;";
  overlay.innerHTML = `<img src="${src}" style="max-width:90vw; max-height:90vh; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.5);" />`;
  overlay.onclick = () => overlay.remove();
  modalRoot.appendChild(overlay);
}
