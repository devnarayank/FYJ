"""Resume analysis agent using a clean, provider-aware LLM factory."""

import logging
from typing import Any

from config.prompts import RESUME_ANALYSIS_PROMPT
from config.settings import AppSettings
from llm.factory import build_llm
from models.schemas import CandidateProfile, Education, Skills, WorkExperience
from tools.embedding_tools import embed_text, store_embedding
from tools.resume_parser import parse_resume
from tools.skill_matcher import extract_skills_from_text
from tools.validators import parse_json_safely

logger = logging.getLogger(__name__)


def analyze_resume(resume_path: str, settings: AppSettings) -> dict[str, Any]:
    """Parse resumes, extract a structured candidate profile, and index embeddings."""
    logger.info("━━━ Agent 1: Resume Analysis ━━━")

    resume_text = parse_resume(resume_path)
    if not resume_text or len(resume_text) < 50:
        raise ValueError("Resume text too short or empty. Check the file.")

    profile = _llm_extract_profile(resume_text, settings)
    taxonomy_skills = extract_skills_from_text(resume_text)
    profile = _merge_taxonomy_skills(profile, taxonomy_skills)

    resume_embedding = embed_text(resume_text)
    store_embedding(
        doc_id="resume_full",
        text=resume_text,
        embedding=resume_embedding,
        metadata={"type": "full_resume", "name": profile.name},
        persist_dir=settings.chroma_path,
    )

    skills_text = " ".join(profile.skills.all_skills)
    if skills_text:
        skills_embedding = embed_text(skills_text)
        store_embedding(
            doc_id="resume_skills",
            text=skills_text,
            embedding=skills_embedding,
            metadata={"type": "skills_section"},
            persist_dir=settings.chroma_path,
        )

    return {"resume_text": resume_text, "candidate_profile": profile, "current_phase": "matching"}


def _llm_extract_profile(resume_text: str, settings: AppSettings) -> CandidateProfile:
    """Ask the configured LLM to convert the resume into a structured profile."""
    llm = build_llm(settings, task="resume_analysis")

    from langchain_core.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(content=RESUME_ANALYSIS_PROMPT),
        HumanMessage(content=f"Here is the resume text to analyze:\n\n{resume_text[:6000]}"),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    default_profile = {
        "name": "Unknown",
        "email": "unknown@example.com",
        "phone": None,
        "location": None,
        "linkedin_url": None,
        "portfolio_url": None,
        "seniority_level": "mid",
        "professional_summary": "",
        "total_years_experience": 0,
        "skills": {},
        "work_experience": [],
        "education": [],
    }

    try:
        data = parse_json_safely(raw, default_profile)
        if not data or data == default_profile:
            raise ValueError("Could not parse LLM response")
    except Exception as exc:  # pragma: no cover - fallback safe path
        logger.warning("Resume LLM parsing failed: %s. Using fallback defaults.", exc)
        data = default_profile

    skills_data = data.get("skills", {})
    skills = Skills(
        languages=skills_data.get("languages", []),
        frameworks=skills_data.get("frameworks", []),
        databases=skills_data.get("databases", []),
        cloud_devops=skills_data.get("cloud_devops", []),
        tools=skills_data.get("tools", []),
        concepts=skills_data.get("concepts", []),
        soft_skills=skills_data.get("soft_skills", []),
        certifications=skills_data.get("certifications", []),
    )

    work_exp = [
        WorkExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            start_date=exp.get("start_date", ""),
            end_date=exp.get("end_date", ""),
            key_achievements=exp.get("key_achievements", []),
            technologies_used=exp.get("technologies_used", []),
        )
        for exp in data.get("work_experience", [])
    ]

    education = [
        Education(
            institution=edu.get("institution", ""),
            degree=edu.get("degree", ""),
            field=edu.get("field", ""),
            graduation_year=edu.get("graduation_year"),
        )
        for edu in data.get("education", [])
    ]

    return CandidateProfile(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone"),
        location=data.get("location"),
        linkedin_url=data.get("linkedin_url"),
        portfolio_url=data.get("portfolio_url"),
        seniority_level=data.get("seniority_level", "mid"),
        professional_summary=data.get("professional_summary", ""),
        total_years_experience=data.get("total_years_experience", 0),
        skills=skills,
        work_experience=work_exp,
        education=education,
    )


def _merge_taxonomy_skills(profile: CandidateProfile, taxonomy_skills: dict[str, list[str]]) -> CandidateProfile:
    """Merge taxonomy-detected skills into the LLM-extracted profile."""
    category_mapping = {
        "languages": "languages",
        "frameworks_frontend": "frameworks",
        "frameworks_backend": "frameworks",
        "databases": "databases",
        "cloud_platforms": "cloud_devops",
        "devops_infra": "cloud_devops",
        "ci_cd": "tools",
        "data_ml": "tools",
        "testing": "tools",
        "tools": "tools",
        "security": "concepts",
        "mobile": "frameworks",
        "architecture": "concepts",
        "methodologies": "concepts",
        "soft_skills": "soft_skills",
    }

    for tax_category, skills in taxonomy_skills.items():
        profile_field = category_mapping.get(tax_category, "tools")
        existing = {s.lower() for s in getattr(profile.skills, profile_field, [])}
        new_skills = [s for s in skills if s.lower() not in existing]
        if new_skills:
            current = list(getattr(profile.skills, profile_field, []))
            setattr(profile.skills, profile_field, current + new_skills)

    return profile
