# Tasks: Phase 3 — XP Engine, Streaks & Leveling

**Input**: Design documents from `/specs/003-xp-streaks-leveling/`
**Prerequisites**: Phase 1 complete (foundation), Phase 2 complete (HP/coin engines)

**Tests**: Included — the spec and constitution require pytest coverage for all tools.

**Organization**: Tasks grouped by user story. XP engine and streak engine are independent and can be built in parallel. Habit engine depends on both and is built last.

**Clarifications integrated**: Multi-stat XP split (equal, floor), timezone-aware day boundary, no XP penalty on decay, real-time stat updates after every XP event, rank is display-only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Test Infrastructure Setup

**Purpose**: Extend test fixtures with XP, streak, and habit mock data

- [ ] T201 Extend `tests/conftest.py` with Phase 3 fixtures — mock Activity Log entries with XP columns (EXP + Habit, EXP + Goal, EXP + Tasks) for various domains, mock Activity Log entries for multi-stat Goals (Goal relating to 2+ skills in different stats), mock Good Habit rows with Domain/EXP Earn/Active properties, mock Bad Habit rows with HP Damage/Domain properties, mock Streak Tracker rows (various streak counts and tiers), mock Character page with Class/stat XP/stat Level/Player Level/Total XP/Current Rank properties, mock Skill/Area rows with Stat mappings, mock config overrides for XP formula constants (B, E, L), streak tier thresholds, class-to-stat mappings, and `PLAYER_TIMEZONE` setting

---

## Phase 2: User Story 1 — Exponential XP Progression (Priority: P1)

**Goal**: XP accumulates per stat from Activity Log entries, levels calculated via exponential formula, all values written to Character page in real-time

**Independent Test**: Grant XP to a stat, verify level calculation matches formula. Delivers visible progression.

### Implementation for User Story 1

- [ ] T202 [P] [US1] Implement `xp_for_level()` and `cumulative_xp_for_level()` in `tools/xp_engine.py` — `xp_for_level(n)` returns `floor(B * n^E + L * n)` using constants from `tools/config.py`. `cumulative_xp_for_level(n)` returns sum of `xp_for_level(1..n)`. All values integers
- [ ] T203 [P] [US1] Implement `level_from_xp()` and `progress_to_next_level()` in `tools/xp_engine.py` — `level_from_xp(total_xp)` iterates from level 1 upward until cumulative exceeds total_xp, returns level (minimum 1). `progress_to_next_level(total_xp)` returns float 0.0–1.0 showing progress into current level
- [ ] T204 [US1] Implement `aggregate_stat_xp()` in `tools/xp_engine.py` — query Activity Log for all XP entries, filter by domain-to-stat mapping from `tools/config.py`. For multi-stat entries (Goals/Tasks relating to multiple skills in different stats), split XP equally among mapped stats using floor division (remainder dropped). Sum EXP columns per stat. Return integer total for the given stat. Use `notion_client.query_database()` with auto-pagination
- [ ] T205 [US1] Implement `update_character_stats()` in `tools/xp_engine.py` — for each of 5 stats: call `aggregate_stat_xp()`, call `apply_class_bonus()`, calculate level via `level_from_xp()`. Compute Player Level = `floor(avg(5 stat levels))`, Total XP = sum of 5 stat XPs, Current Rank from `RANK_THRESHOLDS` in config (display-only — no Activity Log entry on rank change). Write all values to Character DB via `notion_client.update_page()`. **This function is called after every XP-granting event (real-time), not just during daily automation.** Return dict with all stats, levels, player_level, total_xp, rank

### Tests for User Story 1

- [ ] T206 [P] [US1] Write tests in `tests/test_xp_engine.py` — XP formula and aggregation tests:
  - test `xp_for_level(1)` returns 1200 with default constants (1000*1^1.8 + 200*1)
  - test `xp_for_level(5)` matches expected value
  - test `xp_for_level(10)` matches expected value
  - test `cumulative_xp_for_level(1)` equals `xp_for_level(1)`
  - test `cumulative_xp_for_level(3)` equals sum of levels 1-3
  - test `level_from_xp(0)` returns 1 (minimum level)
  - test `level_from_xp(1199)` returns 1 (just below threshold)
  - test `level_from_xp(1200)` returns 1 (exactly at threshold — need cumulative > total)
  - test `level_from_xp(5082)` returns 2 (crosses level 2 cumulative)
  - test multi-level jump: large XP correctly lands on right level
  - test `progress_to_next_level()` returns 0.0 at level boundary
  - test `progress_to_next_level()` returns ~0.5 at midpoint
  - test `aggregate_stat_xp()` sums only entries matching the stat's domain
  - test `aggregate_stat_xp()` returns 0 for stat with no matching entries
  - test `aggregate_stat_xp()` multi-stat split: 10 XP Goal with 2 stats = 5 each
  - test `aggregate_stat_xp()` multi-stat split: 7 XP Goal with 2 stats = 3 each (floor, 1 dropped)
  - test `aggregate_stat_xp()` single-stat Goal: full XP to that stat (no split)
  - test `update_character_stats()` writes correct values to Character DB
  - test Player Level is floor of average of 5 stat levels
  - test Total XP is sum of all 5 stat XPs
  - test Current Rank matches highest qualifying threshold
  - test rank change is display-only (no Activity Log entry created)

**Checkpoint**: XP formula, level calculation, multi-stat split, and real-time stat aggregation working

---

## Phase 3: User Story 2 — Streak Tracking and Multipliers (Priority: P2)

**Goal**: Consecutive daily check-ins build streaks with tier-based XP multipliers. Missing a day resets to zero (no XP penalty). Day boundary is timezone-aware.

**Independent Test**: Simulate consecutive check-ins, verify streak counts, tiers, and multiplier values.

### Implementation for User Story 2

- [ ] T207 [P] [US2] Implement `get_today()` in `tools/streak_engine.py` — read `PLAYER_TIMEZONE` from config (Settings DB or `.env`, default: UTC). Return today's date as `YYYY-MM-DD` string in the player's local timezone
- [ ] T208 [P] [US2] Implement `calculate_multiplier()` and `get_streak_tier()` in `tools/streak_engine.py` — `calculate_multiplier(streak_count)` finds the highest tier threshold <= streak_count from `config.STREAK_TIERS`, returns the multiplier (1.0 if below first tier). `get_streak_tier(count)` returns tier name string (None/Bronze/Silver/Gold/Platinum/Diamond/Mythic)
- [ ] T209 [US2] Implement `update_streak_tracker()` in `tools/streak_engine.py` — if completed: increment Current Streak, update Best Streak if new high (never decrease), recalculate tier and multiplier, set Last Completed = date. If not completed: call `apply_decay()` (no XP penalty). If no Streak Tracker row exists for this habit, create one (lazy initialization). Write to Streak Tracker DB via `notion_client.update_page()` or `create_page()`. Return `{"streak": int, "best": int, "tier": str, "multiplier": float}`
- [ ] T210 [US2] Implement `apply_decay()` in `tools/streak_engine.py` — reset Current Streak to 0, tier to "None", multiplier to 1.0 on the Streak Tracker row. **No XP penalty applied.** Best Streak preserved. Log decay event. Return `{"habit_id": str, "previous_streak": int, "previous_tier": str}`
- [ ] T211 [US2] Implement `check_streaks()` in `tools/streak_engine.py` — query all active good habits for the character, use `get_today()` for timezone-aware date, read today's Activity Log entries (Type=GOOD), determine which habits were checked in. For each active habit: call `update_streak_tracker(habit_id, completed, date)`. Return `{"updated": int, "decayed": int, "details": [...]}`

### Tests for User Story 2

- [ ] T212 [P] [US2] Write tests in `tests/test_streak_engine.py`:
  - test `get_today()` returns correct date for configured timezone
  - test `get_today()` defaults to UTC when no timezone configured
  - test `get_today()` handles timezone where "today" differs from UTC date
  - test `calculate_multiplier(0)` returns 1.0
  - test `calculate_multiplier(3)` returns 1.1 (Bronze)
  - test `calculate_multiplier(7)` returns 1.25 (Silver)
  - test `calculate_multiplier(14)` returns 1.5 (Gold)
  - test `calculate_multiplier(30)` returns 2.0 (Platinum)
  - test `calculate_multiplier(60)` returns 2.5 (Diamond)
  - test `calculate_multiplier(100)` returns 3.0 (Mythic)
  - test `calculate_multiplier(150)` returns 3.0 (above Mythic stays at Mythic)
  - test `get_streak_tier(0)` returns "None"
  - test `get_streak_tier(5)` returns "Bronze" (between Bronze and Silver)
  - test `get_streak_tier(100)` returns "Mythic"
  - test `update_streak_tracker()` increments streak on check-in
  - test `update_streak_tracker()` updates Best Streak when current exceeds it
  - test `update_streak_tracker()` does NOT decrease Best Streak on decay
  - test `update_streak_tracker()` creates new row on first check-in (lazy init)
  - test `update_streak_tracker()` advances tier at threshold (2→3 = Bronze)
  - test `apply_decay()` resets streak to 0 and tier to None
  - test `apply_decay()` preserves Best Streak
  - test `apply_decay()` does NOT deduct any XP (no penalty)
  - test `check_streaks()` processes all active habits
  - test `check_streaks()` correctly identifies checked-in vs missed habits
  - test streak across tier boundary: day 6→7 advances Silver, multiplier changes

**Checkpoint**: Streak system fully operational — timezone-aware tracking, tier advancement, penalty-free decay

---

## Phase 4: User Story 3 — Daily Habit Processing (Priority: P3)

**Goal**: Single idempotent daily pass processes all habits — XP for good habits (base * streak multiplier), HP damage for bad habits, real-time stat updates on Character.

**Independent Test**: Create mock daily Activity Log entries, run processor, verify XP/streak/HP all updated correctly. Run again, verify no duplicates.

### Implementation for User Story 3

- [ ] T213 [US3] Implement `get_active_habits()` in `tools/habit_engine.py` — query Good Habit DB for habits where Active=True. Return list of dicts with id, name, domain, base_xp (EXP Earn property)
- [ ] T214 [US3] Implement `calculate_habit_xp()` in `tools/habit_engine.py` — `calculate_habit_xp(base_xp, multiplier)` returns `floor(base_xp * multiplier)` as integer
- [ ] T215 [US3] Implement `process_daily_habits()` in `tools/habit_engine.py` — idempotent daily orchestration using timezone-aware date from `streak_engine.get_today()`: (1) read today's Activity Log entries (Type=GOOD), (2) get all active habits, (3) for each habit determine if checked in today, (4) call `streak_engine.check_streaks()` to update all streaks (no XP penalty on decay), (5) for each completed habit: get multiplier from streak tracker, calculate XP via `calculate_habit_xp()`, create XP Activity Log entry (skip if one already exists for this habit+date — idempotency guard), (6) call `xp_engine.update_character_stats()` for real-time stat refresh. Return `{"processed": int, "xp_granted": int, "streaks_updated": int, "streaks_decayed": int, "already_processed": bool}`
- [ ] T216 [US3] Implement `process_bad_habits()` in `tools/habit_engine.py` — read today's Activity Log entries (Type=BAD) using timezone-aware date, for each call `hp_engine.apply_damage(character_id, damage_amount, source)` using the bad habit's HP Damage value. Return `{"processed": int, "total_damage": int, "died": bool}`
- [ ] T217 [US3] Implement `get_trailing_adherence()` in `tools/habit_engine.py` — query Activity Log for the last N days (timezone-aware), count days where habit was completed, return float 0.0–1.0

### Tests for User Story 3

- [ ] T218 [P] [US3] Write tests in `tests/test_habit_engine.py`:
  - test `get_active_habits()` returns only habits with Active=True
  - test `get_active_habits()` returns correct domain and base_xp
  - test `calculate_habit_xp(5, 1.0)` returns 5
  - test `calculate_habit_xp(5, 1.5)` returns 7 (floor of 7.5)
  - test `calculate_habit_xp(5, 2.5)` returns 12 (floor of 12.5)
  - test `process_daily_habits()` grants XP for checked-in habits
  - test `process_daily_habits()` updates streaks for all active habits
  - test `process_daily_habits()` decays streaks for missed habits (no XP penalty)
  - test `process_daily_habits()` applies streak multiplier to XP
  - test `process_daily_habits()` calls `update_character_stats()` for real-time refresh
  - test `process_daily_habits()` is idempotent — second run creates no duplicate XP
  - test `process_daily_habits()` with no Activity Log entries still decays all streaks
  - test `process_daily_habits()` uses timezone-aware date from `get_today()`
  - test `process_bad_habits()` applies HP damage for each bad habit entry
  - test `process_bad_habits()` triggers death when cumulative damage pushes HP ≤ 0
  - test `process_bad_habits()` with no bad habit entries returns zero damage
  - test `get_trailing_adherence()` returns 1.0 for perfect 30-day streak
  - test `get_trailing_adherence()` returns 0.0 for no completions
  - test `get_trailing_adherence()` returns correct ratio for partial adherence

**Checkpoint**: Full daily processing loop operational — habits → streaks → XP → HP → Character stats (real-time)

---

## Phase 5: User Story 4 — Class Bonus and Stat Aggregation (Priority: P4)

**Goal**: Character class provides +10% XP to matching stat. All stat XPs, levels, Player Level, Total XP, and Rank written to Character page.

**Independent Test**: Set class to Warrior, grant STR XP, verify 10% bonus applied. Verify non-matching stats get no bonus.

### Implementation for User Story 4

- [ ] T219 [US4] Implement `apply_class_bonus()` in `tools/xp_engine.py` — read character's Class from Character DB, look up class-to-stat mapping from config (Warrior→STR, Mage→INT, Rogue→CHA, Paladin→VIT, Ranger→WIS). If stat matches class: return `floor(base_xp * 1.1)`. Otherwise return base_xp unchanged

### Tests for User Story 4

- [ ] T220 [P] [US4] Write class bonus tests in `tests/test_xp_engine.py` (append to existing):
  - test `apply_class_bonus(100, "STR", "Warrior")` returns 110
  - test `apply_class_bonus(100, "INT", "Warrior")` returns 100 (no bonus)
  - test `apply_class_bonus(100, "INT", "Mage")` returns 110
  - test `apply_class_bonus(100, "CHA", "Rogue")` returns 110
  - test `apply_class_bonus(100, "VIT", "Paladin")` returns 110
  - test `apply_class_bonus(100, "WIS", "Ranger")` returns 110
  - test all 5 class-stat combinations produce +10%
  - test non-matching class-stat pairs produce 0% bonus
  - test bonus rounds down: `apply_class_bonus(7, "STR", "Warrior")` returns 7 (floor of 7.7)

**Checkpoint**: Class system adds strategic depth to progression

---

## Phase 6: User Story 5 — Visual Progress Display (Priority: P5)

**Goal**: Progress bars show current XP / XP-to-next-level per stat in `◾◾◾◽◽ X/Y | LV Z` format.

**Independent Test**: Set specific XP values, verify bar string matches expected format.

### Implementation for User Story 5

- [ ] T221 [US5] Implement `generate_progress_bar()` in `tools/xp_engine.py` — `generate_progress_bar(current, target, segments=10)` calculates fill = `floor(current / target * segments)`, builds string with `◾` for filled and `◽` for empty, appends ` X/Y` where X=current, Y=target. Return formatted string

### Tests for User Story 5

- [ ] T222 [P] [US5] Write progress bar tests in `tests/test_xp_engine.py` (append to existing):
  - test 0% fill: `generate_progress_bar(0, 1200)` → `◽◽◽◽◽◽◽◽◽◽ 0/1200`
  - test ~33% fill: `generate_progress_bar(400, 1200)` → `◾◾◾◽◽◽◽◽◽◽ 400/1200`
  - test 50% fill: `generate_progress_bar(600, 1200)` → `◾◾◾◾◾◽◽◽◽◽ 600/1200`
  - test 100% fill: `generate_progress_bar(1200, 1200)` → `◾◾◾◾◾◾◾◾◾◾ 1200/1200`
  - test custom segments: `generate_progress_bar(50, 100, 5)` → `◾◾◽◽◽ 50/100`
  - test rounding: partial segments round down

**Checkpoint**: Visual feedback completes the progression loop

---

## Phase 7: Integration & Polish

**Purpose**: Cross-engine validation, end-to-end daily processing, and documentation

- [ ] T223 [P] Write integration tests in `tests/test_xp_streak_integration.py`:
  - test full daily flow: check in habits → update streaks → grant XP → update stats → verify Character page
  - test streak multiplier affects XP correctly in end-to-end flow
  - test bad habit processing triggers HP damage through to death (cross-engine with hp_engine)
  - test class bonus applies correctly in full aggregation pipeline
  - test idempotent daily processing: run twice, verify identical results
  - test mixed day: some habits checked in (XP granted), some missed (streaks decayed, no XP penalty), some bad habits (HP damage)
  - test new habit with no Streak Tracker row: lazy creation works in full flow
  - test multi-stat Goal: XP split equally among stats in full pipeline
  - test real-time stat refresh: Goal completion triggers immediate stat update without daily processing
  - test timezone-aware day boundary: check-in at 11:55 PM local time counts for today
- [ ] T224 [P] Update `workflows/` with Phase 3 operational notes — daily habit processing usage, XP engine usage, streak engine usage, timezone configuration, manual verification steps from quickstart.md
- [ ] T225 Run `pytest tests/test_xp_engine.py tests/test_streak_engine.py tests/test_habit_engine.py tests/test_xp_streak_integration.py -v` and verify all tests pass
- [ ] T226 Run `pytest tests/ -v` and verify all tests pass (Phase 1 + Phase 2 + Phase 3)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Test Infrastructure (Phase 1)**: Extend existing conftest.py — no blockers
- **US1 XP Progression (Phase 2)**: Depends on Phase 1 project (config, notion_client)
- **US2 Streak Tracking (Phase 3)**: Depends on Phase 1 project (config, notion_client) — **INDEPENDENT of US1**
- **US3 Daily Processing (Phase 4)**: Depends on US1 (update_character_stats) + US2 (check_streaks) + Phase 2 project (hp_engine)
- **US4 Class Bonus (Phase 5)**: Depends on US1 (part of xp_engine) — can be done during US1 or after
- **US5 Progress Bar (Phase 6)**: Depends on US1 (part of xp_engine) — can be done during US1 or after
- **Integration (Phase 7)**: Depends on all user stories complete

### Engine Dependencies

```
Phase 1+2 (Foundation + HP/Coin — already complete)
  ├── XP Engine (T202-T206) ──────────────────┐
  │     ├── Class Bonus (T219-T220)            │
  │     └── Progress Bar (T221-T222)           ├── Habit Engine (T213-T218)
  └── Streak Engine (T207-T212) ──────────────┘        │
                                                        └── Integration (T223-T226)
```

### Key Cross-Engine Dependencies

`habit_engine` imports from:
- `xp_engine.update_character_stats()` — real-time stat refresh after XP grants
- `streak_engine.check_streaks()` — update all streaks during daily processing
- `streak_engine.calculate_multiplier()` — get XP multiplier for each habit
- `streak_engine.get_today()` — timezone-aware date for daily processing
- `hp_engine.apply_damage()` (Phase 2) — apply HP damage from bad habits

`xp_engine` and `streak_engine` are **independent of each other** and can be built in parallel.

### Parallel Opportunities

- T201 (conftest fixtures) can run in parallel with T202-T203 (XP formula) and T207-T208 (streak tier/timezone)
- **T202-T206 (XP engine) + T207-T212 (streak engine)**: Fully parallel — different files, no shared dependencies
- T219-T220 (class bonus) + T221-T222 (progress bar): Parallel with each other, can overlap with US1 core
- T223 (integration tests) + T224 (workflows): Parallel with each other after all engines complete

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Extend conftest.py with Phase 3 fixtures (T201)
2. **In parallel**:
   - Build XP engine: formula, levels, aggregation with multi-stat split, real-time stats (T202-T205)
   - Build streak engine: timezone, multiplier, tracker, decay (no penalty), check (T207-T211)
3. Write and run XP engine tests (T206)
4. Write and run streak engine tests (T212)
5. **STOP and VALIDATE**: XP formula correct, multi-stat split works, streaks track with timezone awareness

### Full Phase

6. Build habit engine: active habits, XP calc, daily processing with real-time refresh, bad habits (T213-T217)
7. Write and run habit engine tests (T218)
8. Add class bonus (T219-T220)
9. Add progress bar (T221-T222)
10. Write and run integration tests (T223)
11. Update workflows (T224)
12. Run full test suite (T225-T226)

### Parallel Example: After Phase 1 Setup

```bash
# These two engines can be built simultaneously:
Agent 1: XP Engine — formula, levels, multi-stat split, aggregation, real-time stats (T202-T206)
Agent 2: Streak Engine — timezone, multiplier, tracker, decay (no penalty), check (T207-T212)

# After both complete:
Agent 1: Habit Engine — daily processing with real-time refresh (T213-T218)
Agent 2: Class Bonus + Progress Bar (T219-T222)

# Final:
Agent 1: Integration tests + workflows (T223-T226)
```

---

## Notes

- All XP values are integers. Fractional results from multipliers and multi-stat splits are floored.
- Multi-stat XP split: Goals/Tasks with N related stats get `floor(total_xp / N)` per stat; remainder dropped.
- Activity Log is append-only — XP grants create new entries, never modify existing ones.
- Streak decay is binary (reset to 0), **no XP penalty**. Losing the multiplier is the only consequence.
- Day boundary for streaks is timezone-aware: `PLAYER_TIMEZONE` from Settings DB / `.env`, default UTC.
- `update_character_stats()` runs after **every XP-granting event** (real-time), not just during daily automation.
- Rank changes are display-only in Phase 3 — no Activity Log entry. Deferred to Phase 5 (Achievements).
- Class bonus applies at aggregation, not per-event. Changing class takes effect on next recalculation.
- Streak Tracker rows are lazily created on first check-in — no pre-seeding needed for new habits.
- Daily processing is idempotent via habit+date dedup for XP entries.
- All functions use `tools/logger.py` for structured logging to stderr.
- All game balance constants read from `tools/config.py` / Settings DB — no hardcoded values in engine files.
- Commit after each task or logical group.
