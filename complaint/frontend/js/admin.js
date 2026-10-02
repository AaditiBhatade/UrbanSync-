// UrbanSync — Department Admin & Hotspot Analytics Module

let hotspotMap = null;

function renderAdminSidebar(activeRoute = "") {
  return `
    <div class="sidebar">
      <div>
        <div class="sidebar-heading">${state.user.department_code || 'BMC'} Operations</div>
        <ul class="sidebar-menu">
          <li class="sidebar-item">
            <a href="/admin/dashboard" class="${activeRoute === '/admin/dashboard' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/admin/dashboard');">
              📁 <span>Department Queue</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="/admin/city-analytics" class="${activeRoute.includes('analytics') ? 'active' : ''}" onclick="event.preventDefault(); navigate('/admin/city-analytics');">
              🗺️ <span>City Analytics & Hotspots</span>
            </a>
          </li>
        </ul>
      </div>

      <div class="sidebar-user">
        <div class="avatar-circle">🏛️</div>
        <div class="user-info">
          <span class="user-name">${state.user.full_name}</span>
          <span class="user-role-badge">${state.user.department_code || 'BMC'} Admin</span>
        </div>
      </div>
    </div>
  `;
}

// 1. Department Admin Dashboard & Complaints Queue
async function renderAdminDashboard() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderAdminSidebar('/admin/dashboard')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">${state.user.department_code || 'Municipal'} Operations Queue</h1>
            <p class="page-subtitle">Triage, dispatch field engineers, and manage complaint lifecycle.</p>
          </div>
          <button class="btn btn-outline" onclick="navigate('/admin/city-analytics')">
            🗺️ View City Hotspots
          </button>
        </div>

        <div id="admin-stats-grid" class="cards-grid">
          <div class="stat-card"><div class="stat-desc">Loading statistics...</div></div>
        </div>

        <div class="table-card">
          <div class="table-toolbar">
            <div style="font-weight:700; color:var(--primary);">Department Complaints</div>
            <div class="table-filters">
              <select id="admin-status-filter" class="select-input" onchange="loadAdminComplaints()">
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>

          <div id="admin-complaints-container" class="table-responsive">
            <div style="padding:2.5rem; text-align:center; color:var(--text-muted);">Loading department queue...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  loadAdminComplaints();
}

async function loadAdminComplaints() {
  const filter = document.getElementById("admin-status-filter") ? document.getElementById("admin-status-filter").value : "ALL";
  try {
    const res = await apiFetch(`/api/admin/complaints?status_filter=${filter}`);
    const container = document.getElementById("admin-complaints-container");
    const statsEl = document.getElementById("admin-stats-grid");
    if (!container || !res || !res.success) return;

    const complaints = res.complaints;
    const total = complaints.length;
    const pending = complaints.filter(c => ["PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS"].includes(c.status)).length;
    const resolved = complaints.filter(c => ["RESOLVED", "CLOSED"].includes(c.status)).length;

    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-card">
          <div class="stat-header">Total in Queue <span>📁</span></div>
          <div class="stat-value">${total}</div>
          <div class="stat-desc">${state.user.department_code || 'Assigned'} department</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Active / Pending <span>⏳</span></div>
          <div class="stat-value" style="color:var(--info);">${pending}</div>
          <div class="stat-desc">Requiring action or ongoing</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Resolved & Closed <span>✅</span></div>
          <div class="stat-value" style="color:var(--success);">${resolved}</div>
          <div class="stat-desc">Completed municipal works</div>
        </div>
      `;
    }

    if (complaints.length === 0) {
      container.innerHTML = `<div style="padding:3rem; text-align:center; color:var(--text-muted);">No complaints in this queue.</div>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Citizen & Contact</th>
            <th>Title & Location</th>
            <th>Category</th>
            <th>Assigned Head</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${complaints.map(c => `
            <tr>
              <td><strong>${c.complaint_id}</strong></td>
              <td>
                <div style="font-weight:600;">${c.citizen_name}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.citizen_mobile || '--'}</div>
              </td>
              <td>
                <div style="font-weight:600; max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${c.title}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.location}</div>
              </td>
              <td><span class="badge" style="background:#EEF2FF; color:#4338CA;">${c.category}</span></td>
              <td>
                ${c.assigned_department_head ? `<span style="font-size:0.8rem; font-weight:600; color:var(--accent);">${c.assigned_department_head}</span>` : `<span style="font-size:0.8rem; color:var(--text-light);">Unassigned</span>`}
              </td>
              <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ')}</span></td>
              <td>
                <button class="btn btn-primary btn-sm" onclick="navigate('/admin/complaints/${c.complaint_id}')">
                  Manage
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load complaints.", "error");
  }
}

// 2. Department Admin Complaint Detail & Action View
async function renderAdminComplaintDetail(complaintRef) {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderAdminSidebar('/admin/dashboard')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Manage Complaint: ${complaintRef}</h1>
            <p class="page-subtitle">Review citizen grievance, update status, and assign responsible municipal engineer.</p>
          </div>
          <button class="btn btn-outline btn-sm" onclick="navigate('/admin/dashboard')">← Back to Queue</button>
        </div>

        <div id="admin-detail-content">
          <div class="stat-card"><div class="stat-desc">Loading complaint details...</div></div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch(`/api/admin/complaints/${complaintRef}`);
    const container = document.getElementById("admin-detail-content");
    if (!container || !res || !res.success) return;

    const c = res.complaint;

    container.innerHTML = `
      <div style="display:grid; grid-template-columns:2fr 1fr; gap:1.5rem;">
        <div>
          <!-- Complaint Information Card -->
          <div class="stat-card" style="padding:1.75rem; margin-bottom:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
              <span class="badge badge-${c.status}" style="font-size:0.85rem; padding:0.35rem 0.75rem;">${c.status.replace('_', ' ')}</span>
              <span style="font-size:0.8rem; color:var(--text-light);">${new Date(c.created_at).toLocaleString()}</span>
            </div>

            <h2 style="color:var(--primary); font-size:1.35rem; margin-bottom:0.75rem;">${c.title}</h2>
            <p style="color:var(--text-main); font-size:0.95rem; line-height:1.6; margin-bottom:1.5rem;">${c.description}</p>

            ${c.image ? `
              <div style="margin-bottom:1.5rem;">
                <label class="form-label">Citizen Uploaded Site Photo:</label>
                <img src="${c.image}" alt="Site Photo" style="max-height:280px; border-radius:var(--radius-md); border:1px solid var(--border); object-fit:cover;" />
              </div>
            ` : ''}

            <!-- Municipal Actions Toolbar -->
            <div style="display:flex; gap:0.75rem; flex-wrap:wrap; border-top:1px solid var(--border); padding-top:1.25rem;">
              <button class="btn btn-secondary" onclick="openAdminStatusModal('${c.complaint_id}', '${c.status}')">
                🔄 Update Status
              </button>
              <button class="btn btn-primary" onclick="openAdminAssignModal('${c.complaint_id}', '${c.assigned_department_head || ''}')">
                👷 Assign Department Head
              </button>
            </div>

            ${c.resolution_description ? `
              <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:var(--radius-md); padding:1rem; margin-top:1.25rem;">
                <strong style="color:#065F46;">Resolution Summary:</strong>
                <div style="color:#047857; font-size:0.875rem; margin-top:0.25rem;">${c.resolution_description}</div>
              </div>
            ` : ''}
          </div>

          <!-- History -->
          <div class="stat-card" style="padding:1.5rem;">
            <h3 style="font-size:1.05rem; color:var(--primary); margin-bottom:1rem;">Lifecycle & Audit Trail</h3>
            <div style="display:flex; flex-direction:column; gap:0.75rem;">
              ${c.history.map(h => `
                <div style="display:flex; gap:1rem; border-left:2px solid var(--accent); padding-left:1rem;">
                  <div>
                    <div style="font-size:0.85rem; font-weight:700;">${h.status}</div>
                    <div style="font-size:0.8rem; color:var(--text-muted);">${h.comment}</div>
                    <div style="font-size:0.75rem; color:var(--text-light);">${new Date(h.timestamp).toLocaleString()} • ${h.actor_role}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Sidebar Metadata -->
        <div>
          <div class="stat-card" style="padding:1.5rem; margin-bottom:1.5rem;">
            <h3 style="font-size:1.05rem; color:var(--primary); margin-bottom:1rem;">Grievance Details</h3>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Citizen:</span>
              <strong>${c.citizen_name}</strong>
              <div style="font-size:0.8rem; color:var(--text-light);">${c.citizen_phone || 'Phone not provided'}</div>
            </div>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Assigned Category:</span>
              <span class="badge" style="background:#DBEAFE; color:#1E40AF;">${c.category}</span>
            </div>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Civic Hotspot Zone:</span>
              <strong style="font-size:0.85rem; color:var(--purple);">${c.cluster_name}</strong>
            </div>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Assigned Department Head:</span>
              <strong style="font-size:0.85rem; color:var(--accent);">
                ${c.assigned_department_head || 'Not yet assigned'}
              </strong>
            </div>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Incident Location:</span>
              <span style="font-size:0.85rem;">${c.location}</span>
            </div>

            ${c.latitude && c.longitude ? `
              <div>
                <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Coordinates:</span>
                <span style="font-size:0.8rem; font-family:monospace;">${c.latitude}, ${c.longitude}</span>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load complaint detail.", "error");
  }
}

// 3. Status Transition Modal
function openAdminStatusModal(complaintRef, currentStatus) {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Update Complaint Status</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
      </div>
      <form onsubmit="handleAdminStatusSubmit(event, '${complaintRef}')">
        <div class="form-group">
          <label class="form-label">New Status <span class="req">*</span></label>
          <select id="modal-status-select" class="form-control select-input" required onchange="toggleResolutionField()">
            <option value="ACKNOWLEDGED" ${currentStatus === 'ACKNOWLEDGED' ? 'selected' : ''}>ACKNOWLEDGED — Department acknowledged</option>
            <option value="IN_PROGRESS" ${currentStatus === 'IN_PROGRESS' ? 'selected' : ''}>IN_PROGRESS — Field crew dispatched</option>
            <option value="RESOLVED" ${currentStatus === 'RESOLVED' ? 'selected' : ''}>RESOLVED — Works completed</option>
          </select>
        </div>

        <div class="form-group" id="resolution-group" style="display:none;">
          <label class="form-label">Resolution Description <span class="req">*</span></label>
          <textarea id="modal-resolution-desc" class="form-control" rows="3" placeholder="Detail the repairs and actions taken to rectify the issue..."></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Internal Comment</label>
          <input type="text" id="modal-status-comment" class="form-control" placeholder="Optional audit memo" />
        </div>

        <div style="display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button type="submit" class="btn btn-primary">Update Status</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  toggleResolutionField();
}

function toggleResolutionField() {
  const val = document.getElementById("modal-status-select").value;
  const resGroup = document.getElementById("resolution-group");
  if (resGroup) {
    resGroup.style.display = (val === "RESOLVED") ? "block" : "none";
  }
}

async function handleAdminStatusSubmit(event, complaintRef) {
  event.preventDefault();
  const status = document.getElementById("modal-status-select").value;
  const comment = document.getElementById("modal-status-comment").value.trim();
  const resDescInput = document.getElementById("modal-resolution-desc");
  const resolution_description = resDescInput ? resDescInput.value.trim() : "";

  if (status === "RESOLVED" && !resolution_description) {
    showToast("Please provide a resolution description when marking as resolved.", "warning");
    return;
  }

  const formData = new FormData();
  formData.append("status", status);
  if (comment) formData.append("comment", comment);
  if (resolution_description) formData.append("resolution_description", resolution_description);

  try {
    const res = await apiFetch(`/api/admin/complaints/${complaintRef}/status`, {
      method: "POST",
      body: formData
    });
    if (res && res.success) {
      document.querySelector(".modal-overlay").remove();
      showToast(res.message, "success");
      renderAdminComplaintDetail(complaintRef);
    }
  } catch (err) {
    showToast(err.message || "Failed to update status.", "error");
  }
}

// 4. Section 9 & 10: Manual Municipal Assignment Modal
function openAdminAssignModal(complaintRef, currentHead) {
  const officers = [
    "Hydraulic Engineer (Water Supply Operations)",
    "Chief Engineer (Roads & Infrastructure)",
    "Chief Engineer (Solid Waste Management)",
    "Superintending Engineer (Power & Illumination)",
    "Executive Engineer (Stormwater & Drainage)",
    "Deputy Commissioner of Traffic",
    "Chief Officer (Disaster Management & Safety)",
    "Executive Health Officer (Pollution Control)",
    "Superintendent of Gardens & Trees",
    "Assistant Municipal Commissioner (Ward Control)"
  ];

  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Manual Municipal Assignment</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
      </div>
      <form onsubmit="handleAdminAssignSubmit(event, '${complaintRef}')">
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.25rem;">
          In accordance with municipal governance, assign this categorized complaint directly to the responsible BMC department head or designated executive engineer.
        </p>

        <div class="form-group">
          <label class="form-label">Assign Department Head / Lead Engineer <span class="req">*</span></label>
          <select id="modal-dept-head" class="form-control select-input" required>
            ${officers.map(o => `
              <option value="${o}" ${currentHead === o ? 'selected' : ''}>${o}</option>
            `).join('')}
          </select>
        </div>

        <div style="display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button type="submit" class="btn btn-primary">Confirm Assignment</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

async function handleAdminAssignSubmit(event, complaintRef) {
  event.preventDefault();
  const department_head = document.getElementById("modal-dept-head").value;

  const formData = new FormData();
  formData.append("department_head", department_head);

  try {
    const res = await apiFetch(`/api/admin/complaints/${complaintRef}/assign`, {
      method: "POST",
      body: formData
    });
    if (res && res.success) {
      document.querySelector(".modal-overlay").remove();
      showToast(res.message, "success");
      renderAdminComplaintDetail(complaintRef);
    }
  } catch (err) {
    showToast(err.message || "Failed to assign department head.", "error");
  }
}

// 5. Section 2, 3, 6, 19: City Analytics & Hotspot Map Visualization
async function renderAdminMlAnalytics() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderAdminSidebar('/admin/city-analytics')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">City Analytics & Hotspot Overview</h1>
            <p class="page-subtitle">Overview of grievance distribution across municipal categories and geographic hotspot zones.</p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="initHotspotMap()">
            🗺️ Reset Map View
          </button>
        </div>

        <!-- Section 6: Interactive Mumbai Hotspot Map -->
        <div class="table-card" style="padding:1.5rem; margin-bottom:2rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
            <div>
              <h2 style="font-size:1.25rem; color:var(--primary); font-weight:800;">Geographic Complaint Hotspot Zones</h2>
              <p style="font-size:0.85rem; color:var(--text-muted);">
                Geographical grievance concentration mapped across Mumbai's administrative zones.
              </p>
            </div>
            <div id="hotspot-badge-container" style="display:flex; gap:0.5rem; flex-wrap:wrap;"></div>
          </div>

          <div id="hotspot-map" class="map-container"></div>
        </div>

        <!-- Section 19: Two-column overview grid -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;" class="detail-two-col">
          <!-- Component 1: 15 BMC Categories -->
          <div class="table-card" style="padding:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
              <h3 style="color:var(--primary); font-size:1.15rem; font-weight:700;">1. Grievance Distribution (15 Municipal Categories)</h3>
              <span class="badge" style="background:#DBEAFE; color:#1E40AF;">Municipal Classification</span>
            </div>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:1rem;">
              Distribution of complaints across Mumbai municipal service categories:
            </p>
            <div id="categories-table-container">
              <div style="padding:2rem; text-align:center; color:var(--text-muted);">Loading categories...</div>
            </div>
          </div>

          <!-- Component 2: Hotspot Zones List -->
          <div class="table-card" style="padding:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
              <h3 style="color:var(--primary); font-size:1.15rem; font-weight:700;">2. Civic Complaint Hotspots</h3>
              <span class="badge" style="background:#FCE7F3; color:#9D174D;">Geographic Zones (6 Areas)</span>
            </div>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:1rem;">
              Geographical complaint concentrations and key hotspot centers:
            </p>
            <div id="hotspots-table-container">
              <div style="padding:2rem; text-align:center; color:var(--text-muted);">Loading hotspots...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  loadMlAnalyticsData();
}

async function loadMlAnalyticsData() {
  try {
    const res = await apiFetch("/api/admin/city-analytics");
    if (!res || !res.success) return;

    // 1. Render Categories Table (Section 19)
    const catContainer = document.getElementById("categories-table-container");
    if (catContainer) {
      const maxCount = Math.max(...res.categories.map(c => c.count), 1);
      catContainer.innerHTML = `
        <table class="data-table" style="font-size:0.825rem;">
          <thead>
            <tr>
              <th>BMC Category</th>
              <th style="text-align:right;">Complaints</th>
              <th style="width:30%;">Distribution</th>
            </tr>
          </thead>
          <tbody>
            ${res.categories.map(c => {
              const pct = Math.round((c.count / maxCount) * 100);
              return `
                <tr>
                  <td><strong>${c.category}</strong></td>
                  <td style="text-align:right; font-weight:700;">${c.count.toLocaleString()}</td>
                  <td>
                    <div style="background:#F1F5F9; height:8px; border-radius:4px; overflow:hidden;">
                      <div style="background:var(--accent); height:100%; width:${pct}%;"></div>
                    </div>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;
    }

    // 2. Render Hotspots List
    const hotContainer = document.getElementById("hotspots-table-container");
    if (hotContainer) {
      hotContainer.innerHTML = res.hotspots.map(h => `
        <div style="background:#F8FAFC; border:1px solid var(--border); border-left:4px solid ${h.color || '#3B82F6'}; border-radius:var(--radius-sm); padding:1rem; margin-bottom:0.75rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
            <strong style="color:var(--primary); font-size:0.95rem;">Hotspot Zone ${h.cluster_id + 1}: ${h.zone_name}</strong>
            <span class="badge" style="background:#FFFFFF; border:1px solid var(--border); color:var(--primary); font-weight:700;">
              ${h.complaint_count.toLocaleString()} Complaints
            </span>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted); display:flex; justify-content:space-between; flex-wrap:wrap;">
            <span>Center: (${h.centroid_latitude}, ${h.centroid_longitude})</span>
            <span>${h.percentage || '0'}% of city grievances</span>
          </div>
        </div>
      `).join('');
    }

    // 3. Render Leaflet Map
    renderHotspotMap(res.hotspots);

  } catch (err) {
    showToast(err.message || "Failed to load analytics.", "error");
  }
}

function renderHotspotMap(hotspots) {
  const mapEl = document.getElementById("hotspot-map");
  if (!mapEl || typeof L === "undefined") return;

  if (hotspotMap) {
    hotspotMap.remove();
    hotspotMap = null;
  }

  // Centered on Mumbai
  hotspotMap = L.map("hotspot-map").setView([19.0760, 72.8777], 11);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '© OpenStreetMap contributors | UrbanSync Smart City'
  }).addTo(hotspotMap);

  hotspots.forEach(h => {
    const lat = h.centroid_latitude;
    const lon = h.centroid_longitude;
    const color = h.color || "#2563EB";

    // Cluster Area Circle (hotspot radius proportional to complaints)
    const radius = Math.min(3200, Math.max(1600, h.complaint_count * 0.7));
    L.circle([lat, lon], {
      color: color,
      fillColor: color,
      fillOpacity: 0.22,
      radius: radius
    }).addTo(hotspotMap);

    // Centroid Marker
    const marker = L.circleMarker([lat, lon], {
      radius: 9,
      fillColor: color,
      color: "#FFFFFF",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    }).addTo(hotspotMap);

    marker.bindPopup(`
      <div style="font-family:Inter, sans-serif; font-size:0.85rem; padding:0.25rem;">
        <strong style="color:${color}; font-size:0.95rem;">Hotspot Zone ${h.cluster_id + 1}</strong>
        <div style="font-weight:700; color:#0F172A; margin:0.25rem 0;">${h.zone_name}</div>
        <div style="color:#64748B;"><strong>Total Complaints:</strong> ${h.complaint_count.toLocaleString()}</div>
        <div style="color:#64748B;"><strong>Center:</strong> (${lat.toFixed(4)}, ${lon.toFixed(4)})</div>
      </div>
    `);
  });

  // Re-size after rendering
  setTimeout(() => {
    if (hotspotMap) hotspotMap.invalidateSize();
  }, 300);
}
