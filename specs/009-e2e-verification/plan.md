# Implementation Plan: End-to-End Verification

**Branch**: `009-e2e-verification` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-e2e-verification/spec.md`

## Summary

Comprehensive verification suite for the RPG-Gamified Life Tracker: unit tests for all 9 game engines using mocked Notion responses, a 15-step integration smoke test sequence against a live Notion workspace, an 8-item manual user verification checklist, and CI pipeline validation. This phase does not introduce new game functionality — it validates that Phases 1-8 work correctly end-to-end.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pytest, unittest.mock, notion-client (for integration tests only)
**Storage**: N/A (tests read from mocked responses or live Notion)
**Testing**: pytest with conftest.py shared fixtures, unittest.mock for Notion API mocking
**Target Platform**: Local development + GitHub Actions CI (Ubuntu runner)
**Project Type**: Test suite + verification checklists
**Performance Goals**: Full unit test suite completes in <30 seconds (all mocked, no network calls)
**Constraints**: Unit tests must never call live Notion API; integration tests must skip gracefully without credentials
**Scale/Scope**: 9 unit test files, 1 integration test runner/checklist, 1 manual verification checklist, 1 CI workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Notion as Headless DB | **PASS** | Tests validate engines that read/write Notion — they don't bypass Notion. Integration tests use live Notion API. |
| II. Python for Complex Orchestration Only | **PASS** | Test files are stateless, independently testable, and import from `tools/`. No game logic in test files. |
| III. WAT Architecture | **PASS** | Tests live in `tests/`, not `tools/`. Verification checklists are workflow-adjacent documentation. |
| IV. Settings DB as Canonical Config | **PASS** | Tests import constants from `config.py` (which sources from Settings DB). Mock fixtures simulate Settings DB responses. |
| V. Idempotency and Safe Re-Runs | **PASS** | Integration test step 12 explicitly validates idempotency (run daily_automation twice, verify zero duplicates). |
| VI. Free-First, Cost-Controlled AI | **PASS** | pytest, unittest.mock are free. No paid services required for unit tests. Integration tests use existing Notion API (already provisioned). |

**Gate result: ALL PASS** — no violations, no complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/009-e2e-verification/
├── plan.md              # This file
├── research.md          # Phase 0: Testing patterns and decisions
├── data-model.md        # Phase 1: Test fixture structure
├── quickstart.md        # Phase 1: How to run tests
├── contracts/           # Phase 1: Test file contracts
│   └── test-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tests/
├── conftest.py              # Shared mock fixtures (mock_notion_client, mock_character_page, etc.)
├── test_xp_engine.py        # XP engine: non-linear curve, level roundtrip, class bonus
├── test_hp_engine.py        # HP engine: damage, death at 0, respawn, hotel recovery
├── test_coin_engine.py      # Coin engine: overdraft, market purchase, hotel cost
├── test_streak_engine.py    # Streak engine: increment, reset, decay, tier advancement
├── test_financial_engine.py # Financial engine: surplus, Gold conversion, breach penalty
├── test_fitness_engine.py   # Fitness engine: Epley 1RM, RPE weighting, overload detection
├── test_nutrition_engine.py # Nutrition engine: symmetric adherence, streak multiplier, negative XP
├── test_loot_box.py         # Loot box: weight distribution ±5% over 10k, pity timer
├── test_chart_renderer.py   # Chart renderer: file exists, dimensions, 5 axes
└── integration/
    └── smoke_test_checklist.md  # 15-step integration checklist (runnable doc)

checklists/
└── manual_verification.md   # 8-item manual verification checklist

.github/workflows/
└── tests.yml                # CI pipeline: pytest on push/PR, block merge on failure
```

**Structure Decision**: Flat `tests/` directory mirroring `tools/` engine files (constitution: "Test files mirror engine files"). Integration checklist is a structured markdown doc. CI workflow in standard `.github/workflows/` location.

## Complexity Tracking

> No violations — section intentionally empty.
