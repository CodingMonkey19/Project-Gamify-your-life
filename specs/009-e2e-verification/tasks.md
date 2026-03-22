# Tasks: End-to-End Verification

**Input**: Design documents from `/specs/009-e2e-verification/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — this entire phase IS the test suite. Constitution mandates "No engine ships without tests" and the spec explicitly requires test files for all 9 engines.

**Organization**: Tasks grouped by user story. US1 (Unit Tests) and US2 (Integration Smoke Tests) are co-P1. US3 (Manual Verification) is P2, independent of code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Test infrastructure and shared fixtures

- [ ] T001 Create tests/ directory and tests/__init__.py (empty) to make tests a Python package
- [ ] T002 Extend tests/conftest.py with additional mock fixtures (Phase 1 may already have created this file with basic fixtures — add any missing ones): mock_notion_client (patched Client with configurable .databases.query() and .pages.create()), mock_character_page (Level 5, HP 800, 150 coins, known stat XPs), mock_settings (dict matching config.py defaults), mock_habit_rows (5 good + 3 bad habits), mock_workout_rows (3 entries with weight/reps/RPE), mock_meal_rows (3 entries with macros), mock_expense_rows (5 entries), mock_activity_log (empty default + populated variant). All response dicts must match Notion API shape (id, properties, results array).
- [ ] T003 [P] Verify pytest is in requirements.txt — add if missing. No other test dependencies needed (unittest.mock is stdlib).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: CI pipeline must exist before test files are meaningful in the workflow

**CRITICAL**: CI pipeline should be set up early so tests are validated on every push as they're written.

- [ ] T004 Verify or create .github/workflows/tests.yml (Phase 1 may already have this) — trigger on push (all branches) and pull_request (all branches), ubuntu-latest runner, Python 3.10, steps: checkout, setup-python, pip install -r requirements.txt, python -m pytest tests/ -v --tb=short. No NOTION_TOKEN or .env needed (unit tests are mocked).

**Checkpoint**: CI pipeline active. Every subsequent test file pushed will be validated automatically.

---

## Phase 3: User Story 1 — Automated Unit Test Suite (Priority: P1) MVP

**Goal**: Unit test files for all 9 game engines, each mirroring its engine file, using mock Notion responses. Full suite passes with 0 failures in <30 seconds.

**Independent Test**: Run `python -m pytest tests/ -v`. All tests pass. No external dependencies needed.

### Implementation for User Story 1

- [ ] T005 [P] [US1] Write tests/test_xp_engine.py — test non-linear curve calculation (XP = XP_BASE * level^XP_EXPONENT), level_from_xp roundtrip accuracy for levels 1-50, class bonus application (Warrior→STR, Mage→INT, etc.), class bonus multiplier value matches config. Import from tools.xp_engine, use mock_settings and mock_character_page fixtures.
- [ ] T006 [P] [US1] Write tests/test_hp_engine.py — test damage application reduces HP, death trigger at HP ≤ 0, death trigger when HP goes negative, respawn resets to STARTING_HP, hotel recovery by tier (tier 1/2/3 restore correct amounts from config), hotel recovery caps at max HP (cannot exceed STARTING_HP). Import from tools.hp_engine, use mock_character_page fixture.
- [ ] T007 [P] [US1] Write tests/test_coin_engine.py — test overdraft detection (balance < 0 after deduction), market purchase deducts correct coins, hotel check-in cost by tier matches config, insufficient coins rejected (purchase blocked). Import from tools.coin_engine, use mock_character_page fixture.
- [ ] T008 [P] [US1] Write tests/test_streak_engine.py — test streak increment on consecutive day, reset to 0 on miss, decay penalty calculation (penalty = decay rate * streak tier), tier advancement at exact thresholds (3, 7, 14, 30, 60, 100 days), tier stays within bounds (streak 1000 doesn't exceed max tier). Import from tools.streak_engine, use mock_settings fixture.
- [ ] T009 [P] [US1] Write tests/test_financial_engine.py — test surplus calculation (income - expenses), Gold conversion at configured rate (Gold = surplus / GOLD_CONVERSION_RATE), budget breach XP penalty on negative surplus, zero expenses = full surplus. Import from tools.financial_engine, use mock_expense_rows and mock_settings fixtures.
- [ ] T010 [P] [US1] Write tests/test_fitness_engine.py — test Epley 1RM formula accuracy (1RM = weight * (1 + reps/30), verify to 2 decimal places), RPE-weighted XP calculation (higher RPE = more XP), progressive overload detection over 14-day window, no overload flag when weight is stable. Import from tools.fitness_engine, use mock_workout_rows fixture.
- [ ] T011 [P] [US1] Write tests/test_nutrition_engine.py — test symmetric adherence scoring (80% of target penalized same as 120%), negative XP on significant overshoot (>130% target), streak multiplier application on consecutive adherent days, perfect adherence (100% target) awards maximum XP. Import from tools.nutrition_engine, use mock_meal_rows and mock_settings fixtures.
- [ ] T012 [P] [US1] Write tests/test_loot_box.py — test weight distribution within ±5% of configured weights over 10,000 samples (use random.seed(42) for seeded run), pity timer triggers after PITY_TIMER_THRESHOLD draws without Legendary, pity timer resets to 0 after Legendary drop, seeded reproducibility (same seed = same sequence). Import from tools.loot_box, use mock_settings fixture.
- [ ] T013 [P] [US1] Write tests/test_chart_renderer.py — test output file is created after generation, correct image dimensions (e.g., 800x800), 5-axis radar chart renders (STR/INT/WIS/VIT/CHA), zero stats input produces valid chart without crash. Import from tools.chart_renderer, use mock_character_page fixture. Use tmp_path pytest fixture for output file.

**Checkpoint**: All 9 test files pass. Run `python -m pytest tests/ -v` — 0 failures, 0 errors, <30 seconds. SC-001 and SC-008 satisfied.

---

## Phase 4: User Story 2 — Integration Smoke Tests (Priority: P1)

**Goal**: 15-step structured integration test checklist that validates every major system interaction end-to-end against a live Notion workspace.

**Independent Test**: Follow the 15-step sequence on a test Notion workspace. Each step has a clear pass/fail checkpoint.

### Implementation for User Story 2

- [ ] T014 [US2] Create tests/integration/ directory and tests/integration/smoke_test_checklist.md — structured 15-step checklist with each step containing: step number, title, action (what to run/do), verification (what to check in Notion), pass criteria (specific measurable outcome), pass/fail checkbox, notes field. Steps in order: (1) Environment smoke test, (2) Database creation, (3) Seed data, (4) Onboarding, (5) Good habit check-in → XP increase, (6) Bad habit → HP decrease → death, (7) Hotel check-in → HP recovery, (8) Expense tracking → financial surplus → Gold, (9) Workout logging → fitness 1RM + STR XP, (10) Meal logging → nutrition adherence + VIT XP, (11) Weekly report → AI briefing + quests, (12) Daily automation idempotency (run twice, zero duplicates), (13) Radar chart generation, (14) CI pipeline validation (push, verify tests run), (15) Manual workflow trigger via CI interface.
- [ ] T015 [US2] Add graceful skip logic to tests/conftest.py — add a `notion_available` fixture that checks for NOTION_TOKEN environment variable. Integration tests using this fixture skip with message "NOTION_TOKEN not configured — skipping integration test" when credentials are unavailable (FR-016). Unit tests must NOT use this fixture.

**Checkpoint**: Integration checklist complete. A developer can follow it step-by-step on a test workspace.

---

## Phase 5: User Story 3 — Manual User Verification Checklist (Priority: P2)

**Goal**: 8-item manual verification checklist covering subjective and experiential aspects that automated tests cannot capture.

**Independent Test**: Open Notion dashboard, spend 15-30 minutes with realistic data, work through all 8 items.

### Implementation for User Story 3

- [ ] T016 [US3] Create checklists/ directory and checklists/manual_verification.md — 8-item checklist with each item containing: item number, title, action (what to do in Notion), explicit pass criteria (non-subjective where possible), pass/fail checkbox, notes field. Items: (1) Dashboard displays 7 panels with current data, (2) Full day data entry → stats/HP/coins/level/rank update correctly, (3) Radar chart shows 5 stat axes with correct proportions, (4) Bad habits repeated → HP=0 → "You Died!" event visible, (5) Respawn via marketplace → HP resets to STARTING_HP, (6) Loot box pull → reward appears in inventory with correct rarity, (7) AI coaching briefing contains real numbers + non-sycophantic tone + actionable suggestions, (8) Overall game feel — responsive, punishing-but-fair death cycle, rewarding loot.

**Checkpoint**: Manual verification checklist ready for player walkthrough.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and completeness checks

- [ ] T017 Run full pytest suite: `python -m pytest tests/ -v` — verify all 9 test files pass with 0 failures, 0 errors, <30 seconds (SC-001, SC-007)
- [ ] T018 Run loot box test 3 consecutive times to rule out flakiness (SC-005): `python -m pytest tests/test_loot_box.py -v` × 3
- [ ] T019 Verify test coverage completeness (SC-008): confirm every engine file in tools/ that contains game logic has a corresponding test file in tests/ — check: xp_engine, hp_engine, coin_engine, streak_engine, financial_engine, fitness_engine, nutrition_engine, loot_box, chart_renderer
- [ ] T020 Verify CI pipeline catches failures (SC-004): intentionally break a test assertion, push to branch, confirm CI fails, revert, confirm CI passes
- [ ] T021 Verify daily automation idempotency (SC-006): run daily_automation.py twice on test workspace, query Activity Log and Daily Snapshots counts before and after, confirm zero duplicates

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001-T003) — CI pipeline
- **US1 Unit Tests (Phase 3)**: Depends on Phase 1 (T002 conftest.py) — all 9 test files are independent of each other
- **US2 Integration (Phase 4)**: Depends on Phase 1 (T002 for skip fixture) — checklist is a document, not code
- **US3 Manual Verification (Phase 5)**: No code dependencies — can be written any time
- **Polish (Phase 6)**: Depends on US1 + US2 complete

### User Story Dependencies

- **US1 (P1)**: After Setup → all 9 test files independent of each other, all parallelizable
- **US2 (P1)**: After Setup → checklist is a markdown document, T015 adds to conftest.py
- **US3 (P2)**: No dependencies — pure documentation

### Within Each User Story

- US1: conftest.py fixtures must exist before any test file (T002 before T005-T013)
- US2: Checklist first (T014), then skip logic (T015)
- US3: Single task (T016)

### Parallel Opportunities

- T002 + T003: conftest.py and requirements.txt are independent files
- T005 through T013: ALL 9 unit test files are independent — maximum parallelism
- T014 + T016: Integration checklist and manual verification checklist are independent documents
- T017 through T021: Polish tasks are sequential (each validates a different success criterion)

---

## Parallel Example: User Story 1 (Unit Test Files)

```bash
# Launch ALL 9 test files together (all independent, different files):
Task: "Write tests/test_xp_engine.py"
Task: "Write tests/test_hp_engine.py"
Task: "Write tests/test_coin_engine.py"
Task: "Write tests/test_streak_engine.py"
Task: "Write tests/test_financial_engine.py"
Task: "Write tests/test_fitness_engine.py"
Task: "Write tests/test_nutrition_engine.py"
Task: "Write tests/test_loot_box.py"
Task: "Write tests/test_chart_renderer.py"
```

## Parallel Example: Documentation Tasks

```bash
# Launch both checklists together (independent documents):
Task: "Write tests/integration/smoke_test_checklist.md"
Task: "Write checklists/manual_verification.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: CI Pipeline (T004)
3. Complete Phase 3: US1 Unit Tests (T005-T013) — all 9 in parallel
4. **STOP and VALIDATE**: Run `python -m pytest tests/ -v`. All tests pass.
5. Push to branch — CI validates automatically.

### Incremental Delivery

1. Setup + Foundational → CI pipeline active
2. US1 Unit Tests → All 9 engines verified → **MVP! Automated regression safety net**
3. US2 Integration Checklist → 15-step verification sequence documented
4. US3 Manual Verification → Experiential quality checklist ready
5. Polish → All success criteria validated → Phase 9 complete

### Single Developer Strategy

Work sequentially: Phase 1 → Phase 2 → US1 (T005-T013 can interleave — each is a separate file) → US2 → US3 → Polish.

Key insight: All 9 unit test files (T005-T013) are completely independent. A single developer can write them in any order. Start with the engines you're most familiar with to build momentum.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a verification phase — all "implementation" is test code and documentation, not game logic
- Engine files in tools/ must exist before their test files can import from them (Phases 1-8 prerequisite)
- Unit tests use mocked Notion responses — no live API calls, no .env needed
- Integration tests require a live test Notion workspace — keep separate from production
- The loot box statistical test uses random.seed(42) for CI reproducibility
- Commit after each test file or logical group
