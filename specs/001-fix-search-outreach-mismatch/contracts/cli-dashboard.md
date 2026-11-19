# CLI Command Contract: dashboard

**Feature**: Fix Misleading Search & Outreach Behavior  
**Command**: `main.py dashboard` (existing, labels corrected)  
**Status**: Modified — terminology aligned with "matched/saved" reality

---

## Signature

```bash
python main.py dashboard [OPTIONS]
```

### Options (unchanged)

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--verbose` | `-v` | `is_flag` | No | `False` | Debug logging |

---

## Modified Output Contracts

### Dashboard Title (FR-007)

**Before**:
```
  Application Status Dashboard  
```

**After**:
```
  Matched Jobs Dashboard  
```

**Rationale**: No applications have been sent; only matched jobs are saved.

---

### Total Row (FR-007)

**Before**:
```
│ Total                │    10 │  ← "Total applications"
```

**After**:
```
│ Total matched jobs saved │    10 │
```

**Rationale**: Count reflects jobs persisted to DB with `status="matched"`, not applications sent.

---

### Status Breakdown (FR-007)

**Before** (could imply multiple statuses):
```
┌──────────────────────┬───────┐
│ Status               │ Count │
├──────────────────────┼───────┤
│ matched              │    10 │
│ applied              │     0 │  ← misleading
│ interviewed          │     0 │  ← misleading
└──────────────────────┴───────┘
```

**After** (only real status):
```
┌──────────────────────┬───────┐
│ Status               │ Count │
├──────────────────────┼───────┤
│ matched              │    10 │
└──────────────────────┴───────┘
```

**Rules**:
- Only statuses that actually exist in the database are shown
- Currently only `"matched"` exists (set by `node_execute_outreach`)
- No "applied", "sent", "interviewed", "rejected" rows until those states are real

---

### Recent Activity (FR-007)

**Before** (generic):
```
│ 2026-11-15 14:30 │ Job saved      │ Machine Learning Engineer @ Acme AI │
```

**After** (explicit):
```
│ 2026-11-15 14:30 │ Saved to DB    │ Machine Learning Engineer @ Acme AI │
```

**Rationale**: "Job saved" → "Saved to DB" clarifies persistence action, not application submission.

---

## Integration Points

- **Reads**: `models/database.Database.get_status_breakdown()` → returns `dict[str, int]`
- **Reads**: `models/database.Database.get_recent_activity(limit=20)` → returns `list[TrackingEntry]`
- **TrackingEntry** (`models/schemas.py:188-197`): `last_action` should be `"saved to database"` (not "job saved" or "application submitted")

---

## Non-Functional Requirements

- **Consistency**: Dashboard labels match `search` and `run` output terminology
- **Zero data risk**: Read-only command; no database writes
- **Forward compatibility**: When real outreach adds statuses ("applied", "interviewed"), they will appear automatically via `get_status_breakdown()`