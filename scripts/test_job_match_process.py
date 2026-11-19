"""
Smoke-test the resume-to-job-match process without live scraping or LLM calls.

Run from the project root:
    python scripts/test_job_match_process.py

This verifies:
    - target roles are passed into the job-match search query step
    - the expanded default platform list is used
    - only jobs above the 95% threshold are returned
    - matched jobs include apply/source URLs
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _install_import_stubs() -> None:
    """Stub optional external modules so this smoke test stays offline."""
    langchain_groq = types.ModuleType("langchain_groq")

    class ChatGroq:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, messages):
            return SimpleNamespace(content='{"queries": ["python ai engineer"]}')

    langchain_groq.ChatGroq = ChatGroq
    sys.modules.setdefault("langchain_groq", langchain_groq)

    langchain_core = types.ModuleType("langchain_core")
    messages = types.ModuleType("langchain_core.messages")

    class _Message:
        def __init__(self, content=""):
            self.content = content

    messages.SystemMessage = _Message
    messages.HumanMessage = _Message
    sys.modules.setdefault("langchain_core", langchain_core)
    sys.modules.setdefault("langchain_core.messages", messages)

    settings = types.ModuleType("config.settings")

    class AppSettings:
        pass

    settings.AppSettings = AppSettings
    sys.modules.setdefault("config.settings", settings)

    validators = types.ModuleType("tools.validators")
    validators.parse_json_safely = lambda raw, fallback=None: fallback or {}
    sys.modules.setdefault("tools.validators", validators)

    job_scraper = types.ModuleType("tools.job_scraper")
    job_scraper.scrape_jobs_multi_query = lambda *args, **kwargs: []
    sys.modules.setdefault("tools.job_scraper", job_scraper)

    embedding_tools = types.ModuleType("tools.embedding_tools")
    embedding_tools.embed_text = lambda text: [1.0, 0.0]
    embedding_tools.embed_batch = lambda texts, batch_size=32: [[1.0, 0.0] for _ in texts]
    embedding_tools.cosine_similarity_batch = lambda resume, jobs: [1.0 for _ in jobs]
    sys.modules.setdefault("tools.embedding_tools", embedding_tools)

    tfidf_matcher = types.ModuleType("tools.tfidf_matcher")
    tfidf_matcher.compute_tfidf_batch = lambda resume, descriptions: [1.0 for _ in descriptions]
    sys.modules.setdefault("tools.tfidf_matcher", tfidf_matcher)

    skill_matcher = types.ModuleType("tools.skill_matcher")
    skill_matcher.extract_skills_from_text = lambda text: {}
    skill_matcher.compute_skill_overlap = lambda skills, description: (1.0, {"matched": [], "missing": []})
    sys.modules.setdefault("tools.skill_matcher", skill_matcher)


def main() -> int:
    _install_import_stubs()

    from agents.matcher_agent import job_match_agent
    from config.constants import DEFAULT_BOARDS, NICHE_JOB_PLATFORMS
    from models.schemas import CandidateProfile, Skills, WorkExperience

    calls: dict[str, object] = {}

    profile = CandidateProfile(
        name="Test Candidate",
        email="test@example.com",
        seniority_level="mid",
        total_years_experience=3,
        skills=Skills(
            languages=["Python", "SQL"],
            frameworks=["FastAPI", "LangChain"],
            tools=["Docker", "Git"],
            concepts=["Machine Learning", "APIs"],
        ),
        work_experience=[
            WorkExperience(
                company="Example AI",
                title="AI Engineer",
                start_date="2022-01",
                end_date="Present",
                key_achievements=["Built production AI matching systems"],
                technologies_used=["Python", "FastAPI", "LangChain"],
            )
        ],
    )

    resume_text = (
        "AI Engineer with Python, FastAPI, LangChain, SQL, Docker, "
        "machine learning, APIs, and production matching system experience."
    )

    settings = SimpleNamespace(
        match_threshold=0.95,
        max_results_per_board=10,
        batch_size=10,
        groq=SimpleNamespace(model="test-model", api_key="test-key"),
    )

    def fake_generate_search_queries(candidate_profile, app_settings, target_roles=None):
        calls["target_roles"] = target_roles
        return list(target_roles or []) + ["python ai engineer"]

    def fake_scrape_jobs_multi_query(queries, location="", boards=None, results_per_query=50):
        calls["queries"] = queries
        calls["location"] = location
        calls["boards"] = boards
        calls["results_per_query"] = results_per_query
        return [
            {
                "title": "AI Engineer",
                "company": "Focused AI Startup",
                "location": "Remote",
                "description": (
                    "Python FastAPI LangChain SQL Docker machine learning APIs "
                    "production AI matching systems"
                ),
                "job_url": "https://wellfound.com/jobs/test-ai-engineer",
                "source": "Wellfound",
                "date_posted": "2026-06-16",
                "salary": None,
            },
            {
                "title": "Sales Manager",
                "company": "Unrelated Co",
                "location": "Remote",
                "description": "Sales pipeline account management quotas CRM",
                "job_url": "https://example.com/jobs/sales-manager",
                "source": "Example",
                "date_posted": "2026-06-16",
                "salary": None,
            },
        ]

    def fake_embed_text(text):
        return [1.0, 0.0]

    def fake_embed_batch(texts, batch_size=32):
        return [[1.0, 0.0] for _ in texts]

    def fake_cosine_similarity_batch(resume_embedding, jd_embeddings):
        return [0.99, 0.10]

    def fake_compute_tfidf_batch(resume, descriptions):
        return [0.98 for _ in descriptions]

    def fake_compute_skill_overlap(resume_skills, description):
        return 0.99, {
            "matched": ["Python", "FastAPI", "LangChain", "SQL", "Docker"],
            "missing": [],
        }

    def fake_llm_verify_match(candidate_profile, job, app_settings):
        return {
            "match_score": 0.99,
            "matched_skills": ["Python", "FastAPI", "LangChain", "SQL", "Docker"],
            "missing_skills": [],
            "match_reasoning": "Strong match for the candidate's AI engineering profile.",
        }

    job_match_agent._generate_search_queries = fake_generate_search_queries
    job_match_agent.scrape_jobs_multi_query = fake_scrape_jobs_multi_query
    job_match_agent.embed_text = fake_embed_text
    job_match_agent.embed_batch = fake_embed_batch
    job_match_agent.cosine_similarity_batch = fake_cosine_similarity_batch
    job_match_agent.compute_tfidf_batch = fake_compute_tfidf_batch
    job_match_agent.compute_skill_overlap = fake_compute_skill_overlap
    job_match_agent._llm_verify_match = fake_llm_verify_match

    result = job_match_agent.search_and_match_jobs(
        candidate_profile=profile,
        resume_text=resume_text,
        settings=settings,
        target_locations=[],
        target_roles=["AI Engineer", "ML Engineer"],
        boards=None,
    )

    matched_jobs = result["matched_jobs"]
    assert calls["target_roles"] == ["AI Engineer", "ML Engineer"]
    assert calls["location"] == ""
    assert calls["boards"] == DEFAULT_BOARDS
    assert all(platform in calls["boards"] for platform in NICHE_JOB_PLATFORMS)
    assert result["search_queries"][:2] == ["AI Engineer", "ML Engineer"]
    assert len(matched_jobs) == 1

    job = matched_jobs[0]
    assert job.title == "AI Engineer"
    assert job.source_board == "Wellfound"
    assert job.source_url == "https://wellfound.com/jobs/test-ai-engineer"
    assert job.match_scores.composite_score >= settings.match_threshold

    print("Job-match process smoke test passed")
    print(f"Default platforms checked: {', '.join(DEFAULT_BOARDS)}")
    print(f"Matched: {job.title} at {job.company}")
    print(f"Score: {job.match_scores.composite_score:.1%}")
    print(f"Apply link: {job.source_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
