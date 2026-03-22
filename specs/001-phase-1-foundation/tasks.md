# Tasks: Phase 1 Foundation

**Input**: Design documents from `/specs/001-phase-1-foundation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — the spec and constitution require pytest coverage for all tools.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and shared utilities

- [ ] T001 Create project directory structure: `tools/`, `tests/`, `workflows/`, `.github/workflows/`, `assets/frames/`, `assets/icons/`, `assets/backgrounds/`, `assets/charts/`
- [ ] T002 Initialize Python project with `requirements.txt` containing `notion-client`, `python-dotenv`, `pytest`
- [ ] T003 Create `.env.example` with `NOTION_API_KEY`, `NOTION_PARENT_PAGE_ID`, `OPENAI_API_KEY` placeholders
- [ ] T004 [P] Create `.gitignore` with `.env`, `credentials.json`, `token.json`, `.tmp/`, `__pycache__/`, `.automation.lock`, `db_ids.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement structured logger in `tools/logger.py` — `get_logger(name)` returning a logger with timestamps, severity level, and module name in consistent format
- [ ] T006 Implement config module in `tools/config.py` — all game balance constants as Python defaults (LEVEL_BASE_XP, STARTING_HP, STREAK_TIERS, HOTEL_TIERS, LOOT_WEIGHTS, RANK_THRESHOLDS, MOOD_TYPES, DIFFICULTY_REWARDS, DEFAULT_HABIT_XP, DEFAULT_BAD_HABIT_HP, OPENAI settings, etc.) plus `load_settings_from_notion(notion_client, settings_db_id)` that reads overrides from Notion Settings DB and returns merged config
- [ ] T007 Implement Notion API wrapper in `tools/notion_client.py` — `get_client()`, `create_database()`, `query_database()` (auto-pagination), `create_page()`, `update_page()`, `get_page()`, `delete_page()` with exponential backoff + jitter on 429 responses, max 3 req/sec, max 3 retries. Include lock file utilities: `acquire_lock(module)`, `release_lock()`, `check_lock()` using `.automation.lock`
- [ ] T008 [P] Create shared test fixtures in `tests/conftest.py` — mock Notion client, mock API responses for databases/pages/queries, mock Settings DB responses, temp `.env` fixture

**Checkpoint**: Foundation ready — logger, config, Notion client, and test infrastructure operational

---

## Phase 3: User Story 1 — Configurable Game Balance (Priority: P1) MVP

**Goal**: Player can change game balance values in Notion Settings DB and have them take effect on next automation run

**Independent Test**: Change a value in Notion Settings, run config loader, verify the overridden value is returned instead of the default

### Tests for User Story 1

- [ ] T009 [P] [US1] Write tests in `tests/test_config.py` — test default values load correctly, test Settings DB override replaces defaults, test invalid value in Settings DB falls back to default with warning, test missing Settings DB falls back to all defaults, test mid-run config change picked up on next load

### Implementation for User Story 1

- [ ] T010 [US1] Verify `tools/config.py` handles all US1 acceptance scenarios: Notion override, fallback on empty/unreachable, invalid type handling (log warning, use default), config refresh on each load call

**Checkpoint**: Config system complete — player can tune any balance value from Notion

---

## Phase 4: User Story 2 — Complete Game Workspace Setup (Priority: P2)

**Goal**: Single command creates all 33 Notion databases with properties, relations, buttons, and stores ID mapping

**Independent Test**: Run `create_databases.py`, inspect Notion workspace for all 33 databases with correct schemas

### Tests for User Story 2

- [ ] T011 [P] [US2] Write tests in `tests/test_create_dbs.py` — test all 33 databases created with correct properties, test two-pass (create then link relations), test idempotency (re-run skips existing by ID), test ID fallback to title match when stored ID invalid, test `db_ids.json` written correctly, test buttons added to correct databases

### Implementation for User Story 2

- [ ] T012 [US2] Implement database schema definitions in `tools/create_databases.py` — define all 33 database schemas as data structures: property names, types, select options, formula strings. Schemas for: Character, Activity Log, Good Habit, Bad Habit, Skill/Area, Streak Tracker, Goal, Brain Dump, To-do Difficulty, Market, My Cart, Hotel, Black Market, Overdraft Penalty, Level Setting, Settings, Quests, Daily Journal, Mood, Onboarding Identity, Vision Board Items, Budget Categories, Expense Log, Treasury, Exercise Dictionary, Workout Sessions, Set Log, Meal Log, Ingredients Library, Loot Box Inventory, Achievements, Player Achievements, Daily Snapshots
- [ ] T013 [US2] Implement Pass 1 in `tools/create_databases.py` — `create_all_databases(parent_page_id)`: create each database with non-relation properties (Title, Number, Select, Checkbox, Date, Text, Files, Formula, Status). Write each ID to `db_ids.json` after creation. Skip if ID already exists and is valid, fall back to title match
- [ ] T014 [US2] Implement Pass 2 in `tools/create_databases.py` — `link_all_relations()`: add Relation and Rollup properties referencing other databases by ID from `db_ids.json`. Add button properties to applicable databases (Good Habit, Bad Habit, Goal, Brain Dump, Market, Hotel, Black Market)
- [ ] T015 [US2] Implement CLI entry point in `tools/create_databases.py` — `main()` with `--parent-page-id` argument (or from `.env`), JSON output summary (`created`, `skipped`, `relations_linked`, `buttons_added`), exit code 0/1

**Checkpoint**: 33 databases exist in Notion with all schemas, relations, and buttons

---

## Phase 5: User Story 3 — Pre-Flight System Check (Priority: P3)

**Goal**: Standalone readiness check validates credentials, Notion connectivity, and database existence with clear pass/fail per check

**Independent Test**: Run `smoke_test.py` with valid config → all pass. Remove API key → specific failure reported

### Tests for User Story 3

- [ ] T016 [P] [US3] Write tests in `tests/test_smoke_test.py` — test all checks pass with valid config, test missing NOTION_API_KEY identified by name, test missing NOTION_PARENT_PAGE_ID identified, test Notion connectivity failure reported, test missing database identified by name, test OPENAI_API_KEY validated, test JSON output format, test exit code 0 on pass / 1 on fail

### Implementation for User Story 3

- [ ] T017 [US3] Implement smoke test in `tools/smoke_test.py` — check `.env` for NOTION_API_KEY, NOTION_PARENT_PAGE_ID, OPENAI_API_KEY; test Notion connectivity via `users.me()`; test parent page accessible; verify all 33 databases exist (from `db_ids.json`); verify Settings DB readable. JSON output with per-check pass/fail and messages. Exit code 0/1. Complete within 30 seconds

**Checkpoint**: Pre-flight check catches all missing dependencies before automation runs

---

## Phase 6: User Story 4 — Resilient Automation Connectivity (Priority: P4)

**Goal**: Notion client automatically retries on rate-limit and transient failures without manual intervention

**Independent Test**: Simulate 429 response, verify automatic retry with backoff; simulate persistent failure, verify clean exit with logged error

### Tests for User Story 4

- [ ] T018 [P] [US4] Write tests in `tests/test_notion_client.py` — test exponential backoff on 429, test jitter applied, test max 3 retries then fail, test max 3 req/sec rate limiting, test successful retry logged, test permanent failure logged with reason, test pagination auto-follows, test lock file creation/detection/cleanup

### Implementation for User Story 4

- [ ] T019 [US4] Verify `tools/notion_client.py` handles all US4 scenarios: rate-limit retry with exponential backoff + jitter, sustained 3 req/sec cap, max 3 retries with clean error on exhaustion, retry events logged, lock file acquire/release/stale detection

**Checkpoint**: All Notion operations resilient to transient failures

---

## Phase 7: User Story 5 — Pre-Populated Reference Data (Priority: P5)

**Goal**: Single command seeds all reference data (~160 rows) into existing databases with title-based deduplication

**Independent Test**: Run `seed_data.py` after `create_databases.py`, verify expected row counts. Re-run, verify zero duplicates

### Tests for User Story 5

- [ ] T020 [P] [US5] Write tests in `tests/test_seed_data.py` — test all seed categories created (exercises, achievements, habits, hotels, difficulties, moods, skills, character, settings, vision board), test expected row counts, test title-based dedup on re-run, test player custom data not deleted, test failure when required database missing, test JSON output format

### Implementation for User Story 5

- [ ] T021 [US5] Define all seed data in `tools/seed_data.py` — 25+ exercises, 8+ budget categories, 40+ ingredients with macros, 43 achievement definitions, 5 default good habits (Exercise/STR, Read 30min/INT, Track Expenses/WIS, Eat Clean/VIT, Social Interaction/CHA), 3 default bad habits, 3 hotel tiers with prices/HP, 3 difficulty levels with XP/coins, 7 mood types, 7 skills mapped to stats, 1 default Character (Starting HP=1000), 1 default Settings row (all config defaults), 8 vision board categories
- [ ] T022 [US5] Implement seeding logic in `tools/seed_data.py` — `seed_all(db_ids)`: for each database, query existing rows by title, skip matches, create missing rows. JSON output (`seeded` counts, `skipped` counts, `total_created`, `total_skipped`). Exit 1 if any required database missing from `db_ids.json`

**Checkpoint**: Notion workspace fully populated and ready for play

---

## Phase 8: User Story 6 — Schema Migration Path (Priority: P6)

**Goal**: Versioned, ordered schema migrations applied exactly once, tracked in `migrations.json`

**Independent Test**: Define a sample migration, run it, verify schema changed and migration recorded. Re-run, verify skipped

### Tests for User Story 6

- [ ] T023 [P] [US6] Write tests in `tests/test_migrate.py` — test migration applied and recorded, test already-applied migration skipped, test multiple pending migrations applied in order, test failed migration not recorded (allows retry), test migration referencing missing database fails cleanly, test JSON output format

### Implementation for User Story 6

- [ ] T024 [US6] Implement migration runner in `tools/migrate.py` — read `migrations.json` for applied list, scan migration definitions for pending, apply each in order (add property, rename property, add database), record each successful migration with timestamp, skip failed (do not record). JSON output (`applied`, `skipped`, `failed`, `pending`). Exit 0/1
- [ ] T025 [US6] Create initial `migrations.json` with empty applied list. Create sample migration definition demonstrating the format

**Checkpoint**: Schema evolution path available from day one

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Workflow documentation and end-to-end validation

- [ ] T026 [P] Create `workflows/setup-notion.md` SOP — step-by-step Notion integration setup, parent page creation, `.env` configuration, running create_databases + seed_data + smoke_test
- [ ] T027 [P] Create `workflows/onboarding.md` SOP — character creation flow, identity setup, death penalty definition
- [ ] T028 Run full quickstart.md validation — execute all steps from `specs/001-phase-1-foundation/quickstart.md` end-to-end, verify all success criteria (SC-001 through SC-009)
- [ ] T029 Run `pytest tests/ -v` and verify all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 Config (Phase 3)**: Depends on Phase 2
- **US2 Database Creation (Phase 4)**: Depends on Phase 2
- **US3 Smoke Test (Phase 5)**: Depends on Phase 2 + US2 (needs db_ids.json)
- **US4 Resilient Connectivity (Phase 6)**: Depends on Phase 2
- **US5 Seed Data (Phase 7)**: Depends on US2 (databases must exist)
- **US6 Migration Runner (Phase 8)**: Depends on Phase 2 + US2 (needs db_ids.json)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 2 (Foundation)
  ├── US1 (Config) ────────────────────────────────┐
  ├── US2 (Database Creation) ─┬── US3 (Smoke Test)├── Phase 9 (Polish)
  ├── US4 (Resilient Conn.)    ├── US5 (Seed Data) │
  └────────────────────────────┴── US6 (Migration) ┘
```

- US1 and US4 can run in parallel with US2
- US3, US5, US6 depend on US2 (need databases to exist)
- US3, US5, US6 can run in parallel with each other after US2

### Parallel Opportunities

- T003 + T004: Setup tasks on different files
- T009 + T011 + T016 + T018 + T020 + T023: All test files can be written in parallel
- US1 + US2 + US4: Can be developed in parallel after Phase 2
- US3 + US5 + US6: Can be developed in parallel after US2

---

## Parallel Example: After Phase 2

```bash
# These three user stories can start simultaneously:
Agent 1: US1 — Config system (T009, T010)
Agent 2: US2 — Database creation (T011-T015)
Agent 3: US4 — Resilient connectivity (T018-T019)

# After US2 completes, these three can start simultaneously:
Agent 1: US3 — Smoke test (T016-T017)
Agent 2: US5 — Seed data (T020-T022)
Agent 3: US6 — Migration runner (T023-T025)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008)
3. Complete US1: Config (T009-T010)
4. Complete US2: Database Creation (T011-T015)
5. **STOP and VALIDATE**: 33 databases in Notion, configurable settings
6. This alone is a functional workspace skeleton

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. + US1 + US2 → Workspace skeleton with config (MVP!)
3. + US3 → Pre-flight safety gate
4. + US4 → Resilient automation
5. + US5 → Ready-to-play workspace
6. + US6 → Future-proofed with migrations
7. Polish → Documented and validated

---

## Notes

- All tools output JSON to stdout for machine-readable results
- All tools use `tools/logger.py` for structured logging to stderr
- `db_ids.json` is the shared state between create_databases, smoke_test, seed_data, and migrate
- `.automation.lock` prevents concurrent runs across all automation entry points
- Commit after each task or logical group
