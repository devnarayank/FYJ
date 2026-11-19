"""
Pydantic models for all data structures used across the pipeline.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# New models for Matching Calibration (Score Breakdown & Audit Trail)
# ──────────────────────────────────────────────

class ComponentScore(BaseModel):
    """Raw score, weight, and weighted contribution for a single matching dimension."""
    raw_score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    weighted_contribution: float = Field(ge=0.0, le=1.0)


class ScoreBreakdown(BaseModel):
    """Full score breakdown showing all component scores, weights, and formulas."""
    stage1_components: dict[str, ComponentScore]
    stage2_components: dict[str, ComponentScore]
    stage1_formula: str
    stage2_formula: str
    interpretation_band: dict[str, float]


class WeightConfigSnapshot(BaseModel):
    """Immutable snapshot of weight configuration at runtime."""
    semantic_weight: float
    tfidf_weight: float
    skill_overlap_weight: float
    final_semantic_weight: float
    final_tfidf_weight: float
    final_skill_weight: float
    llm_verification_weight: float
    stage1_sum: float
    stage2_sum: float


class ThresholdsSnapshot(BaseModel):
    """Immutable snapshot of thresholds at runtime."""
    semantic_pre_filter: float
    match_threshold: float
    score_band_strong_min: float
    score_band_moderate_min: float


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
        from dateutil.parser import parse
        from dateutil.relativedelta import relativedelta
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
    graduation_year: int | None = None


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
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
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
    semantic_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    tfidf_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_verification_score: float = Field(default=0.0, ge=0.0, le=1.0)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Stage 1 weighted contributions
    semantic_contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    tfidf_contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_contribution: float = Field(default=0.0, ge=0.0, le=1.0)

    # Stage 2 weighted contributions
    semantic_contribution_final: float = Field(default=0.0, ge=0.0, le=1.0)
    tfidf_contribution_final: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_contribution_final: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_contribution_final: float = Field(default=0.0, ge=0.0, le=1.0)

    # Formulas for audit trail
    stage1_formula: str = ""
    stage2_formula: str = ""


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
    salary_range: str | None = None
    posted_date: str | None = None
    description: str = ""
    description_snippet: str = ""
    match_scores: MatchScores = Field(default_factory=MatchScores)
    skill_analysis: SkillAnalysis = Field(default_factory=SkillAnalysis)
    status: str = "matched"

    # Calibrated interpretation and audit trail
    score_interpretation: Literal["strong", "moderate", "weak"] = "moderate"
    score_breakdown: ScoreBreakdown | None = None
    weight_config_used: WeightConfigSnapshot | None = None


class SearchMetadata(BaseModel):
    total_scraped: int = 0
    passed_semantic_gate: int = 0
    passed_final_filter: int = 0
    searched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Audit trail: weight configuration and thresholds used for this run
    weight_configuration: WeightConfigSnapshot | None = None
    thresholds_used: ThresholdsSnapshot | None = None
    schema_version: str = "2.0"


# ──────────────────────────────────────────────
# Agent 3: Outreach
# ──────────────────────────────────────────────

class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    title: str | None = None
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
    email_sent: EmailSent | None = None
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
    next_action: str | None = None
    next_action_at: str | None = None


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
    candidate_profile: CandidateProfile | None = None
    search_queries: list[str] = Field(default_factory=list)
    matched_jobs: list[MatchedJob] = Field(default_factory=list)
    search_metadata: SearchMetadata | None = None
    outreach_results: list[OutreachResult] = Field(default_factory=list)
    outreach_summary: OutreachSummary | None = None
    tracking_dashboard: TrackingDashboard | None = None

    # Control
    errors: list[str] = Field(default_factory=list)
    current_phase: str = "init"
