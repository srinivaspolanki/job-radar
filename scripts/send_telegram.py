#!/usr/bin/env python3
"""
scripts/send_telegram.py
Delivers a morning Job Radar intelligence digest to Telegram.
Uses standard library urllib (no external dependencies required).
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from rank_jobs import rank_all_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_bot")

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_file():
    """Load environment variables from .env file if present."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

def format_relative_time(date_str):
    if not date_str:
        return "Recent"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00").replace(" ", "T"))
        now = datetime.now(timezone.utc)
        diff_hours = int((now - dt).total_seconds() // 3600)
        diff_days = diff_hours // 24
        if diff_hours < 1:
            return "Just now"
        if diff_hours < 24:
            return f"{diff_hours}h ago"
        if diff_days == 1:
            return "Yesterday"
        if diff_days < 7:
            return f"{diff_days}d ago"
        return date_str.split(" ")[0]
    except Exception:
        return str(date_str).split(" ")[0] if date_str else "Recent"

def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_telegram_message(ranked_jobs, profile, dashboard_url=None):
    candidate_name = profile.get("candidate_name", "Candidate")
    degree = profile.get("degree", "Student")
    try:
        from zoneinfo import ZoneInfo
        now_berlin = datetime.now(ZoneInfo("Europe/Berlin"))
        today_str = now_berlin.strftime("%A, %b %d, %Y (%Z)")
    except Exception:
        today_str = datetime.now().strftime("%A, %b %d, %Y")
    
    # Filter top matches (score >= 70, up to 5 jobs)
    top_jobs = [j for j in ranked_jobs if j.get("composite_score", 0) >= 70][:5]
    if not top_jobs:
        top_jobs = ranked_jobs[:3]

    high_match_count = len([j for j in ranked_jobs if j.get("composite_score", 0) >= 80])

    lines = []
    lines.append("🎯 <b>Job Radar Morning Intelligence</b>")
    lines.append(f"📅 <i>{today_str} · Digest for {escape_html(candidate_name)}</i>")
    lines.append("")

    if high_match_count > 0:
        lines.append(f"🔥 <b>Found {high_match_count} High Match (>80%) roles today:</b>")
    else:
        lines.append("⚡ <b>Top Ranked Roles Today:</b>")
    lines.append("")

    for i, job in enumerate(top_jobs, 1):
        title = escape_html(job.get("title", "Role"))
        company = escape_html(job.get("company", "Company"))
        location = escape_html(job.get("location", "Germany"))
        work_type = escape_html(job.get("work_type", "On-site"))
        score = job.get("composite_score", 0)
        apply_url = job.get("apply_url", "#")
        posted = format_relative_time(job.get("posted_date"))
        
        matched_skills = job.get("matched_skills", [])
        skills_str = ", ".join(matched_skills[:3]) if matched_skills else "Standard fit"

        lines.append(f"<b>{i}️⃣ {title}</b>")
        lines.append(f"🏢 <b>{company}</b> · 📍 <i>{location} ({work_type})</i>")
        lines.append(f"⚡ <b>Match: {score}%</b> · Posted: {posted}")
        lines.append(f"💡 <i>Matched: {escape_html(skills_str)}</i>")
        lines.append(f"🔗 <a href=\"{apply_url}\">Apply on Official Portal ↗</a>")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 <b>Total Analyzed:</b> {len(ranked_jobs)} listings")
    
    if dashboard_url:
        lines.append(f"🌐 <b>Live Radar:</b> <a href=\"{dashboard_url}\">Open Full 3D Dashboard</a>")
    
    return "\n".join(lines)

def send_telegram_notification(bot_token, chat_id, message_text):
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if res_json.get("ok"):
                logger.info("✅ Successfully sent morning digest to Telegram!")
                return True
            else:
                logger.error(f"❌ Telegram API returned error: {res_json}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram message: {e}")
        return False

def main():
    load_env_file()
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    dashboard_url = os.environ.get("DASHBOARD_URL", "").strip()

    is_test = "--test" in sys.argv

    if not bot_token or not chat_id:
        logger.info("ℹ️ Telegram credentials not configured. Skipping alert.")
        logger.info("   (Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env or GitHub Secrets to enable)")
        return

    logger.info("Scoring listings for Telegram digest...")
    ranked_jobs, profile = rank_all_jobs()

    if is_test:
        test_msg = (
            "🚀 <b>Job Radar Test Alert</b>\n\n"
            "✅ Your Telegram Bot connection is successfully configured!\n"
            f"Candidate: <b>{escape_html(profile.get('candidate_name', 'Student'))}</b>\n"
            f"Synced Listings: <b>{len(ranked_jobs)} jobs monitored</b>\n\n"
            "You will receive your daily morning digest every morning at 07:00 AM German Time."
        )
        send_telegram_notification(bot_token, chat_id, test_msg)
        return

    message = build_telegram_message(ranked_jobs, profile, dashboard_url)
    send_telegram_notification(bot_token, chat_id, message)

if __name__ == "__main__":
    main()
