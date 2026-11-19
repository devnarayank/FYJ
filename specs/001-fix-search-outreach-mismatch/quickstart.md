# Quickstart Validation Guide: Fix Misleading Search & Outreach Behavior

**Feature**: specs/001-fix-search-outreach-mismatch/spec.md  
**Generated**: 2026-11-15

---

## Prerequisites

- **Python**: 3.11+ with virtual environment
- **Dependencies**: `pip install -r requirements.txt`
- **Environment**: `.env` configured with one of:
  - `OLLAMA_MODEL` + Ollama running locally (preferred)
  - `GROQ_API_KEY` (fallback)
- **Resume**: Valid PDF at `data/resumes/AI-EGI_DevNK.pdf` (or substitute your own)
- **Database**: SQLite at `data/job_hunt.db` (auto-created)
- **Vector Store**: ChromaDB at `data/chroma_db` (auto-created)

---

## Setup

```bash
cd F:\fyj
.\venv\Scripts\Activate.ps1

# Verify environment
python -c "from config.settings import get_settings; s=get_settings(); print('LLM:', s.model_provider, s.ollama.model if s.model_provider=='ollama' else 'Groq')"
```

Expected output: `LLM: ollama gpt-oss:120b-cloud` (or your configured model)

---

## Validation Scenarios

### Scenario 1: Search Command Returns Real Matches (SC-001, SC-002)

```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
```

**Expected Output**:
```
Found N matched jobs for "machine learning engineer" (threshold: 50%)

┌─ Matched Jobs ──────────────────────────────────────────────┐
│ # │ Title                    │ Company       │ Location   │ Source    │ Score │
├───┼──────────────────────────┼───────────────┼────────────┼───────────┼───────┤
│ 1 │ Machine Learning Engineer│ ...           │ Remote     │ linkedin  │ 62%   │
│ 2 │ Senior ML Engineer       │ ...           │ San Francisco │ wellfound │ 58%   │
│ 3 │ AI/ML Engineer           │ ...           │ Remote     │ cutshort  │ 55%   │
└───┴──────────────────────────┴───────────────┴────────────┴───────────┴───────┘

Run 'main.py run' to save matches and generate dashboard.
```

**Pass Criteria**:
- [ ] Table shows at least 3 jobs (or "No jobs matched" with guidance)
- [ ] At least 2 distinct `Source` values (e.g., linkedin, wellfound, cutshort, indeed)
- [ ] No placeholder text: "guidance", "zero vector", "dummy", "placeholder"
- [ ] Scores shown as percentages (e.g., "62%")
- [ ] Completes within 60 seconds
- [ ] Exit code 0

---

### Scenario 2: Search Command Respects Threshold Override (SC-003)

```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --threshold 0.80
```

**Expected Output** (one of):
- Fewer results than default threshold
- OR: `No jobs matched above threshold 80%. Try adjusting --roles, --locations, or --threshold.`

**Pass Criteria**:
- [ ] Results (if any) have composite score ≥ 80%
- [ ] Threshold value shown in output matches `--threshold` argument
- [ ] Exit code 0

---

### Scenario 3: Search Command Input Validation

```bash
# Missing resume
python main.py search --roles "engineer"
# Expected: exit 1, "Error: At least one --roles required..."

# Missing roles
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf
# Expected: exit 2, "Error: At least one --roles required..."

# Invalid resume path
python main.py search --resume-path nonexistent.pdf --roles "engineer"
# Expected: exit 1, "Error: Resume file not found: nonexistent.pdf"
```

**Pass Criteria**:
- [ ] Correct exit codes (1 for file errors, 2 for missing roles)
- [ ] Clear error messages matching contract

---

### Scenario 4: Run Pipeline Shows Honest Outreach Summary (SC-003, SC-005)

```bash
python main.py run data/resumes/AI-EGI_DevNK.pdf --roles "machine learning engineer" --locations "Remote"
```

**Expected Output** (at end):
```
                       Matched Jobs (10 above threshold)                       
┌┬──────────────────────────┬────────────────┬──────────────┬────┬───────────┐
││ Title                    │ Company        │ Source       │ S… │ Location  │
├┼──────────────────────────┼────────────────┼──────────────┼────┼───────────┤
││ Machine Learning Engineer│ Acme AI        │ linkedin     │ 62%│ Remote    │
└┴──────────────────────────┴────────────────┴──────────────┴────┴───────────┘
┌─ Outreach Summary ─┐
│ Attempted: 0       │
│ Sent: 0            │
│ Skipped: 10        │
│ Failed: 0          │
└────────────────────┘
  Matched Jobs Dashboard  
┌──────────────────────────┬───────┐
│ Status                   │ Count │
├──────────────────────────┼───────┤
│ matched                  │    10 │
└──────────────────────────┴───────┘
```

**Pass Criteria**:
- [ ] Outreach summary shows `Attempted: 0` and `Sent: 0`
- [ ] `Skipped` equals number of matched jobs (10 in example)
- [ ] Dashboard title is "Matched Jobs Dashboard" (not "Application Status Dashboard")
- [ ] Total row says "Total matched jobs saved: 10" (or similar)
- [ ] Status breakdown shows only "matched" row
- [ ] No "applied", "interviewed", "rejected" statuses
- [ ] Exit code 0

---

### Scenario 5: Dashboard Command Shows Consistent Labels (SC-004, SC-005)

```bash
python main.py dashboard
```

**Expected Output**:
```
  Matched Jobs Dashboard  
┌──────────────────────────┬───────┐
│ Status                   │ Count │
├──────────────────────────┼───────┤
│ matched                  │    10 │
└──────────────────────────┴───────┘
```

**Pass Criteria**:
- [ ] Title: "Matched Jobs Dashboard"
- [ ] Total row references "matched jobs saved" (not "applications")
- [ ] Status breakdown only shows "matched"
- [ ] Count matches `Skipped` from previous `run` command
- [ ] Exit code 0

---

### Scenario 6: Terminology Consistency Across Commands (SC-005)

Run all three commands in sequence and verify consistent vocabulary:

| Command | Must Use | Must NOT Use |
|---------|----------|--------------|
| `search` | "matched jobs", "matches", "Score" | "attempted", "applied", "sent", "guidance", "placeholder" |
| `run` | "matched", "saved to database", "skipped" | "attempted" (when >0), "applied", "sent" |
| `dashboard` | "matched jobs saved", "matched" | "applications", "applied", "attempted" |

**Pass Criteria**:
- [ ] No command uses "attempted" with a positive count
- [ ] No command uses "applied" or "sent" for current persistence-only behavior
- [ ] User can correctly infer: 0 applications sent, N matches saved

---

## Regression Checks

### Existing Functionality Unchanged

```bash
# Resume analysis still works
python main.py analyze data/resumes/AI-EGI_DevNK.pdf

# Tracking still works (read-only)
python main.py track
```

**Pass Criteria**:
- [ ] `analyze` completes and stores profile/embedding
- [ ] `track` runs without error (may show empty if no follow-up logic)

### Tests Pass

```bash
pytest tests/ -q
```

**Pass Criteria**:
- [ ] All 35 existing tests pass
- [ ] No new test failures introduced

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| "No LLM provider available" | Ollama not running / Groq key invalid | Start Ollama (`ollama serve`) or set valid `GROQ_API_KEY` |
| "All job sources unavailable" | Network/proxy / all boards blocked | Check internet; set `JOBSPY_PROXIES` in `.env` if needed |
| Zero jobs found | Threshold too high / resume mismatch | Lower `--threshold` or adjust `--roles` |
| Unicode/box-drawing corruption | Terminal encoding | Run `chcp 65001` (Windows) or ensure UTF-8 locale |

---

## Related Artifacts

- **Spec**: `specs/001-fix-search-outreach-mismatch/spec.md`
- **Plan**: `specs/001-fix-search-outreach-mismatch/plan.md`
- **Data Model**: `specs/001-fix-search-outreach-mismatch/data-model.md`
- **Contracts**: `specs/001-fix-search-outreach-mismatch/contracts/`
  - `cli-search.md`
  - `cli-run-summary.md`
  - `cli-dashboard.md`
- **Requirements Checklist**: `specs/001-fix-search-outreach-mismatch/checklists/requirements.md`