// UrbanSync - Authentication & Account Management

function renderLandingPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="hero-section">
      <div class="hero-tagline">UrbanSync Smart City Platform</div>
      <h1 class="hero-title">Connecting Citizens.<br/>Coordinating Cities.</h1>
      <p class="hero-desc">
        Report civic infrastructure issues in seconds. Our smart system automatically categorizes problems, detects duplicates, and routes tasks directly to responsible municipal departments.
      </p>
      <div class="hero-buttons">
        <button class="btn btn-primary btn-lg" onclick="handleReportComplaintClick()">
          📢 Report a Complaint
        </button>
        <button class="btn btn-portal-login btn-lg" onclick="navigate('/login')">
          🔐 Portal Login
        </button>
      </div>
    </div>

    <div class="main-content">
      <div style="text-align:center; margin-top:2rem;">
        <span class="brand-badge">Autonomous Civic Operations</span>
        <h2 style="font-size:2rem; margin-top:0.5rem; color:var(--primary);">How UrbanSync Works</h2>
        <p style="color:var(--text-muted); max-width:600px; margin:0.5rem auto 3rem;">
          From instant citizen reporting to automated department routing and verified resolution.
        </p>
      </div>

      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">📝</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">1. Citizen Reports Issue</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Provide brief description, GPS pin location, and upload site photos. Form auto-saves offline.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">2. Automated Categorization</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Our system analyzes the grievance report, identifies key civic issues, and assigns the responsible department.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">⚡</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">3. Automated Routing</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Issues route instantly to Water, Power, Roads, or Waste department dashboards.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">🛠️</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">4. Department Action</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Department officers acknowledge, start on-ground work, and submit verified photo evidence.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">📍</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">5. Real-Time Tracking</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Citizens receive status notifications at every stage and confirm closure or reopen if unresolved.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">🛡️</div>
          <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">6. Audits & Overrides</h3>
          <p style="color:var(--text-muted); font-size:0.875rem;">
            Super Administrators monitor city analytics, review edge cases, and maintain an immutable audit trail.
          </p>
        </div>
      </div>
    </div>
  `;
}

function handleReportComplaintClick() {
  if (state.token && state.user) {
    if (state.user.role === "CITIZEN" || state.user.role === "SUPER_ADMIN") {
      navigate("/citizen/complaints/new");
    } else {
      navigate("/admin/dashboard");
    }
  } else {
    navigate("/login");
  }
}

function renderLoginPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <div style="display:inline-flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <span style="font-size:1.8rem;">🏙️</span>
            <span style="font-size:1.4rem; font-weight:800; color:var(--primary);">UrbanSync</span>
          </div>
          <h2 class="auth-title">Welcome Back</h2>
          <p class="auth-sub">Sign in to your civic service account</p>
        </div>

        <form id="login-form" onsubmit="handleLoginSubmit(event)">
          <div class="form-group">
            <label class="form-label" for="login-email">Email Address <span class="req">*</span></label>
            <input type="email" id="login-email" class="form-control" placeholder="name@example.com" required autofocus />
          </div>

          <div class="form-group">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
              <label class="form-label" for="login-password" style="margin-bottom:0;">Password <span class="req">*</span></label>
              <a href="/forgot-password" onclick="event.preventDefault(); navigate('/forgot-password');" style="font-size:0.8rem;">Forgot password?</a>
            </div>
            <div style="position:relative;">
              <input type="password" id="login-password" class="form-control" placeholder="••••••••" required />
              <button type="button" onclick="togglePasswordVisibility('login-password')" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:0.85rem;">👁️</button>
            </div>
          </div>

          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.5rem;">
            <label style="display:flex; align-items:center; gap:0.5rem; font-size:0.85rem; color:var(--text-muted); cursor:pointer;">
              <input type="checkbox" id="login-remember" />
              Remember me
            </label>
          </div>

          <button type="submit" id="btn-login-submit" class="btn btn-primary" style="width:100%; padding:0.75rem;">
            Sign In
          </button>
        </form>

        <div style="text-align:center; margin-top:1.5rem; font-size:0.875rem; color:var(--text-muted);">
          Don't have an account? 
          <a href="/register" onclick="event.preventDefault(); navigate('/register');" style="font-weight:600;">Create Account</a>
        </div>
      </div>
    </div>
  `;
}

if (typeof setAuth === "undefined") {
  window.setAuth = function(token, user) {
    state.token = token;
    state.user = user;
    localStorage.setItem("urbansync_token", token);
    localStorage.setItem("urbansync_user", JSON.stringify(user));
    updateNavbar();
  };
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const btn = document.getElementById("btn-login-submit");
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const remember_me = document.getElementById("login-remember").checked;

  btn.disabled = true;
  btn.textContent = "Signing in...";

  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, remember_me })
    });

    if (res && res.success) {
      setAuth(res.access_token, res.user);
      showToast("Signed in successfully!", "success");
      if (res.user.role === "SUPER_ADMIN") navigate("/super-admin/dashboard");
      else if (res.user.role === "DEPARTMENT_ADMIN") navigate("/admin/dashboard");
      else if (res.user.role === "FIELD_WORKER") navigate("/worker/dashboard");
      else navigate("/citizen/dashboard");
    }
  } catch (err) {
    showToast(err.message || "Invalid credentials", "error");
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
}

function renderRegisterPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="auth-container">
      <div class="auth-card" style="max-width:540px;">
        <div class="auth-header">
          <div style="display:inline-flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <span style="font-size:1.8rem;">🏙️</span>
            <span style="font-size:1.4rem; font-weight:800; color:var(--primary);">UrbanSync</span>
          </div>
          <h2 class="auth-title">Citizen Registration</h2>
          <p class="auth-sub">Register to report issues and track civic resolutions</p>
        </div>

        <form id="register-form" onsubmit="handleRegisterSubmit(event)">
          <div class="form-group">
            <label class="form-label">Full Name <span class="req">*</span></label>
            <input type="text" id="reg-name" class="form-control" placeholder="e.g. Ramesh Kumar" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Email Address <span class="req">*</span></label>
              <input type="email" id="reg-email" class="form-control" placeholder="ramesh@example.com" required />
            </div>
            <div class="form-group">
              <label class="form-label">Mobile Number <span class="req">*</span></label>
              <input type="tel" id="reg-mobile" class="form-control" placeholder="10-digit mobile" maxlength="15" required />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Password <span class="req">*</span></label>
              <input type="password" id="reg-password" class="form-control" placeholder="Minimum 6 characters" required minlength="6" />
            </div>
            <div class="form-group">
              <label class="form-label">Confirm Password <span class="req">*</span></label>
              <input type="password" id="reg-confirm-password" class="form-control" placeholder="Re-enter password" required minlength="6" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Address / Landmark</label>
            <input type="text" id="reg-address" class="form-control" placeholder="Apartment / Colony / Street" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">City</label>
              <input type="text" id="reg-city" class="form-control" value="Mumbai" />
            </div>
            <div class="form-group">
              <label class="form-label">Pincode</label>
              <input type="text" id="reg-pincode" class="form-control" placeholder="e.g. 400053" maxlength="6" />
            </div>
          </div>

          <div class="form-group" style="margin-top:0.5rem;">
            <label style="display:flex; align-items:flex-start; gap:0.6rem; font-size:0.85rem; color:var(--text-muted); cursor:pointer;">
              <input type="checkbox" id="reg-terms" required style="margin-top:0.25rem;" />
              <span>I agree to the UrbanSync civic platform <a href="#">Terms & Conditions</a> and privacy guidelines.</span>
            </label>
          </div>

          <button type="submit" id="btn-reg-submit" class="btn btn-primary" style="width:100%; padding:0.75rem; margin-top:1rem;">
            Create Citizen Account
          </button>
        </form>

        <div style="text-align:center; margin-top:1.5rem; font-size:0.875rem; color:var(--text-muted);">
          Already have an account? 
          <a href="/login" onclick="event.preventDefault(); navigate('/login');" style="font-weight:600;">Sign In</a>
        </div>
      </div>
    </div>
  `;
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const btn = document.getElementById("btn-reg-submit");
  const full_name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const mobile = document.getElementById("reg-mobile").value.trim();
  const password = document.getElementById("reg-password").value;
  const confirm_password = document.getElementById("reg-confirm-password").value;
  const address = document.getElementById("reg-address").value.trim();
  const city = document.getElementById("reg-city").value.trim();
  const pincode = document.getElementById("reg-pincode").value.trim();
  const terms_accepted = document.getElementById("reg-terms").checked;

  if (password !== confirm_password) {
    showToast("Passwords do not match.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Creating Account...";

  try {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name,
        email,
        mobile,
        password,
        confirm_password,
        address,
        city,
        pincode,
        terms_accepted
      })
    });

    if (res && res.success) {
      setAuth(res.access_token, res.user);
      showToast(res.message || "Account created successfully!", "success");
      navigate("/citizen/dashboard");
    }
  } catch (err) {
    showToast(err.message || "Registration failed.", "error");
    btn.disabled = false;
    btn.textContent = "Create Citizen Account";
  }
}

function renderForgotPasswordPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h2 class="auth-title">Forgot Password</h2>
          <p class="auth-sub">Enter your email and we'll send you a password reset link</p>
        </div>

        <form onsubmit="handleForgotPasswordSubmit(event)">
          <div class="form-group">
            <label class="form-label">Email Address <span class="req">*</span></label>
            <input type="email" id="forgot-email" class="form-control" placeholder="name@example.com" required autofocus />
          </div>

          <button type="submit" id="btn-forgot-submit" class="btn btn-primary" style="width:100%; padding:0.75rem;">
            Send Reset Link
          </button>
        </form>

        <div id="forgot-result" style="margin-top:1.5rem;"></div>

        <div style="text-align:center; margin-top:1.5rem; font-size:0.875rem;">
          <a href="/login" onclick="event.preventDefault(); navigate('/login');">← Back to Login</a>
        </div>
      </div>
    </div>
  `;
}

async function handleForgotPasswordSubmit(event) {
  event.preventDefault();
  const btn = document.getElementById("btn-forgot-submit");
  const email = document.getElementById("forgot-email").value.trim();
  const resultDiv = document.getElementById("forgot-result");

  btn.disabled = true;
  btn.textContent = "Sending...";

  try {
    const res = await apiFetch("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email })
    });

    resultDiv.innerHTML = `
      <div style="background:#ECFDF5; border:1px solid #A7F3D0; color:#065F46; padding:1rem; border-radius:var(--radius-md); font-size:0.85rem;">
        ✓ ${res.message}
        ${res.dev_reset_url ? `
          <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid #A7F3D0;">
            <strong>Dev Mode Reset Link:</strong><br/>
            <a href="${res.dev_reset_url}" onclick="event.preventDefault(); navigate('${res.dev_reset_url}');" style="color:#0284C7; word-break:break-all;">
              Click here to Reset Password
            </a>
          </div>
        ` : ''}
      </div>
    `;
  } catch (err) {
    showToast(err.message || "Request failed", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Send Reset Link";
  }
}

function renderResetPasswordPage(token) {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h2 class="auth-title">Set New Password</h2>
          <p class="auth-sub">Enter a strong new password for your account</p>
        </div>

        <form onsubmit="handleResetPasswordSubmit(event, '${token}')">
          <div class="form-group">
            <label class="form-label">New Password <span class="req">*</span></label>
            <input type="password" id="reset-password" class="form-control" placeholder="Minimum 6 characters" required minlength="6" autofocus />
          </div>

          <div class="form-group">
            <label class="form-label">Confirm New Password <span class="req">*</span></label>
            <input type="password" id="reset-confirm" class="form-control" placeholder="Re-enter new password" required minlength="6" />
          </div>

          <button type="submit" id="btn-reset-submit" class="btn btn-primary" style="width:100%; padding:0.75rem;">
            Reset Password
          </button>
        </form>
      </div>
    </div>
  `;
}

async function handleResetPasswordSubmit(event, token) {
  event.preventDefault();
  const new_password = document.getElementById("reset-password").value;
  const confirm_password = document.getElementById("reset-confirm").value;

  if (new_password !== confirm_password) {
    showToast("Passwords do not match.", "error");
    return;
  }

  const btn = document.getElementById("btn-reset-submit");
  btn.disabled = true;
  btn.textContent = "Resetting...";

  try {
    const res = await apiFetch("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password, confirm_password })
    });

    if (res && res.success) {
      showToast(res.message, "success");
      navigate("/login");
    }
  } catch (err) {
    showToast(err.message || "Failed to reset password.", "error");
    btn.disabled = false;
    btn.textContent = "Reset Password";
  }
}

function togglePasswordVisibility(id) {
  const input = document.getElementById(id);
  if (input) {
    input.type = input.type === "password" ? "text" : "password";
  }
}

function renderUnauthorizedPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="main-content" style="text-align:center; padding:5rem 2rem;">
      <div style="font-size:3rem; margin-bottom:1rem;">🚫</div>
      <h2 style="font-size:2rem; color:var(--primary); margin-bottom:0.5rem;">Access Unauthorized</h2>
      <p style="color:var(--text-muted); max-width:500px; margin:0 auto 2rem;">
        You do not have the required permissions to access this page or department.
      </p>
      <button class="btn btn-primary" onclick="navigate('/')">Return to Home</button>
    </div>
  `;
}

function renderNotFoundPage() {
  const root = document.getElementById("app-root");
  root.innerHTML = `
    <div class="main-content" style="text-align:center; padding:5rem 2rem;">
      <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
      <h2 style="font-size:2rem; color:var(--primary); margin-bottom:0.5rem;">Page Not Found</h2>
      <p style="color:var(--text-muted); max-width:500px; margin:0 auto 2rem;">
        The requested URL was not found on the UrbanSync civic platform.
      </p>
      <button class="btn btn-primary" onclick="navigate('/')">Go Home</button>
    </div>
  `;
}
