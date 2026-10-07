// UrbanSync — Citizen Module

function renderCitizenSidebar(activeRoute = "") {
  return `
    <div class="sidebar">
      <div>
        <div class="sidebar-heading">Citizen Portal</div>
        <ul class="sidebar-menu">
          <li class="sidebar-item">
            <a href="/citizen/dashboard" class="${activeRoute === '/citizen/dashboard' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/citizen/dashboard');">
              📊 <span>My Dashboard</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="/citizen/report" class="${activeRoute === '/citizen/report' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/citizen/report');">
              ✍️ <span>Register Complaint</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="/citizen/complaints" class="${activeRoute === '/citizen/complaints' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/citizen/complaints');">
              📁 <span>My Complaints</span>
            </a>
          </li>
        </ul>
      </div>

      <div class="sidebar-user">
        <div class="avatar-circle">👤</div>
        <div class="user-info">
          <span class="user-name">${state.user.full_name}</span>
          <span class="user-role-badge">Verified Citizen</span>
        </div>
      </div>
    </div>
  `;
}

// 1. Citizen Dashboard
async function renderCitizenDashboard() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderCitizenSidebar('/citizen/dashboard')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Citizen Command Hub</h1>
            <p class="page-subtitle">Track your reported civic complaints and submit new municipal grievances.</p>
          </div>
          <button class="btn btn-primary" onclick="navigate('/citizen/report')">
            📢 Register Complaint
          </button>
        </div>

        <div id="citizen-stats" class="cards-grid">
          <div class="stat-card"><div class="stat-desc">Loading summary...</div></div>
        </div>

        <div class="table-card">
          <div class="table-toolbar">
            <h3 style="font-size:1.1rem; color:var(--primary); font-weight:700;">Recent Complaints</h3>
            <button class="btn btn-outline btn-sm" onclick="navigate('/citizen/complaints')">View All</button>
          </div>
          <div id="recent-complaints-container" class="table-responsive">
            <div style="padding:2rem; text-align:center; color:var(--text-muted);">Loading complaints...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch("/api/complaints/my");
    if (!res || !res.success) return;

    const complaints = res.complaints;
    const total = complaints.length;
    const active = complaints.filter(c => ["PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS"].includes(c.status)).length;
    const resolved = complaints.filter(c => ["RESOLVED", "CLOSED"].includes(c.status)).length;

    const statsEl = document.getElementById("citizen-stats");
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-card">
          <div class="stat-header">Total Submitted <span>📁</span></div>
          <div class="stat-value">${total}</div>
          <div class="stat-desc">Your registered complaints</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Under Resolution <span>⏳</span></div>
          <div class="stat-value" style="color:var(--info);">${active}</div>
          <div class="stat-desc">Being addressed by BMC</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Resolved & Closed <span>✅</span></div>
          <div class="stat-value" style="color:var(--success);">${resolved}</div>
          <div class="stat-desc">Completed works</div>
        </div>
      `;
    }

    const container = document.getElementById("recent-complaints-container");
    if (!container) return;

    if (complaints.length === 0) {
      container.innerHTML = `
        <div style="padding:3rem 1.5rem; text-align:center;">
          <div style="font-size:2.5rem; margin-bottom:0.5rem;">🏙️</div>
          <h3 style="color:var(--primary); margin-bottom:0.25rem;">No Complaints Registered Yet</h3>
          <p style="color:var(--text-muted); font-size:0.875rem; margin-bottom:1.25rem;">
            Notice a pothole, broken streetlight, or garbage pile? Report it to the city.
          </p>
          <button class="btn btn-primary" onclick="navigate('/citizen/report')">Register Your First Complaint</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Complaint ID</th>
            <th>Title & Location</th>
            <th>Category</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${complaints.slice(0, 5).map(c => `
            <tr>
              <td><strong>${c.complaint_id}</strong></td>
              <td>
                <div style="font-weight:600; color:var(--primary);">${c.title}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.location}</div>
              </td>
              <td><span class="badge" style="background:#EEF2FF; color:#4338CA;">${c.category}</span></td>
              <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ')}</span></td>
              <td><span style="font-size:0.8rem; color:var(--text-light);">${new Date(c.created_at).toLocaleDateString()}</span></td>
              <td>
                <button class="btn btn-outline btn-sm" onclick="navigate('/citizen/complaints/${c.complaint_id}')">
                  View Detail
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load dashboard.", "error");
  }
}

// 2. Register Complaint (Section 18 UI Requirements)
function renderCitizenReportForm() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderCitizenSidebar('/citizen/report')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Register Complaint</h1>
            <p class="page-subtitle">Submit civic issues directly to Mumbai Municipal Corporation.</p>
          </div>
        </div>

        <div style="max-width:760px; background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:2rem; box-shadow:var(--shadow-sm);">
          <form id="complaint-form" onsubmit="handleCitizenComplaintSubmit(event)">
            
            <!-- Complaint Description -->
            <div class="form-group">
              <label class="form-label">Complaint Description <span class="req">*</span></label>
              <textarea 
                id="comp-desc" 
                class="form-control" 
                rows="4" 
                placeholder="Example: There is garbage piling up near my building for the last three days or Huge pothole on the road..." 
                required
              ></textarea>
              <div style="font-size:0.75rem; color:var(--text-light); margin-top:0.25rem;">
                Be descriptive. Our system automatically categorizes the grievance into the responsible municipal department.
              </div>
            </div>

            <!-- Incident Location -->
            <div class="form-group">
              <label class="form-label">Location <span class="req">*</span></label>
              <input 
                type="text" 
                id="comp-location" 
                class="form-control" 
                placeholder="e.g. Near Vidyavihar Station East, LBS Road" 
                required 
              />
            </div>

            <!-- GPS Geolocation Trigger -->
            <div style="margin-bottom:1.25rem; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.5rem;">
              <span style="font-size:0.85rem; font-weight:600; color:var(--primary);">Incident Coordinates</span>
              <button type="button" class="btn btn-secondary btn-sm" onclick="useCurrentLocation()">
                📍 Use Current Location
              </button>
            </div>

            <!-- Latitude & Longitude -->
            <div class="form-row form-group">
              <div style="flex:1;">
                <label class="form-label">Latitude <span class="req">*</span></label>
                <input 
                  type="number" 
                  step="any" 
                  id="comp-lat" 
                  class="form-control" 
                  placeholder="e.g. 19.0760" 
                  required 
                />
              </div>
              <div style="flex:1;">
                <label class="form-label">Longitude <span class="req">*</span></label>
                <input 
                  type="number" 
                  step="any" 
                  id="comp-lon" 
                  class="form-control" 
                  placeholder="e.g. 72.8777" 
                  required 
                />
              </div>
            </div>

            <!-- Upload Optional Complaint Image -->
            <div class="form-group">
              <label class="form-label">Upload Image <span style="font-size:0.75rem; color:var(--text-light); font-weight:normal;">(Optional site photo)</span></label>
              <input 
                type="file" 
                id="comp-image" 
                class="form-control" 
                accept="image/*" 
              />
            </div>

            <div style="margin-top:2rem;">
              <button type="submit" id="comp-submit-btn" class="btn btn-primary btn-lg" style="width:100%;">
                Submit Complaint
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
}

// Geolocation Handler
function useCurrentLocation() {
  if (!navigator.geolocation) {
    showToast("Geolocation is not supported by your browser.", "error");
    return;
  }
  showToast("Locating your GPS coordinates...", "info");
  navigator.geolocation.getCurrentPosition(
    pos => {
      document.getElementById("comp-lat").value = pos.coords.latitude.toFixed(6);
      document.getElementById("comp-lon").value = pos.coords.longitude.toFixed(6);
      showToast("GPS coordinates acquired successfully.", "success");
    },
    err => {
      // Default to Mumbai center if permission denied
      document.getElementById("comp-lat").value = "19.0760";
      document.getElementById("comp-lon").value = "72.8777";
      showToast("Could not retrieve GPS. Populated default Mumbai coordinates.", "warning");
    },
    { enableHighAccuracy: true, timeout: 8000 }
  );
}

// Complaint Submission Handler
async function handleCitizenComplaintSubmit(event) {
  event.preventDefault();
  const submitBtn = document.getElementById("comp-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerText = "Submitting Complaint...";

  const description = document.getElementById("comp-desc").value.trim();
  const address = document.getElementById("comp-location").value.trim();
  const latitude = document.getElementById("comp-lat").value.trim();
  const longitude = document.getElementById("comp-lon").value.trim();
  const imageInput = document.getElementById("comp-image");

  const formData = new FormData();
  formData.append("description", description);
  formData.append("address", address);
  formData.append("latitude", latitude);
  formData.append("longitude", longitude);

  if (imageInput && imageInput.files[0]) {
    formData.append("image", imageInput.files[0]);
  }

  try {
    const res = await apiFetch("/api/complaints", {
      method: "POST",
      body: formData
    });

    if (res && res.success) {
      showComplaintSuccessModal(res);
    }
  } catch (err) {
    showToast(err.message || "Failed to submit complaint.", "error");
    submitBtn.disabled = false;
    submitBtn.innerText = "Submit Complaint";
  }
}

// Section 18: Success Modal strictly displaying Assigned Category without confidence
function showComplaintSuccessModal(data) {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box" style="text-align:center;">
      <div style="font-size:3rem; margin-bottom:0.75rem;">🎉</div>
      <h2 style="color:var(--primary); font-size:1.5rem; margin-bottom:1.5rem;">Complaint Registered Successfully</h2>

      <div style="background:#F8FAFC; border:1px solid var(--border); border-radius:var(--radius-md); padding:1.5rem; margin-bottom:1.5rem; text-align:left;">
        <div style="margin-bottom:0.85rem;">
          <span style="font-size:0.8rem; color:var(--text-muted); display:block;">Complaint ID:</span>
          <strong style="font-size:1.15rem; color:var(--primary);">${data.complaint_id}</strong>
        </div>

        <div style="margin-bottom:0.85rem;">
          <span style="font-size:0.8rem; color:var(--text-muted); display:block;">Assigned Category:</span>
          <span class="badge" style="background:#DBEAFE; color:#1E40AF; font-size:0.9rem; padding:0.35rem 0.75rem;">
            ${data.category || data.predicted_category}
          </span>
        </div>

        <div>
          <span style="font-size:0.8rem; color:var(--text-muted); display:block;">Status:</span>
          <span class="badge badge-PENDING" style="font-size:0.85rem; padding:0.3rem 0.7rem;">Pending</span>
        </div>
      </div>

      <div style="display:flex; gap:0.75rem; justify-content:center;">
        <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove(); navigate('/citizen/report');">
          Register Another
        </button>
        <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove(); navigate('/citizen/complaints/${data.complaint_id}');">
          View Complaint Details
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

// 3. Citizen Complaints List
async function renderCitizenComplaintsList() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderCitizenSidebar('/citizen/complaints')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">My Registered Complaints</h1>
            <p class="page-subtitle">Track status transitions, department routing, and resolution updates.</p>
          </div>
          <button class="btn btn-primary" onclick="navigate('/citizen/report')">📢 Register New</button>
        </div>

        <div class="table-card">
          <div id="complaints-list-container" class="table-responsive">
            <div style="padding:2.5rem; text-align:center; color:var(--text-muted);">Loading complaints...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch("/api/complaints/my");
    const container = document.getElementById("complaints-list-container");
    if (!container || !res || !res.success) return;

    if (res.complaints.length === 0) {
      container.innerHTML = `<div style="padding:3rem; text-align:center; color:var(--text-muted);">No complaints found.</div>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Complaint ID</th>
            <th>Title & Location</th>
            <th>Category</th>
            <th>Routed Department</th>
            <th>Status</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${res.complaints.map(c => `
            <tr>
              <td><strong>${c.complaint_id}</strong></td>
              <td>
                <div style="font-weight:600;">${c.title}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.location}</div>
              </td>
              <td><span class="badge" style="background:#EEF2FF; color:#4338CA;">${c.category}</span></td>
              <td>${c.department}</td>
              <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ')}</span></td>
              <td><span style="font-size:0.8rem; color:var(--text-light);">${new Date(c.created_at).toLocaleDateString()}</span></td>
              <td>
                <button class="btn btn-outline btn-sm" onclick="navigate('/citizen/complaints/${c.complaint_id}')">
                  View Detail
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

// 4. Citizen Complaint Detail View
async function renderCitizenComplaintDetail(complaintRef) {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderCitizenSidebar('/citizen/complaints')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Complaint: ${complaintRef}</h1>
            <p class="page-subtitle">Real-time status updates, municipal dispatch, and resolution verification.</p>
          </div>
          <button class="btn btn-outline btn-sm" onclick="navigate('/citizen/complaints')">← Back to List</button>
        </div>

        <div id="complaint-detail-content">
          <div class="stat-card"><div class="stat-desc">Loading complaint details...</div></div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch(`/api/complaints/${complaintRef}`);
    const container = document.getElementById("complaint-detail-content");
    if (!container || !res || !res.success) return;

    const c = res.complaint;

    container.innerHTML = `
      <div style="display:grid; grid-template-columns:2fr 1fr; gap:1.5rem;">
        <div>
          <!-- Summary Card -->
          <div class="stat-card" style="padding:1.75rem; margin-bottom:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
              <span class="badge badge-${c.status}" style="font-size:0.85rem; padding:0.35rem 0.75rem;">${c.status.replace('_', ' ')}</span>
              <span style="font-size:0.8rem; color:var(--text-light);">Submitted: ${new Date(c.created_at).toLocaleString()}</span>
            </div>

            <h2 style="color:var(--primary); font-size:1.35rem; margin-bottom:0.75rem;">${c.title}</h2>
            <p style="color:var(--text-main); font-size:0.95rem; line-height:1.6; margin-bottom:1.5rem;">${c.description}</p>

            ${c.image ? `
              <div style="margin-bottom:1.5rem;">
                <label class="form-label">Attached Site Image:</label>
                <img src="${c.image}" alt="Site Photo" style="max-height:260px; border-radius:var(--radius-md); border:1px solid var(--border); object-fit:cover;" />
              </div>
            ` : ''}

            ${c.resolution_description ? `
              <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:var(--radius-md); padding:1.25rem; margin-top:1rem;">
                <div style="font-weight:700; color:#065F46; margin-bottom:0.25rem;">✅ Municipal Resolution Report:</div>
                <div style="color:#047857; font-size:0.9rem;">${c.resolution_description}</div>
              </div>
            ` : ''}

            <!-- Citizen Confirm Close Button if status is RESOLVED -->
            ${c.status === 'RESOLVED' ? `
              <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:var(--radius-md); padding:1.25rem; margin-top:1.5rem; display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <div style="font-weight:700; color:#1E40AF;">Is this issue satisfactorily resolved?</div>
                  <div style="font-size:0.8rem; color:#3B82F6;">Please verify the works and confirm closure.</div>
                </div>
                <button class="btn btn-success" onclick="handleCitizenConfirmClose('${c.complaint_id}')">
                  Confirm & Close Complaint
                </button>
              </div>
            ` : ''}
          </div>

          <!-- History Timeline -->
          <div class="stat-card" style="padding:1.5rem;">
            <h3 style="font-size:1.1rem; color:var(--primary); margin-bottom:1rem;">Lifecycle Audit Trail</h3>
            <div style="display:flex; flex-direction:column; gap:0.85rem;">
              ${c.history.map(h => `
                <div style="display:flex; gap:1rem; border-left:2px solid var(--accent); padding-left:1rem;">
                  <div>
                    <div style="font-size:0.85rem; font-weight:700; color:var(--primary);">${h.status}</div>
                    <div style="font-size:0.8rem; color:var(--text-muted);">${h.comment}</div>
                    <div style="font-size:0.75rem; color:var(--text-light);">${new Date(h.timestamp).toLocaleString()} • ${h.actor_role}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Sidebar Info -->
        <div>
          <div class="stat-card" style="padding:1.5rem; margin-bottom:1.5rem;">
            <h3 style="font-size:1.05rem; color:var(--primary); margin-bottom:1rem;">Municipal Details</h3>
            
            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Category:</span>
              <span class="badge" style="background:#DBEAFE; color:#1E40AF;">${c.category}</span>
            </div>

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Responsible Department:</span>
              <strong style="font-size:0.85rem;">${c.department}</strong>
            </div>

            ${c.assigned_department_head ? `
              <div style="margin-bottom:0.85rem;">
                <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Assigned Department Head:</span>
                <strong style="font-size:0.85rem; color:var(--accent);">${c.assigned_department_head}</strong>
              </div>
            ` : ''}

            ${c.assigned_worker ? `
              <div style="margin-bottom:0.85rem; background:#F8FAFC; border:1px solid var(--border); border-radius:var(--radius-sm); padding:0.75rem;">
                <span style="font-size:0.75rem; color:var(--text-muted); display:block; margin-bottom:0.25rem;">Dispatched Field Worker:</span>
                <strong style="font-size:0.85rem; color:var(--primary);">👷 ${c.assigned_worker.name}</strong>
                <div style="font-size:0.75rem; color:var(--text-muted);">${c.assigned_worker.designation} (${c.assigned_worker.worker_code})</div>
                <div style="font-size:0.75rem; color:var(--accent); margin-top:0.25rem;">📞 ${c.assigned_worker.phone}</div>
              </div>
            ` : ''}

            <div style="margin-bottom:0.85rem;">
              <span style="font-size:0.75rem; color:var(--text-muted); display:block;">Geographic Location:</span>
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

async function handleCitizenConfirmClose(complaintRef) {
  try {
    const res = await apiFetch(`/api/complaints/${complaintRef}/resolve`, { method: "POST" });
    if (res && res.success) {
      showToast("Complaint marked as closed. Thank you!", "success");
      renderCitizenComplaintDetail(complaintRef);
    }
  } catch (err) {
    showToast(err.message || "Failed to confirm resolution.", "error");
  }
}
