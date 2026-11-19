# Implementation Plan: Fix Misleading Search & Outreach Behavior

**Branch**: `001-fix-search-outreach-mismatch` | **Date**: 2026-11-15 | **Spec**: specs/001-fix-search-outreach-mismatch/spec.md

**Input**: Feature specification from `/specs/001-fix-search-outreach-mismatch/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

The CLI's `search` command currently performs a dummy vector-store query with a zero vector and prints placeholder guidance instead of actually searching job boards and returning real matches. The full pipeline (`run`) does search and match correctly, but its outreach step only persists matched jobs to the database while reporting them as "attempted" in the summary. This feature fixes both issues: (1) implements a real `search` command that scrapes job boards, computes match scores, and displays ranked results; (2) corrects the outreach summary and dashboard to use honest terminology ("matched"/"saved" instead of "attempted"/"sent") when no external outreach occurs.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 
- `langchain-core`, `langgraph` (orchestration)
- `sentence-transformers` (embeddings)
- `chromadb` (vector store)
- `jobspy` (Indeed, LinkedIn scraping)
- `requests`, `beautifulsoup4`, `lxml` (direct HTTP scraping for Wellfound, CutShort)
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
- Search command completes within 60 seconds for typical query (SC-001)
- Pipeline processes ~400 jobs in batches of 50 with LLM verification

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
| I. Correctness | ✅ PASS | Search command will validate inputs, flag errors, fail fast on corruption; partial results allowed with WARNING when boards fail |
| II. Candidate Integrity | ✅ PASS | No fabrication; search uses verified resume data only. Known gap in `strongest_achievement` fallback is documented in constitution and not touched by this feature |
| III. Job Matching | ✅ PASS | Search command reuses existing matching pipeline (semantic, TF-IDF, skill, LLM) — dimensions match constitution |
| IV. Application Quality (Future Work) | ✅ PASS | This feature does NOT implement outreach/cover letters; it only fixes misleading labels |
| V. Agent Architecture | ✅ PASS | Search command uses existing Agent 2 (`job_match_agent.py`); no new agents added |
| VI. Web Research & Job Discovery | ✅ PASS | Uses existing provider layer (`tools/job_sources.py`) with 4 sources; modular `JobSource` interface |
| VII. External Integrations | ✅ PASS | Timeout policy enforced (20s); circuit breaker (`SourceHealth`) handles failures gracefully |
| VIII. Security & Privacy | ✅ PASS | No secrets in logs; `.env` for config; paths validated |
| IX. Data Integrity | ✅ PASS | Uses existing Pydantic schemas (`MatchedJob`, `OutreachSummary`, `TrackingDashboard`); DB persistence unchanged |
| X. Testing | ✅ PASS | Offline tests exist for matching, providers, pipeline; new tests for search command behavior will be added |
| XI. Maintainability | ✅ PASS | Changes confined to CLI command (`main.py`), orchestrator persistence node, and summary rendering |
| XII. Production Discipline | ✅ PASS | Structured logging, observability hooks, graceful degradation already present |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-search-outreach-mismatch/
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
├── job_match_agent.py       # Agent 2: Job Search & Matching (used by search command)
graph/
├── orchestrator.py          # LangGraph pipeline (nodes: analyze, search, execute_outreach, track_followups)
main.py                      # CLI entry point (commands: run, analyze, search, outreach, track, dashboard)
models/
├── database.py              # SQLite persistence (insert_job, get_status_breakdown, get_recent_activity)
├── schemas.py               # Pydantic models (MatchedJob, OutreachSummary, TrackingDashboard, CandidateProfile)
tools/
├── job_sources.py           # Provider layer (JobSource interface, JobSpySource, WellfoundSource, CutShortSource)
├── job_scraper.py           # Public API (scrape_jobs_multi_query, build_sources)
├── embedding_tools.py       # Embeddings (MiniLM)
├── tfidf_matcher.py         # TF-IDF similarity
├── skill_matcher.py         # Skill taxonomy + overlap
config/
├── constants.py             # Weights, thresholds, board lists
├── settings.py              # AppSettings (pydantic-settings)
llm/
├── factory.py               # LLM client builder (Ollama/Groq)
tests/
├── test_job_sources.py      # Provider layer offline tests
├── test_pipeline.py         # Pipeline integration tests
specs/
└── 001-fix-search-outreach-mismatch/  # This feature
```

**Structure Decision**: Single-project CLI structure. All changes are within existing modules — no new directories needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

---

## Phase 0: Research

### Unknowns from Technical Context

All technical choices are already established in the codebase. No NEEDS CLARIFICATION items remain. The feature reuses existing components:

1. **Search command implementation** → Uses `agents/job_match_agent.py:search_and_match_jobs` directly (already scrapes, matches, returns `MatchedJob` list)
2. **Outreach summary fix** → Modifies `graph/orchestrator.py:node_execute_outreach` to return honest counts, and `main.py` dashboard rendering
3. **Terminology consistency** → Updates string literals in `orchestrator.py` and `main.py` dashboard output

### Research Tasks Dispatched

No research agents needed — all dependencies and patterns are internal and documented.

### Consolidated Findings

**Decision**: Reuse `search_and_match_jobs` for the `search` command with minimal adapter code.

**Rationale**: The matching agent already implements the full scrape→match→verify pipeline and returns structured `MatchedJob` objects. The `search` command only needs to call it and format output.

**Alternatives considered**: 
- Duplicate matching logic in a new search-only module → rejected (violates Principle V: cross-agent duplication centralized in shared tools)
- Create a new lightweight search agent → rejected (YAGNI; existing agent is already stateless and reusable)

**Decision**: Fix outreach summary by changing the `node_execute_outreach` return values and dashboard labels.

**Rationale**: The persistence node already saves jobs correctly; only the summary counts and labels are wrong. Minimal change, zero risk to data integrity.

**Alternatives considered**:
- Remove the outreach node entirely → rejected (constitution Scope says 4-stage pipeline; node exists for DB persistence)
- Add a flag to distinguish "real outreach" from "persistence" → rejected (over-engineering; no outreach exists yet)

---

## Phase 1: Design & Contracts

### Data Model

#### MatchedJob (existing, `models/schemas.py:118-132`)
```python
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
    status: str = "matched"  # NEW: explicit status for dashboard
```

**Validation rules from requirements**:
- `status` MUST be `"matched"` when persisted by outreach node (FR-005)
- `match_scores.composite_score` MUST be ≥ `MATCH_THRESHOLD` (FR-003)
- `description` MUST be non-empty (real job description, not snippet)

#### OutreachSummary (existing, `models/schemas.py:167-172`)
```python
class OutreachSummary(BaseModel):
    total_attempted: int = 0
    successfully_sent: int = 0
    skipped: int = 0
    failed: int = 0
```

**Updated semantics (FR-006)**:
- `total_attempted` = 0 when no external outreach (always 0 in current implementation)
- `successfully_sent` = 0 (no emails sent)
- `skipped` = number of matched jobs persisted to DB
- `failed` = 0

#### TrackingDashboard (existing, `models/schemas.py:199-203`)
```python
class TrackingDashboard(BaseModel):
    total_applications: int = 0
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[TrackingEntry] = Field(default_factory=list)
```

**Updated semantics (FR-007)**:
- `total_applications` = count of jobs with status `"matched"` in DB
- `status_breakdown` keys = `{"matched": N}` only (no "applied", "sent", etc.)
- `recent_activity` shows persistence events, not outreach events

### Interface Contracts

#### CLI Command: `search`

**Signature** (from `main.py`):
```python
@click.command()
@click.option("--resume-path", "-r", required=True, type=click.Path(exists=True))
@click.option("--roles", "-R", multiple=True, required=True)
@click.option("--locations", "-L", multiple=True, default=["Remote"])
@click.option("--boards", "-b", multiple=True, default=[])
@click.option("--threshold", "-t", type=float, default=None)
@click.option("--verbose", "-v", is_flag=True)
def search(resume_path, roles, locations, boards, threshold, verbose):
```

**Behavior Contract**:
1. Load resume → extract text → generate embedding (reuse `resume_agent.analyze_resume` or call embedding directly)
2. Call `job_match_agent.search_and_match_jobs` with candidate profile, resume text, settings, roles, locations, boards
3. Filter results by threshold (override if provided)
4. Render ranked table: Title | Company | Location | Source | Composite Score
5. Exit 0 on success, non-zero on validation error

**Error Contract**:
- Missing resume file → "Error: Resume file not found: {path}" (exit 1)
- No roles provided → "Error: At least one --roles required" (exit 2)
- No jobs above threshold → "No jobs matched above threshold {threshold:.0%}. Try adjusting --roles or --threshold." (exit 0)

#### CLI Command: `run` (outreach summary changes only)

**Existing signature unchanged**.

**Output Contract** (updated):
- Outreach summary table shows:
  - Attempted: 0
  - Sent: 0  
  - Skipped: {matched_count}
  - Failed: 0
- No "Attempted: N" where N > 0 when no external outreach occurs

#### CLI Command: `dashboard` (label changes only)

**Existing signature unchanged**.

**Output Contract** (updated):
- Title: "Application Status Dashboard" → "Matched Jobs Dashboard" (or similar)
- Total row: "Total applications: N" → "Total matched jobs saved: N"
- Status breakdown: only "matched" status shown

### Quickstart Validation Guide

#### Prerequisites
- Python 3.11+ with virtual environment activated
- `.env` configured with `OLLAMA_MODEL` or `GROQ_API_KEY`
- Ollama running locally (if using Ollama) or Groq API key valid
- Resume PDF at `data/resumes/AI-EGI_DevNK.pdf` (or any valid resume)

#### Setup
```bash
cd F:\fyj
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt  # if not already installed
```

#### Test 1: Search Command Returns Real Matches
```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
```
**Expected**: Ranked table of jobs with Title, Company, Location, Source, Score. No placeholder text. At least 2 boards represented. Completes within 60s.

#### Test 2: Search Command Respects Threshold
```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --threshold 0.80
```
**Expected**: Fewer or zero results. If zero: "No jobs matched above threshold 80%. Try adjusting --roles or --threshold."

#### Test 3: Run Pipeline Shows Honest Outreach Summary
```bash
python main.py run data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
```
**Expected**: Final outreach summary shows:
```
┌─ Outreach Summary ─┐
│ Attempted: 0       │
│ Sent: 0            │
│ Skipped: N         │  (N = matched jobs count)
│ Failed: 0          │
└────────────────────┘
```
No "Attempted: N" with N > 0.

#### Test 4: Dashboard Shows Consistent Labels
```bash
python main.py dashboard
```
**Expected**: 
- Title references "matched jobs" not "applications"
- Total row: "Total matched jobs saved: N"
- Status breakdown: only "matched" key

#### Test 5: Terminology Consistency Across Commands
Run all three commands in sequence and verify:
- `search` output says "matched jobs" / "matches"
- `run` output says "matched" and "saved to database" / "skipped"
- `dashboard` says "matched jobs saved"
- No command uses "attempted", "applied", or "sent" for the current persistence-only behavior

---

## Post-Phase 1 Constitution Re-Check

All principles still PASS. No new violations introduced. The design:
- Reuses existing validated components (Correctness, Agent Architecture)
- Does not fabricate candidate data (Candidate Integrity)
- Uses existing matching dimensions (Job Matching)
- Does not implement outreach (Application Quality - future work)
- Uses existing provider layer (Web Research)
- Respects timeouts and circuit breakers (External Integrations)
- No new secrets or path handling (Security)
- Uses existing Pydantic schemas (Data Integrity)
- Testable via existing + new CLI tests (Testing)
- Changes confined to CLI/orchestrator (Maintainability)
- Structured logging preserved (Production Discipline)