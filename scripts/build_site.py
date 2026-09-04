#!/usr/bin/env python3
"""
scripts/build_site.py
Compiles ranked job data and generates an LN4-inspired 3D interactive site/index.html
with smooth scrolling, 3D scroll entrance, and telemetry breakdown modal.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from rank_jobs import rank_all_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_site")

BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR / "site"
INDEX_HTML_PATH = SITE_DIR / "index.html"

def generate_html(ranked_jobs, profile):
    try:
        from zoneinfo import ZoneInfo
        now_berlin = datetime.now(ZoneInfo("Europe/Berlin"))
        build_time = now_berlin.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        build_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    candidate_name = profile.get("candidate_name", "Candidate")
    degree = profile.get("degree", "M.Sc. Student")
    university = profile.get("university", "University")

    embedded_payload = {
        "build_time": build_time,
        "candidate": {
            "name": candidate_name,
            "degree": degree,
            "university": university,
            "skills": profile.get("skills", []),
            "languages": profile.get("languages", {})
        },
        "jobs": ranked_jobs
    }

    payload_json_str = json.dumps(embedded_payload, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Radar — {candidate_name}</title>
    <meta name="description" content="High Performance Career Intelligence Dashboard ranking tech roles against structured candidate profile.">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800;900&family=Syne:wght@700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Top Telemetry Scroll Progress Bar -->
    <div class="scroll-progress" id="scroll-progress-bar"></div>

    <div class="container">
        <!-- Header -->
        <header class="app-header">
            <div class="brand-group">
                <div class="brand-radar-box">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
                        <path d="M2 12h20"></path>
                    </svg>
                </div>
                <div class="brand-title-wrap">
                    <h1 class="brand-title">JOB RADAR</h1>
                    <span class="brand-subtitle">High-Performance Career Telemetry</span>
                </div>
            </div>
            <div class="header-meta">
                <span class="meta-chip candidate">
                    <span class="live-indicator"></span>
                    {candidate_name} · {degree}
                </span>
                <span class="meta-chip">SYNC: {build_time}</span>
            </div>
        </header>

        <!-- Metrics Row -->
        <div class="metrics-row">
            <div class="metric-card">
                <div>
                    <div class="metric-number" id="metric-high-match">0</div>
                    <div class="metric-label">High Matches (&gt;80%)</div>
                </div>
                <div class="metric-badge-icon badge-neon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                    </svg>
                </div>
            </div>
            <div class="metric-card">
                <div>
                    <div class="metric-number" id="metric-total-jobs">{len(ranked_jobs)}</div>
                    <div class="metric-label">Active Listings Monitored</div>
                </div>
                <div class="metric-badge-icon badge-cyan">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                    </svg>
                </div>
            </div>
            <div class="metric-card">
                <div>
                    <div class="metric-number">07:00 CEST</div>
                    <div class="metric-label">Daily German Morning Sync</div>
                </div>
                <div class="metric-badge-icon badge-mono">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </div>
            </div>
        </div>

        <!-- Quick Telemetry Filters -->
        <div class="quick-filters-row">
            <button class="quick-filter-btn active" data-filter="all">ALL ROLES</button>
            <button class="quick-filter-btn" data-filter="high">⚡ HIGH MATCHES (&gt;80%)</button>
            <button class="quick-filter-btn" data-filter="remote">🌐 100% REMOTE</button>
            <button class="quick-filter-btn" data-filter="working_student">🎓 WORKING STUDENT</button>
            <button class="quick-filter-btn" data-filter="bavaria">📍 BAVARIA / HOF</button>
        </div>

        <!-- Filter & Search Toolbar -->
        <div class="toolbar-panel">
            <div class="search-field">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: var(--text-faint);">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input type="text" id="search-input" placeholder="Search role, company, or stack (e.g. Python, ROS 2, AWS, Docker)..." oninput="filterJobs()">
            </div>
            <div class="filter-actions">
                <select class="custom-select" id="filter-location" onchange="filterJobs()">
                    <option value="">All Locations</option>
                    <option value="Hof">Hof</option>
                    <option value="Munich">Munich / München</option>
                    <option value="Nuremberg">Nuremberg / Nürnberg</option>
                    <option value="Berlin">Berlin</option>
                    <option value="Frankfurt">Frankfurt</option>
                </select>
                <select class="custom-select" id="filter-work-type" onchange="filterJobs()">
                    <option value="">All Work Types</option>
                    <option value="Remote">100% Remote</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="On-site">On-site</option>
                </select>
                <select class="custom-select" id="sort-by" onchange="filterJobs()">
                    <option value="score">Sort: Match %</option>
                    <option value="date">Sort: Newest</option>
                </select>
                <div class="slider-wrapper">
                    <span>Min:</span>
                    <span class="score-chip" id="slider-val-label">0%</span>
                    <input type="range" id="score-slider" min="0" max="95" step="5" value="0" oninput="updateScoreSlider(this.value)">
                </div>
            </div>
        </div>

        <!-- 3D Interactive Job Grid -->
        <main class="job-grid" id="job-grid-container"></main>
    </div>

    <!-- Slide-out Match Breakdown Modal -->
    <div class="modal-backdrop" id="modal-overlay" onclick="closeModal(event)">
        <div class="modal-window" onclick="event.stopPropagation()">
            <div class="modal-top">
                <div>
                    <h2 class="card-title" id="modal-job-title" style="font-size: 1.35rem; margin-bottom: 0.35rem;">Job Title</h2>
                    <p id="modal-job-sub" style="font-size: 0.85rem; color: var(--text-muted); font-family: var(--font-mono);">Company • Location</p>
                </div>
                <div style="display: flex; align-items: center; gap: 0.85rem;">
                    <div class="match-circle high" id="modal-score-badge">0%</div>
                    <button class="modal-close-btn" onclick="closeModal()">✕</button>
                </div>
            </div>

            <!-- Scoring Breakdown Grid -->
            <div class="section-label">4-PILLAR SCORING TELEMETRY</div>
            <div class="breakdown-grid">
                <div class="pillar-box">
                    <div class="pillar-header">
                        <span>Skills Fit (40%)</span>
                        <span id="score-skills">0 / 40</span>
                    </div>
                    <div class="pillar-bar-bg">
                        <div class="pillar-bar-fill" id="bar-skills" style="width: 0%;"></div>
                    </div>
                </div>
                <div class="pillar-box">
                    <div class="pillar-header">
                        <span>Location / Remote (25%)</span>
                        <span id="score-location">0 / 25</span>
                    </div>
                    <div class="pillar-bar-bg">
                        <div class="pillar-bar-fill" id="bar-location" style="width: 0%;"></div>
                    </div>
                </div>
                <div class="pillar-box">
                    <div class="pillar-header">
                        <span>Language CEFR (20%)</span>
                        <span id="score-language">0 / 20</span>
                    </div>
                    <div class="pillar-bar-bg">
                        <div class="pillar-bar-fill" id="bar-language" style="width: 0%;"></div>
                    </div>
                </div>
                <div class="pillar-box">
                    <div class="pillar-header">
                        <span>Role & Student Fit (15%)</span>
                        <span id="score-role">0 / 15</span>
                    </div>
                    <div class="pillar-bar-bg">
                        <div class="pillar-bar-fill" id="bar-role" style="width: 0%;"></div>
                    </div>
                </div>
            </div>

            <!-- Why Matched List -->
            <div class="section-label">MATCH RATIONALE</div>
            <ul class="why-list" id="modal-why-list"></ul>

            <!-- Skill Gaps (if any) -->
            <div id="modal-gap-box" class="gap-box" style="display: none;">
                <div class="section-label" style="color: var(--accent-rose); margin-bottom: 0.5rem;">POTENTIAL SKILL GAPS</div>
                <ul class="gap-list" id="modal-gap-list"></ul>
            </div>

            <!-- Modal Action Buttons -->
            <div style="display: flex; gap: 0.85rem; margin-top: 1.5rem;">
                <a id="modal-apply-btn" href="#" target="_blank" class="btn btn-ghost" style="flex: 1; text-align: center; padding: 0.85rem;">
                    Apply on Official Portal ↗
                </a>
                <button class="btn btn-primary" onclick="closeModal()" style="padding: 0.85rem 1.5rem;">
                    Close
                </button>
            </div>
        </div>
    </div>

    <!-- Embedded State Data -->
    <script>
        window.JOB_RADAR_DATA = {payload_json_str};
    </script>
    <script src="js/app.js"></script>
</body>
</html>
"""
    return html_content

def build():
    logger.info("Building Job Radar 3D site...")
    SITE_DIR.mkdir(exist_ok=True)
    
    ranked_jobs, profile = rank_all_jobs()
    html_content = generate_html(ranked_jobs, profile)
    
    INDEX_HTML_PATH.write_text(html_content, encoding="utf-8")
    logger.info(f"Successfully generated standalone site at {INDEX_HTML_PATH} with {len(ranked_jobs)} ranked jobs.")

if __name__ == "__main__":
    build()
