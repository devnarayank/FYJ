# Feature Specification: Fix Misleading Search & Outreach Behavior

**Feature Branch**: `001-fix-search-outreach-mismatch`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "The CLI's search command is a placeholder: it queries the resume vector store with a zero vector and prints guidance instead of searching jobs. The full pipeline does search, but its outreach step only saves matched jobs; it does not apply or send outreach. Its summary can still report jobs as 'attempted.' Users may mistake a saved match for an application or outreach attempt."

## User Scenarios & Testing

### User Story 1 - Honest Search Command (Priority: P1)

A user runs `main.py search` expecting it to search for jobs matching their resume. Currently the command performs a dummy vector-store query and prints static guidance text instead of actually searching job boards and returning real matches.

**Why this priority**: The search command is advertised as a core workflow step. Misleading behavior erodes trust and prevents users from discovering jobs without running the full pipeline.

**Independent Test**: Can be fully tested by running `main.py search --resume-path <file> --roles "machine learning engineer"` and verifying real job results are returned with titles, companies, and match scores.

**Acceptance Scenarios**:

1. **Given** a valid resume file and target roles, **When** the user runs the search command, **Then** the system scrapes job boards, computes match scores, and displays a ranked list of matching jobs with titles, companies, locations, and composite scores.

2. **Given** a resume with no matches above threshold, **When** the user runs the search command, **Then** the system reports "No jobs matched above the threshold" with the threshold value and offers guidance to adjust roles or threshold.

3. **Given** invalid input (missing resume, no roles), **When** the user runs the search command, **Then** the system shows a clear usage error and exits with a non-zero code.

---

### User Story 2 - Truthful Outreach Summary (Priority: P1)

A user runs the full pipeline (`main.py run`) and sees the outreach summary. Currently the summary reports "Attempted: N" for matched jobs even though no external outreach (email, application submission) was performed—matched jobs are only persisted to the database.

**Why this priority**: The summary misrepresents what happened. Users cannot distinguish between "jobs I applied to" and "jobs that matched my profile," which is a critical distinction for tracking their actual application activity.

**Independent Test**: Can be fully tested by running the full pipeline with a resume that produces matches, then inspecting the outreach summary to confirm it reports "Sent: 0" and does not label saved matches as "attempted."

**Acceptance Scenarios**:

1. **Given** matched jobs exist after the matching stage, **When** the pipeline completes, **Then** the outreach summary shows "Attempted: 0", "Sent: 0", "Skipped: N" (where N = matched count), "Failed: 0" — clearly indicating no external outreach occurred.

2. **Given** future outreach implementation exists, **When** emails are actually sent, **Then** the summary increments "Sent" for each successful delivery and "Failed" for each error, while "Attempted" reflects the total jobs processed for outreach.

---

### User Story 3 - Consistent Terminology Across Commands (Priority: P2)

A user runs `main.py search`, then `main.py run`, then `main.py dashboard` and sees consistent, accurate labels for each stage's output.

**Why this priority**: Inconsistent terminology (search vs. match vs. attempted vs. saved) confuses users about what each command actually does.

**Independent Test**: Can be fully tested by running all three commands and verifying that "search" returns "matched jobs," "run" reports "matched" and "saved" (not "attempted"), and "dashboard" shows the same saved count.

**Acceptance Scenarios**:

1. **Given** a resume that yields 10 matched jobs, **When** the user runs search, run, and dashboard in sequence, **Then** all three commands reference the same job set using consistent labels: "matched" (search/run), "saved to database" (run persistence step), "total applications: 10" (dashboard).

---

### Edge Cases

- What happens when the search command is run without a prior resume analysis (no vector store entry)? → Should either trigger analysis on-the-fly or guide the user to run `analyze` first.
- How does the system handle rate limits or board failures during search? → Should surface partial results with a warning, not fail silently.
- What if the database is unavailable during the outreach persistence step? → Should report the persistence error clearly and not claim jobs were "attempted."

## Requirements

### Functional Requirements

- **FR-001**: The `search` command MUST search configured job boards (Indeed, LinkedIn, Wellfound, CutShort) for jobs matching the user's resume and target roles, returning real job postings with descriptions.

- **FR-002**: The `search` command MUST compute and display composite match scores (semantic, TF-IDF, skill overlap, LLM verification) for each returned job, ranked descending by score.

- **FR-003**: The `search` command MUST respect the configured `MATCH_THRESHOLD` and only display jobs meeting or exceeding it, or clearly indicate when no jobs meet the threshold.

- **FR-004**: The `search` command MUST NOT perform a dummy vector-store query with a zero vector; it MUST use the actual resume embedding for semantic matching.

- **FR-005**: The outreach persistence step (currently labeled "execute_outreach" in the pipeline) MUST persist matched jobs to the database with status "matched" (or equivalent) and MUST NOT label them as "attempted," "sent," or "applied."

- **FR-006**: The outreach summary MUST report accurate counts: "Attempted" = 0 when no external outreach occurs, "Sent" = 0, "Skipped" = number of matched jobs persisted, "Failed" = 0.

- **FR-007**: The dashboard MUST show the same job count as the persistence step saved, labeled as "Matched" or "Saved to database," not "Applied" or "Attempted."

- **FR-008**: All CLI commands (`search`, `run`, `dashboard`) MUST use consistent terminology: "matched" for jobs passing the composite threshold, "saved" or "persisted" for database records, "sent" only when an email/application is actually transmitted.

- **FR-009**: When no external outreach capability exists, the system MUST NOT imply outreach occurred in any summary, log, or dashboard output.

- **FR-010**: The `run` command's outreach stage MUST be renamed or clearly documented as a "persistence" step until actual outreach is implemented.

### Key Entities

- **MatchedJob**: A job posting that meets the composite match threshold. Attributes: title, company, location, description, source board, job URL, match scores (semantic, TF-IDF, skill, LLM, composite), skill analysis (matched/missing skills), status ("matched").

- **OutreachSummary**: Aggregate counts for an outreach cycle. Attributes: attempted (jobs processed for outreach), sent (emails/applications successfully delivered), skipped (jobs not processed for outreach), failed (delivery errors). When outreach is not implemented: attempted=0, sent=0, skipped=matched_count, failed=0.

- **TrackingDashboard**: Read-only view of application status from the database. Attributes: total_applications (saved matched jobs), status_breakdown (counts by status), recent_activity (latest status changes).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Running `main.py search` with a valid resume returns real job postings from at least 2 configured boards within 60 seconds, with composite scores displayed for each.

- **SC-002**: The `search` command output contains zero instances of placeholder text ("guidance," "zero vector," "dummy," "placeholder") when jobs are found.

- **SC-003**: After running `main.py run`, the outreach summary shows "Attempted: 0" and "Sent: 0" when no external outreach is implemented, with "Skipped" equal to the number of matched jobs.

- **SC-004**: The `dashboard` command shows "Total applications: N" where N equals the number of matched jobs persisted by the most recent `run`, and the status breakdown contains only "matched" (or equivalent) statuses.

- **SC-005**: A user unfamiliar with the codebase can run `search`, `run`, and `dashboard` in sequence and correctly understand which jobs they have merely matched vs. actually applied to (zero applications in current state).

## Assumptions

- The existing provider layer (`tools/job_sources.py`) with four sources (Indeed, LinkedIn, Wellfound, CutShort) is functional and returns real job descriptions.
- The matching pipeline (semantic, TF-IDF, skill overlap, LLM verification) computes meaningful composite scores.
- The database persistence (`models/database.py`) correctly stores and retrieves `MatchedJob` records.
- The constitution (v1.1.0) governs this feature: Principles I (Correctness), IV (Application Quality - future work), V (Agent Architecture), and XII (Production Discipline) apply.
- No external email/SMTP outreach will be implemented in this feature; that remains future work (tracked in constitution's Future Work section).
- Users have a valid resume PDF and have run `analyze` at least once (or `search` can trigger analysis on-demand).