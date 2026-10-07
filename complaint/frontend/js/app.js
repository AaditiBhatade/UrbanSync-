// UrbanSync — Global Application Core & SPA Router

const state = {
  user: null,
  token: localStorage.getItem("urbansync_token") || null,
  currentRoute: window.location.pathname || "/"
};

function setAuth(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("urbansync_token", token);
  localStorage.setItem("urbansync_user", JSON.stringify(user));
  updateNavbar();
}
window.setAuth = setAuth;

// API Fetch Helper
async function apiFetch(url, options = {}) {
  const headers = options.headers || {};

  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }

  // Handle FormData vs JSON
  if (options.body && !(options.body instanceof FormData)) {
    if (!headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    if (typeof options.body === "object") {
      options.body = JSON.stringify(options.body);
    }
  }

  options.headers = headers;

  try {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (res.status === 401) {
        logout(false);
        navigate("/login");
        throw new Error(data.detail || "Session expired. Please log in.");
      }
      throw new Error(data.detail || data.message || "An error occurred.");
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div>${message}</div>
    <button style="background:none; border:none; cursor:pointer; color:var(--text-light);" onclick="this.parentElement.remove()">&times;</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 4500);
}

// SPA Router
async function navigate(path, addToHistory = true) {
  if (addToHistory) {
    window.history.pushState({}, "", path);
  }
  state.currentRoute = path;
  updateNavbar();

  // Route Dispatcher
  if (path === "/" || path === "") {
    if (state.user) {
      redirectUserByRole();
    } else {
      renderLandingPage();
    }
  } else if (path === "/login") {
    renderLoginPage();
  } else if (path === "/register") {
    renderRegisterPage();
  } else if (path.startsWith("/citizen/")) {
    if (!requireAuth("CITIZEN")) return;
    if (path === "/citizen/dashboard") renderCitizenDashboard();
    else if (path === "/citizen/report") renderCitizenReportForm();
    else if (path === "/citizen/complaints") renderCitizenComplaintsList();
    else if (path.startsWith("/citizen/complaints/")) {
      const id = path.split("/")[3];
      renderCitizenComplaintDetail(id);
    }
  } else if (path.startsWith("/admin/")) {
    if (!requireAuth(["DEPARTMENT_ADMIN", "SUPER_ADMIN"])) return;
    if (path === "/admin/dashboard") renderAdminDashboard();
    else if (path === "/admin/workers") renderAdminWorkersRoster();
    else if (path.includes("analytics") || path.includes("hotspots")) renderAdminMlAnalytics();
    else if (path.startsWith("/admin/complaints/")) {
      const id = path.split("/")[3];
      renderAdminComplaintDetail(id);
    }
  } else if (path.startsWith("/super-admin/")) {
    if (!requireAuth("SUPER_ADMIN")) return;
    if (path === "/super-admin/dashboard") renderSuperAdminDashboard();
    else if (path.includes("analytics") || path.includes("hotspots")) renderSuperAdminMlAnalytics();
    else if (path.includes("review")) renderAiReviewQueue();
    else if (path === "/super-admin/users") renderSuperAdminUsers();
    else if (path === "/super-admin/departments") renderSuperAdminDepartments();
    else if (path === "/super-admin/audit-logs") renderSuperAdminAuditLogs();
  } else if (path.startsWith("/worker/")) {
    if (!requireAuth(["FIELD_WORKER", "SUPER_ADMIN"])) return;
    if (path === "/worker/dashboard") renderWorkerDashboard();
    else if (path.startsWith("/worker/complaints/")) {
      const id = path.split("/")[3];
      renderWorkerComplaintDetail(id);
    }
  } else {
    // 404 fallback
    const root = document.getElementById("app-root");
    root.innerHTML = `
      <div style="text-align:center; padding:5rem 2rem;">
        <h1 style="font-size:3rem; color:var(--primary);">404</h1>
        <p style="color:var(--text-muted); margin-bottom:1.5rem;">Page Not Found</p>
        <button class="btn btn-primary" onclick="navigate('/')">Return Home</button>
      </div>
    `;
  }
}

function requireAuth(allowedRoles) {
  if (!state.token || !state.user) {
    navigate("/login");
    return false;
  }
  const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
  if (!roles.includes(state.user.role)) {
    showToast("Access forbidden for your user role.", "error");
    redirectUserByRole();
    return false;
  }
  return true;
}

function redirectUserByRole() {
  if (!state.user) {
    navigate("/");
    return;
  }
  if (state.user.role === "SUPER_ADMIN") {
    navigate("/super-admin/dashboard");
  } else if (state.user.role === "DEPARTMENT_ADMIN") {
    navigate("/admin/dashboard");
  } else if (state.user.role === "FIELD_WORKER") {
    navigate("/worker/dashboard");
  } else {
    navigate("/citizen/dashboard");
  }
}

function updateNavbar() {
  const navRight = document.getElementById("navbar-right");
  if (!navRight) return;

  if (state.user) {
    let dashboardLink = "/citizen/dashboard";
    let roleBadge = "Citizen";
    if (state.user.role === "SUPER_ADMIN") {
      dashboardLink = "/super-admin/dashboard";
      roleBadge = "Super Admin";
    } else if (state.user.role === "DEPARTMENT_ADMIN") {
      dashboardLink = "/admin/dashboard";
      roleBadge = `${state.user.department_code} Admin`;
    } else if (state.user.role === "FIELD_WORKER") {
      dashboardLink = "/worker/dashboard";
      roleBadge = `👷 ${state.user.department_code || ''} Worker`;
    }

    navRight.innerHTML = `
      <a href="${dashboardLink}" class="nav-link" onclick="event.preventDefault(); navigate('${dashboardLink}');">Dashboard</a>
      ${state.user.role === "CITIZEN" ? `<a href="/citizen/report" class="nav-link" onclick="event.preventDefault(); navigate('/citizen/report');">Report Issue</a>` : ''}
      ${state.user.role === "FIELD_WORKER" ? `<a href="/worker/dashboard" class="nav-link" onclick="event.preventDefault(); navigate('/worker/dashboard');">My Assigned Tasks</a>` : ''}
      ${state.user.role !== "CITIZEN" && state.user.role !== "FIELD_WORKER" ? `<a href="/admin/city-analytics" class="nav-link" onclick="event.preventDefault(); navigate('/admin/city-analytics');">City Hotspots</a>` : ''}
      <div style="display:flex; align-items:center; gap:0.5rem; margin-left:0.5rem; background:rgba(255,255,255,0.08); padding:0.25rem 0.75rem; border-radius:20px;">
        <span style="font-size:0.8rem; color:#E2E8F0;">${state.user.full_name.split(' ')[0]}</span>
        <span class="badge" style="font-size:0.65rem; background:#38BDF8; color:#0F172A; padding:0.15rem 0.4rem;">${roleBadge}</span>
      </div>
      <button class="btn btn-outline btn-sm" style="color:#FFFFFF; border-color:rgba(255,255,255,0.3);" onclick="logout()">Logout</button>
    `;
  } else {
    navRight.innerHTML = `
      <a href="/login" class="nav-link" onclick="event.preventDefault(); navigate('/login');">Login</a>
      <a href="/register" class="btn btn-primary btn-sm" onclick="event.preventDefault(); navigate('/register');">Sign Up</a>
    `;
  }
}

function logout(notify = true) {
  state.token = null;
  state.user = null;
  localStorage.removeItem("urbansync_token");
  localStorage.removeItem("urbansync_user");
  if (notify) showToast("Logged out successfully.", "info");
  navigate("/");
}

// Popstate listener (Back / Forward button)
window.addEventListener("popstate", () => {
  navigate(window.location.pathname, false);
});

// App Initialization
document.addEventListener("DOMContentLoaded", async () => {
  const savedToken = localStorage.getItem("urbansync_token");
  if (savedToken) {
    try {
      state.token = savedToken;
      const res = await apiFetch("/api/auth/me");
      if (res && res.id) {
        state.user = res;
        localStorage.setItem("urbansync_user", JSON.stringify(res));
      } else {
        logout(false);
      }
    } catch {
      logout(false);
    }
  }
  navigate(window.location.pathname, false);
});
