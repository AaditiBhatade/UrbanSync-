// UrbanSync - Super Admin Module

function renderSuperAdminSidebar(activeRoute = "") {
  return `
    <div class="sidebar">
      <div class="sidebar-heading">Super Admin Console</div>
      <ul class="sidebar-menu">
        <li class="sidebar-item">
          <a href="/super-admin/dashboard" class="${activeRoute === '/super-admin/dashboard' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/dashboard');">
            📊 <span>City Overview</span>
          </a>
        </li>
        <li class="sidebar-item">
          <a href="/super-admin/city-analytics" class="${activeRoute.includes('analytics') ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/city-analytics');">
            🗺️ <span>City Analytics & Hotspots</span>
          </a>
        </li>
        <li class="sidebar-item">
          <a href="/super-admin/triage-review" class="${activeRoute.includes('review') ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/triage-review');">
            📋 <span>Triage & Review Queue</span>
          </a>
        </li>
        <li class="sidebar-item">
          <a href="/super-admin/users" class="${activeRoute === '/super-admin/users' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/users');">
            👥 <span>User Directory</span>
          </a>
        </li>
        <li class="sidebar-item">
          <a href="/super-admin/departments" class="${activeRoute === '/super-admin/departments' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/departments');">
            🏛️ <span>Departments</span>
          </a>
        </li>
        <li class="sidebar-item">
          <a href="/super-admin/audit-logs" class="${activeRoute === '/super-admin/audit-logs' ? 'active' : ''}" onclick="event.preventDefault(); navigate('/super-admin/audit-logs');">
            📜 <span>Audit Trail</span>
          </a>
        </li>
      </ul>

      <div class="sidebar-user">
        <div class="avatar-circle" style="background:linear-gradient(135deg, #0F172A, #38BDF8);">
          👑
        </div>
        <div class="user-info">
          <span class="user-name">${state.user.full_name}</span>
          <span class="user-role-badge">Super Admin</span>
        </div>
      </div>
    </div>
  `;
}

// 1. Super Admin Dashboard
async function renderSuperAdminDashboard() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/dashboard')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">City Command Center</h1>
            <p class="page-subtitle">Unified civic operations, departmental metrics, and city management control.</p>
          </div>
          <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
            <button class="btn btn-outline btn-sm" onclick="navigate('/super-admin/city-analytics')">
              🗺️ City Hotspot Analytics
            </button>
            <button class="btn btn-secondary btn-sm" onclick="navigate('/super-admin/triage-review')">
              📋 Triage Queue
            </button>
            <button class="btn btn-primary btn-sm" onclick="openCreateAdminModal()">
              ➕ Add Dept Admin
            </button>
          </div>
        </div>

        <div id="super-stats-grid" class="cards-grid">
          <div class="stat-card"><div class="stat-value">...</div><div class="stat-desc">Loading metrics</div></div>
        </div>

        <!-- Breakdown Charts/Bars -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:2rem;" class="detail-two-col">
          <div class="table-card" style="padding:1.5rem;">
            <h3 style="color:var(--primary); font-size:1.1rem; margin-bottom:1rem;">Complaints by Municipal Department</h3>
            <div id="dept-breakdown-container">Loading...</div>
          </div>

          <div class="table-card" style="padding:1.5rem;">
            <h3 style="color:var(--primary); font-size:1.1rem; margin-bottom:1rem;">Top Grievance Categories</h3>
            <div id="cat-breakdown-container">Loading...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  loadSuperAdminDashboard();
}

async function loadSuperAdminDashboard() {
  try {
    const res = await apiFetch("/api/super-admin/dashboard");
    if (!res || !res.success) return;

    const m = res.metrics;
    const statsEl = document.getElementById("super-stats-grid");
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-card">
          <div class="stat-header">Total Complaints <span>📁</span></div>
          <div class="stat-value">${m.total_complaints}</div>
          <div class="stat-desc">Across all departments</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Active / Pending <span>⏳</span></div>
          <div class="stat-value" style="color:var(--info);">${m.pending + m.in_progress}</div>
          <div class="stat-desc">Under municipal resolution</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Resolved & Closed <span>✅</span></div>
          <div class="stat-value" style="color:var(--success);">${m.resolved}</div>
          <div class="stat-desc">Completed works</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Triage Review Required <span>📋</span></div>
          <div class="stat-value" style="color:var(--warning);">${m.needs_review}</div>
          <div class="stat-desc">Triage or edge cases</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">Flagged Duplicates <span>⚠️</span></div>
          <div class="stat-value" style="color:var(--purple);">${m.duplicates_flagged}</div>
          <div class="stat-desc">Potential duplicate reports</div>
        </div>
      `;
    }

    // Render department breakdown
    const deptContainer = document.getElementById("dept-breakdown-container");
    if (deptContainer) {
      const maxCount = Math.max(...res.by_department.map(d => d.count), 1);
      deptContainer.innerHTML = res.by_department.map(d => {
        const pct = Math.round((d.count / maxCount) * 100);
        return `
          <div style="margin-bottom:0.85rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <span><strong>${d.department}</strong> (${d.code})</span>
              <span style="font-weight:700;">${d.count}</span>
            </div>
            <div style="background:var(--bg-surface); height:8px; border-radius:4px; overflow:hidden;">
              <div style="background:var(--secondary); height:100%; width:${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render category breakdown
    const catContainer = document.getElementById("cat-breakdown-container");
    if (catContainer) {
      const maxCat = Math.max(...res.by_category.map(c => c.count), 1);
      catContainer.innerHTML = res.by_category.map(c => {
        const pct = Math.round((c.count / maxCat) * 100);
        return `
          <div style="margin-bottom:0.85rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <span>${c.category}</span>
              <span style="font-weight:700;">${c.count}</span>
            </div>
            <div style="background:var(--bg-surface); height:8px; border-radius:4px; overflow:hidden;">
              <div style="background:var(--accent); height:100%; width:${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error("Super Admin error:", err);
  }
}

// 2. Triage & Review Queue
async function renderAiReviewQueue() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/triage-review')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Grievance Triage & Review Queue</h1>
            <p class="page-subtitle">Complaints requiring review, unclassified reports, or flagged duplicates.</p>
          </div>
          <button class="btn btn-outline btn-sm" onclick="renderAiReviewQueue()">
            🔄 Refresh Queue
          </button>
        </div>

        <div class="table-card">
          <div id="review-table-container" class="table-responsive">
            <div style="padding:2.5rem; text-align:center; color:var(--text-muted);">Loading review queue...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch("/api/super-admin/triage-review");
    const container = document.getElementById("review-table-container");
    if (!container) return;

    if (!res || !res.success || res.queue.length === 0) {
      container.innerHTML = `
        <div style="padding:3.5rem 1.5rem; text-align:center;">
          <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎉</div>
          <h3 style="color:var(--primary); margin-bottom:0.25rem;">Review Queue is Empty</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">All incoming complaints have been routed successfully.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Complaint ID</th>
            <th>Title</th>
            <th>Assigned Category</th>
            <th>Status</th>
            <th>Duplicate Flag</th>
            <th>Current Dept</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${res.queue.map(c => `
            <tr>
              <td><strong>${c.complaint_id}</strong></td>
              <td>
                <div style="max-width:200px; font-weight:600;">${c.title}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                  ${c.description}
                </div>
              </td>
              <td>${c.ai_predicted_category}</td>
              <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ')}</span></td>
              <td>
                ${c.is_duplicate ? `<span class="badge badge-NEEDS_REVIEW">Duplicate (${c.duplicate_of_id})</span>` : '<span style="color:var(--text-light); font-size:0.8rem;">Unique</span>'}
              </td>
              <td>${c.current_department}</td>
              <td>
                <button class="btn btn-primary btn-sm" onclick="openOverrideModal('${c.complaint_id}', '${c.ai_predicted_category}', '${c.current_department_code}')">
                  ⚖️ Override & Route
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load review queue.", "error");
  }
}

function openOverrideModal(complaintRef, currentCat, currentDept) {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Manual Category & Routing Reassignment</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
      </div>
      <form onsubmit="handleOverrideSubmit(event, '${complaintRef}')">
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.25rem;">
          Overriding will assign the complaint directly to the chosen department. The original category is preserved in the audit log.
        </p>

        <div class="form-group">
          <label class="form-label">Select Correct Category <span class="req">*</span></label>
          <select id="modal-override-cat" class="form-control select-input" required onchange="handleOverrideCategoryChange()">
            <option value="Water Supply" ${currentCat === 'Water Supply' ? 'selected' : ''}>Water Supply</option>
            <option value="Electricity" ${currentCat === 'Electricity' ? 'selected' : ''}>Electricity & Power</option>
            <option value="Street Lighting" ${currentCat === 'Street Lighting' ? 'selected' : ''}>Street Lighting</option>
            <option value="Roads & Footpaths" ${currentCat === 'Roads & Footpaths' ? 'selected' : ''}>Roads & Footpaths</option>
            <option value="Solid Waste Management" ${currentCat === 'Solid Waste Management' ? 'selected' : ''}>Solid Waste Management</option>
            <option value="Drainage & Sewerage" ${currentCat === 'Drainage & Sewerage' ? 'selected' : ''}>Drainage & Sewerage</option>
            <option value="Traffic & Road Safety" ${currentCat === 'Traffic & Road Safety' ? 'selected' : ''}>Traffic & Road Safety</option>
            <option value="Public Safety & Security" ${currentCat === 'Public Safety & Security' ? 'selected' : ''}>Public Safety & Hazards</option>
            <option value="Pollution" ${currentCat === 'Pollution' ? 'selected' : ''}>Pollution & Environment</option>
            <option value="Other Civic Services" ${currentCat === 'Other Civic Services' ? 'selected' : ''}>Other Civic Services</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Target Municipal Department <span class="req">*</span></label>
          <select id="modal-override-dept" class="form-control select-input" required>
            <option value="WATER" ${currentDept === 'WATER' ? 'selected' : ''}>Water Department</option>
            <option value="ELECTRICITY" ${currentDept === 'ELECTRICITY' ? 'selected' : ''}>Electricity Department</option>
            <option value="ROADS" ${currentDept === 'ROADS' ? 'selected' : ''}>Roads & Infrastructure Department</option>
            <option value="WASTE" ${currentDept === 'WASTE' ? 'selected' : ''}>Waste Management Department</option>
            <option value="DRAINAGE" ${currentDept === 'DRAINAGE' ? 'selected' : ''}>Drainage Department</option>
            <option value="TRAFFIC" ${currentDept === 'TRAFFIC' ? 'selected' : ''}>Traffic Department</option>
            <option value="PUBLIC_SAFETY" ${currentDept === 'PUBLIC_SAFETY' ? 'selected' : ''}>Public Safety Department</option>
            <option value="HEALTHCARE" ${currentDept === 'HEALTHCARE' ? 'selected' : ''}>Healthcare & Environment</option>
            <option value="GENERAL" ${currentDept === 'GENERAL' ? 'selected' : ''}>General Civic Department</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Reason for Override <span class="req">*</span></label>
          <textarea id="modal-override-reason" class="form-control" rows="3" placeholder="Provide justification for administrative audit record..." required></textarea>
        </div>

        <div style="display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save & Route Complaint</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

function handleOverrideCategoryChange() {
  const cat = document.getElementById("modal-override-cat").value;
  const deptSelect = document.getElementById("modal-override-dept");

  const map = {
    "Water Supply": "WATER",
    "Electricity": "ELECTRICITY",
    "Street Lighting": "ELECTRICITY",
    "Roads & Footpaths": "ROADS",
    "Solid Waste Management": "WASTE",
    "Drainage & Sewerage": "DRAINAGE",
    "Traffic & Road Safety": "TRAFFIC",
    "Public Safety & Security": "PUBLIC_SAFETY",
    "Pollution": "HEALTHCARE",
    "Other Civic Services": "GENERAL"
  };

  if (map[cat]) deptSelect.value = map[cat];
}

async function handleOverrideSubmit(event, complaintRef) {
  event.preventDefault();
  const category = document.getElementById("modal-override-cat").value;
  const department_code = document.getElementById("modal-override-dept").value;
  const reason = document.getElementById("modal-override-reason").value.trim();

  try {
    const res = await apiFetch(`/api/super-admin/triage-review/${complaintRef}/override`, {
      method: "POST",
      body: JSON.stringify({ category, department_code, reason })
    });

    if (res && res.success) {
      document.querySelector(".modal-overlay").remove();
      showToast(res.message, "success");
      renderAiReviewQueue();
    }
  } catch (err) {
    showToast(err.message || "Failed to override.", "error");
  }
}

// 3. User Directory
async function renderSuperAdminUsers() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/users')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">User Directory</h1>
            <p class="page-subtitle">Manage citizens and department officers across the city platform.</p>
          </div>
          <button class="btn btn-primary" onclick="openCreateAdminModal()">
            ➕ Add Department Admin
          </button>
        </div>

        <div class="table-card">
          <div class="table-toolbar">
            <div class="table-filters">
              <select id="user-filter-role" class="select-input" onchange="loadUsersList()">
                <option value="ALL">All Roles</option>
                <option value="CITIZEN">Citizens</option>
                <option value="DEPARTMENT_ADMIN">Department Admins</option>
                <option value="SUPER_ADMIN">Super Admins</option>
              </select>
            </div>
          </div>

          <div id="users-table-container" class="table-responsive">
            <div style="padding:2rem; text-align:center; color:var(--text-muted);">Loading users...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  loadUsersList();
}

async function loadUsersList() {
  const role = document.getElementById("user-filter-role") ? document.getElementById("user-filter-role").value : "ALL";
  try {
    const res = await apiFetch(`/api/super-admin/users?role=${role}`);
    const container = document.getElementById("users-table-container");
    if (!container) return;

    if (!res || !res.success || res.users.length === 0) {
      container.innerHTML = `<div style="padding:2rem; text-align:center; color:var(--text-muted);">No users found.</div>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Department</th>
            <th>Mobile</th>
            <th>City</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${res.users.map(u => `
            <tr>
              <td>
                <strong>${u.full_name}</strong><br/>
                <span style="font-size:0.75rem; color:var(--text-muted);">${u.email}</span>
              </td>
              <td><span class="badge ${u.role === 'SUPER_ADMIN' ? 'badge-ASSIGNED' : u.role === 'DEPARTMENT_ADMIN' ? 'badge-PROCESSING' : 'badge-CLOSED'}">${u.role}</span></td>
              <td>${u.department_code || '--'}</td>
              <td>${u.mobile || '--'}</td>
              <td>${u.city || '--'}</td>
              <td>
                <span class="badge" style="background:${u.is_active ? '#D1FAE5' : '#FEE2E2'}; color:${u.is_active ? '#065F46' : '#991B1B'};">
                  ${u.is_active ? 'Active' : 'Disabled'}
                </span>
              </td>
              <td>
                ${u.role !== 'SUPER_ADMIN' ? `
                  <button class="btn btn-outline btn-sm" onclick="toggleUserActive(${u.id}, ${!u.is_active})">
                    ${u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                ` : '--'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load users.", "error");
  }
}

async function toggleUserActive(userId, newStatus) {
  const formData = new FormData();
  formData.append("is_active", newStatus);

  try {
    const res = await apiFetch(`/api/super-admin/users/${userId}/status`, {
      method: "PUT",
      body: formData
    });
    if (res && res.success) {
      showToast(res.message, "success");
      loadUsersList();
    }
  } catch (err) {
    showToast(err.message || "Failed to update user.", "error");
  }
}

function openCreateAdminModal() {
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Create Department Admin</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
      </div>
      <form onsubmit="handleCreateAdminSubmit(event)">
        <div class="form-group">
          <label class="form-label">Full Name <span class="req">*</span></label>
          <input type="text" id="admin-name" class="form-control" placeholder="e.g. Inspector Ramesh Rao" required />
        </div>
        <div class="form-group">
          <label class="form-label">Email Address <span class="req">*</span></label>
          <input type="email" id="admin-email" class="form-control" placeholder="officer@urbansync.city" required />
        </div>
        <div class="form-group">
          <label class="form-label">Password <span class="req">*</span></label>
          <input type="password" id="admin-pw" class="form-control" placeholder="Minimum 6 characters" required minlength="6" />
        </div>
        <div class="form-group">
          <label class="form-label">Department <span class="req">*</span></label>
          <select id="admin-dept" class="form-control select-input" required>
            <option value="WATER">Water Department</option>
            <option value="ELECTRICITY">Electricity Department</option>
            <option value="ROADS">Roads & Infrastructure Department</option>
            <option value="WASTE">Waste Management Department</option>
            <option value="DRAINAGE">Drainage Department</option>
            <option value="TRAFFIC">Traffic Department</option>
            <option value="PUBLIC_SAFETY">Public Safety Department</option>
            <option value="HEALTHCARE">Healthcare & Environment</option>
            <option value="GENERAL">General Civic Department</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Mobile Number</label>
          <input type="tel" id="admin-mobile" class="form-control" placeholder="10-digit mobile" />
        </div>
        <div style="display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button type="submit" class="btn btn-primary">Create Officer Account</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

async function handleCreateAdminSubmit(event) {
  event.preventDefault();
  const full_name = document.getElementById("admin-name").value.trim();
  const email = document.getElementById("admin-email").value.trim();
  const password = document.getElementById("admin-pw").value;
  const department_code = document.getElementById("admin-dept").value;
  const mobile = document.getElementById("admin-mobile").value.trim();

  try {
    const res = await apiFetch("/api/super-admin/users/department-admin", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password, department_code, mobile })
    });
    if (res && res.success) {
      document.querySelector(".modal-overlay").remove();
      showToast(res.message, "success");
      loadUsersList();
    }
  } catch (err) {
    showToast(err.message || "Failed to create officer.", "error");
  }
}

// 4. Department Directory
async function renderSuperAdminDepartments() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/departments')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Municipal Departments</h1>
            <p class="page-subtitle">Civic departments configured for automated routing and staff assignment.</p>
          </div>
        </div>

        <div id="depts-grid" class="cards-grid">
          <div class="stat-card"><div class="stat-desc">Loading departments...</div></div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch("/api/super-admin/departments");
    const container = document.getElementById("depts-grid");
    if (!container || !res || !res.success) return;

    container.innerHTML = res.departments.map(d => `
      <div class="stat-card" style="padding:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span class="badge" style="background:#E0E7FF; color:#4338CA;">${d.code}</span>
          <span class="badge" style="background:#D1FAE5; color:#065F46;">Active</span>
        </div>
        <h3 style="font-size:1.15rem; color:var(--primary); margin-bottom:0.4rem;">${d.name}</h3>
        <p style="color:var(--text-muted); font-size:0.8rem; margin-bottom:1rem; min-height:40px;">${d.description || 'Civic infrastructure maintenance and municipal operations.'}</p>
        <div class="form-row" style="font-size:0.85rem; border-top:1px solid var(--border); padding-top:0.75rem;">
          <div><strong>Complaints:</strong> ${d.complaints_count}</div>
          <div><strong>Officers:</strong> ${d.admins_count}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    showToast(err.message || "Failed to load departments.", "error");
  }
}

// 5. System Audit Trail
async function renderSuperAdminAuditLogs() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/audit-logs')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">System Audit Trail</h1>
            <p class="page-subtitle">Immutable log of security events, status updates, administrative overrides, and user access.</p>
          </div>
        </div>

        <div class="table-card">
          <div id="audit-table-container" class="table-responsive">
            <div style="padding:2.5rem; text-align:center; color:var(--text-muted);">Loading audit records...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch("/api/super-admin/audit-logs?limit=50");
    const container = document.getElementById("audit-table-container");
    if (!container || !res || !res.success) return;

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Action</th>
            <th>Actor</th>
            <th>Entity</th>
            <th>Details / Delta</th>
            <th>IP Address</th>
          </tr>
        </thead>
        <tbody>
          ${res.audit_logs.map(l => `
            <tr>
              <td><span style="font-size:0.8rem; color:var(--text-light);">${new Date(l.created_at).toLocaleString()}</span></td>
              <td><span class="badge" style="background:#F1F5F9; color:var(--primary);">${l.action}</span></td>
              <td><strong>${l.actor}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">(${l.actor_role})</span></td>
              <td><code>${l.entity_type} ${l.entity_id || ''}</code></td>
              <td><div style="max-width:320px; font-size:0.8rem; color:var(--text-muted); word-break:break-all;">${l.new_value || l.old_value || '--'}</div></td>
              <td><span style="font-size:0.75rem; color:var(--text-light);">${l.ip_address || 'local'}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message || "Failed to load audit logs.", "error");
  }
}

// 6. Super Admin City Analytics & Hotspots
async function renderSuperAdminMlAnalytics() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="app-layout">
      ${renderSuperAdminSidebar('/super-admin/city-analytics')}
      <div class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Citywide Analytics & Complaint Hotspots</h1>
            <p class="page-subtitle">Overview of grievance distribution across municipal categories and geographic hotspot zones.</p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="loadMlAnalyticsData()">
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

