# Data Model: Fix Misleading Search & Outreach Behavior

**Feature**: specs/001-fix-search-outreach-mismatch/spec.md  
**Generated**: 2026-11-15

---

## Entities

### MatchedJob
**Source**: `models/schemas.py:118-132` (existing, with one addition)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| job_id | str | Yes | UUID v4, generated on creation |
| source_board | str | Yes | Board name: "indeed", "linkedin", "wellfound", "cutshort" |
| source_url | str | Yes | Direct URL to job posting |
| title | str | Yes | Job title as posted |
| company | str | Yes | Hiring company name |
| location | str | Yes | Job location (city, state, country, or "Remote") |
| salary_range | str | No | Salary range if provided by board |
| posted_date | str | No | ISO date string (YYYY-MM-DD) if available |
| description | str | Yes | **Full job description** (not snippet) — used for matching |
| description_snippet | str | Yes | First 500 chars of description for display |
| match_scores | MatchScores | Yes | Composite and component scores |
| skill_analysis | SkillAnalysis | Yes | Matched/missing skills + reasoning |
| status | str | Yes | **NEW**: Pipeline status — `"matched"` when persisted by outreach node |

**Validation Rules**:
- `description` MUST be non-empty and > 80 chars (enforced by `MIN_DESCRIPTION_CHARS` in provider layer)
- `match_scores.composite_score` MUST be ≥ `MATCH_THRESHOLD` (default 0.50)
- `status` MUST be `"matched"` when inserted by `node_execute_outreach` (FR-005)
- `job_id` is immutable after creation

**Relationships**:
- One `MatchedJob` → One `OutreachSummary` (aggregated)
- Many `MatchedJob` → One `TrackingDashboard` (aggregated)

**State Transitions**:
```
[Created by Agent 2] → status="matched"
       ↓
[Persisted by node_execute_outreach] → status="matched" (unchanged)
       ↓
[Future: Actual outreach sent] → status="sent" (not in this feature)
```

---

### MatchScores
**Source**: `models/schemas.py:104-110` (existing, unchanged)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| semantic_similarity | float | 0.0–1.0 | MiniLM cosine similarity |
| tfidf_similarity | float | 0.0–1.0 | TF-IDF cosine similarity |
| skill_overlap | float | 0.0–1.0 | Weighted skill taxonomy overlap |
| llm_verification_score | float | 0.0–1.0 | LLM verification (0 if skipped) |
| composite_score | float | 0.0–1.0 | Weighted sum per config weights |

**Weights** (from `config/constants.py`):
- Stage 1 (pre-filter): semantic=0.35, tfidf=0.30, skill=0.35
- Stage 2 (final): semantic=0.30, tfidf=0.25, skill=0.25, llm=0.20

---

### SkillAnalysis
**Source**: `models/schemas.py:112-116` (existing, unchanged)

| Field | Type | Description |
|-------|------|-------------|
| matched_skills | list[str] | Skills found in both resume and job description |
| missing_skills | list[str] | Skills in job description not in resume |
| match_reasoning | str | LLM-generated explanation of fit |

---

### OutreachSummary
**Source**: `models/schemas.py:167-172` (existing, semantics updated)

| Field | Type | Current Semantics (Fixed) | Future Semantics (when outreach implemented) |
|-------|------|---------------------------|---------------------------------------------|
| total_attempted | int | **Always 0** (no external outreach) | Jobs processed for outreach |
| successfully_sent | int | **Always 0** | Emails/applications delivered |
| skipped | int | **= matched_jobs_count** | Jobs not processed for outreach |
| failed | int | **Always 0** | Delivery errors |

**Invariant**: `total_attempted == successfully_sent + skipped + failed`

---

### TrackingDashboard
**Source**: `models/schemas.py:199-203` (existing, semantics updated)

| Field | Type | Current Semantics (Fixed) |
|-------|------|---------------------------|
| total_applications | int | **= count of jobs with status="matched" in DB** |
| status_breakdown | dict[str, int] | **{"matched": N}** only |
| recent_activity | list[TrackingEntry] | Persistence events (job_id, "matched", timestamp) |

**TrackingEntry** (`models/schemas.py:188-197`):
| Field | Type | Description |
|-------|------|-------------|
| job_id | str | References MatchedJob |
| company | str | Company name |
| title | str | Job title |
| status | str | "matched" (only value currently) |
| last_action | str | "saved to database" |
| last_action_at | str | ISO timestamp |
| next_action | str | None (no follow-up logic) |
| next_action_at | str | None |

---

### CandidateProfile (referenced, unchanged)
**Source**: `models/schemas.py:68-98`

Used as input to matching. Key fields: `skills`, `work_experience`, `education`, `professional_summary`, `total_years_experience`. The `strongest_achievement` property has a known fallback gap (constitution Principle II) — not addressed in this feature.

---

## Configuration Parameters (affecting data model)

| Parameter | Source | Default | Affects |
|-----------|--------|---------|---------|
| `MATCH_THRESHOLD` | `.env` / `AppSettings` | 0.50 | Minimum composite_score for MatchedJob inclusion |
| `MAX_RESULTS_PER_BOARD` | `.env` / `AppSettings` | 200 | Max jobs scraped per board per query |
| `ENABLED_SOURCES` | `.env` / `AppSettings` | "indeed,linkedin,wellfound,cutshort" | Which JobSource implementations are instantiated |
| `MIN_DESCRIPTION_CHARS` | `.env` / `AppSettings` | 80 | Minimum description length to accept a job |

---

## Database Schema (SQLite, `models/database.py`)

### jobs table
```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    source_board TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_range TEXT,
    posted_date TEXT,
    description TEXT NOT NULL,
    description_snippet TEXT,
    match_scores_json TEXT NOT NULL,  -- JSON-serialized MatchScores
    skill_analysis_json TEXT NOT NULL, -- JSON-serialized SkillAnalysis
    status TEXT NOT NULL DEFAULT 'matched',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Indexes
- `CREATE INDEX idx_jobs_status ON jobs(status);`
- `CREATE INDEX idx_jobs_source ON jobs(source_board);`
- `CREATE INDEX idx_jobs_created ON jobs(created_at);`

---

## Changes in This Feature

| Entity | Change | Reason |
|--------|--------|--------|
| `MatchedJob` | Add `status` field (default "matched") | FR-005: explicit status for dashboard |
| `OutreachSummary` | Semantic fix: `total_attempted=0`, `skipped=N` | FR-006: honest counts when no outreach |
| `TrackingDashboard` | Semantic fix: `total_applications` → matched count, status breakdown only "matched" | FR-007: consistent labels |
| CLI output (search/run/dashboard) | Terminology: "matched"/"saved" not "attempted"/"applied" | FR-008, FR-009 |

No schema migrations needed — `status` field already exists in `MatchedJob` model with default "matched". Database table already has `status` column.