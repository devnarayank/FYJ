# CLI Command Contract: run (Outreach Summary & Dashboard Changes)

**Feature**: Fix Misleading Search & Outreach Behavior  
**Command**: `main.py run` (existing, summary output modified)  
**Status**: Modified — outreach summary and dashboard labels corrected

---

## Signature

```bash
python main.py run [OPTIONS] RESUME_PATH
```

### Options (unchanged)

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `RESUME_PATH` | — | `click.Path(exists=True)` | Yes (arg) | — | Path to resume PDF |
| `--roles` | `-R` | `multiple=True` (str) | No | `[]` | Target role(s) |
| `--locations` | `-L` | `multiple=True` (str) | No | `[]` | Target location(s) |
| `--boards` | `-b` | `multiple=True` (str) | No | `[]` | Job boards to search |
| `--verbose` | `-v` | `is_flag` | No | `False` | Debug logging |

---

## Modified Output Contracts

### Outreach Summary Table (FR-006, FR-009)

**Before (misleading)**:
```
┌─ Outreach Summary ─┐
│ Attempted: 10      │  ← WRONG: implies outreach attempted
│ Sent: 0            │
│ Skipped: 0         │
│ Failed: 0          │
└────────────────────┘
```

**After (honest — current implementation)**:
```
┌─ Outreach Summary ─┐
│ Attempted: 0       │  ← No external outreach performed
│ Sent: 0            │  ← No emails sent
│ Skipped: 10        │  ← 10 matched jobs persisted to DB
│ Failed: 0          │
└────────────────────┘
```

**Rules**:
- `Attempted` = 0 when no external outreach capability exists
- `Sent` = 0
- `Skipped` = number of `MatchedJob` records persisted by `node_execute_outreach`
- `Failed` = 0
- Table title remains "Outreach Summary" for forward compatibility

**Future (when outreach implemented)**:
- `Attempted` = jobs processed for outreach
- `Sent` = successfully delivered
- `Skipped` = not processed (e.g., no contact found)
- `Failed` = delivery errors

---

### Pipeline Configuration Panel (unchanged)
```
┌─────────── Pipeline Configuration ────────────┐
│ Multi-Agent Job Hunter                        │
│ Resume: data/resumes/AI-EGI_DevNK.pdf         │
│ Roles: machine learning engineer              │
│ Locations: Remote                             │
│ Boards: indeed, linkedin, wellfound, cutshort │
└───────────────────────────────────────────────┘
```

### Matched Jobs Table (unchanged structure, label consistency)
```
                       Matched Jobs (10 above threshold)                       
┌┬──────────────────────────┬────────────────┬──────────────┬────┬───────────┐
││ Title                    │ Company        │ Source       │ S… │ Location  │
├┼──────────────────────────┼────────────────┼──────────────┼────┼───────────┤
││ Machine Learning Engineer│ Acme AI        │ linkedin     │ 62%│ Remote    │
└┴──────────────────────────┴────────────────┴──────────────┴────┴───────────┘
```

---

## Integration Points

- **Orchestrator node**: `graph/orchestrator.py:node_execute_outreach` returns corrected summary dict
- **Dashboard rendering**: `main.py` dashboard command reads corrected labels
- **Database**: `models/database.py` inserts jobs with `status="matched"` (unchanged)

---

## Non-Functional Requirements

- **Backward compatibility**: Summary structure unchanged (same keys), only values corrected
- **Forward compatibility**: When real outreach is added, same keys used with real values
- **Zero data risk**: No changes to database writes or job matching logic