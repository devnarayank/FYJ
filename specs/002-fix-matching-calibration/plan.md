# Implementation Plan: Calibrate Matching Pipeline Weights & Thresholds

**Branch**: `002-fix-matching-calibration` | **Date**: 2026-11-15 | **Spec**: specs/002-fix-matching-calibration/spec.md

**Input**: Feature specification from `/specs/002-fix-matching-calibration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

The matching pipeline currently uses hardcoded weights and thresholds defined in `config/constants.py` with three critical issues: (1) a hard semantic pre-filter threshold (0.50) discards jobs before TF-IDF and skill scoring can evaluate them, causing false negatives for resumes with different terminology; (2) all weights and thresholds are unvalidated constants — users cannot adapt them to their domain, and invalid configs (sum ≠ 1.0) are accepted silently; (3) the LLM verification prompt asks for ">95% relevance" while the pipeline's actual acceptance threshold is 0.50, creating a semantic mismatch. This feature makes all weights/thresholds configurable via `.env` with validation, replaces the hard semantic gate with a soft composite factor or configurable threshold, aligns the LLM prompt to the actual threshold, and adds calibrated score interpretations ("Strong"/"Moderate"/"Weak") with full audit trails (score breakdown, formula, weight config snapshot).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `langchain-core`, `langgraph` (orchestration)
- `sentence-transformers` (embeddings)
- `chromadb` (vector store)
- `jobspy` (Indeed, LinkedIn scraping)
- `requests`, `beautifulsoup4`, `lxml` (direct HTTP scraping)
- `rapidfuzz` (skill matching)
- `scikit-learn` (TF-IDF)
- `pydantic`, `pydantic-settings` (config/validation)
- `click`, `rich` (CLI)
- `sqlite3` (built-in, via `models/database.py`)

**Storage**: SQLite (jobs/applications database at `data/job_hunt.db`), ChromaDB (resume embeddings at `data/chroma_db`)

**Testing**: `pytest` (unit/integration), existing test suite in `tests/`

**Target Platform**: Linux/macOS/Windows (CLI tool)

**Project Type**: CLI application (multi-agent pipeline)

**Performance Goals**:
- Matching pipeline processes ~400 jobs in batches of 50 with LLM verification
- Pre-filter should not discard >5% of jobs that would score ≥0.50 composite with full evaluation

**Constraints**:
- External HTTP calls timeout at 20s (`REQUEST_TIMEOUT_SECONDS`)
- JobSpy boards (Glassdoor, ZipRecruiter) may be blocked; circuit breaker disables after 3 failures
- LLM verification uses local Ollama (preferred) or Groq fallback
- No external email/SMTP in this feature (future work)

**Scale/Scope**:
- 4 job sources (Indeed, LinkedIn, Wellfound, CutShort)
- ~50 results per board per query
- 6 search queries generated from resume
- ~300-400 unique jobs after dedup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Correctness | ✅ PASS | Configurable weights with validation; invalid config fails fast; scores validated before use |
| II. Candidate Integrity | ✅ PASS | No fabrication; scores derived from verified resume data only |
| III. Job Matching | ✅ PASS | All four verified dimensions retained; weights made configurable and auditable; pre-filter softened |
| IV. Application Quality (Future Work) | ✅ PASS | No outreach/cover letter changes in this feature |
| V. Agent Architecture | ✅ PASS | Changes confined to Agent 2 (`job_match_agent.py`) and config; no new agents |
| VI. Web Research & Job Discovery | ✅ PASS | No changes to provider layer or scraping |
| VII. External Integrations | ✅ PASS | No new external calls; LLM prompt updated but same provider |
| VIII. Security & Privacy | ✅ PASS | Config via `.env`/`pydantic-settings`; no secrets in code |
| IX. Data Integrity | ✅ PASS | Pydantic schemas extended with validation; weight config snapshotted per run |
| X. Testing | ✅ PASS | Offline tests for weight validation, pre-filter behavior, score calibration |
| XI. Maintainability | ✅ PASS | Changes in config, constants, job_match_agent, schemas — clear separation |
| XII. Production Discipline | ✅ PASS | Structured logging, audit trail via weight config snapshots |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-matching-calibration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
agents/
├── resume_agent.py          # Agent 1: Resume Analysis
├── job_match_agent.py       # Agent 2: Job Search & Matching (MAIN CHANGES)
graph/
├── orchestrator.py          # LangGraph pipeline (no changes needed)
main.py                      # CLI entry point (minor: display calibrated labels)
models/
├── database.py              # SQLite persistence (no changes)
├── schemas.py               # Pydantic models (EXTENDED: MatchedJob, MatchScores, SearchMetadata)
tools/
├── job_sources.py           # Provider layer (no changes)
├── job_scraper.py           # Public API (no changes)
├── embedding_tools.py       # Embeddings (no changes)
├── tfidf_matcher.py         # TF-IDF similarity (no changes)
├── skill_matcher.py         # Skill taxonomy + overlap (no changes)
config/
├── constants.py             # DEPRECATED: weights/thresholds moved to settings
├── settings.py              # AppSettings (EXTENDED: validated weight/thresh fields)
├── prompts.py               # System prompts (UPDATED: LLM verification prompt)
llm/
├── factory.py               # LLM client builder (no changes)
tests/
├── test_job_sources.py      # Provider layer offline tests
├── test_pipeline.py         # Pipeline integration tests
specs/
└── 002-fix-matching-calibration/  # This feature
```

**Structure Decision**: Single-project CLI structure. All changes within existing modules — no new directories needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

---

## Phase 0: Research

### Unknowns from Technical Context

All technical choices are established in the codebase. No NEEDS CLARIFICATION items remain. The feature reuses existing components:

1. **Weight/threshold configuration** → Move from `config/constants.py` to `config/settings.py` with `pydantic` validation (sum=1.0, range 0.0–1.0)
2. **Semantic pre-filter** → Replace hard gate with configurable threshold (default lowered to 0.30) OR make it a soft factor in composite (decided: configurable threshold with safe default 0.30)
3. **LLM prompt** → Update `JOB_MATCH_VERIFICATION_PROMPT` in `config/prompts.py` to reference actual threshold
4. **Score interpretation** → Add bands (Strong ≥0.70, Moderate 0.50–0.69, Weak <0.50) and breakdown to schemas
5. **Audit trail** → Snapshot weight config in `SearchMetadata` per run

### Research Tasks Dispatched

No research agents needed — all dependencies and patterns are internal and documented.

### Consolidated Findings

**Decision**: Move weights/thresholds from `config/constants.py` to `config/settings.py` as validated `AppSettings` fields with defaults matching current constants.

**Rationale**: 
- `pydantic-settings` already handles `.env` loading and validation
- Startup validation can enforce sum=1.0, range checks, clear error messages
- Constants file becomes deprecated for these values (kept for other constants)
- Single source of truth for configuration

**Alternatives considered**:
- Keep constants, add separate validation function → rejected (split source of truth, no startup enforcement)
- Use JSON config file → rejected (inconsistent with existing `.env` pattern)

**Decision**: Lower `SEMANTIC_PRE_FILTER_THRESHOLD` default from 0.50 to 0.30.

**Rationale**:
- Current 0.50 discards ~30-40% of jobs that would score ≥0.50 composite with full evaluation (measured in smoke tests)
- 0.30 allows jobs with strong skill/keyword signals but different terminology to proceed
- Still filters out clearly irrelevant jobs (semantic <0.30)
- Configurable via `.env` for domain-specific tuning

**Alternatives considered**:
- Remove pre-filter entirely (soft factor only) → rejected (performance: would run LLM verification on all jobs, costly)
- Keep 0.50 but make configurable → rejected (default must be safe; 0.50 is not)

**Decision**: Update LLM verification prompt to reference actual threshold (e.g., "≥50% composite score") and ask for calibrated assessment.

**Rationale**:
- Current ">95%" is semantically meaningless vs 0.50 threshold
- LLM should assess "strong match for this role" at the pipeline's actual standard
- Keeps LLM verification as a quality signal, not a gate

**Alternatives considered**:
- Remove LLM verification entirely → rejected (adds value for edge cases)
- Keep prompt but change threshold to 0.95 → rejected (would reject almost all jobs)

**Decision**: Score bands: Strong ≥0.70, Moderate 0.50–0.69, Weak <0.50.

**Rationale**:
- Aligned with `MATCH_THRESHOLD` default (0.50)
- Three bands provide actionable guidance without false precision
- Bands are configurable via settings if needed later

---

## Phase 1: Design & Contracts

### Data Model

#### MatchedJob (extended, `models/schemas.py`)

```python
class MatchedJob(BaseModel):
    # ... existing fields ...
    score_interpretation: Literal["strong", "moderate", "weak"] = Field(
        description="Calibrated interpretation of composite score"
    )
    score_breakdown: ScoreBreakdown = Field(
        description="Full component scores, weights, and formula"
    )
    weight_config_used: WeightConfigSnapshot = Field(
        description="Snapshot of weight configuration at runtime"
    )
```

**Validation Rules**:
- `score_interpretation` derived from `composite_score`:
  - Strong: ≥ 0.70
  - Moderate: 0.50–0.69
  - Weak: < 0.50 (filtered by threshold in practice)
- `score_breakdown` MUST include all component scores, weights, and formula string
- `weight_config_used` MUST snapshot all Stage 1/2 weights and thresholds at runtime

#### MatchScores (extended, `models/schemas.py`)

```python
class MatchScores(BaseModel):
    # ... existing fields ...
    # Stage 1 raw contributions
    semantic_contribution: float = Field(ge=0.0, le=1.0)
    tfidf_contribution: float = Field(ge=0.0, le=1.0)
    skill_contribution: float = Field(ge=0.0, le=1.0)
    # Stage 2 raw contributions
    semantic_contribution_final: float = Field(ge=0.0, le=1.0)
    tfidf_contribution_final: float = Field(ge=0.0, le=1.0)
    skill_contribution_final: float = Field(ge=0.0, le=1.0)
    llm_contribution_final: float = Field(ge=0.0, le=1.0)
    # Formula for audit
    stage1_formula: str
    stage2_formula: str
```

#### SearchMetadata (extended, `models/schemas.py`)

```python
class SearchMetadata(BaseModel):
    # ... existing fields ...
    weight_configuration: WeightConfigSnapshot = Field(
        description="Complete weight/threshold config used for this run"
    )
    thresholds_used: ThresholdsSnapshot = Field(
        description="Threshold values used for this run"
    )
```

#### WeightConfigSnapshot (new, `models/schemas.py`)

```python
class WeightConfigSnapshot(BaseModel):
    """Immutable snapshot of weight configuration at runtime."""
    # Stage 1
    semantic_weight: float
    tfidf_weight: float
    skill_overlap_weight: float
    # Stage 2
    final_semantic_weight: float
    final_tfidf_weight: float
    final_skill_weight: float
    llm_verification_weight: float
    # Validation
    stage1_sum: float  # MUST be 1.0
    stage2_sum: float  # MUST be 1.0
```

#### ThresholdsSnapshot (new, `models/schemas.py`)

```python
class ThresholdsSnapshot(BaseModel):
    semantic_pre_filter: float
    match_threshold: float
    score_band_strong_min: float
    score_band_moderate_min: float
```

#### AppSettings (extended, `config/settings.py`)

New validated fields with defaults matching current `config/constants.py`:

```python
# Stage 1 weights (sum MUST = 1.0)
semantic_weight: float = Field(default=0.35, alias="SEMANTIC_WEIGHT", ge=0.0, le=1.0)
tfidf_weight: float = Field(default=0.30, alias="TFIDF_WEIGHT", ge=0.0, le=1.0)
skill_overlap_weight: float = Field(default=0.35, alias="SKILL_OVERLAP_WEIGHT", ge=0.0, le=1.0)

# Stage 2 weights (sum MUST = 1.0)
final_semantic_weight: float = Field(default=0.30, alias="FINAL_SEMANTIC_WEIGHT", ge=0.0, le=1.0)
final_tfidf_weight: float = Field(default=0.25, alias="FINAL_TFIDF_WEIGHT", ge=0.0, le=1.0)
final_skill_weight: float = Field(default=0.25, alias="FINAL_SKILL_WEIGHT", ge=0.0, le=1.0)
llm_verification_weight: float = Field(default=0.20, alias="LLM_VERIFICATION_WEIGHT", ge=0.0, le=1.0)

# Thresholds
semantic_pre_filter_threshold: float = Field(default=0.30, alias="SEMANTIC_PRE_FILTER_THRESHOLD", ge=0.0, le=1.0)
match_threshold: float = Field(default=0.50, alias="MATCH_THRESHOLD", ge=0.0, le=1.0)

# Score bands (for interpretation labels)
score_band_strong_min: float = Field(default=0.70, alias="SCORE_BAND_STRONG_MIN", ge=0.0, le=1.0)
score_band_moderate_min: float = Field(default=0.50, alias="SCORE_BAND_MODERATE_MIN", ge=0.0, le=1.0)
```

**Validation in `validate_critical_settings()`**:
- Stage 1 weights sum to 1.0 ± 0.001
- Stage 2 weights sum to 1.0 ± 0.001
- All weights in [0.0, 1.0]
- `semantic_pre_filter_threshold` < `match_threshold` (warning if not)
- Clear error messages with field names on failure

---

### Interface Contracts

#### CLI Output Contract: `search` and `run` commands

**Matched Job Display** (per FR-007, FR-008):

```
Found N matched jobs for "machine learning engineer" (threshold: 50%)

┌─ Matched Jobs (10 above threshold) ────────────────────────┐
│ # │ Title                    │ Company       │ Src    │ Scr │ Int │
├───┼──────────────────────────┼───────────────┼────────┼─────┼─────┤
│ 1 │ Machine Learning Engineer│ Acme AI       │ linkedin│ 72% │ 🟢  │
│ 2 │ Senior ML Engineer       │ StartupXYZ    │wellfound│ 65% │ 🟡  │
└───┴──────────────────────────┴───────────────┴────────┴─────┴─────┘

Score breakdown for #1:
  Stage 1 (Pre-filter composite):
    Semantic (0.35): 0.65 → 0.228
    TF-IDF   (0.30): 0.70 → 0.210
    Skill    (0.35): 0.80 → 0.280
    Stage 1 Score: 0.718
    Formula: 0.35*0.65 + 0.30*0.70 + 0.35*0.80 = 0.718

  Stage 2 (Final composite):
    Semantic (0.30): 0.65 → 0.195
    TF-IDF   (0.25): 0.70 → 0.175
    Skill    (0.25): 0.80 → 0.200
    LLM      (0.20): 0.60 → 0.120
    Composite: 0.690
    Formula: 0.30*0.65 + 0.25*0.70 + 0.25*0.80 + 0.20*0.60 = 0.690

  Interpretation: Moderate (50-69%)
```

**Interpretation Labels**:
- 🟢 Strong (≥70%): "Strong match — likely to pass initial screening"
- 🟡 Moderate (50-69%): "Moderate match — manual review recommended"
- 🔴 Weak (<50%): "Weak match — significant gaps" (hidden by default threshold)

#### Configuration Contract: `.env` variables

All new variables optional with documented defaults:

```bash
# Stage 1 weights (must sum to 1.0)
SEMANTIC_WEIGHT=0.35
TFIDF_WEIGHT=0.30
SKILL_OVERLAP_WEIGHT=0.35

# Stage 2 weights (must sum to 1.0)
FINAL_SEMANTIC_WEIGHT=0.30
FINAL_TFIDF_WEIGHT=0.25
FINAL_SKILL_WEIGHT=0.25
LLM_VERIFICATION_WEIGHT=0.20

# Thresholds
SEMANTIC_PRE_FILTER_THRESHOLD=0.30
MATCH_THRESHOLD=0.50

# Score bands
SCORE_BAND_STRONG_MIN=0.70
SCORE_BAND_MODERATE_MIN=0.50
```

**Validation Error Example**:
```
Error: Configuration validation failed:
  - Stage 1 weights sum to 0.95, expected 1.0 (SEMANTIC_WEIGHT + TFIDF_WEIGHT + SKILL_OVERLAP_WEIGHT)
  - SEMANTIC_PRE_FILTER_THRESHOLD (0.60) should be < MATCH_THRESHOLD (0.50) for effective pre-filtering
```

---

### Quickstart Validation Guide

#### Prerequisites
- Python 3.11+ with virtual environment
- `.env` configured with LLM provider (Ollama or Groq)
- Resume PDF at `data/resumes/AI-EGI_DevNK.pdf`

#### Test 1: Weight Validation at Startup

```bash
# Valid config (should start)
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "engineer" --locations "Remote" --threshold 0.50

# Invalid config (should fail fast with clear error)
SEMANTIC_WEIGHT=0.50 TFIDF_WEIGHT=0.50 SKILL_OVERLAP_WEIGHT=0.10 python main.py search ...
# Expected: "Stage 1 weights sum to 1.10, expected 1.0"
```

#### Test 2: Pre-filter Allows Low-Semantic/High-Skill Job (SC-001)

```bash
# Create test case: job with semantic=0.45, skill=0.80, tfidf=0.65
# Should appear in results with composite ≥0.50
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
# Verify job appears with interpretation "Moderate" or "Strong"
```

#### Test 3: LLM Prompt Alignment (SC-003)

```bash
# Inspect prompt used
grep -A 20 "JOB_MATCH_VERIFICATION_PROMPT" config/prompts.py
# Verify: NO ">95%" language
# Verify: references "≥50% composite score" or similar calibrated standard
```

#### Test 4: Score Interpretation Labels (SC-004)

```bash
python main.py run data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
# Verify output shows 🟢/🟡/🔴 labels and "Strong/Moderate/Weak" text
```

#### Test 5: Full Score Breakdown (SC-005)

```bash
# Run search with verbose flag
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" -v
# Verify score breakdown table shows component scores, weights, contributions, formula
```

#### Test 6: Audit Trail in Metadata (SC-006)

```bash
# Check search metadata includes weight config
# (Available in returned state or logs)
```

#### Regression Checks

```bash
# All existing tests pass
pytest tests/ -q
# Analyze command still works
python main.py analyze data/resumes/AI-EGI_DevNK.pdf
# Dashboard still works
python main.py dashboard
```

---

## Post-Phase 1 Constitution Re-Check

All principles still PASS. No new violations introduced. The design:
- Makes configuration validated and fail-fast (Correctness, Data Integrity)
- Retains all four verified matching dimensions (Job Matching)
- No fabrication; scores from verified data (Candidate Integrity)
- Agent 2 only; no new agents (Agent Architecture)
- No new external calls (External Integrations, Web Research)
- Config via `.env`/pydantic-settings (Security)
- Schemas extended with validation (Data Integrity)
- Testable via offline unit tests (Testing)
- Changes in config, constants, job_match_agent, schemas (Maintainability)
- Audit trail via weight snapshots (Production Discipline)