# Quickstart: Validate Matching Pipeline Calibration Fix

**Feature**: specs/002-fix-matching-calibration/spec.md  
**Run after implementing Phase 2 (tasks.md)**

---

## Prerequisites

```bash
# 1. Activate virtual environment
cd F:\fyj
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Ensure .env has LLM provider configured
# OLLAMA_BASE_URL=http://localhost:11434
# GROQ_API_KEY=...

# 3. Resume PDF in place
ls data/resumes/AI-EGI_DevNK.pdf
```

---

## Test 1: Weight Validation at Startup (FR-002, FR-010)

**Valid config** — should start without error:
```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" \
  --threshold 0.50
# Expected: Pipeline runs, outputs matched jobs
```

**Invalid Stage 1 sum** — should fail fast with clear error:
```bash
SEMANTIC_WEIGHT=0.50 TFIDF_WEIGHT=0.50 SKILL_OVERLAP_WEIGHT=0.10 \
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "engineer" --locations "Remote"
# Expected: "Configuration validation failed: Stage 1 weights sum to 1.10, expected 1.0 (SEMANTIC_WEIGHT + TFIDF_WEIGHT + SKILL_OVERLAP_WEIGHT)"
```

**Invalid Stage 2 sum** — should fail fast:
```bash
FINAL_SEMANTIC_WEIGHT=0.40 FINAL_TFIDF_WEIGHT=0.40 FINAL_SKILL_WEIGHT=0.40 LLM_VERIFICATION_WEIGHT=0.20 \
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "engineer"
# Expected: "Stage 2 weights sum to 1.40, expected 1.0"
```

**Out of range weight** — should fail:
```bash
SEMANTIC_WEIGHT=1.5 TFIDF_WEIGHT=0.30 SKILL_OVERLAP_WEIGHT=-0.5 \
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf --roles "engineer"
# Expected: "SEMANTIC_WEIGHT must be in [0.0, 1.0], SKILL_OVERLAP_WEIGHT must be in [0.0, 1.0]"
```

---

## Test 2: Pre-filter Allows Low-Semantic/High-Skill Job (SC-001, FR-003, FR-004)

**Scenario**: Job with semantic=0.45 (below old 0.50 gate), skill=0.85, tfidf=0.65 → composite ≈ 0.62 (Moderate)

```bash
# Use low pre-filter threshold (default 0.30)
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" \
  --threshold 0.50 -v
```

**Verify**:
- Job appears in results with `score_interpretation: "moderate"` or `"strong"`
- `score_breakdown` shows semantic_contribution from 0.45 raw score
- `passed_semantic_gate` in metadata includes this job
- No job with semantic < 0.30 appears (pre-filter still active)

**Compare with old threshold** (should filter out the job):
```bash
SEMANTIC_PRE_FILTER_THRESHOLD=0.50 \
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" --threshold 0.50
# Expected: Fewer results; the low-semantic/high-skill job is missing
```

---

## Test 3: LLM Prompt Alignment (SC-003, FR-006)

```bash
# Inspect the prompt template
grep -A 30 "JOB_MATCH_VERIFICATION_PROMPT" config/prompts.py
```

**Verify**:
- ❌ NO `">95%"` or `"95%"` or `"ninety-five percent"` language
- ✅ References calibrated standard: `"≥50% composite score"`, `"match threshold"`, or similar
- ✅ Asks for assessment relative to actual pipeline threshold
- ✅ Does NOT use absolute percentages that contradict config

**Expected prompt excerpt**:
```python
JOB_MATCH_VERIFICATION_PROMPT = """
...
Assess if this job is a strong match for the candidate.
The pipeline's match threshold is {match_threshold:.0%} composite score.
A 'strong match' means the candidate would likely pass initial screening at this threshold.
...
"""
```

---

## Test 4: Score Interpretation Labels in Output (SC-004, FR-007)

```bash
python main.py run data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote"
```

**Verify output contains**:
```
Found N matched jobs for "machine learning engineer" (threshold: 50%)

┌─ Matched Jobs (X above threshold) ────────────────────────┐
│ # │ Title                    │ Company       │ Src    │ Scr │ Int │
├───┼──────────────────────────┼───────────────┼────────┼─────┼─────┤
│ 1 │ ML Engineer              │ Acme AI       │ linkedin│ 72% │ 🟢  │
│ 2 │ Senior ML Engineer       │ StartupXYZ    │wellfound│ 65% │ 🟡  │
└───┴──────────────────────────┴───────────────┴────────┴─────┴─────┘
```

**Interpretation legend** (displayed or in help):
- 🟢 **Strong** (≥70%): "Strong match — likely to pass initial screening"
- 🟡 **Moderate** (50-69%): "Moderate match — manual review recommended"
- 🔴 **Weak** (<50%): "Weak match — significant gaps" (hidden by default threshold)

---

## Test 5: Full Score Breakdown (SC-005, FR-008)

```bash
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" -v
```

**Verify for each job** (verbose mode):
```
Score breakdown for #1:
  Stage 1 (Pre-filter):
    Semantic (0.35): 0.65 → 0.228
    TF-IDF   (0.30): 0.70 → 0.210
    Skill    (0.35): 0.80 → 0.280
    Stage 1 Score: 0.718
    Formula: 0.35*0.65 + 0.30*0.70 + 0.35*0.80 = 0.718

  Stage 2 (Final):
    Semantic (0.30): 0.65 → 0.195
    TF-IDF   (0.25): 0.70 → 0.175
    Skill    (0.25): 0.80 → 0.200
    LLM      (0.20): 0.60 → 0.120
    Composite: 0.690
    Formula: 0.30*0.65 + 0.25*0.70 + 0.25*0.80 + 0.20*0.60 = 0.690

  Interpretation: Moderate (50-69%)
```

**Check all fields present**:
- Raw scores for each component
- Weights used (matching config)
- Weighted contributions
- Stage formulas
- Final composite
- Interpretation band boundaries

---

## Test 6: Audit Trail in SearchMetadata (SC-006, FR-009)

```bash
# Run search and check metadata (available in logs or returned state)
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" 2>&1 | grep -A 50 "SearchMetadata"
```

**Verify metadata includes**:
```json
{
  "total_scraped": 342,
  "passed_semantic_gate": 156,
  "passed_final_filter": 12,
  "weight_configuration": {
    "semantic_weight": 0.35,
    "tfidf_weight": 0.30,
    "skill_overlap_weight": 0.35,
    "final_semantic_weight": 0.30,
    "final_tfidf_weight": 0.25,
    "final_skill_weight": 0.25,
    "llm_verification_weight": 0.20,
    "stage1_sum": 1.0,
    "stage2_sum": 1.0
  },
  "thresholds_used": {
    "semantic_pre_filter": 0.30,
    "match_threshold": 0.50,
    "score_band_strong_min": 0.70,
    "score_band_moderate_min": 0.50
  }
}
```

---

## Test 7: Configurable via .env (FR-005)

```bash
# Create test .env override
cat > .env.test <<'EOF'
SEMANTIC_WEIGHT=0.40
TFIDF_WEIGHT=0.30
SKILL_OVERLAP_WEIGHT=0.30
FINAL_SEMANTIC_WEIGHT=0.35
FINAL_TFIDF_WEIGHT=0.25
FINAL_SKILL_WEIGHT=0.20
LLM_VERIFICATION_WEIGHT=0.20
SEMANTIC_PRE_FILTER_THRESHOLD=0.25
MATCH_THRESHOLD=0.55
SCORE_BAND_STRONG_MIN=0.75
SCORE_BAND_MODERATE_MIN=0.55
EOF

# Run with test config
env $(cat .env.test | xargs) python main.py search \
  --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "machine learning engineer" --locations "Remote" -v

# Verify score breakdown uses these weights
# Verify metadata.weight_configuration matches .env.test values
# Verify thresholds_used matches .env.test values
```

---

## Regression Checks (All Existing Tests Pass)

```bash
# 1. Full test suite
pytest tests/ -q
# Expected: All tests pass

# 2. Analyze command (Agent 1)
python main.py analyze data/resumes/AI-EGI_DevNK.pdf
# Expected: Skills, roles, locations extracted; no errors

# 3. Dashboard (reads database)
python main.py dashboard
# Expected: Tables render; no errors

# 4. Scraping still works
python main.py search --resume-path data/resumes/AI-EGI_DevNK.pdf \
  --roles "engineer" --locations "Remote" --boards indeed
# Expected: Jobs scraped, matched, displayed
```

---

## Success Criteria Checklist

| Criterion | Test | Pass? |
|-----------|------|-------|
| SC-001: Pre-filter ≤30% allows high-skill jobs | Test 2 | ☐ |
| SC-002: Invalid config rejected at startup | Test 1 | ☐ |
| SC-003: LLM prompt references actual threshold | Test 3 | ☐ |
| SC-004: Output shows Strong/Moderate/Weak labels | Test 4 | ☐ |
| SC-005: Verbose shows full breakdown + formula | Test 5 | ☐ |
| SC-006: Metadata includes weight config snapshot | Test 6 | ☐ |
| SC-007: All weights/thresholds configurable via .env | Test 7 | ☐ |

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| "Stage 1 weights sum to X" error | .env values don't sum to 1.0 | Adjust so SEMANTIC_WEIGHT + TFIDF_WEIGHT + SKILL_OVERLAP_WEIGHT = 1.0 |
| "Stage 2 weights sum to X" error | .env values don't sum to 1.0 | Adjust FINAL_* weights + LLM_VERIFICATION_WEIGHT = 1.0 |
| No jobs pass pre-filter | SEMANTIC_PRE_FILTER_THRESHOLD too high | Lower to 0.30 or below |
| LLM verification skipped | No LLM configured | Set OLLAMA_BASE_URL or GROQ_API_KEY in .env |
| Score bands not showing | Verbose flag missing | Run with `-v` flag |
| Metadata not in output | Log level too high | Check INFO level logs or returned state object |