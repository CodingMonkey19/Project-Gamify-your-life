# Research: Automation Orchestration

**Date**: 2026-03-22 | **Feature**: 007-automation-orchestration

## R1: GitHub Actions Cron Scheduling for Cairo Timezone

**Decision**: Use UTC-based cron expressions that align with Cairo (UTC+2) local times.

**Rationale**: GitHub Actions cron schedules run in UTC only — no timezone parameter. Cairo is UTC+2 year-round (Egypt abolished DST in 2014). The offset is fixed:
- Daily 10 PM Cairo = `0 20 * * *` UTC
- Weekly Sunday 10 AM Cairo = `0 8 * * 0` UTC
- Monthly 1st ~2 AM Cairo = `0 0 1 * *` UTC

Note: GitHub Actions cron has up to 15-minute jitter on public runners. Not a problem for daily/weekly/monthly cadences. Use `workflow_dispatch` trigger alongside cron for manual re-runs.

**Alternatives considered**:
- External cron service (cron-job.org) → rejected: adds external dependency, no advantage over GitHub Actions
- Self-hosted runner with system cron → rejected: overkill for single-player system

## R2: Pipeline Orchestration Pattern (Daily 16-Step)

**Decision**: Sequential function calls in a single Python script with try/except per step. No framework.

**Rationale**: The daily pipeline is a linear sequence of 16 engine calls. Each step is independent enough to continue if a prior step fails (fault tolerance per spec). A simple list-of-callables pattern provides:
- Clear execution order (FR-015)
- Per-step error catching with logging
- No external orchestration framework needed (Airflow, Prefect are overkill)
- Easy to test: mock each engine, verify call order

Pattern:
```python
PIPELINE = [
    ("Smoke Test", smoke_test.run),
    ("Load Settings", load_settings),
    ("Good Habits", habit_engine.process_daily_habits),
    # ... etc
]
for name, fn in PIPELINE:
    try:
        result = fn(ctx)
        logger.info(f"✓ {name}: {result}")
    except Exception as e:
        logger.error(f"✗ {name}: {e}")
        # Continue to next step (fault tolerant)
```

**Alternatives considered**:
- Apache Airflow → rejected: massive dependency, meant for data pipelines at scale
- Simple sequential calls without try/except → rejected: one failure would abort entire pipeline
- Async/parallel execution → rejected: engines have ordering dependencies (XP before stat recalc, stats before death check)

## R3: Idempotency Implementation Patterns

**Decision**: Per-engine idempotency using check-before-write with Notion API queries.

**Rationale**: Each engine independently checks if its work is already done:
- **Snapshot engine**: Query Daily Snapshots DB for `Date == today AND Character == id`. If exists, skip.
- **Habit engine**: Activity Log entries have Date + Habit relation. Query for existing entries before creating.
- **Streak engine**: Checks `Last Processed Date` property on streak records.
- **Treasury**: Query Treasury DB for `Month == target_month AND Character == id`.

This is more robust than a pipeline-level gate because:
- Partial failures can be retried (only unfinished steps re-execute)
- No need for a separate "run status" table
- Each engine is independently testable for idempotency

**Alternatives considered**:
- Pipeline-level gate (single snapshot check blocks everything) → rejected per clarification: too coarse, prevents partial retry
- Separate run-tracking DB → rejected: unnecessary complexity for single-player system

## R4: Weekly Report Delta Calculation

**Decision**: Query 7 days of snapshots, compute deltas between oldest and newest.

**Rationale**: Weekly deltas compare `snapshot[today]` vs `snapshot[today - 7]`. If fewer than 7 snapshots exist (new player), use whatever is available. If only 1 snapshot exists, deltas are 0. No crash from missing data (per acceptance scenario US2-4).

Implementation: Query Daily Snapshots DB with filter `Date >= (today - 7)`, sort by Date ascending. Delta = last.stat - first.stat for each stat field.

**Alternatives considered**:
- Store weekly summaries as separate DB rows → rejected: computed view is sufficient, avoids another DB
- Only compute if exactly 7 snapshots → rejected: would fail for new players

## R5: GitHub Actions Concurrency and Secrets

**Decision**: Use `concurrency` group per workflow to prevent parallel runs. Secrets via `${{ secrets.KEY }}`.

**Rationale**: GitHub Actions supports `concurrency` at the workflow level:
```yaml
concurrency:
  group: daily-automation
  cancel-in-progress: false
```
This ensures if cron fires while a previous run is still active, the new run queues (not cancels). `cancel-in-progress: false` is critical — we don't want to abort a running pipeline.

Secrets: `NOTION_TOKEN`, `OPENAI_API_KEY`, `CHARACTER_ID`, `NOTION_PARENT_PAGE_ID` stored as repository secrets. Accessed via `${{ secrets.NOTION_TOKEN }}` in env block.

**Alternatives considered**:
- No concurrency control → rejected: risk of duplicate processing if cron overlaps
- `cancel-in-progress: true` → rejected: would kill running automation mid-pipeline

## R6: Smoke Test Design

**Decision**: Standalone `smoke_test.py` that validates environment before any processing.

**Rationale**: The smoke test is step 1 of the daily pipeline but also useful independently. It checks:
1. Required env vars exist: `NOTION_TOKEN`, `CHARACTER_ID`
2. Optional env vars warned if missing: `OPENAI_API_KEY` (daily runs without it; weekly needs it)
3. Notion API reachable: simple `notion.users.me()` call
4. Character DB record exists for the given CHARACTER_ID

If any required check fails, raises `SmokeTestError` and the pipeline aborts. Optional failures log warnings.

**Alternatives considered**:
- Inline checks in each automation script → rejected: duplicated code, harder to test
- Skip smoke test, let engines fail naturally → rejected: produces confusing partial failures

## R7: Dual Output Channel (stdout + logger)

**Decision**: All automation scripts print summaries to stdout AND log structured messages via logger.py.

**Rationale**: Per clarification Q9, output goes to both channels:
- **stdout**: Captured by GitHub Actions logs. Human-readable summary at end of run.
- **logger.py (stderr)**: Structured `YYYY-MM-DD HH:MM:SS - module - LEVEL - message` format for debugging.

Implementation: Use `print()` for final summary blocks, `logger.info/warning/error` for step-by-step progress. This is already the pattern in config.py (logger for internals, print for user-facing output).

**Alternatives considered**:
- stdout only → rejected: loses structured timestamps and severity levels
- logger only → rejected: GitHub Actions log viewer works best with stdout
- File-based logging → rejected: GitHub Actions runners are ephemeral, files are lost
