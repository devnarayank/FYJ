# Feature Specification: Calibrate Matching Pipeline Weights & Thresholds

**Feature Branch**: `002-fix-matching-calibration`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Matching relies on fixed, unvalidated score weights and thresholds. A hard semantic cutoff runs before keyword and skill scoring, so a good match with different wording can be discarded early. The LLM verification prompt asks about a '>95%' match, while the pipeline's default acceptance threshold is 0.50. (job_match_agent.py, settings.py, prompts.py) Why it matters: A displayed score is not a probability of being shortlisted. The ranking may not reflect how recruiters or screening systems evaluate the role."

---

## User Scenarios & Testing

### User Story 1 - Transparent Score Interpretation (Priority: P1)

A user sees a job with a "62% match score" and wants to understand what that means. Currently the score is an arbitrary weighted sum with no calibrated interpretation.

**Why this priority**: Users cannot make informed decisions about which jobs to pursue if scores lack clear meaning.

**Independent Test**: Run the pipeline and verify each matched job includes a clear label/interpretation of its composite score (e.g., "Strong match — likely to pass initial screening", "Moderate match — review required", "Weak match — significant gaps").

**Acceptance Scenarios**:

1. **Given** a job with composite score ≥ 0.70, **When** results are displayed, **Then** the score is labeled "Strong match" with explanation that it indicates high likelihood of passing recruiter/ATS screening.

2. **Given** a job with composite score 0.50–0.69, **When** results are displayed, **Then** the score is labeled "Moderate match" with explanation that manual review is recommended.

3. **Given** a job with composite score < 0.50, **When** results are displayed, **Then** the job is not shown (filtered by threshold) or shown with "Weak match" label if threshold is lowered.

---

### User Story 2 - No Premature Filtering by Semantic Similarity Alone (Priority: P1)

A candidate's resume uses different terminology than a job description (e.g., "ML engineering" vs "machine learning engineering"), resulting in low semantic similarity but high skill/keyword overlap. Currently such jobs are discarded at the semantic pre-filter stage.

**Why this priority**: Qualified candidates miss relevant opportunities because the pipeline over-relies on embedding similarity for initial filtering.

**Independent Test**: Create a test case where a job description has low semantic similarity (< 0.50) to the resume but high skill overlap (> 0.70) and TF-IDF score (> 0.60). Verify the job passes through to final scoring and can appear in results.

**Acceptance Scenarios**:

1. **Given** a job with semantic score 0.45, skill overlap 0.80, TF-IDF 0.65, **When** the matching pipeline runs, **Then** the job is NOT discarded at the pre-filter stage and proceeds to full scoring.

2. **Given** a job with semantic score 0.30, skill overlap 0.90, TF-IDF 0.70, **When** the matching pipeline runs, **Then** the job is evaluated on all dimensions and its final composite reflects the strong skill/keyword match.

---

### User Story 3 - Aligned LLM Verification Prompt and Pipeline Threshold (Priority: P1)

The LLM verification prompt asks the model to identify ">95% relevance" matches, but the pipeline accepts jobs at 0.50 composite threshold. This inconsistency confuses both the LLM and the user.

**Why this priority**: The LLM is being asked to judge a standard (95%) that the pipeline doesn't enforce, making its verification score unreliable for the actual threshold.

**Independent Test**: Verify the LLM prompt references the actual pipeline threshold (e.g., "≥50% composite score") or the prompt is removed/replaced with a calibrated verification step.

**Acceptance Scenarios**:

1. **Given** the LLM verification runs, **When** it evaluates a job, **Then** the prompt asks the LLM to assess match quality relative to the actual acceptance threshold (0.50), not an arbitrary 95%.

2. **Given** a job passes the composite threshold, **When** LLM verification runs, **Then** the LLM's output is consistent with the pipeline's definition of a "match."

---

### User Story 4 - Configurable and Validated Weights/Thresholds (Priority: P2)

Weights and thresholds are hardcoded constants. Users cannot adjust them for their domain (e.g., academic roles may value publications more than skills; startup roles may value breadth over depth).

**Why this priority**: Different job markets and role types have different signal importance. Hardcoded values prevent adaptation.

**Independent Test**: Verify all weights and thresholds are loaded from settings (with defaults) and validated at startup.

**Acceptance Scenarios**:

1. **Given** a user sets `SEMANTIC_WEIGHT=0.25, SKILL_OVERLAP_WEIGHT=0.45` in `.env`, **When** the pipeline runs, **Then** those weights are used instead of defaults.

2. **Given** a user sets `SEMANTIC_PRE_FILTER_THRESHOLD=0.30` in `.env`, **When** the pipeline runs, **Then** the lower pre-filter allows more jobs to proceed to full scoring.

3. **Given** invalid weights (sum ≠ 1.0, or negative), **When** the application starts, **Then** a clear validation error is shown.

---

### User Story 5 - Score Calibration and Audit Trail (Priority: P2)

The composite score should be traceable and calibrated against real outcomes (e.g., application response rates).

**Why this priority**: Without calibration, scores are arbitrary numbers. Users need to trust that a "70% match" actually correlates with recruiter interest.

**Independent Test**: Verify each MatchedJob includes a breakdown of component scores and the calculation formula, enabling manual verification and future calibration.

**Acceptance Scenarios**:

1. **Given** a matched job result, **When** the user inspects the match details, **Then** they see: semantic=X, tfidf=Y, skill=Z, llm=W, weights used, and the formula: `composite = w1*X + w2*Y + w3*Z + w4*W`.

2. **Given** the pipeline runs, **When** it completes, **Then** the search metadata includes the weight configuration used for that run.

---

## Requirements

### Functional Requirements

- **FR-001**: The semantic pre-filter MUST use a configurable threshold (default 0.30) that allows jobs with strong skill/keyword signals to proceed to full scoring even with lower semantic similarity. Jobs with semantic similarity below this threshold are discarded before Stage 2; jobs at or above proceed to full evaluation on all four dimensions.

- **FR-002**: All Stage 1 weights (semantic, TF-IDF, skill overlap) MUST be configurable via settings with validation that they sum to 1.0.

- **FR-003**: All Stage 2 weights (semantic, TF-IDF, skill overlap, LLM verification) MUST be configurable via settings with validation that they sum to 1.0.

- **FR-004**: The `SEMANTIC_PRE_FILTER_THRESHOLD` MUST be configurable via settings with a default that allows jobs with strong skill/keyword signals to proceed even with lower semantic similarity.

- **FR-005**: The `MATCH_THRESHOLD` (final acceptance threshold) MUST be configurable via settings with validation 0.0–1.0. Currently defined in `config/constants.py` as `MATCH_THRESHOLD=0.50` with no validation; this FR requires moving to `AppSettings` with range validation.

- **FR-006**: The LLM verification prompt MUST NOT reference a ">95%" match standard. It MUST ask the LLM to evaluate match quality relative to the actual pipeline threshold or use a calibrated scale.

- **FR-007**: Each `MatchedJob` MUST include a calibrated interpretation label for its composite score (e.g., "Strong", "Moderate", "Weak") based on defined score bands.

- **FR-008**: Each `MatchedJob` MUST include a full score breakdown showing all component scores, weights used, and the calculation formula.

- **FR-009**: The pipeline MUST log the weight configuration used for each run in search metadata for auditability.

- **FR-010**: Invalid weight configurations (sum ≠ 1.0, negative values, missing required weights) MUST cause a clear startup validation error.

### Key Entities

- **MatchedJob** (extended): Adds `score_interpretation` (enum: "strong"/"moderate"/"weak"), `score_breakdown` (dict with component scores, weights, formula), and `weight_config_used` (snapshot of weights at runtime).

- **MatchScores** (extended): Adds explicit fields for each stage's raw and weighted contributions.

- **SearchMetadata** (extended): Adds `weight_configuration` snapshot and `thresholds_used`.

- **AppSettings** (extended): Adds validated weight fields and threshold fields with defaults matching current constants.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A job with semantic=0.45, skill=0.80, tfidf=0.65 passes the pre-filter and appears in results with a composite score reflecting all dimensions (verified via unit test).

- **SC-002**: All weights and thresholds are loadable from `.env` with validation; invalid config produces actionable error message (verified via unit test).

- **SC-003**: LLM verification prompt no longer contains ">95%" language; instead references the actual acceptance threshold or uses calibrated scale (verified by inspecting prompt).

- **SC-004**: Each matched job displays a score interpretation label ("Strong"/"Moderate"/"Weak") with defined band boundaries (verified via CLI output inspection).

- **SC-005**: Each matched job shows full score breakdown: component scores, weights, and formula (verified via CLI output inspection).

- **SC-006**: Search metadata includes the weight configuration used for the run (verified via JSON output or log inspection).

- **SC-007**: Default weights produce reasonable rankings on a held-out test set of resume-job pairs (qualitative: domain expert review).

---

## Assumptions

- The existing matching pipeline architecture (Stage 1: semantic+TF-IDF+skill pre-filter → Stage 2: composite + LLM verification) is sound and only needs calibration, not restructuring.

- The embedding model (MiniLM) and TF-IDF vectorizer are adequate for semantic and keyword similarity; no model changes required.

- LLM verification adds value but should not be the primary gate; its weight should be modest (current 0.20 is reasonable).

- Score bands for interpretation: Strong ≥ 0.70, Moderate 0.50–0.69, Weak < 0.50 (aligned with current threshold).

- The constitution (v1.1.0) governs this feature: Principles I (Correctness), III (Job Matching), IX (Data Integrity), X (Testing) apply.

- No changes to job scraping, resume parsing, or database layers needed.