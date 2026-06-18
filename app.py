#!/usr/bin/env python3
"""
customer-app-demo — Intentionally vulnerable dummy web app
===========================================================
Used to simulate a customer's deployed application for VGTSec scanning.
Contains intentional security weaknesses so ZAP finds real findings.

DO NOT use this in production. It is a demo target only.
"""

from flask import Flask, request, jsonify, render_template_string, redirect, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "demo-secret-not-for-prod")

# ── Credentials ───────────────────────────────────────────────────────────────
VALID_USERS = {
    "admin": "admin123",
    "user1": "password123",
}

# ── Dummy data ─────────────────────────────────────────────────────────────────
DOCUMENTS = [
    {"id": 1, "title": "Q1 Financial Report",    "owner": "admin",  "date": "2024-01-15", "status": "Approved"},
    {"id": 2, "title": "Product Roadmap 2024",   "owner": "user1",  "date": "2024-02-03", "status": "Draft"},
    {"id": 3, "title": "Security Policy v2",     "owner": "admin",  "date": "2024-02-20", "status": "Review"},
    {"id": 4, "title": "Employee Handbook",      "owner": "user1",  "date": "2024-03-01", "status": "Approved"},
    {"id": 5, "title": "Infrastructure Diagram", "owner": "admin",  "date": "2024-03-10", "status": "Draft"},
]

ALL_USERS = [
    {"id": 1, "username": "admin",  "email": "admin@corp.local",  "role": "Administrator", "status": "Active"},
    {"id": 2, "username": "user1",  "email": "user1@corp.local",  "role": "Member",        "status": "Active"},
    {"id": 3, "username": "viewer", "email": "viewer@corp.local", "role": "Viewer",        "status": "Inactive"},
]

# ── Shared CSS / Layout ────────────────────────────────────────────────────────
BASE_STYLE = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
         background: #f0f2f5; color: #1a1a2e; min-height: 100vh; }
  a { color: inherit; text-decoration: none; }

  /* Navbar */
  .navbar {
    background: #1a1a2e; color: #fff; display: flex;
    align-items: center; justify-content: space-between;
    padding: 0 2rem; height: 60px; position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,.4);
  }
  .navbar .brand { font-size: 1.2rem; font-weight: 700; letter-spacing: .5px; color: #7c83fd; }
  .navbar .nav-links { display: flex; gap: 1.5rem; align-items: center; }
  .navbar .nav-links a { color: #cbd5e1; font-size: .9rem; transition: color .2s; }
  .navbar .nav-links a:hover { color: #fff; }
  .btn-logout {
    background: #ef4444; color: #fff !important; padding: .35rem .9rem;
    border-radius: 6px; font-size: .85rem; transition: background .2s;
  }
  .btn-logout:hover { background: #dc2626 !important; }

  /* Container */
  .container { max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem; }

  /* Cards */
  .card {
    background: #fff; border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08); padding: 1.75rem;
  }
  .card h2 { font-size: 1.2rem; font-weight: 600; margin-bottom: 1.2rem; color: #1e293b; }

  /* Stat grid */
  .stats-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 1.25rem; margin-bottom: 1.5rem; }
  .stat-card {
    background: #fff; border-radius: 12px; padding: 1.5rem 1.75rem;
    box-shadow: 0 2px 12px rgba(0,0,0,.08); display: flex; flex-direction: column; gap: .4rem;
  }
  .stat-card .label { font-size: .8rem; text-transform: uppercase; letter-spacing: .8px; color: #64748b; }
  .stat-card .value { font-size: 2.4rem; font-weight: 700; color: #7c83fd; }

  /* Table */
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: .75rem 1rem; font-size: .8rem;
       text-transform: uppercase; letter-spacing: .6px; color: #64748b;
       border-bottom: 2px solid #e2e8f0; }
  td { padding: .85rem 1rem; font-size: .9rem; border-bottom: 1px solid #f1f5f9; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #f8fafc; }

  /* Badge */
  .badge { display: inline-block; padding: .25rem .65rem; border-radius: 99px;
           font-size: .75rem; font-weight: 600; }
  .badge-green { background: #dcfce7; color: #15803d; }
  .badge-yellow { background: #fef9c3; color: #a16207; }
  .badge-blue  { background: #dbeafe; color: #1d4ed8; }

  /* Form controls */
  .form-row { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.2rem; }
  input[type=text], input[type=password], input[type=search] {
    padding: .55rem .9rem; border: 1.5px solid #e2e8f0; border-radius: 8px;
    font-size: .9rem; outline: none; transition: border .2s;
  }
  input:focus { border-color: #7c83fd; }
  .btn {
    padding: .55rem 1.2rem; border: none; border-radius: 8px; cursor: pointer;
    font-size: .9rem; font-weight: 600; transition: opacity .2s;
  }
  .btn:hover { opacity: .85; }
  .btn-primary { background: #7c83fd; color: #fff; }
  .btn-secondary { background: #e2e8f0; color: #334155; }

  /* Detail list */
  .detail-list { display: grid; grid-template-columns: 160px 1fr; gap: .75rem 1rem; }
  .detail-list .dk { font-weight: 600; color: #64748b; font-size: .85rem; }
  .detail-list .dv { font-size: .9rem; color: #1e293b; }

  /* Alert */
  .alert { padding: .75rem 1rem; border-radius: 8px; margin-bottom: 1rem;
           font-size: .9rem; }
  .alert-red { background: #fee2e2; color: #b91c1c; border-left: 4px solid #ef4444; }
  .alert-yellow { background: #fef9c3; color: #92400e; border-left: 4px solid #f59e0b; }
  .alert-info { background: #dbeafe; color: #1e40af; border-left: 4px solid #3b82f6; }

  /* Login page */
  .login-wrap {
    min-height: 100vh; display: flex; align-items: center;
    justify-content: center; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  }
  .login-card {
    background: #fff; border-radius: 16px; padding: 2.5rem 2rem;
    width: 100%; max-width: 400px; box-shadow: 0 20px 60px rgba(0,0,0,.4);
  }
  .login-card .logo { text-align: center; margin-bottom: 1.75rem; }
  .login-card .logo span { font-size: 1.5rem; font-weight: 800; color: #7c83fd; }
  .login-card .logo p { font-size: .8rem; color: #64748b; margin-top: .25rem; }
  .login-card label { display: block; font-size: .8rem; font-weight: 600;
                      color: #475569; margin-bottom: .3rem; }
  .login-card input[type=text], .login-card input[type=password] {
    width: 100%; margin-bottom: 1rem;
  }
  .login-card .btn-primary { width: 100%; padding: .7rem; font-size: 1rem; }
</style>
"""

def navbar(active_user=None):
    user = active_user or session.get("user", "")
    return f"""
<nav class="navbar">
  <span class="brand">&#128196; DocVault</span>
  <div class="nav-links">
    <a href="/dashboard">Dashboard</a>
    <a href="/documents">Documents</a>
    <a href="/search">Search</a>
    <a href="/admin">Admin</a>
    {"<a href='/logout' class='btn-logout'>Logout</a>" if user else "<a href='/login'>Login</a>"}
  </div>
</nav>"""

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "app": "customer-app-demo", "version": "2.0.0"})

@app.route("/")
def index():
    return redirect("/login")

# ── LOGIN (intentional: no rate limiting) ──────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if VALID_USERS.get(username) == password:
            session["user"] = username
            return redirect("/dashboard")
        error = "Invalid username or password."
    html = BASE_STYLE + f"""
<div class="login-wrap">
  <div class="login-card">
    <div class="logo">
      <span>&#128196; DocVault</span>
      <p>Document Management System</p>
    </div>
    {"<div class='alert alert-red'>" + error + "</div>" if error else ""}
    <form method="POST" action="/login">
      <label for="username">Username</label>
      <input id="username" type="text" name="username" placeholder="Enter username" />
      <label for="password">Password</label>
      <input id="password" type="password" name="password" placeholder="Enter password" />
      <button id="login-btn" type="submit" class="btn btn-primary">Sign In</button>
    </form>
  </div>
</div>"""
    return render_template_string(html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    username = session.get("user") or request.args.get("user", "guest")
    html = BASE_STYLE + navbar() + f"""
<div class="container">
  <div style="margin-bottom:1.5rem;">
    <h1 style="font-size:1.5rem;font-weight:700;color:#1e293b;">
      Welcome back, {username}!
    </h1>
    <p style="color:#64748b;margin-top:.3rem;">Here's your document overview.</p>
  </div>
  <div class="stats-grid">
    <div class="stat-card">
      <span class="label">Total Documents</span>
      <span class="value">24</span>
    </div>
    <div class="stat-card">
      <span class="label">Shared</span>
      <span class="value">8</span>
    </div>
    <div class="stat-card">
      <span class="label">Recent</span>
      <span class="value">3</span>
    </div>
  </div>
  <div class="card">
    <h2>Quick Actions</h2>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
      <a href="/documents"><button class="btn btn-primary" id="btn-view-docs">View Documents</button></a>
      <a href="/search"><button class="btn btn-secondary" id="btn-search">Search</button></a>
    </div>
  </div>
</div>"""
    return render_template_string(html)

# ── DOCUMENTS LIST ─────────────────────────────────────────────────────────────
@app.route("/documents")
def documents():
    status_cls = {"Approved": "badge-green", "Draft": "badge-yellow", "Review": "badge-blue"}
    rows = "".join(
        f"""<tr>
          <td><a href="/documents/{d['id']}" style="color:#7c83fd;font-weight:600;">{d['title']}</a></td>
          <td>{d['owner']}</td><td>{d['date']}</td>
          <td><span class="badge {status_cls.get(d['status'], '')}">{d['status']}</span></td>
        </tr>""" for d in DOCUMENTS
    )
    html = BASE_STYLE + navbar() + f"""
<div class="container">
  <div class="form-row" style="justify-content:space-between;align-items:center;margin-bottom:1rem;">
    <h1 style="font-size:1.4rem;font-weight:700;color:#1e293b;">Documents</h1>
    <button class="btn btn-primary" id="btn-upload">&#43; Upload Document</button>
  </div>
  <div class="card">
    <div class="form-row">
      <form method="GET" action="/search" style="display:flex;gap:.5rem;">
        <input type="search" name="q" placeholder="Search documents..." style="width:260px;" />
        <button class="btn btn-secondary" type="submit" id="btn-doc-search">Search</button>
      </form>
    </div>
    <table>
      <thead><tr><th>Title</th><th>Owner</th><th>Date</th><th>Status</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""
    return render_template_string(html)

# ── DOCUMENT DETAIL ────────────────────────────────────────────────────────────
@app.route("/documents/<int:doc_id>")
def document_detail(doc_id):
    doc = next((d for d in DOCUMENTS if d["id"] == doc_id), None)
    if not doc:
        html = BASE_STYLE + navbar() + """
<div class="container"><div class="card">
  <div class="alert alert-red">Document not found.</div>
  <a href="/documents"><button class="btn btn-secondary">Back to Documents</button></a>
</div></div>"""
        return render_template_string(html), 404
    status_cls = {"Approved": "badge-green", "Draft": "badge-yellow", "Review": "badge-blue"}
    html = BASE_STYLE + navbar() + f"""
<div class="container">
  <div style="margin-bottom:1rem;">
    <a href="/documents" style="color:#7c83fd;font-size:.9rem;">&#8592; Back to Documents</a>
  </div>
  <div class="card">
    <h2>{doc['title']}</h2>
    <div class="detail-list" style="margin-top:1rem;">
      <span class="dk">Document ID</span><span class="dv">{doc['id']}</span>
      <span class="dk">Owner</span><span class="dv">{doc['owner']}</span>
      <span class="dk">Date</span><span class="dv">{doc['date']}</span>
      <span class="dk">Status</span>
      <span class="dv"><span class="badge {status_cls.get(doc['status'], '')}">{doc['status']}</span></span>
    </div>
    <div style="margin-top:1.5rem;padding-top:1.25rem;border-top:1px solid #f1f5f9;">
      <h3 style="font-size:1rem;margin-bottom:.75rem;color:#475569;">Document Preview</h3>
      <p style="color:#64748b;font-size:.9rem;line-height:1.6;">
        This is a preview of <strong>{doc['title']}</strong>. The full document content
        would be rendered here in a production deployment. File type: PDF. Pages: 12.
      </p>
    </div>
  </div>
</div>"""
    return render_template_string(html)

# ── SEARCH (intentional: query reflected in page — XSS) ───────────────────────
@app.route("/search")
def search():
    query = request.args.get("q", "")
    results_html = ""
    if query:
        matches = [d for d in DOCUMENTS if query.lower() in d["title"].lower()]
        if matches:
            rows = "".join(
                f"""<tr>
                  <td><a href="/documents/{d['id']}" style="color:#7c83fd;font-weight:600;">{d['title']}</a></td>
                  <td>{d['owner']}</td><td>{d['date']}</td>
                </tr>""" for d in matches
            )
            results_html = f"""
<div class="card" style="margin-top:1.25rem;">
  <h2>Results for: {query}</h2>
  <table>
    <thead><tr><th>Title</th><th>Owner</th><th>Date</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""
        else:
            results_html = f"""
<div class="card" style="margin-top:1.25rem;">
  <div class="alert alert-info">No documents found for: {query}</div>
</div>"""
    html = BASE_STYLE + navbar() + f"""
<div class="container">
  <h1 style="font-size:1.4rem;font-weight:700;color:#1e293b;margin-bottom:1.25rem;">Search Documents</h1>
  <div class="card">
    <form method="GET" action="/search" style="display:flex;gap:.75rem;">
      <input type="text" name="q" id="search-input" placeholder="Enter search term..."
             value="{query}" style="flex:1;" />
      <button class="btn btn-primary" type="submit" id="btn-search-submit">Search</button>
    </form>
  </div>
  {results_html}
</div>"""
    return render_template_string(html)

# ── ADMIN PANEL (intentional: unauthenticated) ─────────────────────────────────
@app.route("/admin")
def admin():
    rows = "".join(
        f"""<tr>
          <td>{u['id']}</td><td>{u['username']}</td>
          <td>{u['email']}</td><td>{u['role']}</td>
          <td><span class="badge {'badge-green' if u['status']=='Active' else 'badge-yellow'}">{u['status']}</span></td>
          <td>
            <button class="btn btn-secondary" style="padding:.3rem .7rem;font-size:.8rem;">Edit</button>
          </td>
        </tr>""" for u in ALL_USERS
    )
    html = BASE_STYLE + navbar() + f"""
<div class="container">
  <div class="alert alert-yellow" style="margin-bottom:1.25rem;">
    &#9888; Admin Panel — No authentication required (demo weakness)
  </div>
  <div class="form-row" style="justify-content:space-between;margin-bottom:1rem;">
    <h1 style="font-size:1.4rem;font-weight:700;color:#1e293b;">User Management</h1>
    <button class="btn btn-primary" id="btn-add-user">&#43; Add User</button>
  </div>
  <div class="card">
    <table>
      <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""
    return render_template_string(html)

# ── PROFILE (intentional: user param reflected) ────────────────────────────────
@app.route("/profile")
def profile():
    user = request.args.get("user", "")
    return jsonify({"user": user, "role": "member", "email": f"{user}@example.com"})

# ── API endpoints ──────────────────────────────────────────────────────────────
@app.route("/api/users")
def api_users():
    return jsonify([
        {"id": 1, "username": "admin", "role": "admin"},
        {"id": 2, "username": "user1", "role": "member"},
    ])

@app.route("/api/data", methods=["POST"])
def api_data():
    data = request.get_json(silent=True) or {}
    return jsonify({"received": data, "status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
