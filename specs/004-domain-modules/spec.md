# Feature Specification: Domain Modules — Financial, Fitness & Nutrition Engines

**Feature Branch**: `004-domain-modules`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Phase 4 of the V5 Implementation Plan — build the three domain-specific engines (Financial, Fitness, Nutrition) that feed XP into the stat progression system via the Activity Log."

## Clarifications

### Session 2026-03-22

- Q: What formula converts RPE to XP weighting? → A: Linear scaling: `set_xp = base_xp * (RPE / 10)`. RPE 8 = 80% of base XP, RPE 10 = 100%.
- Q: What formula computes symmetric adherence score? → A: Linear: `adherence = max(0, 1 - abs(actual - target) / target)`. Produces 0-1 scale; +20% and -20% both score 0.8.
- Q: How many consecutive adherent days activate the nutrition streak multiplier? → A: 3 consecutive days (aligned with habit streak Bronze tier threshold).
- Q: How is monthly income tracked for the Treasury? → A: Single `MONTHLY_INCOME` value in Settings DB — same for every month unless manually changed.
- Q: How is base XP per set calculated before RPE weighting? → A: Volume-based: `base_xp = floor(volume * exercise_base_modifier / 1000)`. Heavier lifts with more reps earn more XP.

## User Scenarios & Testing

### User Story 1 - Financial Tracking & WIS XP (Priority: P1)

The player logs expenses in the Expense Log database throughout the month. At month-end, the financial engine calculates total spending per budget category, compares against the monthly limit, determines surplus or deficit, converts surplus into Gold (in-game currency), and grants WIS XP based on financial discipline. If spending exceeds a category's budget, an XP penalty is applied. The Treasury database stores the monthly summary.

**Why this priority**: Financial tracking directly impacts two core RPG currencies (Gold and WIS XP) and is the simplest domain module with the fewest external dependencies — making it the ideal first implementation.

**Independent Test**: Can be fully tested by creating expense entries and running the financial engine — verify surplus/deficit calculation, Gold conversion, WIS XP grant, and budget breach penalty without any other domain module.

**Acceptance Scenarios**:

1. **Given** the player has a "Food" budget category with a $500 monthly limit and $400 in expenses this month, **When** the financial engine runs for that month, **Then** the surplus is $100, Gold earned = floor($100 / GOLD_CONVERSION_RATE), and WIS XP is granted via an Activity Log entry.
2. **Given** the player has a "Entertainment" budget category with a $200 limit and $250 in expenses, **When** the financial engine runs, **Then** the deficit is $50 and a WIS XP penalty (BUDGET_BREACH_XP_PENALTY) is applied via an Activity Log entry.
3. **Given** the financial engine has already run for March 2026, **When** it is triggered again for March 2026, **Then** no duplicate Treasury row or Activity Log entry is created (idempotent).

---

### User Story 2 - Workout Logging & STR XP (Priority: P1)

The player logs individual sets in the Set Log database (linked to exercises from the Exercise Dictionary and grouped into Workout Sessions). The fitness engine calculates estimated 1RM using the Epley formula, tracks volume (weight x reps), detects progressive overload by comparing to historical data within a configurable window, and grants STR XP weighted by RPE (Rate of Perceived Exertion). Higher effort and progressive overload earn bonus XP.

**Why this priority**: Fitness is a primary engagement driver — players see direct physical effort translated into STR stat growth. It has the most complex calculations (1RM, progressive overload) and validates the cross-row comparison pattern.

**Independent Test**: Can be fully tested by creating set log entries and running the fitness engine — verify 1RM calculation, volume tracking, overload detection, RPE-weighted XP grant, and progressive delta without other domain modules.

**Acceptance Scenarios**:

1. **Given** the player logs a set of Bench Press at 100kg x 8 reps with RPE 8, **When** the fitness engine processes the set, **Then** Estimated 1RM = floor(100 x (1 + 8/30)) = 126kg and Volume = 800.
2. **Given** the player's previous best 1RM for Bench Press (within the overload window) was 120kg and the new 1RM is 126kg, **When** the fitness engine calculates progressive delta, **Then** overload is detected (+6kg, +5%) and bonus XP is granted.
3. **Given** RPE_XP_WEIGHT is enabled and the player logs a set with volume=800 and exercise modifier=1.0, **When** XP is calculated at RPE 9 vs RPE 6, **Then** RPE 9 set XP = floor(floor(800 * 1.0 / 1000) * 9/10) and RPE 6 set XP = floor(floor(800 * 1.0 / 1000) * 6/10) — linear RPE scaling.
4. **Given** a Workout Session contains 5 sets across 3 exercises, **When** the fitness engine processes the session, **Then** total session XP is the sum of all individual set XP values (each = floor(volume * modifier / 1000) * RPE/10), recorded as a single Activity Log entry mapped to STR.

---

### User Story 3 - Meal Logging & VIT XP (Priority: P2)

The player logs meals in the Meal Log database with macronutrient values (protein, carbs, fat). The nutrition engine calculates total daily calories, compares macro ratios and total intake against the player's TDEE (Total Daily Energy Expenditure) target from the Character database, computes an adherence score using symmetric scoring (penalizing both over- and under-eating equally), and grants VIT XP proportional to adherence. Consistently hitting targets earns a nutrition streak multiplier.

**Why this priority**: Nutrition tracking completes the health triad (habits + fitness + nutrition) feeding VIT, but has a more complex adherence model (symmetric scoring) and depends on TDEE configuration being set up first.

**Independent Test**: Can be fully tested by creating meal log entries with known macros and running the nutrition engine — verify calorie calculation, macro ratio comparison, symmetric adherence score, VIT XP grant, and nutrition streak multiplier.

**Acceptance Scenarios**:

1. **Given** the player's TDEE target is 2200 calories and they log meals totaling 2150 calories, **When** the nutrition engine calculates adherence, **Then** adherence = max(0, 1 - abs(2150 - 2200) / 2200) = 0.977 and VIT XP = floor(base_vit_xp * 0.977).
2. **Given** the player logs meals totaling 2800 calories (27% over TDEE target of 2200), **When** the nutrition engine calculates adherence, **Then** adherence = max(0, 1 - abs(2800 - 2200) / 2200) = 0.727 — symmetric to undershooting to 1600 calories (also 0.727).
3. **Given** the player has hit their TDEE target within tolerance for 3 consecutive days, **When** VIT XP is calculated on day 3+, **Then** a nutrition streak multiplier (NUTRITION_STREAK_MULTIPLIER = 1.15) is applied.
4. **Given** the player logs a meal with Protein=40g, Carbs=60g, Fat=20g, **When** calories are calculated, **Then** Calories = (40x4) + (60x4) + (20x9) = 580.

---

### Edge Cases

- **No expenses in a month**: Financial engine creates a Treasury row with $0 expenses, full surplus = MONTHLY_INCOME from Settings DB, and corresponding Gold/XP. If MONTHLY_INCOME is 0 or unset, no Treasury row is created.
- **Zero-weight or zero-rep set**: Fitness engine rejects sets where weight or reps is 0 — no 1RM calculation, no XP granted.
- **No previous 1RM history**: First-ever set for an exercise has no progressive delta — overload detection is skipped, base XP is granted.
- **No meals logged for a day**: Nutrition engine records 0 adherence for that day. No VIT XP granted. Nutrition streak broken.
- **Negative surplus (all categories breached)**: Financial engine applies XP penalty per breached category. Gold earned = 0 for the month. WIS XP penalty is capped — cannot reduce that month's net WIS XP grant below the sum of penalties (no retroactive XP removal).
- **Multiple workout sessions per day**: Each session generates its own Activity Log entry. All contribute to STR XP.
- **Meal with 0g of all macros**: Rejected as invalid entry (likely data entry error).
- **Budget category with $0 monthly limit**: Treated as "no budget set" — expenses are logged but no surplus/deficit is calculated for that category.
- **Overload window with no prior data**: Same as "no previous 1RM" — first data point, no comparison possible.
- **Financial engine runs mid-month**: Only processes complete months. Does not create partial Treasury entries.
- **Player changes TDEE mid-month**: Nutrition engine uses the TDEE value at the time of each daily calculation (not retroactive).

## Requirements

### Functional Requirements

#### Financial Engine

- **FR-001**: System MUST calculate monthly surplus or deficit per budget category by comparing total expenses against the category's monthly limit.
- **FR-002**: System MUST convert surplus into Gold using the configurable GOLD_CONVERSION_RATE (default: 10 — meaning $10 surplus = 1 Gold).
- **FR-003**: System MUST apply a WIS XP penalty (BUDGET_BREACH_XP_PENALTY, default: -50) for each budget category where expenses exceed the monthly limit.
- **FR-004**: System MUST read monthly income from `MONTHLY_INCOME` in the Settings DB (single value, same for every month unless manually changed) and create a Treasury row summarizing the month's income, expenses, surplus, Gold earned, and WIS XP.
- **FR-004a**: System MUST grant positive WIS XP for financial discipline when surplus is positive, calculated as `wis_xp = floor(gold_earned * WIS_XP_PER_GOLD)` where WIS_XP_PER_GOLD (default: 5) is configurable via Settings DB. Net WIS XP for the month = positive WIS XP − sum of breach penalties (minimum 0 — net WIS XP cannot go negative).
- **FR-005**: System MUST be idempotent — re-running for the same month MUST NOT create duplicate Treasury rows or Activity Log entries.
- **FR-006**: System MUST only process complete months (not partial/current month data).

#### Fitness Engine

- **FR-007**: System MUST calculate Estimated 1RM using the Epley formula: `weight x (1 + reps / 30)`, floored to an integer.
- **FR-008**: System MUST calculate Volume per set as `weight x reps`.
- **FR-009**: System MUST detect progressive overload by comparing current 1RM against the best 1RM for the same exercise within the configurable overload window (OVERLOAD_WINDOW_DAYS, default: 14 days).
- **FR-010**: System MUST weight XP by RPE when RPE_XP_WEIGHT is enabled using linear scaling: `set_xp = floor(base_xp * (RPE / 10))`. RPE 10 = 100% of base XP, RPE 5 = 50%.
- **FR-011**: System MUST aggregate all set XP within a workout session into a single Activity Log entry mapped to STR.
- **FR-012**: System MUST calculate progressive delta (absolute and percentage) when overload is detected.
- **FR-013**: System MUST reject sets with zero weight or zero reps (no XP, no 1RM calculation).
- **FR-013a**: System MUST calculate base XP per set as `base_xp = floor(volume * exercise_base_modifier / 1000)` before applying RPE weighting. The exercise's Base XP Modifier comes from the Exercise Dictionary.

#### Nutrition Engine

- **FR-014**: System MUST calculate daily total calories by summing per-meal calorie values (each meal's calories are computed in Notion via formula property: `(protein x 4) + (carbs x 4) + (fat x 9)`) across all meal rows for the day. The Python engine performs the cross-row aggregation; per-meal calorie calculation is a Notion formula.
- **FR-015**: System MUST compute an adherence score using linear symmetric scoring: `adherence = max(0, 1 - abs(actual - target) / target)`. Over-eating and under-eating by the same percentage MUST produce the same score.
- **FR-016**: System MUST compare daily intake against the player's TDEE target from the Character database or Settings DB (default: DEFAULT_TDEE = 2200).
- **FR-017**: System MUST apply a nutrition streak multiplier (NUTRITION_STREAK_MULTIPLIER, default: 1.15) when the player hits their TDEE target within tolerance (adherence ≥ 0.9) for 3 or more consecutive days. Streak resets to 0 on a non-adherent day (adherence < 0.9).
- **FR-018**: System MUST grant VIT XP proportional to the daily adherence score via an Activity Log entry.
- **FR-019**: System MUST reject meal entries where all macronutrients are 0 (invalid data).

#### Cross-Cutting

- **FR-020**: All engines MUST read configurable constants from the Settings DB (via `config.py`), falling back to hardcoded defaults.
- **FR-021**: All engines MUST create Activity Log entries as their XP output — the Activity Log remains the single source of truth.
- **FR-022**: All engines MUST log operations using the shared `logger.py` module.

### Key Entities

- **Budget Category**: A spending category with a name, monthly spending limit, and type (needs vs wants). Player-defined.
- **Expense**: A single spending event with amount, date, description, and linked category. Logged by the player in Notion.
- **Treasury**: Monthly financial summary — income, total expenses, surplus/deficit, Gold earned, WIS XP. One row per month.
- **Exercise**: A movement definition from the Exercise Dictionary — name, muscle group, movement type, base XP modifier.
- **Workout Session**: A group of sets performed on a date — session name, duration, linked character.
- **Set**: A single exercise effort — weight, reps, RIR (Reps in Reserve), RPE, linked exercise and session. Volume and Estimated 1RM are derived.
- **Meal**: A logged meal with date, protein (g), carbs (g), fat (g). Calories are derived via formula.
- **Ingredients Library**: Reference data — name, macros per 100g. Used for lookup convenience in Notion, not directly by the engines.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Financial surplus/deficit calculation matches manual spreadsheet verification for 3 test months of data.
- **SC-002**: Gold conversion produces correct integer values (floor division) matching the configured rate.
- **SC-003**: Estimated 1RM matches the Epley formula output within +/-0 (exact integer match via floor).
- **SC-004**: Progressive overload is detected correctly when new 1RM exceeds historical best within the configured window.
- **SC-005**: RPE-weighted XP grants proportionally more XP for higher-effort sets (verifiable with test data at RPE 6, 7, 8, 9, 10).
- **SC-006**: Symmetric adherence scoring produces identical penalties for equal percentage over- and under-eating (e.g., +20% and -20% from TDEE produce the same adherence score).
- **SC-007**: Nutrition streak multiplier activates after 3 consecutive adherent days and resets on non-adherent days.
- **SC-008**: All three engines are idempotent — re-running produces no duplicate Activity Log entries or summary rows.
- **SC-009**: All XP grants flow through the Activity Log and are correctly aggregated by `xp_engine.update_character_stats()` into the corresponding stats (WIS, STR, VIT).

## Assumptions

- Phase 1 (Foundation), Phase 2 (HP/Death/Economy), and Phase 3 (XP Engine/Streaks/Leveling) are complete before Phase 4 implementation begins.
- The Activity Log, Character DB, Settings DB, Budget Categories, Expense Log, Exercise Dictionary, Workout Sessions, Set Log, Meal Log, Ingredients Library, and Treasury databases all exist (created in Phase 1).
- Notion buttons for expense entry, set logging, and meal logging are configured in Phase 1 (database creation).
- The `config.py` Settings DB reader, `logger.py`, `notion_client.py`, `xp_engine.py`, `hp_engine.py`, `streak_engine.py`, and `habit_engine.py` are all operational from prior phases.
- The financial engine runs monthly (triggered by monthly automation in Phase 7). Fitness and nutrition engines run daily (triggered by daily automation in Phase 7).
- `GOLD_CONVERSION_RATE = 10` means "$10 surplus = 1 Gold" (e.g., $95 surplus = 9 Gold).
- `MONTHLY_INCOME` is a single value in Settings DB used for all months. Player updates
  it manually when income changes. Mid-month changes take effect on the next monthly
  automation run; current month's already-calculated surplus uses the value read at
  automation start time.
- RPE is recorded by the player on a 1-10 scale (standard Borg RPE). If RPE is not
  provided for a set (field is empty/null), the fitness engine defaults to RPE=7.
  The Set Log schema has RPE as an optional Number property.
- TDEE is a single number stored in the Character DB or Settings DB — not a calculated value. The player enters it manually or it is seeded during onboarding.
- The Ingredients Library is reference-only — the nutrition engine works with meal-level macros, not individual ingredients. Ingredient lookup is a Notion-native convenience, not a Python concern.
- `habit_engine.py` is already fully designed and built in Phase 3. Phase 4 does not duplicate it.
