"""
Pydantic models for all data structures used across the pipeline.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ──────────────────────────────────────────────
# Agent 1: Resume Analysis
# ──────────────────────────────────────────────

class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str  # YYYY-MM
    end_date: str    # YYYY-MM or "Present"
    key_achievements: list[str] = Field(default_factory=list)
    technologies_used: list[str] = Field(default_factory=list)

    @property
    def duration_months(self) -> int:
        from dateutil.relativedelta import relativedelta
        from dateutil.parser import parse
        try:
            start = parse(self.start_date + "-01")
            end = datetime.now() if self.end_date == "Present" else parse(self.end_date + "-01")
            delta = relativedelta(end, start)
            return delta.years * 12 + delta.months
        except Exception:
            return 0


class Education(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_year: Optional[int] = None


class Skills(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_devops: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    @property
    def all_skills(self) -> list[str]:
        all_s = []
        for field_name in self.model_fields:
            all_s.extend(getattr(self, field_name))
        return all_s

    @property
    def technical_skills(self) -> list[str]:
        return (
            self.languages + self.frameworks + self.databases
            + self.cloud_devops + self.tools + self.concepts
        )


class CandidateProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    seniority_level: str = "mid"
    professional_summary: str = ""
    total_years_experience: float = 0
    skills: Skills = Field(default_factory=Skills)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    @property
    def latest_company(self) -> str:
        if self.work_experience:
            return self.work_experience[0].company
        return "my previous company"

    @property
    def strongest_achievement(self) -> str:
        for exp in self.work_experience:
            if exp.key_achievements:
                return exp.key_achievements[0]
        return "built production-grade software systems"

    @property
    def top_skills(self) -> list[str]:
        return self.skills.technical_skills[:8]


# ──────────────────────────────────────────────
# Agent 2: Job Matching
# ──────────────────────────────────────────────

class MatchScores(BaseModel):
    semantic_similarity: float = 0.0
    tfidf_similarity: float = 0.0
    skill_overlap: float = 0.0
    llm_verification_score: float = 0.0
    composite_score: float = 0.0


class SkillAnalysis(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_reasoning: str = ""


class MatchedJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_board: str = ""
    source_url: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    salary_range: Optional[str] = None
    posted_date: Optional[str] = None
    description: str = ""
    description_snippet: str = ""
    match_scores: MatchScores = Field(default_factory=MatchScores)
    skill_analysis: SkillAnalysis = Field(default_factory=SkillAnalysis)
    status: str = "matched"


class SearchMetadata(BaseModel):
    total_scraped: int = 0
    passed_semantic_gate: int = 0
    passed_final_filter: int = 0
    searched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ──────────────────────────────────────────────
# Agent 3: Outreach
# ──────────────────────────────────────────────

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    source: str = "generic"  # job_posting | career_page | inferred | generic


class EmailSent(BaseModel):
    subject: str = ""
    body: str = ""
    body_preview: str = ""
    sent_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = ""


class OutreachResult(BaseModel):
    job_id: str
    contact: ContactInfo = Field(default_factory=ContactInfo)
    email_sent: Optional[EmailSent] = None
    status: str = "pending"  # sent | skipped_no_contact | failed | rate_limited


class OutreachSummary(BaseModel):
    total_attempted: int = 0
    successfully_sent: int = 0
    skipped: int = 0
    failed: int = 0


# ──────────────────────────────────────────────
# Agent 4: Follow-up & Tracking
# ──────────────────────────────────────────────

class ReplyClassification(BaseModel):
    outreach_id: str
    from_email: str
    subject: str
    body_snippet: str
    classification: str  # positive_response | rejection | auto_reply | info_request | other
    confidence: float = 0.0
    received_at: str = ""


class TrackingEntry(BaseModel):
    job_id: str
    company: str
    title: str
    status: str
    last_action: str
    last_action_at: str
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None


class TrackingDashboard(BaseModel):
    total_applications: int = 0
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[TrackingEntry] = Field(default_factory=list)


# ──────────────────────────────────────────────
# LangGraph Pipeline State
# ──────────────────────────────────────────────

class PipelineState(BaseModel):
    """Full state passed through the LangGraph pipeline."""
    # Input
    resume_path: str = ""
    target_roles: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    boards: list[str] = Field(default_factory=lambda: ["indeed", "linkedin"])

    # Agent outputs
    resume_text: str = ""
    candidate_profile: Optional[CandidateProfile] = None
    search_queries: list[str] = Field(default_factory=list)
    matched_jobs: list[MatchedJob] = Field(default_factory=list)
    search_metadata: Optional[SearchMetadata] = None
    outreach_results: list[OutreachResult] = Field(default_factory=list)
    outreach_summary: Optional[OutreachSummary] = None
    tracking_dashboard: Optional[TrackingDashboard] = None

    # Control
    errors: list[str] = Field(default_factory=list)
    current_phase: str = "init"
