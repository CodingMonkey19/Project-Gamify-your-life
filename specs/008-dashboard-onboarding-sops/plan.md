# Implementation Plan: Dashboard, Onboarding & SOPs

**Branch**: `008-dashboard-onboarding-sops` | **Date**: 2026-03-22 | **Spec**: `specs/008-dashboard-onboarding-sops/spec.md`
**Input**: Feature specification from `/specs/008-dashboard-onboarding-sops/spec.md`

## Summary

Build the player-facing layer (Phase 8) — an interactive CLI onboarding script (`onboarding.py`) that creates a character with starting stats, default habits, vision board, and identity records, then auto-generates a Notion Dashboard page via the API. A separate `dashboard_setup.py` handles programmatic dashboard creation with 7 linked database view panels. Five WAT-format SOP documents in `workflows/` provide operational documentation. All scripts read DB IDs from `.env`/Settings DB consistent with Phase 7 automation patterns.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv`, `pytest`
**Storage**: Notion API (headless DB) — Character DB, Good Habit DB, Bad Habit DB, Vision Board Items DB, Onboarding Identity DB, Journal DB, Brain Dump DB, Quests DB, Daily Snapshots DB
**Testing**: `pytest` with mock Notion responses in `conftest.py`
**Target Platform**: Local CLI (Windows/macOS/Linux) — interactive terminal prompts
**Project Type**: Interactive CLI script + Notion API page builder + documentation
**Performance Goals**: Onboarding completes in under 10 minutes (including user input time). Dashboard creation < 30 seconds (API calls only).
**Constraints**: All DB IDs from `.env` or Settings DB. No paid dependencies. Notion API rate limits (~3 req/sec with backoff from existing `notion_client.py`).
**Scale/Scope**: Single-player system. 1 Character, 5 good habits, 3 bad habits, 8 vision board entries, N identity rows, 1 dashboard page with 7 panels. 5 SOP files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | **PASS** | All records created in Notion DBs. Dashboard is a Notion page with linked DB views. No local DB. |
| II. Python for Complex Orchestration Only | **PASS** | Onboarding script orchestrates multi-DB record creation. Dashboard script composes Notion blocks. Each tool has one concern. |
| III. WAT Architecture | **PASS** | Scripts in `tools/`. SOPs in `workflows/`. Claude orchestrates. Each script is independently testable. |
| IV. Settings DB as Canonical Config | **PASS** | DB IDs from `.env`/Settings DB. Starting stats from `config.py` (STARTING_HP, RANK_THRESHOLDS). No hardcoded game balance. |
| V. Idempotency and Safe Re-Runs | **PASS** | Onboarding detects existing character, resumes partial state. Dashboard detects existing page. No duplicate records on re-run. |
| VI. Free-First, Cost-Controlled AI | **PASS** | No AI calls in onboarding or dashboard. No new paid dependencies. SOPs are markdown files — zero cost. |

**Gate result: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/008-dashboard-onboarding-sops/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contracts)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── config.py                 # [EXISTS] Game balance constants + Settings DB reader
├── logger.py                 # [EXISTS] Structured logging
├── onboarding.py             # [NEW] Interactive character creation CLI + auto-dashboard
├── dashboard_setup.py        # [NEW] Programmatic Notion dashboard page builder
└── ...                       # [EXISTS] Phase 1-7 engines

workflows/
├── setup-notion.md           # [NEW] Database creation from scratch SOP
├── daily-routine.md          # [NEW] Daily player routine SOP
├── weekly-review.md          # [NEW] Weekly report interpretation SOP
├── asset-generation.md       # [NEW] Radar chart + avatar regeneration SOP
└── onboarding.md             # [NEW] Character creation walkthrough SOP

tests/
├── conftest.py               # [EXISTS or NEW] Shared mock Notion fixtures
├── test_onboarding.py        # [NEW] Onboarding unit tests
└── test_dashboard_setup.py   # [NEW] Dashboard setup unit tests
```

**Structure Decision**: Single-project layout per WAT convention. All tools in `tools/`, all SOPs in `workflows/`, tests in `tests/`.

## Complexity Tracking

No constitution violations to justify. All principles pass cleanly.
