---
description: "Task list for Fix Misleading Search & Outreach Behavior"
---

# Tasks: Fix Misleading Search & Outreach Behavior

**Input**: Design documents from `/specs/001-fix-search-outreach-mismatch/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/, quickstart.md

**Tests**: Test tasks included for CLI behavior validation (explicitly requested in quickstart.md validation scenarios)

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new infrastructure needed - all dependencies already exist in codebase.

- [X] T001 Verify existing test suite passes before changes in `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and shared components that user stories depend on.

- [X] T002 [P] Add helper function `render_matched_jobs_table(matched_jobs: list[dict]) -> Table` in `main.py` for consistent table rendering across `search`, `run`, and `dashboard` commands (supports FR-008 consistent terminology)
- [X] T003 [P] Add helper function `render_outreach_summary(summary: dict) -> Panel` in `main.py` for consistent outreach summary display (supports FR-006 honest counts)

---

## Phase 3: User Story 1 - Honest Search Command (Priority: P1) 🎯 MVP

**Goal**: Implement a real `search` command that scrapes job boards, computes match scores, and displays ranked results — replacing the current placeholder that queries with a zero vector and prints guidance.

**Independent Test**: Run `python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"` and verify real job results returned with titles, companies, locations, and composite scores (SC-001, SC-002).

### Tests for User Story 1

- [ ] T004 [P] [US1] Add CLI test for `search` command success case in `tests/test_search_command.py` - validates table output with real jobs, ≥2 boards represented, scores as percentages, no placeholder text
- [ ] T005 [P] [US1] Add CLI test for `search` command threshold override in `tests/test_search_command.py` - validates `--threshold` filters results correctly
- [ ] T006 [P] [US1] Add CLI test for `search` command input validation in `tests/test_search_command.py` - validates exit codes 1 (file not found), 2 (missing roles), 3 (LLM unavailable)
- [ ] T007 [P] [US1] Add CLI test for `search` command no-matches case in `tests/test_search_command.py` - validates "No jobs matched above threshold" message with guidance

### Implementation for User Story 1

- [X] T008 [US1] Replace `search` command in `main.py:166-183` with full implementation per `contracts/cli-search.md`:
  - Validate inputs (resume path exists, at least one role provided)
  - Call `agents.resume_agent.analyze_resume` to get `resume_text` and `candidate_profile`
  - Call `agents.job_match_agent.search_and_match_jobs` with profile, resume text, settings, roles, locations, boards
  - Filter results by threshold (override if `--threshold` provided)
  - Render ranked table using `render_matched_jobs_table` helper (T002)
  - Show "Run 'main.py run' to save matches and generate dashboard." guidance line
  - Exit codes: 0 (success), 1 (file error), 2 (missing roles), 3 (LLM/sources unavailable)
- [X] T009 [US1] Update `search` command signature in `main.py:166-167` to match `contracts/cli-search.md`:
  - Add `--resume-path` / `-r` (required, click.Path(exists=True))
  - Add `--roles` / `-R` (multiple=True, required)
  - Add `--locations` / `-L` (multiple=True, default=["Remote"])
  - Add `--boards` / `-b` (multiple=True, default=[])
  - Add `--threshold` / `-t` (float, default=None)
  - Add `--verbose` / `-v` (is_flag=True)
- [X] T010 [US1] Update `search` command docstring in `main.py:168` to reflect actual behavior (no longer requires prior 'analyze')

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — `search` command returns real matches with composite scores, no placeholder text.

---

## Phase 4: User Story 2 - Truthful Outreach Summary (Priority: P1)

**Goal**: Fix the outreach summary in the `run` pipeline to report honest counts: `Attempted: 0`, `Sent: 0`, `Skipped: N` (matched jobs persisted), `Failed: 0` when no external outreach occurs.

**Independent Test**: Run `python main.py run data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer"` and verify outreach summary shows `Attempted: 0`, `Sent: 0`, `Skipped: N`, `Failed: 0` (SC-003).

### Tests for User Story 2

- [ ] T011 [P] [US2] Add CLI test for `run` command outreach summary in `tests/test_run_command.py` - validates summary shows `Attempted: 0`, `Sent: 0`, `Skipped: N`, `Failed: 0` when N matched jobs exist
- [ ] T012 [P] [US2] Add CLI test for `run` command with zero matches in `tests/test_run_command.py` - validates summary shows all zeros

### Implementation for User Story 2

- [X] T013 [US2] Fix `node_execute_outreach` in `graph/orchestrator.py:291` to return honest summary counts:
  - Change `summary = {"total_attempted": len(jobs), "successfully_sent": 0, "skipped": 0, "failed": 0}` 
  - To `summary = {"total_attempted": 0, "successfully_sent": 0, "skipped": len(jobs), "failed": 0}`
  - Per FR-006 and `contracts/cli-run-summary.md`
- [X] T014 [US2] Update `_display_results` in `main.py:275-283` to use `render_outreach_summary` helper (T003) for consistent formatting
- [X] T015 [US2] Verify `OutreachSummary` model in `models/schemas.py:167-172` already supports the corrected semantics (total_attempted=0, skipped=N) - no code change needed, only semantic fix in orchestrator

**Checkpoint**: At this point, User Story 2 should be fully functional — `run` pipeline shows honest outreach summary with `Attempted: 0` and `Skipped: N`.

---

## Phase 5: User Story 3 - Consistent Terminology Across Commands (Priority: P2)

**Goal**: Align all CLI commands (`search`, `run`, `dashboard`) to use consistent terminology: "matched" for jobs passing threshold, "saved" or "persisted" for database records, "sent" only when email/application actually transmitted.

**Independent Test**: Run all three commands in sequence and verify consistent labels: "matched jobs" (search), "matched" and "saved to database" (run), "matched jobs saved" (dashboard) — no "attempted", "applied", or "sent" for current persistence-only behavior (SC-005).

### Tests for User Story 3

- [ ] T016 [P] [US3] Add CLI test for `dashboard` command labels in `tests/test_dashboard_command.py` - validates title "Matched Jobs Dashboard", total row "Total matched jobs saved: N", status breakdown only "matched"
- [ ] T017 [P] [US3] Add CLI test for terminology consistency in `tests/test_terminology_consistency.py` - runs `search`, `run`, `dashboard` and verifies no command uses "attempted" with positive count, "applied", or "sent"

### Implementation for User Story 3

- [X] T018 [US3] Fix `_display_dashboard` in `main.py:300-317` per `contracts/cli-dashboard.md`:
  - Change title from "Application Status Dashboard" → "Matched Jobs Dashboard"
  - Change total row from "Total" → "Total matched jobs saved"
  - Only display statuses that exist in breakdown (currently only "matched")
  - Remove styling logic that assumes "positive"/"negative"/"cold" statuses
- [X] T019 [US3] Fix `_display_db_dashboard` in `main.py:320-344` per `contracts/cli-dashboard.md`:
  - Change title from "Application Status Dashboard" → "Matched Jobs Dashboard"
  - Only display statuses that exist in breakdown
  - Change recent activity "Last Activity" column to show "Saved to DB" action label (use `r.get("last_action", "saved to database")`)
- [X] T020 [US3] Update `_display_results` in `main.py:238-260` Matched Jobs table title per `contracts/cli-run-summary.md`:
  - Title already says "Matched Jobs" — verify consistent with search command
  - Ensure "Apply Link" column label doesn't imply outreach (keep as "Job Link" or "Source URL")
- [X] T021 [US3] Update `dashboard` command docstring in `main.py:204` to reflect "Show matched jobs dashboard" instead of "application status"
- [X] T022 [US3] Update `track` command in `main.py:186-200` to use consistent terminology:
  - Function `_display_dashboard` already used — verify it now shows correct labels after T018/T019
  - Docstring: "Show matched jobs dashboard" instead of "Run one follow-up cycle"

**Checkpoint**: All three commands (`search`, `run`, `dashboard`) use consistent "matched"/"saved" terminology with zero misleading outreach language.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, regression testing, documentation.

- [X] T023 [P] Run full regression test suite: `pytest tests/ -q` - verify all 35 existing tests still pass
- [X] T024 [P] Run quickstart validation scenarios from `specs/001-fix-search-outreach-mismatch/quickstart.md`:
  - Scenario 1: Search returns real matches (SC-001, SC-002)
  - Scenario 2: Search respects threshold override (SC-003)
  - Scenario 3: Search input validation (exit codes)
  - Scenario 4: Run shows honest outreach summary (SC-003, SC-005)
  - Scenario 5: Dashboard shows consistent labels (SC-004, SC-005)
  - Scenario 6: Terminology consistency across commands (SC-005)
- [X] T025 [P] Verify existing `analyze` and `track` commands still work (regression per quickstart.md)
- [X] T026 [P] Update CLI help text in `main.py` module docstring (lines 1-11) to reflect corrected command behaviors:
  - `search`: "Job search & matching (real job board scraping)"
  - `run`: "Full pipeline (resume > match > save matches > dashboard)"
  - `dashboard`: "Show matched jobs dashboard"
  - `track`: "Show matched jobs dashboard (alias for dashboard)"
- [X] T027 [P] Clean up any unused imports in modified files (`main.py`, `graph/orchestrator.py`)
- [X] T028 [P] Verify structured logging still works (no broken log statements in modified code)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - helpers needed by US1/US3
- **User Story 1 (Phase 3)**: Depends on Foundational (T002 for table rendering) - **MVP, can ship independently**
- **User Story 2 (Phase 4)**: Depends on Foundational (T003 for summary rendering) - can run in parallel with US1 after Phase 2
- **User Story 3 (Phase 5)**: Depends on Foundational (T002 for table rendering) - can run in parallel with US1/US2 after Phase 2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1 (different code paths: orchestrator vs main.py search command)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of US1/US2 (different display functions)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Helpers before command implementations
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001)
- All Foundational tasks marked [P] can run in parallel (T002, T003)
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel (T004-T007, T011-T012, T016-T017)
- Different user stories can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T004 Add CLI test for search command success case in tests/test_search_command.py"
Task: "T005 Add CLI test for search command threshold override in tests/test_search_command.py"
Task: "T006 Add CLI test for search command input validation in tests/test_search_command.py"
Task: "T007 Add CLI test for search command no-matches case in tests/test_search_command.py"

# Launch helpers and implementation:
Task: "T002 Add helper function render_matched_jobs_table in main.py"
Task: "T008 Replace search command in main.py:166-183"
Task: "T009 Update search command signature in main.py:166-167"
Task: "T010 Update search command docstring in main.py:168"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002, T003)
3. Complete Phase 3: User Story 1 (T004-T010)
4. **STOP and VALIDATE**: Run quickstart Scenario 1-3 — `search` command works independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP DELIVERED: Real search command**
3. Add User Story 2 → Test independently → Honest outreach summary
4. Add User Story 3 → Test independently → Consistent terminology everywhere
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (search command implementation)
   - Developer B: User Story 2 (orchestrator outreach summary fix)
   - Developer C: User Story 3 (dashboard/terminology fixes)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story independently completable and testable (validated by quickstart.md scenarios)
- Verify tests fail before implementing (TDD for new test files)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Key files to modify**: `main.py` (search, run display, dashboard), `graph/orchestrator.py` (node_execute_outreach), `tests/` (new test files)
- **No schema migrations needed** - `MatchedJob.status` already exists with default "matched"
- **No new dependencies** - all components already exist in codebase