# Tasks: Domain Modules — Financial, Fitness & Nutrition Engines

**Input**: Design documents from `/specs/004-domain-modules/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md
**Task ID Range**: T301–T330 (Phase 4 — avoids collision with Phase 1: T001-T029, Phase 2: T101-T124, Phase 3: T201-T226)

**Organization**: Tasks grouped by user story. Financial (US1) and Fitness (US2) are both P1 and can be built in parallel. Nutrition (US3) is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1=Financial, US2=Fitness, US3=Nutrition)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Config Updates)

**Purpose**: Add Phase 4 constants to config and extend conftest with domain engine fixtures

- [ ] T301 Add Phase 4 constants to `tools/config.py`: MONTHLY_INCOME, GOLD_CONVERSION_RATE, BUDGET_BREACH_XP_PENALTY, RPE_XP_WEIGHT, OVERLOAD_WINDOW_DAYS, DEFAULT_TDEE, MACRO_TOLERANCE_PCT, NUTRITION_STREAK_MULTIPLIER. Ensure all are readable from Settings DB with fallback defaults.

**Checkpoint**: Config updated — all three engines can read their constants.

---

## Phase 2: User Story 1 — Financial Tracking & WIS XP (Priority: P1) MVP

**Goal**: Monthly budget processing — compare expenses against limits, calculate surplus/deficit, convert surplus to Gold, grant/penalize WIS XP, create Treasury summary.

**Independent Test**: Create expense entries for a past month, run `financial_engine.process_monthly_finances()`, verify Treasury row + Activity Log entry + Gold credit + WIS XP. Re-run and verify idempotency.

### Implementation for User Story 1

- [ ] T302 [US1] Implement `get_budget_categories(character_id)` in `tools/financial_engine.py` — query Budget Categories DB, return list of `{id, name, monthly_limit, type}`
- [ ] T303 [US1] Implement `get_monthly_expenses(character_id, year, month)` in `tools/financial_engine.py` — query Expense Log for date range, group totals by category
- [ ] T304 [US1] Implement `calculate_monthly_summary(categories, expenses, monthly_income)` in `tools/financial_engine.py` — pure math: per-category surplus/deficit, overall surplus, `gold_earned = floor(max(0, surplus) / GOLD_CONVERSION_RATE)`, positive `wis_xp = floor(gold_earned * WIS_XP_PER_GOLD)`, subtract BUDGET_BREACH_XP_PENALTY per breached category, cap net WIS XP at minimum 0 (cannot go negative)
- [ ] T305 [US1] Implement `process_monthly_finances(character_id, year, month)` in `tools/financial_engine.py` — orchestrator: idempotency check (existing Treasury row for YYYY-MM), read MONTHLY_INCOME from Settings DB, call calculate_monthly_summary, create Treasury row, create Activity Log entry (Type: FINANCIAL, WIS XP), add Gold via `coin_engine`, call `xp_engine.update_character_stats()`
- [ ] T306 [US1] Write `tests/test_financial_engine.py` — test cases: surplus calculation (SC-001), Gold floor division (SC-002), budget breach penalty (FR-003), idempotency (SC-008), zero income edge case, all-categories-breached edge case, $0 limit category skipped

**Checkpoint**: Financial engine complete. Run quickstart steps 1-2 to verify.

---

## Phase 3: User Story 2 — Workout Logging & STR XP (Priority: P1)

**Goal**: Process workout sets — calculate 1RM (Epley), volume, RPE-weighted XP, detect progressive overload, aggregate session XP into a single STR Activity Log entry.

**Independent Test**: Create set log entries in a workout session, run `fitness_engine.process_daily_workouts()`, verify per-set 1RM/volume/XP, session Activity Log entry, progressive delta. Re-run and verify idempotency.

### Implementation for User Story 2

- [ ] T307 [P] [US2] Implement `calculate_1rm(weight, reps)` in `tools/fitness_engine.py` — Epley: `floor(weight * (1 + reps / 30))`, return 0 if weight <= 0 or reps <= 0
- [ ] T308 [P] [US2] Implement `calculate_volume(weight, reps)` in `tools/fitness_engine.py` — `weight * reps`, return 0 if invalid
- [ ] T309 [US2] Implement `calculate_set_xp(volume, exercise_modifier, rpe=7)` in `tools/fitness_engine.py` — `base_xp = floor(volume * exercise_modifier / 1000)`, if RPE_XP_WEIGHT: `floor(base_xp * (rpe / 10))`, else base_xp. Return 0 if volume <= 0
- [ ] T310 [US2] Implement `get_best_1rm(character_id, exercise_id, window_days=None)` in `tools/fitness_engine.py` — query Set Log for exercise within OVERLOAD_WINDOW_DAYS, return max 1RM or 0
- [ ] T311 [US2] Implement `calculate_progressive_delta(current_1rm, best_1rm)` in `tools/fitness_engine.py` — return `{overload: bool, absolute: int, percentage: float}`
- [ ] T312 [US2] Implement `process_set(character_id, set_data)` in `tools/fitness_engine.py` — validate weight/reps > 0, calculate 1RM, volume, XP, progressive delta. Return `{1rm, volume, xp, delta, valid}`
- [ ] T313 [US2] Implement `process_workout_session(character_id, session_id)` in `tools/fitness_engine.py` — fetch sets, process each (skip invalid), sum XP, idempotency check, create Activity Log entry (Type: WORKOUT, mapped to STR), write progressive delta to Set Log rows, call `xp_engine.update_character_stats()`
- [ ] T314 [US2] Implement `process_daily_workouts(character_id, date)` in `tools/fitness_engine.py` — fetch all sessions for date, call process_workout_session for each
- [ ] T315 [US2] Write `tests/test_fitness_engine.py` — test cases: Epley accuracy (SC-003), volume calc, RPE linear weighting at RPE 6/7/8/9/10 (SC-005), progressive overload detection (SC-004), zero weight/reps rejection (FR-013), no prior history edge case, session XP aggregation, idempotency (SC-008), base XP volume formula (FR-013a)

**Checkpoint**: Fitness engine complete. Run quickstart steps 3-5 to verify.

---

## Phase 4: User Story 3 — Meal Logging & VIT XP (Priority: P2)

**Goal**: Daily nutrition processing — sum calories from meals, compute symmetric adherence score, track nutrition streak, apply multiplier, grant VIT XP.

**Independent Test**: Create meal log entries, run `nutrition_engine.process_daily_nutrition()`, verify calorie sum, adherence score, streak count, VIT XP with/without multiplier. Verify symmetric scoring (+20% and -20% produce same score).

### Implementation for User Story 3

- [ ] T316 [P] [US3] Implement `calculate_calories(protein, carbs, fat)` in `tools/nutrition_engine.py` — `floor((protein * 4) + (carbs * 4) + (fat * 9))`, return 0 and reject if all macros are 0
- [ ] T317 [P] [US3] Implement `calculate_adherence(actual_calories, target_tdee)` in `tools/nutrition_engine.py` — `max(0, 1 - abs(actual - target) / target)`, return 0.0 if target <= 0, return 1.0 for exact match
- [ ] T318 [US3] Implement `get_daily_meals(character_id, date)` in `tools/nutrition_engine.py` — query Meal Log for date, return list of `{id, protein, carbs, fat, calories}`
- [ ] T319 [US3] Implement `get_nutrition_streak(character_id, date)` in `tools/nutrition_engine.py` — count consecutive adherent days ending at date. Adherent = adherence >= (1 - MACRO_TOLERANCE_PCT / 100). Return 0 if no streak
- [ ] T320 [US3] Implement `calculate_vit_xp(adherence, nutrition_streak, base_vit_xp=None)` in `tools/nutrition_engine.py` — `floor(base_vit_xp * adherence * multiplier)` where multiplier = NUTRITION_STREAK_MULTIPLIER if streak >= 3, else 1.0. Return 0 if adherence == 0
- [ ] T321 [US3] Implement `process_daily_nutrition(character_id, date)` in `tools/nutrition_engine.py` — orchestrator: fetch meals, reject all-zero, sum calories, read TDEE, calculate adherence, get streak, calculate VIT XP, idempotency check, create Activity Log entry (Type: NUTRITION, mapped to VIT), call `xp_engine.update_character_stats()`
- [ ] T322 [US3] Write `tests/test_nutrition_engine.py` — test cases: calorie formula (FR-014), symmetric adherence +20%/-20% produce same score (SC-006), adherence at exact TDEE = 1.0, adherence at 0 calories, nutrition streak threshold at 3 days (SC-007), multiplier activation/reset, all-zero macro rejection (FR-019), no meals edge case, idempotency (SC-008)

**Checkpoint**: Nutrition engine complete. Run quickstart steps 6-9 to verify.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Test fixtures, integration validation, cross-engine verification

- [ ] T323 Extend `tests/conftest.py` with mock Notion responses for Budget Categories, Expense Log, Treasury, Exercise Dictionary, Workout Sessions, Set Log, Meal Log
- [ ] T324 Verify all Activity Log entries from domain engines are correctly aggregated by `xp_engine.update_character_stats()` into WIS (financial), STR (fitness), VIT (nutrition) — cross-engine integration test (SC-009)
- [ ] T325 Run full quickstart.md verification (all 9 steps) — validate end-to-end flow
- [ ] T326 Commit all Phase 4 files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1: T301)**: No dependencies beyond Phase 1-3 being complete
- **Financial (Phase 2: T302-T306)**: Depends on T301 + Phase 2 coin_engine + Phase 3 xp_engine
- **Fitness (Phase 3: T307-T315)**: Depends on T301 + Phase 3 xp_engine
- **Nutrition (Phase 4: T316-T322)**: Depends on T301 + Phase 3 xp_engine
- **Polish (Phase 5: T323-T326)**: Depends on all engine phases complete

### User Story Dependencies

- **US1 (Financial)** and **US2 (Fitness)** are independent — can be built in parallel after T301
- **US3 (Nutrition)** is independent of US1 and US2 — can be built in parallel or after
- All three user stories depend only on Setup (T301) and prior phase infrastructure

### Within Each User Story

- Pure math functions first (no Notion dependencies)
- Notion query functions next (need notion_client)
- Orchestrator functions last (depend on all above)
- Tests after implementation (validate all functions)

### Parallel Opportunities

- T307 + T308 (1RM and volume are pure math, zero dependencies)
- T316 + T317 (calories and adherence are pure math, zero dependencies)
- US1 (T302-T306) can run in parallel with US2 (T307-T315) after T301
- US3 (T316-T322) can run in parallel with US1 and US2 after T301

---

## Parallel Example: User Story 2 (Fitness)

```
# Launch pure math functions in parallel (no dependencies):
T307: calculate_1rm() in tools/fitness_engine.py
T308: calculate_volume() in tools/fitness_engine.py

# Then sequentially:
T309: calculate_set_xp() (depends on T307, T308)
T310: get_best_1rm() (depends on notion_client)
T311: calculate_progressive_delta() (depends on T310)
T312: process_set() (depends on T307-T311)
T313: process_workout_session() (depends on T312)
T314: process_daily_workouts() (depends on T313)
T315: test_fitness_engine.py (depends on T307-T314)
```

---

## Implementation Strategy

### MVP First (Financial Engine Only)

1. Complete T301 (config updates)
2. Complete T302-T306 (financial engine + tests)
3. **STOP and VALIDATE**: Run quickstart steps 1-2
4. Player can track expenses and earn Gold + WIS XP

### Incremental Delivery

1. T301 → Config ready
2. T302-T306 → Financial engine (WIS XP + Gold) → Validate
3. T307-T315 → Fitness engine (STR XP) → Validate
4. T316-T322 → Nutrition engine (VIT XP) → Validate
5. T323-T326 → Polish & integration → Final validation
6. Each engine adds a new stat progression without breaking previous engines

---

## Notes

- Task IDs T301-T326 (26 tasks) to avoid collision with Phase 1 (T001-T029), Phase 2 (T101-T124), Phase 3 (T201-T226)
- [P] tasks = different files, no dependencies between them
- All engines write to Activity Log — `xp_engine.update_character_stats()` handles stat aggregation
- Financial runs monthly (Phase 7 monthly automation), Fitness and Nutrition run daily (Phase 7 daily automation)
- Commit after each completed user story phase
