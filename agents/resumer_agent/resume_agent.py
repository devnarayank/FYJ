"""
Agent 1: Resume Analysis Agent
Parses resume, extracts structured profile using Groq LLM, and generates embeddings.
"""
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config.prompts import RESUME_ANALYSIS_PROMPT
from config.settings import AppSettings
from tools.resume_parser import parse_resume
from tools.embedding_tools import embed_text, store_embedding
from tools.skill_matcher import extract_skills_from_text
from tools.validators import parse_json_safely
from models.schemas import CandidateProfile, Skills, WorkExperience, Education

logger = logging.getLogger(__name__)


def analyze_resume(resume_path: str, settings: AppSettings) -> dict:
    """
    Full resume analysis pipeline:
    1. Parse PDF/DOCX → raw text
    2. LLM structured extraction via Groq
    3. Augment with taxonomy-based skill matching
    4. Generate & store embeddings in ChromaDB
    """
    logger.info(f"━━━ Agent 1: Resume Analysis ━━━")

    # Step 1: Parse resume file
    logger.info(f"Parsing resume: {resume_path}")
    resume_text = parse_resume(resume_path)
    if not resume_text or len(resume_text) < 50:
        raise ValueError("Resume text too short or empty. Check the file.")
    logger.info(f"Extracted {len(resume_text)} chars from resume")

    # Step 2: LLM structured extraction via Groq
    logger.info("Sending to Groq for structured extraction...")
    profile = _llm_extract_profile(resume_text, settings)
    logger.info(f"LLM extracted: {profile.name}, {len(profile.skills.all_skills)} skills")

    # Step 3: Augment with taxonomy-based skill matching
    taxonomy_skills = extract_skills_from_text(resume_text)
    profile = _merge_taxonomy_skills(profile, taxonomy_skills)
    logger.info(f"After taxonomy augmentation: {len(profile.skills.all_skills)} total skills")

    # Step 4: Generate and store embeddings
    logger.info("Generating embeddings...")
    resume_embedding = embed_text(resume_text)
    store_embedding(
        doc_id="resume_full",
        text=resume_text,
        embedding=resume_embedding,
        metadata={"type": "full_resume", "name": profile.name},
        persist_dir=settings.chroma_path,
    )

    # Also embed the skills section separately for better matching
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

    logger.info(f"✓ Resume analysis complete: {profile.name}")
    return {
        "resume_text": resume_text,
        "candidate_profile": profile,
        "current_phase": "matching",
    }


def _llm_extract_profile(resume_text: str, settings: AppSettings) -> CandidateProfile:
    """Use Groq LLM to extract structured profile from resume text."""
    llm = ChatGroq(
        model=settings.groq.model,
        api_key=settings.groq.api_key,
        temperature=0.1,
        max_tokens=4000,
    )

    messages = [
        SystemMessage(content=RESUME_ANALYSIS_PROMPT),
        HumanMessage(content=f"Here is the resume text to analyze:\n\n{resume_text[:6000]}"),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Parse JSON safely from LLM response
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
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}. Using defaults.")
        data = default_profile

    # Build profile from parsed data
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

    work_exp = []
    for exp in data.get("work_experience", []):
        work_exp.append(WorkExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            start_date=exp.get("start_date", ""),
            end_date=exp.get("end_date", ""),
            key_achievements=exp.get("key_achievements", []),
            technologies_used=exp.get("technologies_used", []),
        ))

    education = []
    for edu in data.get("education", []):
        education.append(Education(
            institution=edu.get("institution", ""),
            degree=edu.get("degree", ""),
            field=edu.get("field", ""),
            graduation_year=edu.get("graduation_year"),
        ))

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


def _merge_taxonomy_skills(
    profile: CandidateProfile,
    taxonomy_skills: dict[str, list[str]],
) -> CandidateProfile:
    """Merge taxonomy-detected skills into the LLM-extracted profile."""
    # Map taxonomy categories to profile skill categories
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
        existing = set(s.lower() for s in getattr(profile.skills, profile_field, []))
        new_skills = [s for s in skills if s.lower() not in existing]
        if new_skills:
            current = getattr(profile.skills, profile_field)
            setattr(profile.skills, profile_field, current + new_skills)

    return profile
