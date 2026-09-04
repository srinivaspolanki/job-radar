#!/usr/bin/env bash
set -e

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "===================================================="
echo "🚀 Running ApplyFlow Job Radar Daily Refresh"
echo "===================================================="

# Check if Python is available
PYTHON_CMD="python3"
if [ -d "backend/venv" ]; then
    PYTHON_CMD="backend/venv/bin/python"
elif [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python"
fi

# 1. Fetch live public job feeds into data/arbeitnow_jobs.csv
echo "📥 [1/3] Fetching live feed postings..."
$PYTHON_CMD scripts/fetch_feed.py

# 2. Score, rank, and regenerate site/index.html
echo "⚙️ [2/3] Ranking listings against profile and compiling site/index.html..."
$PYTHON_CMD scripts/build_site.py

# 3. Deliver Telegram Morning Digest (if configured)
echo "📱 [3/3] Checking & dispatching Telegram morning digest..."
$PYTHON_CMD scripts/send_telegram.py

echo "===================================================="
echo "✅ Job Radar refresh complete! Open site/index.html to view."
echo "===================================================="
