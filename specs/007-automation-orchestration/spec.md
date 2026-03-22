# Feature Specification: Automation Orchestration

**Feature Branch**: `007-automation-orchestration`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Phase 7 of V5 Implementation Plan — Daily/Weekly/Monthly Automation + GitHub Actions CI/CD

## Clarifications

### Session 2026-03-22

- Q: What is the daily automation idempotency mechanism? → A: Per-engine idempotency — each engine independently skips already-done work (Activity Log dedup, streak already-processed checks, snapshot date uniqueness). No pipeline-level gate. The pipeline always runs all steps; each engine is individually idempotent.
- Q: Which Phase 6 function names does weekly report call? → A: `coaching_engine.generate_briefing()` and `quest_generator.generate_quests()` (not the V5 plan names `openai_coach.*`). Quest completion uses `quest_engine.process_all_quests()`.
- Q: What does monthly automation reset? → A: AI_MONTHLY_SPEND → 0 in Settings DB. Financial surplus → Gold conversion via `financial_engine` + `coin_engine`. Monthly snapshot row in Daily Snapshots DB.
- Q: Should GitHub Actions workflows use secrets for Notion/OpenAI keys? → A: Yes — `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID`, `OPENAI_API_KEY`, and `CHARACTER_ID` stored as GitHub repository secrets.
- Q: What happens if daily automation runs twice on the same day? → A: Idempotent — each engine independently skips already-completed work. Snapshot engine checks date uniqueness. Second run processes all steps but each engine no-ops. No duplicates.
- Q: Should quest completion run daily or weekly? → A: Daily — add `quest_engine.process_all_quests()` to the daily pipeline after XP aggregation so players get immediate XP/Gold when marking quests complete.
- Q: What timezone are cron schedules in? → A: Cairo (UTC+2). Daily 10 PM local = `0 20 * * *` UTC. Weekly Sun 10 AM local = `0 8 * * 0` UTC. Monthly 1st midnight ≈ `0 0 1 * *` UTC (2 AM Cairo).
- Q: Should weekly.yml run daily_automation.py first? → A: Yes — weekly.yml calls daily_automation.py then weekly_report.py sequentially to guarantee today's snapshot exists for delta calculation.
- Q: Where should automation output go? → A: Both stdout (for GitHub Actions logs) and logger.py structured logging (for persistent debugging). All summaries and reports use both channels.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Daily Automation Pipeline (Priority: P1)

Every night at 10 PM, a GitHub Actions cron job triggers the daily automation script. The script runs a 16-step idempotent pipeline: pre-flight smoke test, settings load, good habit processing, bad habit HP damage, streak decay for missed habits, domain XP aggregation from fitness/nutrition/financial engines, character stat recalculation, death check, rank check with avatar update, achievement evaluation, radar chart regeneration, daily snapshot capture, and quest completion processing. The pipeline always runs all steps; each engine is individually idempotent (per-engine idempotency, not pipeline-level gating).

**Why this priority**: The daily automation is the heartbeat of the entire system. Without it, no habits are processed, no streaks decay, no XP is aggregated, no death checks fire, and no snapshots are taken. Every other automation (weekly, monthly) depends on daily snapshots existing. This is the single most critical piece of the orchestration layer.

**Independent Test**: Manually create some Activity Log entries (good/bad habits), Set Log entries (fitness), and Meal Log entries (nutrition) for today. Run `python tools/daily_automation.py --character-id <ID>`. Verify: habits processed, streaks updated, XP aggregated to Character DB, HP adjusted, snapshot row created in Daily Snapshots DB with all stat values. Run again — verify no duplicate processing.

**Acceptance Scenarios**:

1. **Given** today has no Daily Snapshot and there are unchecked good habits, **When** daily automation runs, **Then** good habits are processed, XP Activity Log entries created, streak tiers updated, character stats recalculated, radar chart regenerated, and a Daily Snapshot row is created with all current stat values
2. **Given** today has no Daily Snapshot and there are bad habit check-ins, **When** daily automation runs, **Then** HP damage is applied via hp_engine, and if HP reaches 0, death event is triggered
3. **Given** today's Daily Snapshot already exists, **When** daily automation runs again, **Then** the pipeline runs all steps but each engine independently skips already-completed work (per-engine idempotency). No duplicate data is created. Snapshot engine detects existing snapshot and skips.
4. **Given** the smoke test fails (missing env vars, Notion API unreachable), **When** daily automation runs, **Then** the script exits immediately with a clear error message before any processing begins

---

### User Story 2 — Weekly Report & AI Integration (Priority: P1)

Every Sunday at 10 AM, a GitHub Actions cron job triggers the weekly report script. The script queries the last 7 days of Daily Snapshots to calculate stat deltas, checks for coin overdraft and applies penalties if needed, queries active/broken streaks and quest completion rates, calls the AI coaching engine for a personalized weekly briefing (rotating persona), calls the AI quest generator to create 3 new quests, processes any completed quests via quest_engine, and logs the full weekly report. The report aggregates the week's performance into a single summary including XP gained, streaks maintained/broken, quests completed, HP changes, and AI cost.

**Why this priority**: The weekly report ties together all game mechanics into a coherent weekly cycle. It's the integration point for Phase 6's AI features (coaching + quest generation) and Phase 2's overdraft penalties. Without weekly automation, coaching briefings and AI quests would need to be triggered manually, and overdraft penalties would never fire. Co-P1 with daily because the weekly depends on daily snapshots existing.

**Independent Test**: Ensure at least 7 days of Daily Snapshots exist. Run `python tools/weekly_report.py --character-id <ID>`. Verify: stat deltas calculated correctly, overdraft check performed, coaching briefing generated with rotating persona, 3 new AI quests created in Quests DB, any completed quests processed, report summary logged. Check AI_MONTHLY_SPEND was incremented in Settings DB.

**Acceptance Scenarios**:

1. **Given** 7 days of Daily Snapshots exist and player's coin balance is positive, **When** weekly report runs, **Then** stat deltas are calculated, coaching briefing is generated, 3 AI quests are created, completed quests are processed, and a summary report is logged
2. **Given** player's coin balance is negative (overdrawn), **When** weekly report runs, **Then** `coin_engine.check_overdraft()` detects the overdraft and `coin_engine.apply_overdraft_penalty()` applies HP damage before continuing with the rest of the report
3. **Given** the AI monthly cost cap has been reached, **When** weekly report runs, **Then** coaching briefing and quest generation are skipped with warnings, but the rest of the report (deltas, overdraft check, quest completion) still executes
4. **Given** fewer than 7 Daily Snapshots exist (new player or gaps), **When** weekly report runs, **Then** deltas are calculated from whatever snapshots are available, no crash from missing data

---

### User Story 3 — Monthly Automation (Priority: P2)

On the 1st of each month at midnight, a GitHub Actions cron job triggers the monthly automation script. The script performs three operations: (1) calls `financial_engine` to calculate the previous month's budget surplus and converts surplus to Gold via `coin_engine`, creating a Treasury row with income/expenses/surplus/Gold earned/WIS XP; (2) takes a monthly-level snapshot summarizing the month's totals; (3) resets AI_MONTHLY_SPEND to 0 in Settings DB, enabling AI coaching and quest generation for the new month.

**Why this priority**: Monthly automation is lower frequency and less critical than daily/weekly — the game loop functions without it. Gold settlement from financial surplus is a nice reward but not mechanically blocking. The AI spend reset is important but only blocks AI features after the $1.00 cap is hit (which takes ~140+ calls at current pricing). P2 because missing a month's Gold settlement and AI reset can be manually recovered.

**Independent Test**: Ensure the previous month has expense entries in Expense Log. Set AI_MONTHLY_SPEND to some non-zero value. Run `python tools/monthly_automation.py --character-id <ID>`. Verify: Treasury row created with correct surplus, Gold credited via coin_engine, WIS XP awarded for financial discipline, AI_MONTHLY_SPEND reset to 0 in Settings DB.

**Acceptance Scenarios**:

1. **Given** the previous month has a positive budget surplus, **When** monthly automation runs, **Then** surplus is converted to Gold via the configured rate, Treasury row is created, WIS XP is awarded, and Gold is credited to the character
2. **Given** the previous month has a deficit (expenses > income), **When** monthly automation runs, **Then** no Gold is earned (deficit doesn't penalize Gold), Treasury row still records the deficit, WIS XP is still calculated
3. **Given** AI_MONTHLY_SPEND is $0.45, **When** monthly automation runs, **Then** AI_MONTHLY_SPEND is reset to 0 in Settings DB
4. **Given** monthly automation has already run for this month (Treasury row exists), **When** it runs again, **Then** no duplicate Treasury row is created (idempotent)

---

### User Story 4 — GitHub Actions CI/CD (Priority: P2)

Four GitHub Actions workflow YAML files automate the system: `daily.yml` (cron: 10 PM daily), `weekly.yml` (cron: Sunday 10 AM), `monthly.yml` (cron: 1st of month midnight), and `tests.yml` (triggered on every push and pull request). Each workflow sets up Python, installs dependencies from `requirements.txt`, loads secrets as environment variables, and calls the corresponding automation script. The `tests.yml` workflow runs the full pytest suite to prevent regressions.

**Why this priority**: GitHub Actions is the delivery mechanism, not the functionality. All automation scripts work via CLI independently — GitHub Actions just schedules them. P2 because the player can run scripts manually during development. GitHub Actions is the "set and forget" layer added once everything else is validated.

**Independent Test**: Push the workflow YAML files to the repository. Verify `tests.yml` triggers on push and runs pytest successfully. Manually trigger `daily.yml` via GitHub Actions UI (workflow_dispatch) and verify it calls `daily_automation.py` correctly with secrets injected.

**Acceptance Scenarios**:

1. **Given** the repository has all 4 workflow YAML files, **When** code is pushed to the repository, **Then** `tests.yml` triggers and runs the full pytest suite
2. **Given** `daily.yml` is configured with the correct cron schedule, **When** 10 PM arrives, **Then** GitHub Actions runs `daily_automation.py` with `NOTION_TOKEN`, `OPENAI_API_KEY`, and `CHARACTER_ID` from repository secrets
3. **Given** `weekly.yml` is configured, **When** Sunday 10 AM arrives, **Then** GitHub Actions runs `weekly_report.py` with the same secrets
4. **Given** any workflow fails, **When** the failure is detected, **Then** GitHub Actions sends a notification (default email) and the failure is logged in the Actions tab

---

### Edge Cases

- What happens when the Notion API is unreachable during daily automation? The smoke test (step 1) catches this and aborts the entire run before any processing begins. Next run will retry.
- What happens when one engine fails mid-pipeline in daily automation? The pipeline logs the error for that step and continues with remaining steps. Partial processing is acceptable — the failed step will be retried on the next run (engines are idempotent).
- What happens when GitHub Actions cron fires but the previous run is still executing? GitHub Actions has a default concurrency limit of 1 per workflow — the second run queues or is cancelled via `concurrency` settings.
- What happens when daily automation runs at 11:59 PM and crosses midnight? The snapshot date is determined at the start of the run (`date.today()` captured once), so all processing is attributed to the same day.
- What happens when weekly report runs but no daily snapshots exist for the week? Deltas default to 0, coaching context uses current character stats only, quest generation proceeds normally (it doesn't depend on deltas).
- What happens when monthly automation runs but there are no expense entries? Surplus is calculated as 0, Treasury row is still created (records $0 surplus), AI_MONTHLY_SPEND is still reset.
- What happens when the OpenAI API key is missing from GitHub Actions secrets? The smoke test warns about missing OPENAI_API_KEY, but daily automation continues (quest engine has no AI dependency). Weekly report skips coaching and quest generation with warnings.
- What happens when the daily automation cron doesn't fire (GitHub Actions outage)? Next day's run processes normally — each engine handles the gap. Streaks may decay an extra day. No data loss, just delayed processing.
- What happens when `requirements.txt` has a version conflict in GitHub Actions? The `tests.yml` workflow catches this on every push — pip install failures cause the workflow to fail before any automation runs.
- What happens when the character has died (HP = 0) at the start of daily automation? Daily automation still runs — habits are processed, but the death state persists until the player respawns via the marketplace.

## Requirements *(mandatory)*

### Functional Requirements

**Daily Automation**

- **FR-001**: System MUST run a pre-flight smoke test checking environment variables (NOTION_TOKEN, CHARACTER_ID), API connectivity (Notion reachable), and database existence before any processing begins
- **FR-002**: System MUST load settings from Notion Settings DB and merge with config.py defaults at the start of each run
- **FR-003**: System MUST implement per-engine idempotency — each engine independently skips already-done work (Activity Log dedup, streak already-processed checks, snapshot date uniqueness). The pipeline always runs all steps; each engine is individually idempotent. No pipeline-level skip gate.
- **FR-004**: System MUST process good habits via `habit_engine.process_daily_habits()` creating Activity Log entries
- **FR-005**: System MUST process bad habits via `habit_engine.process_bad_habits()` applying HP damage via hp_engine
- **FR-006**: System MUST apply streak decay via `streak_engine.apply_decay()` for habits with missed check-ins
- **FR-007**: System MUST aggregate domain XP from Set Log (STR via fitness_engine), Meal Log (VIT via nutrition_engine), and Expense Log (WIS via financial_engine)
- **FR-008**: System MUST call `xp_engine.update_character_stats()` to recalculate stat levels after all XP aggregation
- **FR-009**: System MUST call `hp_engine.check_death()` to detect and trigger death events when HP reaches 0
- **FR-010**: System MUST call `rank_engine.check_rank_up()` and trigger `avatar_renderer` if rank changes
- **FR-011**: System MUST call `achievement_engine.check_all_achievements()` to evaluate unlock conditions
- **FR-012**: System MUST call `chart_renderer.update_character_chart()` to regenerate the stat radar chart
- **FR-013**: System MUST call `snapshot_engine.take_snapshot()` AFTER steps 1-12 complete to capture the day's final state (all XP/HP/Gold changes from habits, streaks, domain engines, death checks, rank, achievements, and chart)
- **FR-013a**: System MUST call `quest_engine.process_all_quests()` AFTER snapshot capture. Quest rewards (XP/Gold) create new Activity Log entries but are reflected in the NEXT day's snapshot
- **FR-014**: System MUST print a summary of all processing results at the end of the run
- **FR-015**: System MUST execute the 16-step pipeline in the specified order — habit processing before streak decay, XP aggregation before stat recalculation, death check after stat update

**Snapshot Engine**

- **FR-016**: System MUST write a Daily Snapshot row to the Daily Snapshots DB with: Date, Character, all 5 stat XPs (STR/INT/WIS/VIT/CHA), Player Level, Gold balance, Coin balance, HP current, Rank, Active Streak count, and Mood
- **FR-017**: System MUST check for existing snapshot for the given date and character before creating a new one (idempotent)
- **FR-018**: System MUST read current character state from Character DB and related DBs to populate snapshot fields

**Weekly Report**

- **FR-019**: System MUST query Daily Snapshots for the trailing 7 days and calculate deltas for all stats, HP, Gold, and Coins
- **FR-020**: System MUST call `coin_engine.check_overdraft()` and apply `coin_engine.apply_overdraft_penalty()` if the player's coin balance is negative
- **FR-021**: System MUST query active streaks and quest completion rate for the current week
- **FR-022**: System MUST call `coaching_engine.generate_briefing()` (Phase 6) to produce a weekly coaching briefing with the next rotating persona
- **FR-023**: System MUST call `quest_generator.generate_quests()` (Phase 6) to create 3 new AI-generated quests
- **FR-024**: System MUST call `quest_engine.process_all_quests()` (Phase 6) to process any completed quests with XP/Gold rewards
- **FR-025**: System MUST log a weekly report summary including: stat deltas, streaks active/broken, quests completed/generated, coaching persona used, AI cost incurred, overdraft status
- **FR-026**: System MUST handle AI failures gracefully — if coaching or quest generation fails, the rest of the report still executes

**Monthly Automation**

- **FR-027**: System MUST call `financial_engine` to calculate the previous month's budget surplus from Expense Log and Budget Categories
- **FR-028**: System MUST convert positive surplus to Gold via `coin_engine` and award WIS XP for financial discipline
- **FR-029**: System MUST create a Treasury row recording: Month, Income, Expenses, Surplus, Gold Earned, WIS XP
- **FR-030**: System MUST be idempotent — check for existing Treasury row for the target month before creating
- **FR-031**: System MUST reset AI_MONTHLY_SPEND to 0 in Settings DB on the 1st of each month
- **FR-032**: System MUST take a monthly-level snapshot summarizing end-of-month state

**GitHub Actions**

- **FR-033**: System MUST provide `daily.yml` with cron schedule `0 18 * * *` (UTC) = 8 PM Cairo (UTC+2) running `daily_automation.py`
- **FR-034**: System MUST provide `weekly.yml` with cron schedule `0 6 * * 0` (UTC) = Sunday 8 AM Cairo (UTC+2) running `weekly_report.py`
- **FR-035**: System MUST provide `monthly.yml` with cron schedule `0 22 1 * *` (UTC) = 1st of month midnight Cairo (UTC+2) running `monthly_automation.py`
- **FR-036**: System MUST provide `tests.yml` triggered on push and pull_request events running the full pytest suite
- **FR-037**: All workflow YAML files MUST load `NOTION_TOKEN`, `OPENAI_API_KEY`, `CHARACTER_ID`, and `NOTION_PARENT_PAGE_ID` from GitHub repository secrets
- **FR-038**: All workflow YAML files MUST set up Python 3.10+, install dependencies from `requirements.txt`, and use `concurrency` settings to prevent parallel execution: `concurrency: { group: <workflow-name>, cancel-in-progress: true }`

### Key Entities

- **Daily Snapshot**: A point-in-time capture of all character state (5 stat XPs, level, Gold, Coins, HP, Rank, streaks, Mood) stored as a row in the Daily Snapshots DB. One per day per character. Used for trend analysis and weekly delta calculations.
- **Weekly Report**: A computed summary (not persisted as a DB row) of 7-day performance including stat deltas, streak status, quest completion rate, overdraft status, AI coaching briefing, and AI cost. Logged via logger.py.
- **Treasury Row**: A monthly financial summary in the Treasury DB recording income, expenses, surplus, Gold earned from surplus, and WIS XP awarded. One per month per character.
- **Automation Pipeline**: An ordered sequence of engine calls that processes game state changes. Each step in the pipeline is idempotent and safe to retry. The pipeline captures date at the start to prevent cross-midnight issues.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Daily automation processes all pending habits, updates all stats, and creates a Daily Snapshot in a single run — completing in under 60 seconds
- **SC-002**: Running daily automation twice on the same day produces identical results — no duplicate Activity Log entries, no duplicate snapshots, no double XP/Gold
- **SC-003**: Weekly report correctly calculates 7-day stat deltas by comparing current snapshot to 7-days-ago snapshot
- **SC-004**: Weekly report successfully calls Phase 6 AI engines (coaching + quest generation + quest completion) in the correct sequence
- **SC-005**: Monthly automation creates exactly one Treasury row per month with correct surplus and Gold calculations
- **SC-006**: AI_MONTHLY_SPEND is reset to 0 on the 1st of each month, re-enabling AI features for the new month
- **SC-007**: All 4 GitHub Actions workflows execute successfully with secrets injected — verified by at least one manual `workflow_dispatch` trigger per workflow
- **SC-008**: `tests.yml` catches test failures on push/PR and blocks merging of broken code
- **SC-009**: A smoke test failure in daily automation prevents any processing — no partial state changes from a failed pre-flight check
- **SC-010**: If any single engine fails mid-pipeline with a recoverable error (Notion rate-limit timeout, transient API error), the error is logged and remaining pipeline steps still execute. Unrecoverable errors (missing database, invalid character_id) log a fatal error and halt the pipeline at that step

## Assumptions

- Phases 1-6 are complete: all engines (habit, streak, XP, HP, coin, financial, fitness, nutrition, quest, coaching, cost tracker, achievement, rank, chart, avatar) are operational and independently testable
- Daily Snapshots DB exists with schema from Phase 1 (Date, Character, STR XP, INT XP, WIS XP, VIT XP, CHA XP, Level, Gold, Coins, HP, Rank, Active Streaks, Mood)
- Treasury DB exists with schema from Phase 1 (Month, Income, Expenses, Surplus, Gold Earned, WIS XP)
- All engine functions are idempotent — safe to call multiple times with the same input
- The `smoke_test.py` script exists from Phase 1 and checks env vars + Notion connectivity
- Settings DB contains all required keys (AI_MONTHLY_SPEND, LAST_COACH_PERSONA, OPENAI_MODEL, etc.)
- CHARACTER_ID is a single player system — all automation scripts take `--character-id` as a CLI argument
- GitHub Actions runners have Python 3.10+ available
- GitHub repository secrets are configured before workflows are enabled
- Cron schedules are in UTC — the player's local timezone offset is handled by choosing appropriate UTC times

## Scope Boundaries

**In scope**: Daily automation pipeline (16-step), snapshot engine, weekly report with AI integration, monthly Gold settlement + AI spend reset, 4 GitHub Actions workflow YAML files, CLI entry points for all automation scripts, idempotency for all operations, error handling and fault tolerance

**Out of scope**: Dashboard display of reports (Phase 8), character onboarding (Phase 8), workflow SOP documentation (Phase 8), notification system beyond GitHub Actions default email, retry scheduling for failed runs (manual re-run via GitHub Actions UI), multi-player support, timezone configuration UI, custom cron schedule configuration
