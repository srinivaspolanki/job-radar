# Job Radar (Werkstudent & Junior Tech)

A privacy-minimized personal dashboard that ranks new working-student and junior tech roles in Germany against a structured CV profile.

---

## Features

- **Privacy-Minimized Profile**: Stores candidate skills, education, and language proficiencies in a local `profile.json` (ignored by Git).
- **Multi-Source Ingestion**:
  - `data/jobs.csv`: Curated direct company career links (Celonis, Siemens, BMW, Personio, Flix, Delivery Hero, DeepL, SAP).
  - `data/arbeitnow_jobs.csv`: Normalized live feed of fresh tech & student roles fetched automatically from the Arbeitnow public API.
- **Transparent 4-Signal Ranking**:
  - **40%**: Required & Preferred Skill Overlap (Exact & Synonym matching)
  - **25%**: Location & Remote Compatibility
  - **20%**: CEFR Language Requirements (English C1, German B1/B2)
  - **15%**: Working Student Enrollment & Job-Type Fit
- **Explainable Match Breakdown**:
  - *"Why It Matches"*: Direct evidence citations from candidate profile.
  - *"Missing Requirements"*: Honest gap analysis for missing tools or language requirements.
- **Zero-Backend Static Site**: Compiles into `site/index.html` with responsive filtering (search, city, remote, min score) and detail modal.

---

## Quick Start

### 1. Configure Your Candidate Profile
Copy the template and adjust your skills, languages, and locations:
```bash
cp profile.example.json profile.json
# Edit profile.json with your actual skills and degree
```

*(Note: `profile.json` is ignored by Git and will never be committed).*

### 2. Run Daily Refresh
Run the pipeline to fetch fresh jobs, rank them, and regenerate `site/index.html`:
```bash
./run_daily_refresh.sh
```

Open `site/index.html` directly in your browser:
```bash
# Example using Python's built-in static server
python3 -m http.server 8080 --directory site
# Then visit http://localhost:8080
```

---

## Local Daily Automation (Cron)

To automatically refresh jobs every morning at 07:00 AM locally, add this line to your crontab (`crontab -e`):

```bash
# See cron.example
0 7 * * * cd /path/to/project && ./run_daily_refresh.sh >> radar_refresh.log 2>&1
```

---

## Telegram Morning Alert Setup

Every morning at 07:00 AM UTC (09:00 AM German time), Job Radar can send a morning digest of the top ranked jobs directly to your Telegram chat.

### 1. Create a Free Telegram Bot (30 seconds)
1. Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
2. Send `/newbot`, choose a name (e.g. `MyJobRadarBot`) and username (e.g. `srinivas_job_radar_bot`).
3. Copy the **HTTP API Token** (e.g. `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 2. Get Your Personal Chat ID (10 seconds)
1. In Telegram, search for [`@userinfobot`](https://t.me/userinfobot) and press **Start**.
2. Copy your numerical **Id** (e.g. `987654321`).
3. Also open a chat with your newly created bot and send `/start`.

### 3. Configure Locally (Optional)
```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
```
Test your bot connection:
```bash
python3 scripts/send_telegram.py --test
```

---

## GitHub Pages Deployment & Automated Morning Cloud Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/daily_radar.yml`) that runs every morning at 07:00 UTC, compiles the dashboard, deploys **only the `site/` folder** to GitHub Pages, and delivers the top jobs directly to your Telegram.

### Cloud Setup Instructions:
1. Push this repository to GitHub (Public or Private).
2. Go to **Settings > Secrets and variables > Actions** in your GitHub repo and add these repository secrets:
   - `JOB_RADAR_PROFILE`: Paste the exact JSON contents of your `profile.json`.
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token from `@BotFather`.
   - `TELEGRAM_CHAT_ID`: Your numerical Telegram user ID from `@userinfobot`.
   - `DASHBOARD_URL`: Your live GitHub Pages URL (e.g. `https://<username>.github.io/<repo-name>`).
3. Go to **Settings > Pages**:
   - Under **Build and deployment > Source**, select **GitHub Actions**.
4. Push to `main` or trigger manually under the **Actions** tab!

> **Privacy Guarantee**: The workflow restores your profile only in memory during the private build to score jobs, removes it before artifact upload, and publishes only the static HTML/CSS/JS in `site/`. Your `profile.json`, data source CSVs, and scripts are never exposed on your public GitHub Pages site.

