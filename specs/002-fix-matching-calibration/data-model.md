# Data Model: Calibrate Matching Pipeline Weights & Thresholds

**Feature**: specs/002-fix-matching-calibration/spec.md  
**Generated**: 2026-11-15

---

## Entities

### MatchedJob (Extended)
**Source**: `models/schemas.py` (existing, extended)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| job_id | str | Yes | UUID v4 |
| source_board | str | Yes | Board name |
| source_url | str | Yes | Direct URL to job posting |
| title | str | Yes | Job title |
| company | str | Yes | Hiring company |
| location | str | Yes | Job location |
| salary_range | str | No | Salary range |
| posted_date | str | No | ISO date |
| description | str | Yes | Full job description |
| description_snippet | str | Yes | First 500 chars |
| match_scores | MatchScores | Yes | Composite and component scores |
| skill_analysis | SkillAnalysis | Yes | Matched/missing skills |
| status | str | Yes | Pipeline status ("matched") |
| **score_interpretation** | **Literal["strong","moderate","weak"]** | **Yes** | **NEW: Calibrated label** |
| **score_breakdown** | **ScoreBreakdown** | **Yes** | **NEW: Full audit trail** |
| **weight_config_used** | **WeightConfigSnapshot** | **Yes** | **NEW: Runtime config snapshot** |

**Score Interpretation Rules**:
- `strong`: `composite_score ≥ score_band_strong_min` (default 0.70)
- `moderate`: `score_band_moderate_min ≤ composite_score < score_band_strong_min` (default 0.50–0.69)
- `weak`: `composite_score < score_band_moderate_min` (default < 0.50)

**Relationships**:
- One `MatchedJob` → One `ScoreBreakdown`
- One `MatchedJob` → One `WeightConfigSnapshot`

---

### MatchScores (Extended)
**Source**: `models/schemas.py:104-110` (existing, extended)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| semantic_similarity | float | 0.0–1.0 | MiniLM cosine similarity |
| tfidf_similarity | float | 0.0–1.0 | TF-IDF cosine similarity |
| skill_overlap | float | 0.0–1.0 | Weighted skill taxonomy overlap |
| llm_verification_score | float | 0.0–1.0 | LLM verification (0 if skipped) |
| composite_score | float | 0.0–1.0 | Weighted sum per config weights |
| **semantic_contribution** | **float** | **0.0–1.0** | **NEW: Stage 1 weighted contribution** |
| **tfidf_contribution** | **float** | **0.0–1.0** | **NEW: Stage 1 weighted contribution** |
| **skill_contribution** | **float** | **0.0–1.0** | **NEW: Stage 1 weighted contribution** |
| **semantic_contribution_final** | **float** | **0.0–1.0** | **NEW: Stage 2 weighted contribution** |
| **tfidf_contribution_final** | **float** | **0.0–1.0** | **NEW: Stage 2 weighted contribution** |
| **skill_contribution_final** | **float** | **0.0–1.0** | **NEW: Stage 2 weighted contribution** |
| **llm_contribution_final** | **float** | **0.0–1.0** | **NEW: Stage 2 weighted contribution** |
| **stage1_formula** | **str** | — | **NEW: Formula string** |
| **stage2_formula** | **str** | — | **NEW: Formula string** |

**Weights** (from `AppSettings`, defaults from `config/constants.py`):
- Stage 1: semantic=0.35, tfidf=0.30, skill=0.35
- Stage 2: semantic=0.30, tfidf=0.25, skill=0.25, llm=0.20

---

### ScoreBreakdown (New)
**Source**: `models/schemas.py` (new)

| Field | Type | Description |
|-------|------|-------------|
| stage1_components | dict[str, ComponentScore] | Raw + weighted for semantic, tfidf, skill |
| stage2_components | dict[str, ComponentScore] | Raw + weighted for semantic, tfidf, skill, llm |
| stage1_formula | str | Human-readable formula |
| stage2_formula | str | Human-readable formula |
| interpretation_band | dict[str, float] | Band boundaries used |

**ComponentScore**:
```python
class ComponentScore(BaseModel):
    raw_score: float
    weight: float
    weighted_contribution: float
```

---

### WeightConfigSnapshot (New)
**Source**: `models/schemas.py` (new)

| Field | Type | Description |
|-------|------|-------------|
| semantic_weight | float | Stage 1 semantic |
| tfidf_weight | float | Stage 1 TF-IDF |
| skill_overlap_weight | float | Stage 1 skill |
| final_semantic_weight | float | Stage 2 semantic |
| final_tfidf_weight | float | Stage 2 TF-IDF |
| final_skill_weight | float | Stage 2 skill |
| llm_verification_weight | float | Stage 2 LLM |
| stage1_sum | float | MUST be 1.0 |
| stage2_sum | float | MUST be 1.0 |

---

### ThresholdsSnapshot (New)
**Source**: `models/schemas.py` (new)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| semantic_pre_filter | float | 0.30 | Pre-filter threshold |
| match_threshold | float | 0.50 | Final acceptance |
| score_band_strong_min | float | 0.70 | Strong band start |
| score_band_moderate_min | float | 0.50 | Moderate band start |

---

### SearchMetadata (Extended)
**Source**: `models/schemas.py` (existing, extended)

| Field | Type | Description |
|-------|------|-------------|
| total_scraped | int | Total jobs scraped |
| passed_semantic_gate | int | Jobs passing pre-filter |
| passed_final_filter | int | Jobs in final results |
| **weight_configuration** | **WeightConfigSnapshot** | **NEW: Config used** |
| **thresholds_used** | **ThresholdsSnapshot** | **NEW: Thresholds used** |

---

### AppSettings (Extended)
**Source**: `config/settings.py` (existing, extended)

New validated fields (all optional in `.env`, defaults from `config/constants.py`):

| Field | Alias | Default | Validation |
|-------|-------|---------|------------|
| semantic_weight | SEMANTIC_WEIGHT | 0.35 | ≥0, ≤1; Stage 1 sum=1.0 |
| tfidf_weight | TFIDF_WEIGHT | 0.30 | ≥0, ≤1; Stage 1 sum=1.0 |
| skill_overlap_weight | SKILL_OVERLAP_WEIGHT | 0.35 | ≥0, ≤1; Stage 1 sum=1.0 |
| final_semantic_weight | FINAL_SEMANTIC_WEIGHT | 0.30 | ≥0, ≤1; Stage 2 sum=1.0 |
| final_tfidf_weight | FINAL_TFIDF_WEIGHT | 0.25 | ≥0, ≤1; Stage 2 sum=1.0 |
| final_skill_weight | FINAL_SKILL_WEIGHT | 0.25 | ≥0, ≤1; Stage 2 sum=1.0 |
| llm_verification_weight | LLM_VERIFICATION_WEIGHT | 0.20 | ≥0, ≤1; Stage 2 sum=1.0 |
| semantic_pre_filter_threshold | SEMANTIC_PRE_FILTER_THRESHOLD | 0.30 | ≥0, ≤1; < match_threshold (warn) |
| match_threshold | MATCH_THRESHOLD | 0.50 | ≥0, ≤1 |
| score_band_strong_min | SCORE_BAND_STRONG_MIN | 0.70 | ≥0, ≤1 |
| score_band_moderate_min | SCORE_BAND_MODERATE_MIN | 0.50 | ≥0, ≤1 |

**Validation in `validate_critical_settings()`**:
- Stage 1 sum = 1.0 ± 0.001
- Stage 2 sum = 1.0 ± 0.001
- All weights in [0.0, 1.0]
- `semantic_pre_filter_threshold` < `match_threshold` (warning if not)
- Clear error with field names on failure

---

### Configuration Parameters

| Parameter | Source | Default | Affects |
|-----------|--------|---------|---------|
| `SEMANTIC_WEIGHT` | `.env` / `AppSettings` | 0.35 | Stage 1 semantic contribution |
| `TFIDF_WEIGHT` | `.env` / `AppSettings` | 0.30 | Stage 1 TF-IDF contribution |
| `SKILL_OVERLAP_WEIGHT` | `.env` / `AppSettings` | 0.35 | Stage 1 skill contribution |
| `FINAL_SEMANTIC_WEIGHT` | `.env` / `AppSettings` | 0.30 | Stage 2 semantic contribution |
| `FINAL_TFIDF_WEIGHT` | `.env` / `AppSettings` | 0.25 | Stage 2 TF-IDF contribution |
| `FINAL_SKILL_WEIGHT` | `.env` / `AppSettings` | 0.25 | Stage 2 skill contribution |
| `LLM_VERIFICATION_WEIGHT` | `.env` / `AppSettings` | 0.20 | Stage 2 LLM contribution |
| `SEMANTIC_PRE_FILTER_THRESHOLD` | `.env` / `AppSettings` | 0.30 | Pre-filter gate |
| `MATCH_THRESHOLD` | `.env` / `AppSettings` | 0.50 | Final acceptance gate |
| `SCORE_BAND_STRONG_MIN` | `.env` / `AppSettings` | 0.70 | Strong interpretation |
| `SCORE_BAND_MODERATE_MIN` | `.env` / `AppSettings` | 0.50 | Moderate interpretation |

---

## Changes in This Feature

| Entity | Change | Reason |
|--------|--------|--------|
| `MatchedJob` | Add `score_interpretation`, `score_breakdown`, `weight_config_used` | FR-007, FR-008, FR-009 |
| `MatchScores` | Add component contributions, formulas | FR-008 |
| `SearchMetadata` | Add `weight_configuration`, `thresholds_used` | FR-009 |
| `AppSettings` | Add 11 validated weight/threshold fields | FR-002, FR-003, FR-004, FR-005, FR-010 |
| `ScoreBreakdown` | New entity for audit trail | FR-008 |
| `WeightConfigSnapshot` | New entity for audit trail | FR-009 |
| `ThresholdsSnapshot` | New entity for audit trail | FR-009 |
| `JOB_MATCH_VERIFICATION_PROMPT` | Update to reference actual threshold | FR-006 |
| `config/constants.py` | Deprecate weight/threshold constants | Single source of truth |

No database migrations needed — new fields are optional in schema with defaults, populated at runtime.