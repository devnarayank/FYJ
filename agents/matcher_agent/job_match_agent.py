"""
Agent 2: Job Search & Matching Agent
Scrapes job boards, applies 3-stage hybrid matching, and stores results.
"""
import gc
import json
import logging
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config.prompts import JOB_MATCH_VERIFICATION_PROMPT, SEARCH_QUERY_GENERATION_PROMPT
from config.settings import AppSettings
from config.constants import (
    DEFAULT_BOARDS,
    FINAL_SEMANTIC_WEIGHT, FINAL_TFIDF_WEIGHT, FINAL_SKILL_WEIGHT,
    LLM_VERIFICATION_WEIGHT,
    SEMANTIC_WEIGHT, TFIDF_WEIGHT, SKILL_OVERLAP_WEIGHT,
    SEMANTIC_PRE_FILTER_THRESHOLD, GROQ_DELAY_SECONDS,
)
from tools.job_scraper import scrape_jobs_multi_query
from tools.embedding_tools import embed_text, embed_batch, cosine_similarity_batch
from tools.tfidf_matcher import compute_tfidf_batch
from tools.skill_matcher import extract_skills_from_text, compute_skill_overlap
from tools.validators import parse_json_safely
from models.schemas import (
    CandidateProfile, MatchedJob, MatchScores, SkillAnalysis, SearchMetadata,
)

logger = logging.getLogger(__name__)


def search_and_match_jobs(
    candidate_profile: CandidateProfile,
    resume_text: str,
    settings: AppSettings,
    target_locations: list[str] | None = None,
    target_roles: list[str] | None = None,
    boards: list[str] | None = None,
) -> dict:
    """
    Full job search & matching pipeline:
    1. Generate search queries from profile (LLM)
    2. Scrape jobs from multiple boards
    3. 3-Stage hybrid matching:
       Stage 1: Semantic similarity (MiniLM) — broad filter
       Stage 2: TF-IDF keyword matching — keyword relevance
       Stage 3: Skill overlap + LLM verification — precision
    4. Composite score > 95% filter
    """
    logger.info(f"━━━ Agent 2: Job Search & Matching ━━━")

    # Step 1: Generate search queries
    search_queries = _generate_search_queries(candidate_profile, settings, target_roles)
    logger.info(f"Generated {len(search_queries)} search queries: {search_queries}")

    # Step 2: Scrape jobs
    location = (target_locations[0] if target_locations else "")
    raw_jobs = scrape_jobs_multi_query(
        queries=search_queries,
        location=location,
        boards=boards or DEFAULT_BOARDS,
        results_per_query=settings.max_results_per_board,
    )
    total_scraped = len(raw_jobs)
    logger.info(f"Scraped {total_scraped} total unique jobs")

    if not raw_jobs:
        return {
            "matched_jobs": [],
            "search_metadata": SearchMetadata(total_scraped=0),
            "search_queries": search_queries,
            "current_phase": "outreach",
        }

    # Step 3: Generate resume embedding
    resume_embedding = embed_text(resume_text)

    # Step 4: 3-Stage matching (memory-efficient batching)
    matched_jobs = _run_matching_pipeline(
        resume_embedding=resume_embedding,
        resume_text=resume_text,
        candidate_profile=candidate_profile,
        raw_jobs=raw_jobs,
        settings=settings,
    )

    metadata = SearchMetadata(
        total_scraped=total_scraped,
        passed_semantic_gate=len([j for j in matched_jobs if j.match_scores.semantic_similarity > 0]),
        passed_final_filter=len(matched_jobs),
    )

    logger.info(f"✓ Matching complete: {len(matched_jobs)} jobs above {settings.match_threshold * 100}%")

    return {
        "matched_jobs": matched_jobs,
        "search_metadata": metadata,
        "search_queries": search_queries,
        "current_phase": "outreach",
    }


def _generate_search_queries(
    profile: CandidateProfile,
    settings: AppSettings,
    target_roles: list[str] | None = None,
) -> list[str]:
    """Use Groq LLM to generate optimal search queries for job boards."""
    role_queries = _normalize_queries(target_roles or [])

    try:
        llm = ChatGroq(
            model=settings.groq.model,
            api_key=settings.groq.api_key,
            temperature=0.3,
            max_tokens=500,
        )

        profile_summary = (
            f"Title: {profile.work_experience[0].title if profile.work_experience else 'Software Engineer'}\n"
            f"Skills: {', '.join(profile.top_skills)}\n"
            f"Experience: {profile.total_years_experience} years\n"
            f"Level: {profile.seniority_level}"
        )

        messages = [
            SystemMessage(content=SEARCH_QUERY_GENERATION_PROMPT),
            HumanMessage(content=profile_summary),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Parse JSON safely
        default_queries = [
            profile.work_experience[0].title if profile.work_experience else "software engineer"
        ]
        data = parse_json_safely(raw, {"queries": default_queries})
        return _normalize_queries(role_queries + data.get("queries", default_queries))

    except Exception as e:
        logger.warning(f"Query generation failed: {e}. Using fallback queries.")
        # Fallback: construct from profile
        queries = []
        if profile.work_experience:
            queries.append(profile.work_experience[0].title)
        queries.append(" ".join(profile.top_skills[:3]))
        return _normalize_queries(role_queries + (queries or ["software engineer"]))


def _normalize_queries(queries: list[str]) -> list[str]:
    """Trim, deduplicate, and cap search queries while preserving order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for query in queries:
        clean = " ".join(str(query).split())
        key = clean.lower()
        if clean and key not in seen:
            normalized.append(clean)
            seen.add(key)
    return normalized[:8]


def _run_matching_pipeline(
    resume_embedding: list[float],
    resume_text: str,
    candidate_profile: CandidateProfile,
    raw_jobs: list[dict],
    settings: AppSettings,
) -> list[MatchedJob]:
    """
    Memory-efficient 3-stage matching pipeline.
    Processes jobs in batches to keep RAM usage low.
    """
    batch_size = settings.batch_size
    all_matches: list[MatchedJob] = []

    # Resume skills for overlap computation
    resume_skills_dict = {}
    for field_name in candidate_profile.skills.model_fields:
        skills = getattr(candidate_profile.skills, field_name)
        if skills:
            resume_skills_dict[field_name] = skills

    for i in range(0, len(raw_jobs), batch_size):
        batch = raw_jobs[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} jobs)")

        # ── Stage 1: Semantic similarity (fast broad filter) ──
        descriptions = [j["description"] for j in batch]
        jd_embeddings = embed_batch(descriptions, batch_size=32)
        semantic_scores = cosine_similarity_batch(resume_embedding, jd_embeddings)

        candidates = []
        for j, job in enumerate(batch):
            if semantic_scores[j] >= SEMANTIC_PRE_FILTER_THRESHOLD:
                job["_semantic_score"] = semantic_scores[j]
                candidates.append(job)

        if not candidates:
            del batch, jd_embeddings, semantic_scores
            gc.collect()
            continue

        logger.info(f"  Stage 1 passed: {len(candidates)}/{len(batch)}")

        # ── Stage 2: TF-IDF keyword matching ──
        candidate_descs = [c["description"] for c in candidates]
        tfidf_scores = compute_tfidf_batch(resume_text, candidate_descs)

        for j, cand in enumerate(candidates):
            cand["_tfidf_score"] = tfidf_scores[j]

        # ── Stage 3: Skill overlap scoring ──
        for cand in candidates:
            overlap_score, skill_analysis = compute_skill_overlap(
                resume_skills_dict, cand["description"]
            )
            cand["_skill_score"] = overlap_score
            cand["_skill_analysis"] = skill_analysis

        # ── Composite scoring ──
        for cand in candidates:
            composite = (
                SEMANTIC_WEIGHT * cand["_semantic_score"]
                + TFIDF_WEIGHT * cand["_tfidf_score"]
                + SKILL_OVERLAP_WEIGHT * cand["_skill_score"]
            )
            if composite >= settings.match_threshold:
                # LLM verification for final confirmation
                llm_result = _llm_verify_match(
                    candidate_profile, cand, settings
                )
                # Recompute with LLM score included
                final_composite = (
                    FINAL_SEMANTIC_WEIGHT * cand["_semantic_score"]
                    + FINAL_TFIDF_WEIGHT * cand["_tfidf_score"]
                    + FINAL_SKILL_WEIGHT * cand["_skill_score"]
                    + LLM_VERIFICATION_WEIGHT * llm_result.get("match_score", 0)
                )

                if final_composite >= settings.match_threshold:
                    matched_job = MatchedJob(
                        source_board=cand.get("source", ""),
                        source_url=cand.get("job_url", ""),
                        title=cand.get("title", ""),
                        company=cand.get("company", ""),
                        location=cand.get("location", ""),
                        salary_range=cand.get("salary"),
                        posted_date=cand.get("date_posted"),
                        description=cand["description"],
                        description_snippet=cand["description"][:500],
                        match_scores=MatchScores(
                            semantic_similarity=cand["_semantic_score"],
                            tfidf_similarity=cand["_tfidf_score"],
                            skill_overlap=cand["_skill_score"],
                            llm_verification_score=llm_result.get("match_score", 0),
                            composite_score=final_composite,
                        ),
                        skill_analysis=SkillAnalysis(
                            matched_skills=llm_result.get("matched_skills", cand["_skill_analysis"]["matched"]),
                            missing_skills=llm_result.get("missing_skills", cand["_skill_analysis"]["missing"]),
                            match_reasoning=llm_result.get("match_reasoning", ""),
                        ),
                    )
                    all_matches.append(matched_job)

        # Free batch memory
        del batch, candidates, jd_embeddings, semantic_scores, tfidf_scores
        gc.collect()

    # Sort by composite score descending
    all_matches.sort(key=lambda j: j.match_scores.composite_score, reverse=True)
    return all_matches


def _llm_verify_match(
    profile: CandidateProfile,
    job: dict,
    settings: AppSettings,
) -> dict:
    """Use Groq LLM to verify match quality with skill-gap analysis."""
    try:
        time.sleep(GROQ_DELAY_SECONDS)  # Rate limit
        llm = ChatGroq(
            model=settings.groq.model,
            api_key=settings.groq.api_key,
            temperature=0.1,
            max_tokens=1000,
        )

        prompt = (
            f"CANDIDATE PROFILE:\n"
            f"Current Role: {profile.work_experience[0].title if profile.work_experience else 'N/A'}\n"
            f"Skills: {', '.join(profile.top_skills)}\n"
            f"Experience: {profile.total_years_experience} years\n"
            f"Level: {profile.seniority_level}\n\n"
            f"JOB DESCRIPTION:\n"
            f"Title: {job.get('title', 'N/A')}\n"
            f"Company: {job.get('company', 'N/A')}\n"
            f"Description: {job['description'][:2000]}"
        )

        messages = [
            SystemMessage(content=JOB_MATCH_VERIFICATION_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Parse JSON safely
        default_result = {
            "match_score": 0.7,
            "matched_skills": [],
            "missing_skills": [],
            "match_reasoning": "Could not parse LLM response",
        }
        data = parse_json_safely(raw, default_result)

        return {
            "match_score": data.get("match_score", 0.5),
            "matched_skills": data.get("matched_skills", []),
            "missing_skills": data.get("missing_skills", []),
            "match_reasoning": data.get("match_reasoning", ""),
        }

    except Exception as e:
        logger.warning(f"LLM verification failed: {e}. Using heuristic score.")
        return {
            "match_score": 0.7,
            "matched_skills": [],
            "missing_skills": [],
            "match_reasoning": "LLM verification unavailable",
        }
