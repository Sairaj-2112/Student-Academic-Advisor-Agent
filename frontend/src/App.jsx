
import { useState } from "react";
import AdvisorWorkspace from "./AdvisorWorkspace";
import "./App.css";

const DEMO_EMAIL = "demo@student.com";
const DEMO_PASSWORD = "student123";

const navigation = [
  { id: "home", label: "Dashboard", icon: "\u{1F3E0}", group: "MAIN" },
  { id: "academic", label: "Academic Advisor", icon: "\u{1F393}", group: "MAIN" },
  { id: "prerequisite", label: "Prerequisite Verification", icon: "\u{1F50D}", group: "MAIN" },
  { id: "assessments", label: "AI Assessments", icon: "\u{1F4DD}", group: "MAIN" },
  { id: "career", label: "Career Advisor", icon: "\u{1F4BC}", group: "TOOLS" },
  { id: "progress", label: "Profile & Progress", icon: "\u{1F4CA}", group: "TOOLS" },
];

function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("academic_user")) || null;
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState("home");
  const [authMode, setAuthMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function saveUser(account) {
    const student = {
      name: account.name,
      email: account.email,
    };

    localStorage.setItem("academic_user", JSON.stringify(student));
    setUser(student);
    setPage("home");
    setMessage("");
  }

  function handleLogin(event) {
    event.preventDefault();
    setMessage("");

    const normalizedEmail = email.trim().toLowerCase();

    if (normalizedEmail === DEMO_EMAIL && password === DEMO_PASSWORD) {
      saveUser({ name: "Demo Student", email: DEMO_EMAIL });
      return;
    }

    let accounts = [];

    try {
      accounts = JSON.parse(localStorage.getItem("academic_accounts") || "[]");
    } catch {
      accounts = [];
    }

    const account = accounts.find(
      (item) =>
        item.email.toLowerCase() === normalizedEmail &&
        item.password === password
    );

    if (!account) {
      setMessage("Invalid email or password. Please try again.");
      return;
    }

    saveUser(account);
  }

  function handleRegister(event) {
    event.preventDefault();
    setMessage("");

    if (!name.trim() || !email.trim() || !password) {
      setMessage("Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setMessage("Password must contain at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    const normalizedEmail = email.trim().toLowerCase();

    let accounts = [];

    try {
      accounts = JSON.parse(localStorage.getItem("academic_accounts") || "[]");
    } catch {
      accounts = [];
    }

    if (accounts.some((item) => item.email.toLowerCase() === normalizedEmail)) {
      setMessage("This email is already registered. Please log in.");
      return;
    }

    const account = {
      name: name.trim(),
      email: normalizedEmail,
      password,
    };

    accounts.push(account);
    localStorage.setItem("academic_accounts", JSON.stringify(accounts));
    saveUser(account);
  }

  function handleLogout() {
    localStorage.removeItem("academic_user");
    setUser(null);
    setPage("home");
    setAuthMode("login");
    setEmail("");
    setPassword("");
    setMessage("");
  }

  function navigateTo(section) {
    setPage(section);
    setSidebarOpen(false);
  }

  if (!user) {
    return (
      <div className="auth-page">
        <div className="auth-left">
          <div className="brand">
            <div className="brand-icon">A</div>
            <span>AcadAI</span>
          </div>

          <div className="auth-intro">
            <span className="eyebrow">YOUR PERSONAL AI GUIDE</span>
            <h1>
              Make smarter
              <br />
              <span>academic decisions.</span>
            </h1>
            <p>
              Discover learning opportunities, understand course
              prerequisites, assess your knowledge and plan your career
              with your AI-powered academic advisor.
            </p>

            <div className="auth-benefits">
              <div>✓ Personalized academic recommendations</div>
              <div>✓ Intelligent prerequisite verification</div>
              <div>✓ AI-powered quizzes and assessments</div>
              <div>✓ Career and skill development guidance</div>
            </div>
          </div>

          <div className="auth-footer">AI Academic &amp; Career Advisor</div>
        </div>

        <div className="auth-right">
          <div className="auth-card">
            <div className="mobile-brand">AcadAI</div>
            <span className="eyebrow">
              {authMode === "login" ? "WELCOME BACK" : "GET STARTED"}
            </span>

            <h2>
              {authMode === "login"
                ? "Sign in to your account"
                : "Create your account"}
            </h2>

            <p className="auth-subtitle">
              {authMode === "login"
                ? "Continue your academic journey with AcadAI."
                : "Join AcadAI and start planning your future."}
            </p>

            <form onSubmit={authMode === "login" ? handleLogin : handleRegister}>
              {authMode === "register" && (
                <label>
                  Full name
                  <input
                    type="text"
                    placeholder="Enter your full name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    required
                  />
                </label>
              )}

              <label>
                Email address
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>

              <label>
                Password
                <input
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </label>

              {authMode === "register" && (
                <label>
                  Confirm password
                  <input
                    type="password"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                  />
                </label>
              )}

              {message && <div className="auth-message">{message}</div>}

              <button className="primary-button" type="submit">
                {authMode === "login" ? "Sign In" : "Create Account"}
                <span>→</span>
              </button>
            </form>

            <div className="auth-switch">
              {authMode === "login" ? (
                <>
                  Don't have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("register");
                      setMessage("");
                    }}
                  >
                    Register
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("login");
                      setMessage("");
                    }}
                  >
                    Sign in
                  </button>
                </>
              )}
            </div>

            {authMode === "login" && (
              <div className="demo-box">
                <strong>Demo account</strong>
                <p>Email: {DEMO_EMAIL}</p>
                <p>Password: {DEMO_PASSWORD}</p>
                <button
                  type="button"
                  onClick={() => {
                    setEmail(DEMO_EMAIL);
                    setPassword(DEMO_PASSWORD);
                  }}
                >
                  Use demo credentials
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const activeItem = navigation.find((item) => item.id === page);
  const workspacePages = [
    "academic",
    "prerequisite",
    "assessments",
    "career",
    "progress",
  ];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-icon">A</div>
          <div>
            <strong>AcadAI</strong>
            <small>STUDENT PLATFORM</small>
          </div>
        </div>

        {/* CLICKABLE STUDENT ACCOUNT */}
        <button
          type="button"
          className="sidebar-student clickable-account"
          onClick={() => navigateTo("progress")}
          title="Open your profile"
        >
          <button
  type="button"
  className="student-profile-button"
  onClick={() => navigateTo("progress")}
  title="Open Profile & Progress"
>
  <div className="user-avatar">
    {user.name?.charAt(0).toUpperCase()}
  </div>

  <div className="student-details">
    <strong>{user.name}</strong>
    <small>Student Account</small>
  </div>

  <span className="profile-arrow">›</span>
</button>
        </button>

        <nav className="sidebar-navigation">
          <div className="nav-group-label">MAIN MENU</div>

          {navigation.filter((item) => item.group === "MAIN").map((item) => (
            <button
              key={item.id}
              className={`sidebar-link ${page === item.id ? "selected" : ""}`}
              onClick={() => navigateTo(item.id)}
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span>{item.label}</span>
              {page === item.id && <span className="active-indicator" />}
            </button>
          ))}

          <div className="nav-group-label tools-label">MY WORKSPACE</div>

          {navigation.filter((item) => item.group === "TOOLS").map((item) => (
            <button
              key={item.id}
              className={`sidebar-link ${page === item.id ? "selected" : ""}`}
              onClick={() => navigateTo(item.id)}
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span>{item.label}</span>
              {page === item.id && <span className="active-indicator" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <span>✨</span>
            <strong>Keep learning!</strong>
            <p>Your next opportunity starts with a small step.</p>
          </div>

          <button className="sidebar-logout" onClick={handleLogout}>
            <span>↪</span> Sign Out
          </button>

          <small className="sidebar-version">AcadAI · Student Edition</small>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="menu-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle navigation"
            >
              ☰
            </button>
            <div>
              <div className="breadcrumb">AcadAI / {activeItem?.label}</div>
              <h2>{activeItem?.label}</h2>
            </div>
          </div>

          {/* CLICKABLE TOP-RIGHT PROFILE */}
          <div className="topbar-right">
            <button
              type="button"
              className="topbar-profile-button"
              onClick={() => navigateTo("progress")}
              title="Open your profile"
            >
              <span className="topbar-greeting">Welcome, {user.name}</span>
              <span className="topbar-avatar">
                {user.name?.charAt(0).toUpperCase()}
              </span>
            </button>
          </div>
        </header>

        <main className="main-content">
          {page === "home" ? (
            <Dashboard user={user} onNavigate={navigateTo} />
          ) : workspacePages.includes(page) ? (
            <div className="workspace-container">
              <AdvisorWorkspace student={user} section={page} />
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}

function Dashboard({ user, onNavigate }) {
  const cards = [
    {
      id: "academic",
      icon: "\u{1F393}",
      title: "Academic Recommendations",
      description: "Discover courses and learning opportunities matched to your interests.",
      color: "blue",
    },
    {
      id: "prerequisite",
      icon: "\u{1F50D}",
      title: "Prerequisite Verification",
      description: "Check your knowledge and readiness before taking a course.",
      color: "purple",
    },
    {
      id: "assessments",
      icon: "\u{1F4DD}",
      title: "AI Assessments",
      description: "Practice concepts, take quizzes and review your performance.",
      color: "orange",
    },
    {
      id: "career",
      icon: "\u{1F4BC}",
      title: "Career Advisor",
      description: "Explore career paths, required skills and learning roadmaps.",
      color: "green",
    },
    {
      id: "progress",
      icon: "\u{1F4CA}",
      title: "Profile & Progress",
      description: "Review your learning activity and student profile.",
      color: "pink",
    },
  ];

  return (
    <div className="dashboard">
      <section className="welcome-banner">
        <div className="welcome-content">
          <span className="eyebrow">YOUR ACADEMIC JOURNEY</span>
          <h1>Hello, {user.name}!</h1>
          <p>
            Welcome to your personal AI Academic &amp; Career Advisor.
            Explore your options, strengthen your knowledge and plan
            your future.
          </p>
          <button
            className="primary-button dashboard-cta"
            onClick={() => onNavigate("academic")}
          >
            Explore Academic Advisor <span>→</span>
          </button>
        </div>

        <div className="welcome-illustration">
          <div className="illustration-orbit"></div>
          <div className="illustration-card">
            <span>YOUR FUTURE</span>
            <strong>Starts with a plan.</strong>
            <small>LEARN · EXPLORE · GROW</small>
          </div>
        </div>
      </section>

      <section className="dashboard-section-heading">
        <div>
          <span className="eyebrow">EXPLORE YOUR PLATFORM</span>
          <h2>Your learning workspace</h2>
          <p>Choose a section to get started.</p>
        </div>
      </section>

      <section className="feature-grid">
        {cards.map((card) => (
          <button
            key={card.id}
            className="feature-card"
            onClick={() => onNavigate(card.id)}
          >
            <div className={`feature-icon ${card.color}`}>{card.icon}</div>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
            <span className="feature-link">
              Open section <span>→</span>
            </span>
          </button>
        ))}
      </section>

      <section className="dashboard-insight">
        <div className="insight-heading">
          <span className="insight-eyebrow">YOUR LEARNING JOURNEY</span>
          <h2>Everything you need to move forward</h2>
          <p>
            Build knowledge, check your readiness and turn your interests
            into a career plan.
          </p>
        </div>

        <div className="insight-grid">
          <div className="insight-item">
            <span className="insight-icon">📖</span>
            <div>
              <strong>Learn</strong>
              <p>Explore subjects and discover relevant courses.</p>
            </div>
          </div>

          <div className="insight-item">
            <span className="insight-icon">🎯</span>
            <div>
              <strong>Practice</strong>
              <p>Test your knowledge with AI-powered assessments.</p>
            </div>
          </div>

          <div className="insight-item">
            <span className="insight-icon">🚀</span>
            <div>
              <strong>Grow</strong>
              <p>Find career paths and skills to work towards.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-footer">
        <div className="footer-star">✨</div>
        <div className="dashboard-footer-copy">
          <span className="footer-kicker">YOUR LEARNING JOURNEY</span>
          <strong>Make every learning decision count.</strong>
          <p>
            Explore opportunities, build skills, check your readiness
            and move closer to your career goals.
          </p>
          <div className="footer-highlights">
            <span>📚 Explore</span>
            <span>✍️ Practice</span>
            <span>🏆 Achieve</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;
