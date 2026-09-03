"""
Skill matching tool — uses curated taxonomy + fuzzy matching.
"""
import re
import logging
from rapidfuzz import fuzz
from config.skill_taxonomy import SKILL_TAXONOMY

logger = logging.getLogger(__name__)


def extract_skills_from_text(text: str, threshold: int = 80) -> dict[str, list[str]]:
    """
    Extract skills from text using taxonomy fuzzy matching.
    Returns a dict of {category: [matched_skills]}.
    """
    text_lower = text.lower()
    found: dict[str, list[str]] = {}

    for category, skills in SKILL_TAXONOMY.items():
        matched = []
        for skill in skills:
            skill_lower = skill.lower()
            # First try exact substring match (fast)
            if skill_lower in text_lower:
                matched.append(skill)
                continue
            # Then try fuzzy match for variations (slower, catch typos)
            # Only for multi-word skills — single words should be exact
            if len(skill_lower.split()) > 1:
                if fuzz.partial_ratio(skill_lower, text_lower) >= threshold:
                    matched.append(skill)
        if matched:
            found[category] = list(set(matched))  # Deduplicate

    return found


def compute_skill_overlap(
    resume_skills: dict[str, list[str]],
    jd_text: str,
    category_weights: dict[str, float] | None = None,
) -> tuple[float, dict]:
    """
    Compute weighted skill overlap between resume skills and a job description.

    Returns:
        (overlap_score, analysis_dict)
        overlap_score: float 0.0 - 1.0
        analysis_dict: {"matched": [...], "missing": [...]}
    """
    # Default weights — technical skills matter more
    if category_weights is None:
        category_weights = {
            "languages": 1.5,
            "frameworks_frontend": 1.3,
            "frameworks_backend": 1.3,
            "databases": 1.2,
            "cloud_platforms": 1.0,
            "devops_infra": 1.0,
            "ci_cd": 0.8,
            "data_ml": 1.2,
            "testing": 0.8,
            "tools": 0.7,
            "security": 0.9,
            "mobile": 1.0,
            "architecture": 1.0,
            "methodologies": 0.6,
            "soft_skills": 0.4,
        }

    # Extract skills from JD
    jd_skills = extract_skills_from_text(jd_text)

    # Flatten resume skills for comparison
    resume_flat: set[str] = set()
    for category_skills in resume_skills.values():
        resume_flat.update(s.lower() for s in category_skills)

    jd_flat: set[str] = set()
    for category_skills in jd_skills.values():
        jd_flat.update(s.lower() for s in category_skills)

    if not jd_flat:
        return 0.0, {"matched": [], "missing": []}

    # Compute weighted overlap
    matched = []
    missing = []
    weighted_matched = 0.0
    weighted_total = 0.0

    for category, skills in jd_skills.items():
        weight = category_weights.get(category, 1.0)
        for skill in skills:
            weighted_total += weight
            if skill.lower() in resume_flat:
                weighted_matched += weight
                matched.append(skill)
            else:
                # Fuzzy match against resume skills
                best_ratio = 0
                for rs in resume_flat:
                    ratio = fuzz.ratio(skill.lower(), rs)
                    best_ratio = max(best_ratio, ratio)
                if best_ratio >= 85:
                    weighted_matched += weight * 0.8  # Slight penalty for fuzzy match
                    matched.append(skill)
                else:
                    missing.append(skill)

    if weighted_total == 0:
        return 0.0, {"matched": matched, "missing": missing}

    score = weighted_matched / weighted_total
    return min(score, 1.0), {"matched": matched, "missing": missing}


def get_flat_skills(skills_dict: dict[str, list[str]]) -> list[str]:
    """Flatten a categorized skills dict into a single list."""
    flat = []
    for category_skills in skills_dict.values():
        flat.extend(category_skills)
    return list(set(flat))
