# CLI Command Contract: search

**Feature**: Fix Misleading Search & Outreach Behavior  
**Command**: `main.py search`  
**Status**: New implementation (replaces placeholder)

---

## Signature

```bash
python main.py search [OPTIONS]
```

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--resume-path` | `-r` | `click.Path(exists=True)` | Yes | — | Path to resume PDF |
| `--roles` | `-R` | `multiple=True` (str) | Yes | — | Target role(s) to search for |
| `--locations` | `-L` | `multiple=True` (str) | No | `["Remote"]` | Target location(s) |
| `--boards` | `-b` | `multiple=True` (str) | No | `[]` (uses `ENABLED_SOURCES`) | Job boards to search |
| `--threshold` | `-t` | `float` | No | `None` (uses `MATCH_THRESHOLD`) | Override match threshold |
| `--verbose` | `-v` | `is_flag` | No | `False` | Debug logging |

---

## Behavior Contract

### Preconditions
1. Resume file exists and is readable PDF
2. At least one `--roles` value provided
3. Ollama running (if `MODEL_PROVIDER=ollama`) or `GROQ_API_KEY` valid

### Execution Flow
1. **Validate inputs** → exit with code 1/2 on failure
2. **Analyze resume** (reuse `agents/resume_agent.analyze_resume`):
   - Extract text from PDF
   - Generate `CandidateProfile` via LLM
   - Compute embedding via `sentence-transformers/all-MiniLM-L6-v2`
   - Store embedding in ChromaDB (optional, for future use)
3. **Search & match** (call `agents/job_match_agent.search_and_match_jobs`):
   - Generate search queries from profile + `--roles`
   - Scrape configured boards via provider layer (`tools/job_sources.py`)
   - Run 3-stage hybrid match (semantic, TF-IDF, skill overlap)
   - LLM verification for candidates above pre-filter threshold
   - Return `List[MatchedJob]` with `composite_score ≥ MATCH_THRESHOLD`
4. **Filter by threshold** (override if `--threshold` provided)
5. **Render output** (see Output Contract below)
6. **Exit 0**

### Postconditions
- Real job postings returned (no placeholder/dummy results)
- Each result has non-empty description, composite score, source board
- Results ranked descending by `composite_score`
- At least 2 boards represented if jobs found (per SC-001)

---

## Output Contract

### Success (jobs found)
```
Found N matched jobs for "machine learning engineer" (threshold: 50%)

┌─ Matched Jobs ──────────────────────────────────────────────┐
│ # │ Title                    │ Company       │ Location   │ Source    │ Score │
├───┼──────────────────────────┼───────────────┼────────────┼───────────┼───────┤
│ 1 │ Machine Learning Engineer│ Acme AI       │ Remote     │ linkedin  │ 62%   │
│ 2 │ Senior ML Engineer       │ StartupXYZ    │ San Francisco │ wellfound │ 58%   │
│ 3 │ AI/ML Engineer           │ DataCorp      │ Remote     │ cutshort  │ 55%   │
└───┴──────────────────────────┴───────────────┴────────────┴───────────┴───────┘

Run 'main.py run' to save matches and generate dashboard.
```

**Rules**:
- Table columns: Rank, Title (truncated), Company (truncated), Location, Source, Composite Score (%)
- Score shown as integer percentage (`composite_score * 100`, rounded)
- No placeholder words: "guidance", "zero vector", "dummy", "placeholder"
- Final line guides to `run` command

### Success (no jobs above threshold)
```
No jobs matched above threshold 50% for "machine learning engineer".
Try adjusting --roles, --locations, or --threshold.
```
- Exit code: 0 (not an error)

### Error Cases

| Condition | Exit Code | Output |
|-----------|-----------|--------|
| Resume file not found | 1 | `Error: Resume file not found: {path}` |
| Resume not a valid PDF | 1 | `Error: Invalid PDF file: {path}` |
| No roles provided | 2 | `Error: At least one --roles required. Use -R/--roles to specify target roles.` |
| LLM unavailable | 3 | `Error: No LLM provider available. Configure OLLAMA_MODEL or GROQ_API_KEY.` |
| All job sources failed | 3 | `Error: All job sources unavailable. Check network/proxy settings.` |

---

## Integration Points

- **Calls**: `agents.resume_agent.analyze_resume(resume_path, settings)` → returns `{resume_text, candidate_profile}`
- **Calls**: `agents.job_match_agent.search_and_match_jobs(candidate_profile, resume_text, settings, target_locations, target_roles, boards)` → returns `{matched_jobs, search_metadata, search_queries}`
- **Reads**: `config.settings.AppSettings` for thresholds, sources, timeouts
- **Writes**: ChromaDB (resume embedding) — optional, for future `track` command reuse

---

## Non-Functional Requirements

- **Latency**: ≤ 60 seconds end-to-end (SC-001)
- **Reliability**: Partial results returned with WARNING if some boards fail (circuit breaker)
- **Observability**: Structured logs with correlation ID; stage timings logged