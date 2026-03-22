# Tasks: Automation Orchestration

**Input**: Design documents from `/specs/007-automation-orchestration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks included because constitution mandates "No engine ships without tests" and spec includes test workflows (tests.yml).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization — dependencies, test infrastructure, shared utilities

- [ ] T001 Create requirements.txt with notion-client, openai, python-dotenv, Pillow, matplotlib, pytest
- [ ] T002 Create tests/ directory with tests/__init__.py and tests/conftest.py providing shared mock Notion fixtures (mock_notion_client, mock_character_page, mock_settings)
- [ ] T003 Create .github/workflows/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Smoke test and snapshot engine that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement smoke_test.py in tools/smoke_test.py — validate env vars (NOTION_TOKEN, CHARACTER_ID required; OPENAI_API_KEY, NOTION_PARENT_PAGE_ID optional warnings), Notion API reachability (notion.users.me()), raise SmokeTestError on required failures
- [ ] T005 Implement snapshot_engine.py in tools/snapshot_engine.py — take_snapshot(notion_client, character_id, run_date) reads Character DB + Streak Tracker, writes Daily Snapshot row with all 14 fields (Date, Character, 5 stat XPs, Level, Gold, Coins, HP, Rank, Active Streaks, Mood). Idempotent: query Date+Character before insert, skip if exists
- [ ] T006 [P] Write tests/test_smoke_test.py — test required env var missing raises SmokeTestError, optional missing logs warning, API unreachable raises SmokeTestError, all-pass returns cleanly
- [ ] T007 [P] Write tests/test_snapshot_engine.py — test snapshot creation with correct fields, test idempotency (existing snapshot returns skip), test Character DB read populates all fields

**Checkpoint**: Foundation ready — smoke test and snapshot engine validated. User story implementation can begin.

---

## Phase 3: User Story 1 — Daily Automation Pipeline (Priority: P1) MVP

**Goal**: 16-step idempotent daily pipeline that processes habits, aggregates XP, updates stats, and captures a daily snapshot.

**Independent Test**: Create Activity Log entries (good/bad habits), Set Log entries (fitness), Meal Log entries (nutrition) for today. Run `python tools/daily_automation.py --character-id <ID>`. Verify habits processed, streaks updated, XP aggregated, HP adjusted, snapshot created. Run again — verify no duplicates.

### Implementation for User Story 1

- [ ] T008 [US1] Implement daily_automation.py in tools/daily_automation.py — CLI entry point with argparse (--character-id), capture run_date at start, build Pipeline Context dict, execute 16-step PIPELINE list-of-callables with try/except per step (fault tolerant), print final summary to stdout, log per-step results via logger.py
- [ ] T009 [US1] Implement the 16 pipeline steps in tools/daily_automation.py — ordered sequence: (1) smoke_test.run, (2) load_settings via config.get_config, (3) habit_engine.process_daily_habits, (4) habit_engine.process_bad_habits, (5) streak_engine.apply_decay, (6) fitness_engine.aggregate_xp, (7) nutrition_engine.aggregate_xp, (8) financial_engine.aggregate_xp, (9) xp_engine.update_character_stats, (10) hp_engine.check_death, (11) rank_engine.check_rank_up, (12) avatar_renderer.update_avatar (conditional on rank change), (13) achievement_engine.check_all_achievements, (14) chart_renderer.update_character_chart, (15) snapshot_engine.take_snapshot, (16) quest_engine.process_all_quests
- [ ] T010 [US1] Add dual output to tools/daily_automation.py — per-step logger.info/error for structured stderr, print() summary block at end for stdout (GitHub Actions log capture)
- [ ] T011 [US1] Write tests/test_daily_automation.py — test full pipeline execution order with mocked engines, test fault tolerance (one engine raises, remaining steps still run), test idempotency (snapshot exists → per-engine no-ops), test smoke test failure aborts before processing, test summary output includes step counts

**Checkpoint**: Daily automation fully functional and testable independently.

---

## Phase 4: User Story 2 — Weekly Report & AI Integration (Priority: P1)

**Goal**: Weekly report calculating 7-day stat deltas, overdraft check, AI coaching briefing, AI quest generation, and quest completion processing.

**Independent Test**: Ensure 7 days of Daily Snapshots exist. Run `python tools/weekly_report.py --character-id <ID>`. Verify stat deltas correct, overdraft checked, coaching briefing generated, 3 quests created, completed quests processed, summary logged, AI_MONTHLY_SPEND incremented.

### Implementation for User Story 2

- [ ] T012 [US2] Implement weekly_report.py in tools/weekly_report.py — CLI entry point with argparse (--character-id). Step 1: call daily_automation.py to ensure today's snapshot exists (per clarification Q8). Then: query 7 days of snapshots, compute deltas (last - first per stat), check overdraft, call coaching_engine, call quest_generator, call quest_engine, log summary
- [ ] T013 [US2] Implement delta calculation in tools/weekly_report.py — query Daily Snapshots DB with filter Date >= (today-7), sort ascending. Delta = newest.field - oldest.field for each stat/HP/Gold/Coins. Handle <7 snapshots gracefully (deltas from available data, no crash)
- [ ] T014 [US2] Implement overdraft check in tools/weekly_report.py — call coin_engine.check_overdraft(), if negative balance call coin_engine.apply_overdraft_penalty() applying HP damage before rest of report
- [ ] T015 [US2] Implement AI integration in tools/weekly_report.py — call coaching_engine.generate_briefing() with rotating persona, call quest_generator.generate_quests() for 3 new quests, call quest_engine.process_all_quests() for completed quests. Check AI_MONTHLY_SPEND against OPENAI_MONTHLY_COST_CAP_USD first — skip AI sections with warning if cap reached. Increment AI_MONTHLY_SPEND after each AI call
- [ ] T016 [US2] Add report summary output to tools/weekly_report.py — print formatted summary (stat deltas, streaks active/broken, quests completed/generated, coaching persona, AI cost, overdraft status) to stdout + logger
- [ ] T017 [US2] Write tests/test_weekly_report.py — test delta calculation with 7 snapshots, test delta with <7 snapshots (no crash), test overdraft detection and penalty, test AI cost cap skips coaching/quests with warning, test AI failure doesn't crash report (graceful degradation), test daily_automation called first

**Checkpoint**: Weekly report fully functional. Both US1 and US2 work independently.

---

## Phase 5: User Story 3 — Monthly Automation (Priority: P2)

**Goal**: Monthly Gold settlement from budget surplus, Treasury row creation, and AI_MONTHLY_SPEND reset.

**Independent Test**: Create expense entries for previous month. Set AI_MONTHLY_SPEND to non-zero. Run `python tools/monthly_automation.py --character-id <ID>`. Verify Treasury row created, Gold credited, WIS XP awarded, AI_MONTHLY_SPEND reset to 0.

### Implementation for User Story 3

- [ ] T018 [US3] Implement monthly_automation.py in tools/monthly_automation.py — CLI entry point with argparse (--character-id). Steps: (1) smoke test, (2) load settings, (3) call financial_engine to calculate previous month surplus from Expense Log, (4) convert surplus to Gold via coin_engine (Gold = max(0, surplus) / GOLD_CONVERSION_RATE), (5) award WIS XP via xp_engine, (6) create Treasury row, (7) take monthly snapshot via snapshot_engine, (8) reset AI_MONTHLY_SPEND to 0 in Settings DB
- [ ] T019 [US3] Implement Treasury idempotency in tools/monthly_automation.py — query Treasury DB for Month (YYYY-MM) + Character before creating. If exists, log "already processed" and skip Treasury/Gold/XP steps. AI_MONTHLY_SPEND reset is always safe to re-run (idempotent by nature)
- [ ] T020 [US3] Add summary output to tools/monthly_automation.py — print surplus amount, Gold earned, WIS XP awarded, AI spend reset confirmation to stdout + logger
- [ ] T021 [US3] Write tests/test_monthly_automation.py — test surplus calculation and Gold conversion, test deficit produces no Gold (but Treasury row still created), test Treasury idempotency (duplicate row prevented), test AI_MONTHLY_SPEND reset to 0, test smoke test failure aborts, test monthly snapshot created with end-of-month state, test WIS XP awarded for financial discipline

**Checkpoint**: Monthly automation fully functional. All 3 automation scripts work independently.

---

## Phase 6: User Story 4 — GitHub Actions CI/CD (Priority: P2)

**Goal**: Four GitHub Actions workflow YAML files that schedule and execute all automation scripts with secrets injection.

**Independent Test**: Push workflow files. Verify tests.yml triggers on push. Manually trigger daily.yml via workflow_dispatch, verify it runs daily_automation.py with secrets.

### Implementation for User Story 4

- [ ] T022 [P] [US4] Create .github/workflows/daily.yml — cron `0 20 * * *`, workflow_dispatch, concurrency group daily-automation (cancel-in-progress: false), setup Python 3.10, pip install, run daily_automation.py with secrets as env vars
- [ ] T023 [P] [US4] Create .github/workflows/weekly.yml — cron `0 8 * * 0`, workflow_dispatch, concurrency group weekly-report, setup Python 3.10, pip install, run daily_automation.py THEN weekly_report.py sequentially, secrets as env vars
- [ ] T024 [P] [US4] Create .github/workflows/monthly.yml — cron `0 0 1 * *`, workflow_dispatch, concurrency group monthly-automation, setup Python 3.10, pip install, run monthly_automation.py with secrets as env vars
- [ ] T025 [P] [US4] Create .github/workflows/tests.yml — trigger on push (all branches) and pull_request (main), concurrency group tests-${{ github.ref }} (cancel-in-progress: true), setup Python 3.10, pip install, run pytest tests/ -v

**Checkpoint**: All 4 workflows in place. CI/CD layer complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 Validate all scripts work end-to-end by running quickstart.md steps locally
- [ ] T027 Verify idempotency: run daily_automation twice, confirm no duplicates in Activity Log, Snapshots, or any DB
- [ ] T028 Verify fault tolerance: mock one engine to raise, confirm remaining pipeline steps still execute
- [ ] T029 Run full pytest suite and confirm all tests pass: `python -m pytest tests/ -v`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001-T003)
- **US1 Daily (Phase 3)**: Depends on Phase 2 (T004-T007) — smoke_test + snapshot_engine required
- **US2 Weekly (Phase 4)**: Depends on Phase 2 + US1 (weekly calls daily_automation first)
- **US3 Monthly (Phase 5)**: Depends on Phase 2 only (uses snapshot_engine + smoke_test, independent of daily/weekly)
- **US4 GitHub Actions (Phase 6)**: Depends on US1+US2+US3 being implemented (workflows call the scripts)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational → no dependencies on other stories
- **US2 (P1)**: After Foundational + US1 → calls daily_automation.py as first step
- **US3 (P2)**: After Foundational → independent of US1/US2
- **US4 (P2)**: After US1+US2+US3 → workflow files reference all scripts

### Within Each User Story

- Engine composition before output formatting
- Idempotency logic integrated with main flow (not separate)
- Tests after implementation (tests validate working code)

### Parallel Opportunities

- T002 + T003: conftest.py and workflow dir can be created in parallel
- T004 + T005: smoke_test and snapshot_engine are independent modules
- T006 + T007: test files for smoke_test and snapshot_engine are independent
- US3 can run in parallel with US1 (no dependency between monthly and daily)
- T022 + T023 + T024 + T025: all 4 workflow YAML files are independent

---

## Parallel Example: User Story 4 (GitHub Actions)

```bash
# Launch all workflow YAML files together (all independent):
Task: "Create .github/workflows/daily.yml"
Task: "Create .github/workflows/weekly.yml"
Task: "Create .github/workflows/monthly.yml"
Task: "Create .github/workflows/tests.yml"
```

## Parallel Example: Foundational Phase

```bash
# Launch smoke test and snapshot engine together (independent modules):
Task: "Implement smoke_test.py in tools/smoke_test.py"
Task: "Implement snapshot_engine.py in tools/snapshot_engine.py"

# Launch their tests together (independent test files):
Task: "Write tests/test_smoke_test.py"
Task: "Write tests/test_snapshot_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007) — smoke_test + snapshot_engine
3. Complete Phase 3: US1 Daily Automation (T008-T011)
4. **STOP and VALIDATE**: Run `python tools/daily_automation.py --character-id <ID>` twice. Verify processing + idempotency.
5. Daily pipeline is operational — the heartbeat of the system works.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 Daily Automation → Test independently → **MVP! Daily pipeline runs**
3. US2 Weekly Report → Test independently → Weekly reports with AI coaching
4. US3 Monthly Automation → Test independently → Monthly Gold settlement
5. US4 GitHub Actions → Push workflows → Fully automated, hands-off operation
6. Polish → End-to-end validation → Production-ready

### Single Developer Strategy

Work sequentially: Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → Polish.
Within each phase, exploit [P] parallel tasks where marked.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Engine imports will be thin wrappers initially if Phase 1-6 engines aren't built yet — daily_automation.py should handle ImportError gracefully during development
