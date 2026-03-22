# Feature Specification: End-to-End Verification

**Feature Branch**: `009-e2e-verification`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Phase 9 of V5 Implementation Plan — End-to-End Verification (Automated Tests, Integration Smoke Tests, Manual User Verification)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Automated Unit Test Suite (Priority: P1)

The developer runs the full automated test suite and every engine in the system passes its unit tests. The test suite covers all core engines: XP (non-linear curve, level roundtrip, class bonus), HP (damage, death at 0, respawn resets, hotel recovery), Coin (overdraft detection, market purchase, hotel cost), Streak (increment, reset, decay penalty, tier advancement), Financial (surplus calculation, Gold conversion, breach penalty), Fitness (Epley accuracy, RPE weighting, overload detection), Nutrition (symmetric adherence, streak multiplier, negative XP on overshoot), Loot Box (weight distribution ±5% over 10k samples, pity timer), and Chart Renderer (output exists, correct dimensions, 5 axes). Each test file mirrors its engine file and uses mock Notion responses. The suite runs on every push/PR via the CI pipeline.

**Why this priority**: Unit tests are the foundation of system confidence. If any engine has a regression, every downstream feature (daily automation, weekly reports, monthly settlement) produces wrong results. The test suite is the single fastest way to verify correctness across all 9+ engines. P1 because without passing unit tests, no other verification step is meaningful.

**Independent Test**: Run the full test suite from the command line. Every test should pass. If any test fails, the specific engine and assertion that failed is immediately visible. No external dependencies needed — tests use mocked Notion responses.

**Acceptance Scenarios**:

1. **Given** all engine source files exist in `tools/`, **When** the full test suite runs, **Then** all tests pass with 0 failures and 0 errors
2. **Given** the XP engine test file, **When** tests execute, **Then** non-linear curve calculations are verified, `level_from_xp` roundtrips correctly, and class bonuses apply correctly
3. **Given** the HP engine test file, **When** tests execute, **Then** damage application, death trigger at HP = 0, respawn reset to STARTING_HP, and hotel recovery amounts are verified
4. **Given** the Coin engine test file, **When** tests execute, **Then** overdraft detection, market purchase deductions, and hotel check-in costs are verified
5. **Given** the Streak engine test file, **When** tests execute, **Then** increment, reset, decay penalty, and tier advancement (3→7→14→30→60→100 day thresholds) are verified
6. **Given** the Loot Box test file, **When** 10,000 samples are drawn, **Then** Common/Rare/Epic/Legendary weights are within ±5% of configured weights, and pity timer triggers after threshold
7. **Given** the Chart Renderer test file, **When** a radar chart is generated, **Then** the output file exists, has correct dimensions, and renders 5 stat axes (STR/INT/WIS/VIT/CHA)

---

### User Story 2 — Integration Smoke Tests (Priority: P1)

The developer runs a structured 15-step integration test sequence that validates every major system interaction end-to-end against a live Notion workspace. The sequence starts with environment validation (smoke test), proceeds through database creation, seed data, onboarding, and then exercises every game mechanic: good habit check-in → XP increase, bad habit → HP decrease → death event, hotel check-in → HP recovery, expense tracking → financial surplus → Gold, workout logging → fitness 1RM + STR XP, meal logging → nutrition adherence + VIT XP, weekly report → AI briefing + quests, daily automation idempotency, radar chart generation, and CI pipeline validation. Each step builds on the previous, creating a complete game lifecycle from zero to weekly cycle.

**Why this priority**: Unit tests verify individual engines in isolation; integration tests verify they work together through the Notion API with real data. A passing unit test suite with a broken integration (wrong DB schema, missing relations, API changes) gives false confidence. Co-P1 with unit tests because both are needed for full verification.

**Independent Test**: Follow the 15-step sequence in order on a test Notion workspace. Each step has a clear verification checkpoint. A failure at any step identifies exactly which system boundary is broken.

**Acceptance Scenarios**:

1. **Given** environment variables are configured, **When** the smoke test runs, **Then** all required checks pass (env vars present, Notion API reachable, databases exist)
2. **Given** a blank Notion workspace, **When** `create_databases.py` runs, **Then** all databases are created with correct schemas and relations
3. **Given** databases exist, **When** `seed_data.py` runs, **Then** seed data is visible in Notion (sample habits, expenses, meals, workouts)
4. **Given** seed data exists, **When** `onboarding.py` runs, **Then** a character is created with identity questions, default habits, vision board, and dashboard
5. **Given** a character with good habits, **When** a habit is checked in and `daily_automation.py` runs, **Then** an Activity Log entry exists and character XP increases
6. **Given** a character with bad habits, **When** a bad habit is triggered, **Then** HP decreases, and if HP reaches 0 a death event fires
7. **Given** a dead character, **When** a hotel check-in is performed, **Then** HP restores by the hotel tier amount and coins are deducted
8. **Given** expense entries exist, **When** `financial_engine` runs, **Then** surplus is calculated correctly and Gold is converted at the configured rate
9. **Given** workout entries in Set Log, **When** `fitness_engine` runs, **Then** 1RM is calculated (Epley formula) and STR XP is awarded
10. **Given** meal entries in Meal Log, **When** `nutrition_engine` runs, **Then** adherence score is calculated and VIT XP is awarded
11. **Given** a fully populated week, **When** `weekly_report.py` runs, **Then** overdraft check executes, AI coaching briefing is generated, and 3 quest JSONs are created
12. **Given** daily automation has already run today, **When** it runs again, **Then** no duplicate entries are created in any database (idempotent)
13. **Given** character stats exist, **When** radar chart generation runs, **Then** the chart image is generated and visible in the Character page
14. **Given** code is pushed to the repository, **When** the CI pipeline triggers, **Then** the full test suite runs and passes
15. **Given** the daily workflow is configured, **When** triggered manually via the CI interface, **Then** it completes without errors

---

### User Story 3 — Manual User Verification Checklist (Priority: P2)

After all automated and integration tests pass, the player performs a hands-on walkthrough of the complete game experience. This manual verification covers the subjective and experiential aspects that automated tests cannot capture: does the dashboard look right, does the game feel responsive, are AI coaching briefings useful and non-sycophantic, does the death/respawn cycle feel punishing but fair, do loot box rewards feel rewarding. The player enters a full day of real data (habits, meals, workout, expenses, journal), runs the daily automation, reviews the results, triggers edge cases (death, respawn, loot box), and confirms the weekly AI briefing contains real numbers and actionable coaching.

**Why this priority**: Automated tests verify correctness; manual verification confirms the experience is enjoyable and the system is ready for daily use. P2 because the system is technically correct after P1 stories — manual verification adds confidence in usability and game feel, but doesn't block functionality.

**Independent Test**: Open the Notion Daily Dashboard. Spend 15-30 minutes entering realistic data and triggering all game mechanics. Use the manual verification checklist as a guide. Every item should feel correct and complete.

**Acceptance Scenarios**:

1. **Given** the dashboard is set up, **When** the player opens it, **Then** all 7 panels display correctly with current data
2. **Given** a full day of habit/meal/expense/journal data, **When** daily automation runs, **Then** stats, HP, coins, level, and rank update correctly and are visible in the dashboard
3. **Given** the radar chart has been generated, **When** the player views it, **Then** the 5 stat axes show correct proportions relative to each other
4. **Given** the player triggers bad habits repeatedly, **When** HP reaches 0, **Then** a "You Died!" event is visible and the configured death penalty text appears
5. **Given** a dead character, **When** the player performs a hotel check-in, **Then** HP restores by the hotel tier amount and coins are deducted
6. **Given** coins are available, **When** the player pulls a loot box, **Then** a reward appears in the inventory with the correct rarity tier
7. **Given** the weekly report has run, **When** the player reads the AI coaching briefing, **Then** the briefing contains real stat numbers (not placeholder text), references the player's actual performance, and uses a non-sycophantic tone with actionable suggestions
8. **Given** a full week of gameplay data, **When** the player reviews the overall game experience, **Then** the system feels responsive, the death cycle is punishing but fair, and loot rewards feel satisfying

---

### Edge Cases

- What happens when a test file references an engine function that was renamed during development? Each test file should import from the canonical engine module. If an import fails, the test runner reports the broken import immediately — not a silent skip.
- What happens when integration tests are run against a Notion workspace with pre-existing data from a previous test run? Each integration step should either clean up after itself or be idempotent. The seed data step should check for existing records before creating duplicates.
- What happens when the CI pipeline runs tests but the Notion API is unreachable? Unit tests use mocked responses and should pass regardless. Integration tests (if run in CI) should skip with a clear "NOTION_TOKEN not configured" message rather than failing cryptically.
- What happens when the loot box statistical test fails due to randomness? The ±5% tolerance over 10k samples gives >99.9% statistical confidence. If it still fails, re-run once — two consecutive failures indicate a real bug.
- What happens when the manual verification reveals a UX issue (e.g., dashboard layout is confusing)? Log the issue as a follow-up item. Manual verification does not block release — it generates improvement tickets for future iterations.
- What happens when an AI coaching briefing is sycophantic or contains hallucinated numbers? The prompt engineering in `coaching_engine` should enforce structured output with real stat references. If the briefing quality is poor, it's a prompt engineering fix — not a Phase 9 scope item.

## Requirements *(mandatory)*

### Functional Requirements

**Automated Unit Tests**

- **FR-001**: System MUST provide unit test files for all core engines: xp_engine, hp_engine, coin_engine, streak_engine, financial_engine, fitness_engine, nutrition_engine, loot_box, chart_renderer
- **FR-002**: Each test file MUST mirror its engine file naming convention (e.g., `test_xp_engine.py` tests `xp_engine.py`)
- **FR-003**: All unit tests MUST use mock Notion API responses — no live API calls during unit testing
- **FR-004**: The XP engine tests MUST verify: non-linear curve calculation, `level_from_xp` roundtrip accuracy, and class bonus application
- **FR-005**: The HP engine tests MUST verify: damage application, death trigger at HP ≤ 0, respawn reset to STARTING_HP, and hotel recovery by tier
- **FR-006**: The Coin engine tests MUST verify: overdraft detection (balance < 0), market purchase deduction, and hotel check-in cost deduction
- **FR-007**: The Streak engine tests MUST verify: streak increment, reset on miss, decay penalty calculation, and tier advancement at thresholds (3, 7, 14, 30, 60, 100 days)
- **FR-008**: The Financial engine tests MUST verify: surplus calculation (income - expenses), Gold conversion at configured rate, and budget breach XP penalty
- **FR-009**: The Fitness engine tests MUST verify: Epley 1RM formula accuracy, RPE-weighted XP calculation, and progressive overload detection over 14-day window
- **FR-010**: The Nutrition engine tests MUST verify: symmetric adherence scoring (under/over target penalized equally), streak multiplier application, and negative XP on significant overshoot
- **FR-011**: The Loot Box tests MUST verify: weight distribution within ±5% of configured weights over 10,000 samples, and pity timer activation after configured threshold
- **FR-012**: The Chart Renderer tests MUST verify: output file creation, correct image dimensions, and 5-axis radar chart (STR/INT/WIS/VIT/CHA)

**Integration Smoke Tests**

- **FR-013**: System MUST provide a structured 15-step integration test sequence documented as a runnable checklist
- **FR-014**: Each integration step MUST have a clear pass/fail verification checkpoint
- **FR-015**: Integration steps MUST be ordered by dependency: environment → databases → seed data → onboarding → game mechanics → automation → CI
- **FR-016**: Integration tests that require live Notion API MUST skip gracefully with informative messages when credentials are unavailable

**Manual User Verification**

- **FR-017**: System MUST provide a manual verification checklist covering: dashboard display, full-day data entry, daily automation results, radar chart accuracy, death/respawn cycle, loot box pull, and AI coaching briefing quality
- **FR-018**: Each manual verification item MUST have explicit pass/fail criteria (not subjective "looks good")
- **FR-019**: Manual verification results MUST be recordable (checklist with checkbox + notes field per item)

**CI Pipeline**

- **FR-020**: The CI pipeline MUST run the full unit test suite on every push and pull request
- **FR-021**: The CI pipeline MUST report test failures clearly with the failing test name, assertion, and engine file
- **FR-022**: The CI pipeline MUST block merging of code that fails any unit test

### Key Entities

- **Test Suite**: The collection of all unit test files — one per engine, using mock fixtures. Runs locally and in CI. Reports pass/fail per test case.
- **Integration Checklist**: A 15-step ordered sequence of verification actions that exercise the full system against a live Notion workspace. Each step has a checkpoint and builds on previous steps.
- **Manual Verification Checklist**: An 8-item subjective + objective walkthrough that the player completes after automated tests pass. Captures both correctness and experience quality.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unit tests pass across all 9 engine test files with 0 failures and 0 errors
- **SC-002**: All 15 integration smoke test steps pass in sequence on a test Notion workspace
- **SC-003**: All 8 manual verification checklist items are completed and marked as pass
- **SC-004**: The CI pipeline catches test failures on push/PR and blocks merging — verified by intentionally breaking a test, confirming the pipeline fails, then reverting
- **SC-005**: The loot box statistical test passes on 3 consecutive runs (ruling out random flakiness)
- **SC-006**: Running daily automation twice produces zero duplicate records across all databases — verified by querying Activity Log, Daily Snapshots, and Streak Tracker counts before and after
- **SC-007**: The full unit test suite completes in under 30 seconds (no slow network calls — all mocked)
- **SC-008**: Every engine file in `tools/` that contains game logic (functions that calculate values or modify game state — xp_engine, hp_engine, coin_engine, streak_engine, habit_engine, fitness_engine, nutrition_engine, financial_engine, quest_engine, coaching_engine, rank_engine, achievement_engine, snapshot_engine, chart_renderer, avatar_renderer, loot_engine) has a corresponding test file in `tests/`. Infrastructure files (logger.py, notion_client.py, config.py) are tested implicitly via engine tests

## Assumptions

- Phases 1-8 are complete: all engines exist and are functional, all databases are created, onboarding and dashboard are operational, automation workflows run correctly
- The `conftest.py` file provides shared mock Notion fixtures (mock_notion_client, mock_character_page, mock_settings) — established in Phase 7
- All engine functions are importable from `tools/` (Python package structure with `__init__.py` if needed)
- The test Notion workspace for integration tests is separate from production (to avoid data pollution). Each integration test sequence uses idempotency (each step checks for existing data before creating) so the same workspace can be re-used across runs
- GitHub Actions `tests.yml` workflow exists from Phase 7 and runs pytest on push/PR
- `seed_data.py` exists from Phase 1 and creates sample data for integration testing
- The AI coaching briefing quality check in manual verification is subjective but guided by explicit criteria (real numbers, non-sycophantic tone, actionable suggestions)
- The loot box ±5% tolerance means ±5 percentage points: if configured weight for Common is 70%, acceptable range is 65%-75%. Over 10,000 samples, this provides >99% statistical confidence that distribution matches weights

## Scope Boundaries

**In scope**: Unit test files for 9 engines, integration smoke test checklist (15 steps), manual user verification checklist (8 items), CI pipeline validation, idempotency verification, test documentation

**Out of scope**: Performance/load testing (single-player system), security penetration testing, automated UI testing (Notion is the UI — no browser automation), test data cleanup automation, code coverage metrics enforcement, cross-browser testing, accessibility testing of Notion pages
