---

description: "Task list template for feature implementation"
---

# Tasks: Fix Matching Calibration

**Input**: Design documents from `/specs/002-fix-matching-calibration/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/, quickstart.md

**Tests**: Test tasks included per quickstart.md validation scenarios

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (this project uses `agents/`, `config/`, `models/`, `tools/`, `tests/` at root)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project structure and dependencies

- [ ] T001 Verify Python 3.11+ environment and virtual environment active
- [ ] T002 Verify existing dependencies: pydantic, pydantic-settings, sentence-transformers, chromadb, jobspy, rapidfuzz, scikit-learn, click, rich
- [ ] T003 [P] Verify test suite runs: `pytest tests/ -q` passes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema and config extensions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Config & Settings Extensions

- [ ] T004 [P] Add 11 validated weight/threshold fields to `AppSettings` in `config/settings.py` with Field(ge=0.0, le=1.0) and aliases:
  - `semantic_weight` (SEMANTIC_WEIGHT, default=0.35)
  - `tfidf_weight` (TFIDF_WEIGHT, default=0.30)
  - `skill_overlap_weight` (SKILL_OVERLAP_WEIGHT, default=0.35)
  - `final_semantic_weight` (FINAL_SEMANTIC_WEIGHT, default=0.30)
  - `final_tfidf_weight` (FINAL_TFIDF_WEIGHT, default=0.25)
  - `final_skill_weight` (FINAL_SKILL_WEIGHT, default=0.25)
  - `llm_verification_weight` (LLM_VERIFICATION_WEIGHT, default=0.20)
  - `semantic_pre_filter_threshold` (SEMANTIC_PRE_FILTER_THRESHOLD, default=0.30)
  - `match_threshold` (MATCH_THRESHOLD, default=0.50)
  - `score_band_strong_min` (SCORE_BAND_STRONG_MIN, default=0.70)
  - `score_band_moderate_min` (SCORE_BAND_MODERATE_MIN, default=0.50)

- [ ] T005 Implement `validate_critical_settings()` in `config/settings.py`:
  - Stage 1 sum = 1.0 ± 0.001 (semantic_weight + tfidf_weight + skill_overlap_weight)
  - Stage 2 sum = 1.0 ± 0.001 (final_semantic_weight + final_tfidf_weight + final_skill_weight + llm_verification_weight)
  - All weights in [0.0, 1.0]
  - `semantic_pre_filter_threshold` < `match_threshold` (emit `warnings.warn()` if not)
  - Clear error messages with field names on failure
  - Call at AppSettings initialization

- [ ] T006 [P] Deprecate weight/threshold constants in `config/constants.py`:
  - Add deprecation comments pointing to `config.settings.AppSettings`
  - Keep other constants (WORKING_JOBSPY_BOARDS, DIRECT_BOARDS, etc.)

- [ ] T007 [P] Add migration strategy for schema evolution in `models/schemas.py`:
  - Document that new fields have defaults and SQLite schema is flexible (no ALTER TABLE needed)
  - Add `schema_version` field to SearchMetadata for future migration tracking
  - Verify backward compatibility: existing database records work with new schema
  - Add note to constitution Principle IX that migration system is deferred (future work item 5)

### Schema Extensions (models/schemas.py)

- [ ] T008 [P] Add new models to `models/schemas.py`:
  - `ComponentScore` (raw_score: float, weight: float, weighted_contribution: float)
  - `ScoreBreakdown` (stage1_components: dict[str, ComponentScore], stage2_components: dict[str, ComponentScore], stage1_formula: str, stage2_formula: str, interpretation_band: dict[str, float])
  - `WeightConfigSnapshot` (all 7 weights + stage1_sum: float, stage2_sum: float)
  - `ThresholdsSnapshot` (semantic_pre_filter: float, match_threshold: float, score_band_strong_min: float, score_band_moderate_min: float)

- [ ] T009 [P] Extend `MatchScores` in `models/schemas.py` with new fields:
  - `semantic_contribution`, `tfidf_contribution`, `skill_contribution` (Stage 1 weighted)
  - `semantic_contribution_final`, `tfidf_contribution_final`, `skill_contribution_final`, `llm_contribution_final` (Stage 2 weighted)
  - `stage1_formula: str`, `stage2_formula: str`
  - All float fields: Field(ge=0.0, le=1.0)

- [ ] T010 Extend `MatchedJob` in `models/schemas.py` with:
  - `score_interpretation: Literal["strong", "moderate", "weak"]`
  - `score_breakdown: ScoreBreakdown`
  - `weight_config_used: WeightConfigSnapshot`

- [ ] T011 Extend `SearchMetadata` in `models/schemas.py` with:
  - `weight_configuration: WeightConfigSnapshot`
  - `thresholds_used: ThresholdsSnapshot`
  - `schema_version: str` (default "2.0" for this feature)

**Checkpoint**: Foundation ready - all schemas and config validation in place. User stories can now proceed.

---

## Phase 3: User Story 1 - Transparent Score Interpretation (Priority: P1) 🎯 MVP

**Goal**: Each matched job displays a calibrated interpretation label ("Strong"/"Moderate"/"Weak") with explanation, plus full score breakdown in verbose mode.

**Independent Test**: Run pipeline and verify each matched job includes `score_interpretation` label and `score_breakdown` with component scores, weights, and formula (FR-007, FR-008).

### Implementation for User Story 1

- [ ] T012 [P] [US1] Add score interpretation logic in `agents/job_match_agent.py`:
  - Function `get_score_interpretation(composite_score: float, settings: AppSettings) -> Literal["strong","moderate","weak"]`
  - Strong: ≥ `score_band_strong_min` (default 0.70)
  - Moderate: ≥ `score_band_moderate_min` (default 0.50) and < strong_min
  - Weak: < `score_band_moderate_min`

- [ ] T013 [P] [US1] Add score breakdown builder in `agents/job_match_agent.py`:
  - Function `build_score_breakdown(match_scores: MatchScores, settings: AppSettings) -> ScoreBreakdown`
  - Populate stage1_components with semantic, tfidf, skill_overlap (raw, weight, weighted_contribution)
  - Populate stage2_components with semantic, tfidf, skill_overlap, llm_verification
  - Generate stage1_formula string: "w1*X + w2*Y + w3*Z = stage1_score"
  - Generate stage2_formula string: "w1*X + w2*Y + w3*Z + w4*W = composite"
  - Include interpretation_band with strong_min, moderate_min from settings

- [ ] T014 [P] [US1] Create weight config snapshot in `agents/job_match_agent.py`:
  - Function `create_weight_config_snapshot(settings: AppSettings) -> WeightConfigSnapshot`
  - Capture all 7 weights + computed stage1_sum, stage2_sum

- [ ] T015 [P] [US1] Create thresholds snapshot in `agents/job_match_agent.py`:
  - Function `create_thresholds_snapshot(settings: AppSettings) -> ThresholdsSnapshot`
  - Capture semantic_pre_filter_threshold, match_threshold, score_band_strong_min, score_band_moderate_min

- [ ] T016 [US1] Integrate interpretation and breakdown into matching pipeline in `agents/job_match_agent.py`:
  - In match scoring function: compute interpretation, build breakdown, create snapshots
  - Attach to MatchedJob: score_interpretation, score_breakdown, weight_config_used

- [ ] T017 [US1] Update CLI output in `main.py`:
  - Add "Int" column to job table with 🟢/🟡/🔴 emoji and Strong/Moderate/Weak text
  - Verbose mode (-v): print full score breakdown per job (stage1, stage2, formulas, interpretation)
  - Show threshold in header: "Found N matched jobs for X (threshold: Y%)"

**Checkpoint**: User Story 1 complete - jobs show interpretation labels and verbose shows full breakdown.

---

## Phase 4: User Story 2 - No Premature Filtering by Semantic Similarity Alone (Priority: P1)

**Goal**: Lower semantic pre-filter default from 0.50 to 0.30, make it configurable, allow high-skill/keyword jobs to pass through.

**Independent Test**: Job with semantic=0.45, skill=0.80, tfidf=0.65 passes pre-filter and appears in results with composite ≥0.50 (SC-001, FR-001, FR-003, FR-004).

### Implementation for User Story 2

- [ ] T018 [P] [US2] Update semantic pre-filter in `agents/job_match_agent.py`:
  - Replace hardcoded 0.50 threshold with `settings.semantic_pre_filter_threshold` (default 0.30)
  - Use configurable threshold from AppSettings
  - Ensure jobs with semantic ≥ threshold proceed to full Stage 2 scoring

- [ ] T019 [P] [US2] Verify Stage 1 scoring still computes all three dimensions:
  - Semantic, TF-IDF, Skill overlap all calculated before pre-filter decision
  - Stage 1 composite = w1*semantic + w2*tfidf + w3*skill (for logging/audit)
  - Pre-filter only gates whether job proceeds to Stage 2 (LLM verification + final composite)

- [ ] T020 [US2] Update `passed_semantic_gate` counter in SearchMetadata:
  - Count jobs where semantic_similarity ≥ semantic_pre_filter_threshold
  - Include in SearchMetadata for audit trail

**Checkpoint**: User Story 2 complete - low-semantic/high-skill jobs pass pre-filter with default 0.30.

---

## Phase 5: User Story 3 - Aligned LLM Verification Prompt and Pipeline Threshold (Priority: P1)

**Goal**: LLM verification prompt references actual pipeline threshold (e.g., "≥50% composite score"), not ">95%".

**Independent Test**: Inspect `config/prompts.py` and verify NO ">95%" language; prompt references calibrated standard (SC-003, FR-006).

### Implementation for User Story 3

- [ ] T021 [P] [US3] Update `JOB_MATCH_VERIFICATION_PROMPT` in `config/prompts.py`:
  - Remove all ">95%", "95%", "ninety-five percent" language
  - Add template variable `{match_threshold}` for actual threshold
  - Prompt should ask: "Assess if this job is a strong match for the candidate. The pipeline's match threshold is {match_threshold:.0%} composite score. A 'strong match' means the candidate would likely pass initial screening at this threshold."
  - LLM should output score 0.0-1.0 calibrated to this standard

- [ ] T022 [US3] Update LLM verification call in `agents/job_match_agent.py`:
  - Pass `settings.match_threshold` to prompt template
  - Ensure LLM verification score integrates with Stage 2 weights correctly

**Checkpoint**: User Story 3 complete - LLM prompt aligned with pipeline threshold.

---

## Phase 6: User Story 4 - Configurable and Validated Weights/Thresholds (Priority: P2)

**Goal**: All weights/thresholds loadable from `.env` with validation; invalid config produces actionable error at startup.

**Independent Test**: Invalid weights (sum ≠ 1.0) cause clear startup error with field names; valid .env overrides work (SC-002, FR-002, FR-003, FR-004, FR-005, FR-010).

### Implementation for User Story 4

- [ ] T023 [P] [US4] Verify `.env` loading works for all 11 new fields in `config/settings.py`:
  - Test each field loads from environment with correct alias
  - Defaults match current constants when not in .env

- [ ] T024 [P] [US4] Add unit tests for config validation in `tests/test_config_validation.py`:
  - Test valid Stage 1 sum = 1.0 passes
  - Test valid Stage 2 sum = 1.0 passes
  - Test Stage 1 sum ≠ 1.0 raises clear error with field names
  - Test Stage 2 sum ≠ 1.0 raises clear error with field names
  - Test negative weight raises error
  - Test weight > 1.0 raises error
  - Test semantic_pre_filter_threshold ≥ match_threshold emits `warnings.warn()` (captured via pytest.warns)

- [ ] T025 [US4] Integration test: startup with invalid .env fails fast:
  - `SEMANTIC_WEIGHT=0.50 TFIDF_WEIGHT=0.50 SKILL_OVERLAP_WEIGHT=0.10 python main.py ...` → clear error
  - `SEMANTIC_WEIGHT=1.5 python main.py ...` → clear error

**Checkpoint**: User Story 4 complete - all weights/thresholds configurable and validated at startup.

---

## Phase 7: User Story 5 - Score Calibration and Audit Trail (Priority: P2)

**Goal**: Each MatchedJob includes full score breakdown; SearchMetadata includes weight config snapshot for auditability.

**Independent Test**: MatchedJob has score_breakdown with all components, weights, formulas; SearchMetadata has weight_configuration and thresholds_used (SC-005, SC-006, FR-008, FR-009).

### Implementation for User Story 5

- [ ] T026 [P] [US5] Ensure SearchMetadata populated with snapshots in `agents/job_match_agent.py`:
  - After matching complete, create SearchMetadata with weight_configuration and thresholds_used
  - Include total_scraped, passed_semantic_gate, passed_final_filter

- [ ] T027 [P] [US5] Log SearchMetadata at INFO level in `agents/job_match_agent.py`:
  - Structured JSON log with weight_configuration and thresholds_used
  - Available in CLI output and log files

- [ ] T028 [US5] Verify score breakdown formula strings are human-readable:
  - Stage 1: "0.35*0.65 + 0.30*0.70 + 0.35*0.80 = 0.718"
  - Stage 2: "0.30*0.65 + 0.25*0.70 + 0.25*0.80 + 0.20*0.60 = 0.690"
  - Use actual runtime weights from settings

**Checkpoint**: User Story 5 complete - full audit trail in each job and search metadata.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories, regression testing

- [ ] T029 [P] Run full regression test suite: `pytest tests/ -q` - all tests pass
- [ ] T030 [P] Run quickstart.md Test 1: Weight validation at startup (valid + invalid configs)
- [ ] T031 [P] Run quickstart.md Test 2: Pre-filter allows low-semantic/high-skill job
- [ ] T032 [P] Run quickstart.md Test 3: LLM prompt alignment check
- [ ] T033 [P] Run quickstart.md Test 4: Score interpretation labels in output
- [ ] T034 [P] Run quickstart.md Test 5: Full score breakdown in verbose mode
- [ ] T035 [P] Run quickstart.md Test 6: Audit trail in SearchMetadata
- [ ] T036 [P] Run quickstart.md Test 7: Configurable via .env override
- [ ] T037 [P] Run quickstart.md Regression: analyze, dashboard, scraping still work
- [ ] T038 Update `.env.example` with all 11 new variables and comments
- [ ] T039 [P] Configure mypy --strict on core packages (agents/, models/, tools/, graph/)
- [ ] T040 [P] Configure ruff for linting and formatting
- [ ] T041 [P] Configure CI pipeline (GitHub Actions) to enforce mypy, ruff, tests
- [ ] T042 Code cleanup: remove any dead code, unused imports

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed) after Phase 2
  - Or sequentially in priority order: US1 → US2 → US3 → US4 → US5
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Independent
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Independent

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

---

## Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **all 5 user stories can start in parallel** (if team capacity allows)
- All test tasks for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all US1 model/schema tasks together:
Task: "T012 [P] [US1] Add score interpretation logic in agents/job_match_agent.py"
Task: "T013 [P] [US1] Add score breakdown builder in agents/job_match_agent.py"
Task: "T014 [P] [US1] Create weight config snapshot in agents/job_match_agent.py"
Task: "T015 [P] [US1] Create thresholds snapshot in agents/job_match_agent.py"

# Launch US1 tests (if written first):
Task: "Test score interpretation function"
Task: "Test score breakdown builder"
```

---

## Parallel Example: Foundational Phase

```bash
# All these can run simultaneously:
Task: "T004 [P] Add 11 validated fields to AppSettings in config/settings.py"
Task: "T006 [P] Deprecate constants in config/constants.py"
Task: "T007 [P] Add migration strategy for schema evolution in models/schemas.py"
Task: "T008 [P] Add new models to models/schemas.py"
Task: "T009 [P] Extend MatchScores in models/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only - All P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Transparent Score Interpretation)
4. Complete Phase 4: User Story 2 (No Premature Filtering)
5. Complete Phase 5: User Story 3 (Aligned LLM Prompt)
6. **STOP and VALIDATE**: Run quickstart.md Tests 1-6
7. Deploy/demo if ready

### Incremental Delivery (Add P2 Stories)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
   - Developer E: User Story 5
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD for test tasks)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are absolute from repository root (F:\fyj)