/**
 * Job Radar — LN4 High-Performance 3D Interactive Client Engine
 */

let allJobs = [];
let activeQuickFilter = 'all';
let scrollObserver = null;

document.addEventListener('DOMContentLoaded', () => {
    initScrollProgress();
    initQuickFilters();

    if (window.JOB_RADAR_DATA) {
        allJobs = window.JOB_RADAR_DATA.jobs || [];
        renderMetrics(allJobs);
        filterJobs();
    }
});

/**
 * Top Telemetry Scroll Progress Bar
 */
function initScrollProgress() {
    const progressBar = document.getElementById('scroll-progress-bar');
    if (!progressBar) return;

    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrollPercent = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
        progressBar.style.width = `${scrollPercent}%`;
    }, { passive: true });
}

/**
 * Quick Telemetry Filter Pills
 */
function initQuickFilters() {
    const buttons = document.querySelectorAll('.quick-filter-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeQuickFilter = btn.getAttribute('data-filter') || 'all';
            filterJobs();
        });
    });
}

function renderMetrics(jobs) {
    const highMatches = jobs.filter(j => j.composite_score >= 80).length;
    const highElem = document.getElementById('metric-high-match');
    const totalElem = document.getElementById('metric-total-jobs');
    if (highElem) highElem.textContent = highMatches;
    if (totalElem) totalElem.textContent = jobs.length;
}

function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Recent';
    try {
        const date = new Date(dateStr.replace(' ', 'T'));
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (isNaN(diffHours) || diffHours < 0) {
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        }
        if (diffHours < 1) return 'Just now';
        if (diffHours === 1) return '1h ago';
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch (e) {
        return dateStr.split(' ')[0] || 'Recent';
    }
}

function renderJobList(jobs) {
    const container = document.getElementById('job-grid-container');
    if (!jobs || jobs.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 4.5rem 1rem; color: var(--text-faint);">
                <p style="font-size: 1.25rem; font-weight: 700; color: var(--text-muted); margin-bottom: 0.5rem; font-family: var(--font-display);">NO MATCHING ROLES IN RADAR</p>
                <p style="font-size: 0.85rem; font-family: var(--font-mono);">Adjust telemetry filters or lower minimum match threshold.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = jobs.map((job, idx) => {
        const score = job.composite_score;
        let badgeClass = 'low';
        if (score >= 80) badgeClass = 'high';
        else if (score >= 65) badgeClass = 'med';

        const matchedTags = (job.matched_skills || []).slice(0, 3).map(s => 
            `<span class="tag-pill skill-match">✓ ${escapeHtml(s)}</span>`
        ).join('');

        const missingTags = (job.missing_skills || []).slice(0, 2).map(s => 
            `<span class="tag-pill skill-gap">✕ ${escapeHtml(s)}</span>`
        ).join('');

        const timeTag = `<span class="tag-pill time" title="Posted: ${escapeHtml(job.posted_date || '')}">🕒 ${formatRelativeTime(job.posted_date)}</span>`;

        return `
            <div class="job-card" id="job-card-${idx}">
                <div class="card-content-wrap">
                    <div class="card-top">
                        <div>
                            <h3 class="card-title">${escapeHtml(job.title)}</h3>
                            <div class="card-company-meta">
                                <strong>${escapeHtml(job.company)}</strong>
                                <span>•</span>
                                <span>${escapeHtml(job.location)}</span>
                            </div>
                        </div>
                        <div class="match-circle ${badgeClass}">${score}%</div>
                    </div>

                    <div class="tags-row">
                        ${timeTag}
                        <span class="tag-pill">${escapeHtml(job.work_type)}</span>
                        <span class="tag-pill">${escapeHtml((job.job_type || 'working_student').replace('_', ' ').toUpperCase())}</span>
                        ${matchedTags}
                        ${missingTags}
                    </div>
                </div>

                <div class="card-bottom">
                    <button class="btn btn-primary" onclick="openDetailModal(${idx})">
                        Match Telemetry
                    </button>
                    <a href="${escapeHtml(job.apply_url)}" target="_blank" class="btn btn-ghost" title="Open Job Posting">
                        Apply ↗
                    </a>
                </div>
            </div>
        `;
    }).join('');

    // Attach 3D Scroll Reveal
    init3DScrollReveal();
}

/**
 * 3D Scroll Reveal Observer (Smooth entrance on scroll)
 */
function init3DScrollReveal() {
    if (scrollObserver) {
        scrollObserver.disconnect();
    }

    const cards = document.querySelectorAll('.job-card');
    
    // Fallback if IntersectionObserver is not supported
    if (!('IntersectionObserver' in window)) {
        cards.forEach(card => card.classList.add('in-view'));
        return;
    }

    scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    cards.forEach((card, i) => {
        // Stagger initial items in viewport
        card.style.transitionDelay = `${Math.min(i * 35, 250)}ms`;
        scrollObserver.observe(card);
    });
}

function updateScoreSlider(val) {
    const lbl = document.getElementById('slider-val-label');
    if (lbl) lbl.textContent = `${val}%`;
    filterJobs();
}

function filterJobs() {
    const searchInput = document.getElementById('search-input');
    const locSelect = document.getElementById('filter-location');
    const workSelect = document.getElementById('filter-work-type');
    const slider = document.getElementById('score-slider');
    const sortSelect = document.getElementById('sort-by');

    const search = searchInput ? searchInput.value.toLowerCase() : '';
    const location = locSelect ? locSelect.value.toLowerCase() : '';
    const workType = workSelect ? workSelect.value.toLowerCase() : '';
    const minScore = slider ? (parseInt(slider.value, 10) || 0) : 0;
    const sortBy = sortSelect ? sortSelect.value : 'score';

    let filtered = allJobs.filter(job => {
        const matchesSearch = !search || 
            job.title.toLowerCase().includes(search) || 
            job.company.toLowerCase().includes(search) ||
            (job.required_skills || '').toLowerCase().includes(search);

        const matchesLoc = !location || job.location.toLowerCase().includes(location);
        const matchesWork = !workType || job.work_type.toLowerCase().includes(workType);
        const matchesScore = job.composite_score >= minScore;

        // Apply Quick Filter Pills
        let matchesQuick = true;
        if (activeQuickFilter === 'high') {
            matchesQuick = job.composite_score >= 80;
        } else if (activeQuickFilter === 'remote') {
            matchesQuick = job.work_type.toLowerCase().includes('remote');
        } else if (activeQuickFilter === 'working_student') {
            matchesQuick = (job.job_type || '').toLowerCase().includes('working_student') || job.title.toLowerCase().includes('werkstudent');
        } else if (activeQuickFilter === 'bavaria') {
            const loc = job.location.toLowerCase();
            matchesQuick = loc.includes('hof') || loc.includes('munich') || loc.includes('münchen') || loc.includes('nuremberg') || loc.includes('nürnberg') || loc.includes('erlangen') || loc.includes('regensburg');
        }

        return matchesSearch && matchesLoc && matchesWork && matchesScore && matchesQuick;
    });

    if (sortBy === 'date') {
        filtered.sort((a, b) => new Date(b.posted_date || 0) - new Date(a.posted_date || 0));
    } else {
        filtered.sort((a, b) => b.composite_score - a.composite_score);
    }

    renderJobList(filtered);
}

function openDetailModal(idx) {
    const job = allJobs[idx];
    if (!job) return;

    document.getElementById('modal-job-title').textContent = job.title;
    document.getElementById('modal-job-sub').textContent = `${job.company} • ${job.location} (${job.work_type}) • Posted: ${formatRelativeTime(job.posted_date)}`;
    
    const badge = document.getElementById('modal-score-badge');
    badge.textContent = `${job.composite_score}%`;
    badge.className = `match-circle ${job.composite_score >= 80 ? 'high' : (job.composite_score >= 65 ? 'med' : 'low')}`;

    document.getElementById('modal-apply-btn').href = job.apply_url;

    // 4 Pillars
    const p = job.pillar_scores || {};
    document.getElementById('score-skills').textContent = `${p.skills || 0} / 40`;
    document.getElementById('bar-skills').style.width = `${((p.skills || 0) / 40) * 100}%`;

    document.getElementById('score-location').textContent = `${p.location || 0} / 25`;
    document.getElementById('bar-location').style.width = `${((p.location || 0) / 25) * 100}%`;

    document.getElementById('score-language').textContent = `${p.language || 0} / 20`;
    document.getElementById('bar-language').style.width = `${((p.language || 0) / 20) * 100}%`;

    document.getElementById('score-role').textContent = `${p.role_fit || 0} / 15`;
    document.getElementById('bar-role').style.width = `${((p.role_fit || 0) / 15) * 100}%`;

    // Why Matched
    const whyList = document.getElementById('modal-why-list');
    whyList.innerHTML = (job.why_matched || []).map(w => `<li>${escapeHtml(w)}</li>`).join('') || '<li>Standard role requirements match profile.</li>';

    // Missing
    const gapList = document.getElementById('modal-gap-list');
    const gapBox = document.getElementById('modal-gap-box');
    if (!job.missing_requirements || job.missing_requirements.length === 0) {
        gapBox.style.display = 'none';
    } else {
        gapBox.style.display = 'block';
        gapList.innerHTML = job.missing_requirements.map(g => `<li>${escapeHtml(g)}</li>`).join('');
    }

    const overlay = document.getElementById('modal-overlay');
    overlay.style.display = 'flex';
    setTimeout(() => overlay.classList.add('active'), 10);
}

function closeModal(event) {
    if (event && event.target !== event.currentTarget) return;
    const overlay = document.getElementById('modal-overlay');
    if (!overlay) return;
    overlay.classList.remove('active');
    setTimeout(() => { overlay.style.display = 'none'; }, 250);
}

// Close modal when Escape key is pressed
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' || e.key === 'Esc') {
        const overlay = document.getElementById('modal-overlay');
        if (overlay && (overlay.classList.contains('active') || overlay.style.display === 'flex')) {
            closeModal();
        }
    }
});

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
