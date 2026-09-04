#!/usr/bin/env python3
"""
scripts/rank_jobs.py
Loads profile.json (or JOB_RADAR_PROFILE env var), ingests data/*.csv,
and performs transparent 4-pillar deterministic ranking and explainable gap analysis.
"""

import os
import csv
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rank_jobs")

BASE_DIR = Path(__file__).resolve().parent.parent

CEFR_LEVELS = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

SKILL_SYNONYMS = {
    "postgres": "postgresql",
    "postgresql": "postgres",
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "k8s": "kubernetes",
    "rest": "rest api",
    "restful": "rest api",
    "aws": "amazon web services",
    "ros": "ros 2",
    "ros2": "ros 2",
    "powerbi": "power bi",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "llm": "large language models",
    "react.js": "react",
    "nextjs": "next.js"
}

def load_profile():
    # Check environment variable first (for GitHub Actions Secret JOB_RADAR_PROFILE)
    env_profile = os.getenv("JOB_RADAR_PROFILE")
    if env_profile:
        try:
            logger.info("Loading profile from JOB_RADAR_PROFILE environment variable / secret.")
            return json.loads(env_profile)
        except Exception as e:
            logger.error(f"Failed to parse JOB_RADAR_PROFILE env var: {e}")

    # Otherwise load from local profile.json
    profile_path = BASE_DIR / "profile.json"
    if profile_path.exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback to profile.example.json
    example_path = BASE_DIR / "profile.example.json"
    if example_path.exists():
        logger.warning("profile.json not found, falling back to profile.example.json")
        with open(example_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise FileNotFoundError("Could not find profile.json or profile.example.json")

def load_jobs():
    jobs = []
    seen_ids = set()

    for csv_file in [BASE_DIR / "data" / "jobs.csv", BASE_DIR / "data" / "arbeitnow_jobs.csv"]:
        if not csv_file.exists():
            continue
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                jid = row.get("job_id", "")
                if jid and jid not in seen_ids:
                    seen_ids.add(jid)
                    jobs.append(row)

    logger.info(f"Loaded {len(jobs)} unique job listings from CSVs.")
    return jobs

def parse_skills_list(skills_str):
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]

def parse_languages_dict(lang_str):
    res = {}
    if not lang_str:
        return {"English": "C1"}
    parts = lang_str.split(",")
    for p in parts:
        if ":" in p:
            k, v = p.split(":", 1)
            res[k.strip()] = v.strip().upper()
        else:
            res[p.strip()] = "B2"
    return res

def score_job(job, profile):
    why_matched = []
    missing_requirements = []

    # 1. Skill Overlap (40%)
    cand_skills = {s.lower() for s in profile.get("skills", [])}
    for s in list(cand_skills):
        if s in SKILL_SYNONYMS:
            cand_skills.add(SKILL_SYNONYMS[s])

    req_skills = parse_skills_list(job.get("required_skills", ""))
    pref_skills = parse_skills_list(job.get("preferred_skills", ""))

    matched_req = [s for s in req_skills if s.lower() in cand_skills]
    missing_req = [s for s in req_skills if s.lower() not in cand_skills]
    matched_pref = [s for s in pref_skills if s.lower() in cand_skills]

    total_req = len(req_skills)
    req_ratio = len(matched_req) / total_req if total_req > 0 else 1.0
    pref_bonus = (len(matched_pref) / max(1, len(pref_skills))) * 8.0 if pref_skills else 0.0

    skill_score = min(40.0, (req_ratio * 32.0) + pref_bonus)

    if matched_req:
        why_matched.append(f"Required skills match: {', '.join(matched_req[:4])}")
    if matched_pref:
        why_matched.append(f"Bonus preferred tools: {', '.join(matched_pref[:3])}")
    if missing_req:
        missing_requirements.append(f"Missing required skills: {', '.join(missing_req[:3])}")

    # 2. Location & Remote Compatibility (25%)
    cand_locs = [l.lower() for l in profile.get("locations", ["Munich", "Berlin", "Remote"])]
    cand_models = [m.lower() for m in profile.get("work_models", ["Hybrid", "Remote"])]
    
    job_loc = (job.get("location", "")).lower()
    job_work = (job.get("work_type", "Hybrid")).lower()

    if job_work == "remote" and ("remote" in cand_locs or "remote" in cand_models):
        loc_score = 25.0
        why_matched.append("100% Remote role matching candidate work preference")
    elif any(c in job_loc for c in cand_locs):
        loc_score = 25.0 if ("hybrid" in job_work or any(m in job_work for m in cand_models)) else 18.0
        why_matched.append(f"Location match: {job.get('location')} ({job.get('work_type')})")
    elif "remote" in job_work:
        loc_score = 20.0
        why_matched.append("Remote job position compatible across Germany")
    else:
        loc_score = 8.0
        missing_requirements.append(f"Location difference: Position based in {job.get('location')}")

    # 3. Language Match (20%)
    job_langs = parse_languages_dict(job.get("languages", ""))
    cand_langs = profile.get("languages", {"English": "C1", "German": "B2"})

    lang_satisfied = 0
    total_job_langs = len(job_langs)

    for l_name, req_level in job_langs.items():
        req_val = CEFR_LEVELS.get(req_level[:2], 3)
        cand_level = cand_langs.get(l_name, "B1")
        cand_val = CEFR_LEVELS.get(cand_level[:2], 3)

        if cand_val >= req_val:
            lang_satisfied += 1
        elif cand_val == req_val - 1:
            lang_satisfied += 0.6
            missing_requirements.append(f"Language level notice: Candidate has {l_name} {cand_level} (Job asks {req_level})")
        else:
            missing_requirements.append(f"Language gap: {l_name} {req_level} required")

    lang_score = (lang_satisfied / total_job_langs) * 20.0 if total_job_langs > 0 else 20.0
    if not any("Language" in g for g in missing_requirements):
        why_matched.append(f"Language requirements met ({', '.join(job_langs.keys())})")

    # 4. Student Status & Job-Type Fit (15%)
    cand_enrolled = profile.get("is_enrolled_student", True)
    job_type = job.get("job_type", "working_student")

    if job_type in ["working_student", "internship"] and cand_enrolled:
        role_score = 15.0
        deg = profile.get("degree", "University Degree")
        uni = profile.get("university", "University")
        why_matched.append(f"Working student eligibility confirmed: Enrolled in {deg} at {uni}")
    elif not cand_enrolled and job_type == "working_student":
        role_score = 4.0
        missing_requirements.append("Student status required for Werkstudent contract")
    else:
        role_score = 15.0
        why_matched.append("Role eligibility confirmed")

    composite = int(round(skill_score + loc_score + lang_score + role_score))
    composite = max(0, min(100, composite))

    return {
        **job,
        "composite_score": composite,
        "pillar_scores": {
            "skills": int(round(skill_score)),
            "location": int(round(loc_score)),
            "language": int(round(lang_score)),
            "role_fit": int(round(role_score))
        },
        "matched_skills": matched_req + matched_pref,
        "missing_skills": missing_req,
        "why_matched": why_matched,
        "missing_requirements": missing_requirements
    }

def rank_all_jobs():
    profile = load_profile()
    jobs = load_jobs()

    ranked = []
    for j in jobs:
        scored = score_job(j, profile)
        ranked.append(scored)

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    logger.info(f"Successfully scored & ranked {len(ranked)} jobs. Top score: {ranked[0]['composite_score'] if ranked else 0}%")
    return ranked, profile

if __name__ == "__main__":
    ranked, profile = rank_all_jobs()
    print(f"Candidate: {profile.get('candidate_name')} | Ranked {len(ranked)} jobs")
    for r in ranked[:3]:
        print(f"- {r['company']}: {r['title']} ({r['composite_score']}%)")
