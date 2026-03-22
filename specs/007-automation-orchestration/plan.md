# Implementation Plan: Automation Orchestration

**Branch**: `007-automation-orchestration` | **Date**: 2026-03-22 | **Spec**: `specs/007-automation-orchestration/spec.md`
**Input**: Feature specification from `/specs/007-automation-orchestration/spec.md`

## Summary

Build the automation orchestration layer (Phase 7) — three Python CLI scripts (`daily_automation.py`, `weekly_report.py`, `monthly_automation.py`) that compose existing Phase 1-6 engines into idempotent pipelines, plus a `snapshot_engine.py` for daily state capture, and four GitHub Actions workflow YAML files for scheduled execution. All scripts follow the WAT architecture: deterministic tools called in sequence, with dual-channel output (stdout + logger.py).

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `openai`, `python-dotenv`, `Pillow`, `matplotlib`, `pytest`
**Storage**: Notion API (headless DB) — Daily Snapshots DB, Treasury DB, Settings DB, Character DB, Activity Log, Streak Tracker, Quests DB, Expense Log, Set Log, Meal Log
**Testing**: `pytest` with mock Notion responses in `conftest.py`
**Target Platform**: GitHub Actions runners (Ubuntu latest) + local Windows dev
**Project Type**: CLI automation scripts + CI/CD workflows
**Performance Goals**: Daily pipeline completes in < 60 seconds
**Constraints**: All game balance from config.py / Settings DB. OpenAI cost cap $1.00/month. Free-first tooling only.
**Scale/Scope**: Single-player system. ~16 engine calls per daily run. 3 automation cadences (daily/weekly/monthly).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | **PASS** | All data reads/writes go through Notion API. No local DB. Single-row formulas stay in Notion; multi-row aggregation in Python. |
| II. Python for Complex Orchestration Only | **PASS** | Each automation script orchestrates existing engines. No new game balance constants — all from config.py/Settings DB. Each tool has one concern. |
| III. WAT Architecture | **PASS** | Scripts live in `tools/`. Workflows will document SOPs. Claude orchestrates. Pipeline scripts call engines, not inline logic. |
| IV. Settings DB as Canonical Config | **PASS** | `config.py` already sources from Settings DB with fallback defaults. Automation scripts use `get_config()`. |
| V. Idempotency and Safe Re-Runs | **PASS** | Per-engine idempotency (clarified in spec). Snapshot date uniqueness. Treasury month uniqueness. Activity Log dedup. |
| VI. Free-First, Cost-Controlled AI | **PASS** | Weekly report checks `AI_MONTHLY_SPEND` against cap before calling OpenAI. Monthly resets spend to 0. No new paid deps. |

**Gate result: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/007-automation-orchestration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI + workflow contracts)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── config.py                 # [EXISTS] Game balance constants + Settings DB reader
├── logger.py                 # [EXISTS] Structured logging
├── snapshot_engine.py        # [NEW] Daily Snapshot capture — idempotent by date
├── daily_automation.py       # [NEW] 16-step daily pipeline CLI
├── weekly_report.py          # [NEW] Weekly report + AI integration CLI
├── monthly_automation.py     # [NEW] Monthly Gold settlement + AI spend reset CLI
└── smoke_test.py             # [NEW] Pre-flight environment validation

.github/workflows/
├── daily.yml                 # [NEW] Cron: 0 20 * * * (10 PM Cairo = 8 PM UTC)
├── weekly.yml                # [NEW] Cron: 0 8 * * 0 (Sun 10 AM Cairo = 8 AM UTC)
├── monthly.yml               # [NEW] Cron: 0 0 1 * * (1st midnight ≈ 2 AM Cairo)
└── tests.yml                 # [NEW] On push + PR: pytest suite

tests/
├── conftest.py               # [NEW if not exists] Shared mock Notion fixtures
├── test_snapshot_engine.py   # [NEW] Snapshot engine unit tests
├── test_daily_automation.py  # [NEW] Daily pipeline tests (idempotency, ordering, fault tolerance)
├── test_weekly_report.py     # [NEW] Weekly report tests (deltas, AI fallback, overdraft)
└── test_monthly_automation.py # [NEW] Monthly tests (Treasury dedup, spend reset)
```

**Structure Decision**: Single-project layout. All Python tools in `tools/` per WAT convention. GitHub Actions workflows in `.github/workflows/`. Tests in `tests/` mirroring engine files.

## Complexity Tracking

No constitution violations to justify. All principles pass cleanly.
