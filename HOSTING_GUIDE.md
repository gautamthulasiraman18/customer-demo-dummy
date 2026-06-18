# Customer App Demo — Hosting Guide

A dummy vulnerable Flask app to act as the "customer's deployed application"
that VGTSec will scan. Has a `/health` endpoint so the CD scanner can detect
when it's ready before starting the scan.

---

## Option A — Run locally + expose via Ngrok (5 minutes)

This runs the app on your laptop and gives it a real public HTTPS URL via Ngrok.
Best for quick demos — no signup needed for basic use.

### Step 1 — Run the dummy app locally

```bash
cd customer-app-demo

# Install dependencies
pip install flask gunicorn

# Run the app
python app.py
# App is now at http://localhost:5000
```

Verify it's running:
```bash
curl http://localhost:5000/health
# Expected: {"status":"healthy","app":"customer-app-demo","version":"1.0.0"}
```

### Step 2 — Install Ngrok

Windows (WSL2):
```bash
# Download and install
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

Or download directly from https://ngrok.com/download and unzip.

### Step 3 — Expose the app publicly

```bash
# In a new terminal — keep this running
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abc123def456.ngrok-free.app -> http://localhost:5000
```

That `https://abc123def456.ngrok-free.app` is your public URL.

### Step 4 — Update .env.sim with the Ngrok URL

```env
TARGET_URL=https://abc123def456.ngrok-free.app
DEPLOY_HEALTH_CHECK_PATH=/health
DEPLOY_HEALTH_TIMEOUT=120
DEPLOY_HEALTH_INTERVAL=10
DEPLOY_FALLBACK_DELAY=30
```

Restart the scanner to pick up the new URL:
```bash
cd /mnt/c/Users/gautam.thulasiraman/vgtsec-cd-scanner/vgtsec-cd-scanner
docker compose -f docker-compose.sim.yml --env-file .env.sim restart cd-scanner
```

### Step 5 — Trigger a push and watch

```bash
cd /mnt/c/Users/gautam.thulasiraman/customer-app
echo "deploy trigger $(date)" >> README.md
git add README.md && git commit -m "deploy: update app" && git push origin main
```

Scanner logs will show:
```
✔ Accepted push — repo=gautam18/customer-app branch=main
⏳ Waiting for deployment to become healthy...
   Health check URL : https://abc123.ngrok-free.app/health
   Attempt 1: HTTP 200 — healthy!
✅ App is healthy after 10s — proceeding to scan
🔐 Authenticating with VGTSec...
✅ Authenticated as 'ci-scanner'
🚀 Starting scan against: https://abc123.ngrok-free.app
✅ Scan started — mission_id: mission_xxxxx
```

### Ngrok notes
- Free tier: URL changes every time you restart Ngrok — update TARGET_URL each session
- Ngrok free has a request limit (~40 req/min) — fine for a demo scan
- For a stable URL across sessions, create a free Ngrok account and use a static domain

---

## Option B — Deploy to Render.com (free cloud, stable URL)

Render gives you a real cloud deployment at `https://your-app.onrender.com`.
Best for client demos — professional-looking, persistent URL, no laptop needed.

### Step 1 — Push the dummy app to GitHub

```bash
cd customer-app-demo

git init
git add .
git commit -m "initial: customer app demo"

# Create a new repo on GitHub (github.com → New repository → customer-app-demo)
# Then:
git remote add origin https://github.com/YOUR_USERNAME/customer-app-demo.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Render

1. Go to https://render.com and sign up (free)
2. Click **New** → **Web Service**
3. Connect your GitHub account
4. Select the `customer-app-demo` repository
5. Fill in:
   - **Name:** `customer-app-demo`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
6. Click **Create Web Service**

Render will build and deploy. Takes ~2-3 minutes first time.
Your URL will be: `https://customer-app-demo.onrender.com`

### Step 3 — Verify it's running

```bash
curl https://customer-app-demo.onrender.com/health
# Expected: {"status":"healthy","app":"customer-app-demo","version":"1.0.0"}
```

### Step 4 — Update .env.sim with the Render URL

```env
TARGET_URL=https://customer-app-demo.onrender.com
DEPLOY_HEALTH_CHECK_PATH=/health
DEPLOY_HEALTH_TIMEOUT=300
DEPLOY_HEALTH_INTERVAL=15
DEPLOY_FALLBACK_DELAY=60
```

Note: Free Render instances **spin down after 15 minutes of inactivity** and take
~30 seconds to wake up. The health-check polling handles this automatically —
the scanner will wait until the app wakes up before scanning.

### Step 5 — Wire Render deploys to git pushes

Render auto-deploys when you push to `main`. So your full flow becomes:

```
git push to Gitea (local sim)
    → CD scanner webhook fires
    → scanner polls https://customer-app-demo.onrender.com/health
    → app wakes up / becomes healthy
    → scan starts on VGTSec
    → findings appear on http://localhost:4200
```

But wait — Gitea is local and Render deploys from GitHub. For the full
end-to-end demo you'd push to GitHub (triggers Render deploy) and also
push to Gitea (triggers the scanner). Or mirror pushes to both:

```bash
# Add both remotes
git remote add gitea http://localhost:3000/gautam18/customer-app.git
git remote add github https://github.com/YOUR_USERNAME/customer-app-demo.git

# Push to both at once
git push gitea main && git push github main
```

### Render notes
- Free tier: 750 hours/month (enough for continuous demo use)
- Cold start: ~30s after inactivity — health-check polling handles this
- No credit card required
- Auto-deploys on every push to main

---

## Comparison

| | Ngrok | Render |
|---|---|---|
| Setup time | 5 minutes | 10 minutes |
| URL stability | Changes on restart | Permanent |
| Requires internet | Yes (tunnel) | Yes (cloud) |
| Cold start | None | ~30s (free tier) |
| Best for | Quick local demos | Client presentations |
| Cost | Free (basic) | Free tier available |

---

## What the dummy app exposes for scanning

The app has these intentional weaknesses ZAP will find:

| Route | Weakness |
|-------|----------|
| `/login` | No rate limiting, credentials in URL on redirect |
| `/dashboard?user=` | User parameter reflected without validation |
| `/profile?user=` | Parameter enumeration possible |
| `/search?q=` | Input reflected in response |
| `/admin` | No authentication on admin endpoint |
| `/api/users` | User enumeration — returns all users unauthenticated |

These are intentional for demo purposes — enough for VGTSec to find
real High/Medium findings without being a genuinely dangerous application.
