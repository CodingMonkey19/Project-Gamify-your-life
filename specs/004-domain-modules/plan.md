# Implementation Plan: Phase 4 — Domain Modules (Financial, Fitness & Nutrition Engines)

**Branch**: `004-domain-modules` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-domain-modules/spec.md`

## Summary

Build three domain-specific engines that translate real-world activities (spending, workouts,
meals) into RPG stat progression via the Activity Log. The financial engine processes monthly
expense data against budget categories, converts surplus to Gold, and grants/penalizes WIS XP.
The fitness engine calculates 1RM (Epley), tracks volume and progressive overload, and grants
RPE-weighted STR XP. The nutrition engine computes symmetric calorie adherence scores and grants
VIT XP with a nutrition streak multiplier. All engines are idempotent, read config from Settings
DB, and output exclusively through Activity Log entries.

Key clarifications integrated:
- RPE-to-XP weighting: linear scaling `set_xp = floor(base_xp * (RPE / 10))`
- Base set XP: volume-based `base_xp = floor(volume * exercise_base_modifier / 1000)`
- Adherence formula: linear symmetric `adherence = max(0, 1 - abs(actual - target) / target)`
- Nutrition streak threshold: 3 consecutive adherent days (matches habit Bronze tier)
- Income source: single `MONTHLY_INCOME` value in Settings DB

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv` (inherited from Phase 1)
**Storage**: Notion — Budget Categories, Expense Log, Treasury, Exercise Dictionary, Workout Sessions, Set Log, Meal Log, Activity Log, Character DB, Settings DB
**Testing**: `pytest` with mock Notion responses (`conftest.py` from Phases 1-3, extended)
**Target Platform**: GitHub Actions (scheduled daily/monthly), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Financial engine < 15s per month; fitness engine < 20s per session; nutrition engine < 10s per day
**Constraints**: All XP/Gold values are integers (floor rounding). Activity Log is append-only.
Phases 1-3 must be complete. Notion API rate limit (3 req/sec). Financial engine runs monthly only.
Fitness and nutrition engines run daily.
**Scale/Scope**: Single player, ~10-30 expenses/month, ~5-15 sets/session, ~3-6 meals/day,
8+ budget categories, 25+ exercises in dictionary

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All data stored in Notion (Expense Log, Set Log, Meal Log). Notion formulas handle single-row calculations (Calories, Volume, Est 1RM). Python handles cross-row aggregation (monthly budget rollup, progressive overload comparison, daily calorie totals). Buttons create log entries (Notion-native). Python writes results back to Activity Log and Treasury |
| II. Python for Complex Orchestration | PASS | Three new tools in `tools/`, each handling one concern: `financial_engine.py` (budget rollup + Gold conversion), `fitness_engine.py` (1RM + overload + RPE XP), `nutrition_engine.py` (adherence + nutrition streak). No tool does reasoning. All are deterministic and independently testable |
| III. WAT Architecture | PASS | Three new tools added to `tools/`. Each is a deterministic execution unit callable independently or via daily/monthly automation. No embedded reasoning |
| IV. Settings DB as Canonical Config | PASS | GOLD_CONVERSION_RATE, BUDGET_BREACH_XP_PENALTY, RPE_XP_WEIGHT, OVERLOAD_WINDOW_DAYS, DEFAULT_TDEE, MACRO_TOLERANCE_PCT, NUTRITION_STREAK_MULTIPLIER, MONTHLY_INCOME — all read from `config.py` / Settings DB. No hardcoded balance values in engine files |
| V. Idempotency | PASS | Financial engine checks for existing Treasury row for the month before creating. All engines check for existing Activity Log entries before creating XP grants. Re-runs produce no duplicates |
| VI. Free-First | PASS | No new dependencies. Reuses Phase 1 infrastructure. No paid services |

## Project Structure

### Documentation (this feature)

```text
specs/004-domain-modules/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── financial_engine.py  # Monthly budget rollup, Gold conversion, WIS XP
├── fitness_engine.py    # 1RM, volume, progressive overload, RPE-weighted STR XP
├── nutrition_engine.py  # Calorie adherence, symmetric scoring, nutrition streak, VIT XP
│
├── config.py            # (Phase 1 — already exists) Domain engine constants from Settings DB
├── logger.py            # (Phase 1 — already exists)
├── notion_client.py     # (Phase 1 — already exists)
├── xp_engine.py         # (Phase 3 — already exists) Called after XP grants for stat refresh
├── hp_engine.py         # (Phase 2 — already exists)
├── streak_engine.py     # (Phase 3 — already exists)
├── habit_engine.py      # (Phase 3 — already exists)
└── coin_engine.py       # (Phase 2 — already exists) Gold added via coin_engine

tests/
├── test_financial_engine.py  # Surplus/deficit, Gold conversion, breach penalty, idempotency
├── test_fitness_engine.py    # Epley accuracy, RPE weighting, overload detection, volume
├── test_nutrition_engine.py  # Symmetric adherence, nutrition streak, calorie calc, edge cases
├── conftest.py               # (Phases 1-3 — extend with domain engine mock fixtures)
```

**Structure Decision**: Flat `tools/` layout consistent with Phases 1-3. Each engine is a single file with clear boundaries. Tests mirror engine files 1:1.

## Contracts

### financial_engine.py

```python
def get_budget_categories(character_id: str) -> list
    """Fetch all budget categories with monthly limits.
    Returns: [{"id": str, "name": str, "monthly_limit": float, "type": str}, ...]"""

def get_monthly_expenses(character_id: str, year: int, month: int) -> list
    """Fetch all expenses for a given month, grouped by category.
    Returns: [{"category_id": str, "category_name": str, "total": float}, ...]"""

def calculate_monthly_summary(categories: list, expenses: list, monthly_income: float) -> dict
    """Calculate surplus/deficit per category and overall.
    Returns: {
        "month": str,
        "income": float,
        "total_expenses": float,
        "surplus": float,
        "categories": [{"name": str, "limit": float, "spent": float, "surplus": float, "breached": bool}, ...],
        "gold_earned": int,  # floor(max(0, surplus) / GOLD_CONVERSION_RATE)
        "wis_xp": int,       # positive for surplus, negative for breaches (sum of penalties)
        "breached_count": int
    }"""

def process_monthly_finances(character_id: str, year: int, month: int) -> dict
    """Orchestrator: runs full monthly financial processing.
    1. Check Treasury for existing row (idempotency guard)
    2. Fetch budget categories and monthly expenses
    3. Read MONTHLY_INCOME from Settings DB
    4. Calculate summary
    5. Create Treasury row
    6. Create Activity Log entry (WIS XP) if XP != 0
    7. Add Gold via coin_engine if gold_earned > 0
    8. Call xp_engine.update_character_stats()
    Returns: summary dict or None if already processed"""
```

### fitness_engine.py

```python
def calculate_1rm(weight: float, reps: int) -> int
    """Epley formula: floor(weight * (1 + reps / 30)).
    Returns 0 if weight <= 0 or reps <= 0."""

def calculate_volume(weight: float, reps: int) -> int
    """Volume = weight * reps. Returns 0 if invalid input."""

def calculate_set_xp(volume: int, exercise_modifier: float, rpe: int = 7) -> int
    """Base XP = floor(volume * exercise_modifier / 1000).
    If RPE_XP_WEIGHT enabled: set_xp = floor(base_xp * (rpe / 10)).
    If disabled: set_xp = base_xp.
    Returns 0 if volume <= 0."""

def get_best_1rm(character_id: str, exercise_id: str, window_days: int = None) -> int
    """Query Set Log for best 1RM of this exercise within the overload window.
    window_days defaults to OVERLOAD_WINDOW_DAYS from config.
    Returns 0 if no prior data."""

def calculate_progressive_delta(current_1rm: int, best_1rm: int) -> dict
    """Compare current vs historical best.
    Returns: {"overload": bool, "absolute": int, "percentage": float}
    overload=True if current_1rm > best_1rm."""

def process_set(character_id: str, set_data: dict) -> dict
    """Process a single set: calculate 1RM, volume, XP, progressive delta.
    set_data: {"exercise_id": str, "weight": float, "reps": int, "rpe": int|None}
    Returns: {"1rm": int, "volume": int, "xp": int, "delta": dict, "valid": bool}
    Returns {"valid": False} for zero weight/reps."""

def process_workout_session(character_id: str, session_id: str) -> dict
    """Orchestrator: process all sets in a session.
    1. Fetch all sets for session
    2. Process each set (skip invalid)
    3. Sum XP across all sets
    4. Check for existing Activity Log entry (idempotency)
    5. Create single Activity Log entry (Type: WORKOUT, mapped to STR)
    6. Write progressive delta to each set row
    7. Call xp_engine.update_character_stats()
    Returns: {"session_id": str, "total_xp": int, "sets_processed": int, "overloads": int}"""

def process_daily_workouts(character_id: str, date: str) -> list
    """Process all workout sessions for a given date.
    Returns: list of session results."""
```

### nutrition_engine.py

```python
def calculate_calories(protein: float, carbs: float, fat: float) -> int
    """Calories = floor((protein * 4) + (carbs * 4) + (fat * 9)).
    Returns 0 if all macros are 0 (invalid — rejected)."""

def calculate_adherence(actual_calories: int, target_tdee: int) -> float
    """Symmetric adherence: max(0, 1 - abs(actual - target) / target).
    Returns 0.0 if target_tdee <= 0. Returns 1.0 for exact match."""

def get_daily_meals(character_id: str, date: str) -> list
    """Fetch all meals for a given date.
    Returns: [{"id": str, "protein": float, "carbs": float, "fat": float, "calories": int}, ...]"""

def get_nutrition_streak(character_id: str, date: str) -> int
    """Count consecutive adherent days ending at date (inclusive).
    An adherent day = adherence >= (1 - MACRO_TOLERANCE_PCT / 100).
    Returns 0 if no streak."""

def calculate_vit_xp(adherence: float, nutrition_streak: int, base_vit_xp: int = None) -> int
    """VIT XP = floor(base_vit_xp * adherence * streak_multiplier).
    streak_multiplier = NUTRITION_STREAK_MULTIPLIER if nutrition_streak >= 3, else 1.0.
    base_vit_xp defaults to DEFAULT_HABIT_XP from config.
    Returns 0 if adherence == 0."""

def process_daily_nutrition(character_id: str, date: str) -> dict
    """Orchestrator: full daily nutrition processing.
    1. Fetch all meals for date
    2. Reject meals with all-zero macros
    3. Sum daily calories
    4. Read TDEE from Character DB or Settings DB
    5. Calculate adherence score
    6. Calculate nutrition streak
    7. Calculate VIT XP (with streak multiplier if applicable)
    8. Check for existing Activity Log entry (idempotency)
    9. Create Activity Log entry (VIT XP)
    10. Call xp_engine.update_character_stats()
    Returns: {"date": str, "total_calories": int, "tdee": int, "adherence": float,
              "streak": int, "multiplier": float, "vit_xp": int}
    Returns None if no valid meals logged."""
```

## Implementation Order

| Step | Function/File | Depends On | Delivers |
|------|--------------|------------|----------|
| 1 | `config.py` updates | Phase 1 config | New constants: MONTHLY_INCOME, GOLD_CONVERSION_RATE, BUDGET_BREACH_XP_PENALTY, RPE_XP_WEIGHT, OVERLOAD_WINDOW_DAYS, DEFAULT_TDEE, MACRO_TOLERANCE_PCT, NUTRITION_STREAK_MULTIPLIER |
| 2 | `financial_engine.get_budget_categories()` | Phase 1 (notion_client) | Budget category query |
| 3 | `financial_engine.get_monthly_expenses()` | Phase 1 (notion_client) | Monthly expense aggregation |
| 4 | `financial_engine.calculate_monthly_summary()` | Steps 2-3 | Pure math: surplus/deficit, Gold, WIS XP |
| 5 | `financial_engine.process_monthly_finances()` | Steps 2-4, Phase 2 (coin_engine), Phase 3 (xp_engine) | Full monthly orchestration |
| 6 | `test_financial_engine.py` | Steps 2-5 | Financial engine test suite |
| 7 | `fitness_engine.calculate_1rm()` | None (pure math) | Epley formula |
| 8 | `fitness_engine.calculate_volume()` | None (pure math) | Volume calc |
| 9 | `fitness_engine.calculate_set_xp()` | Steps 7-8 | RPE-weighted XP per set |
| 10 | `fitness_engine.get_best_1rm()` | Phase 1 (notion_client) | Historical 1RM query |
| 11 | `fitness_engine.calculate_progressive_delta()` | Step 10 | Overload detection |
| 12 | `fitness_engine.process_set()` | Steps 7-9, 11 | Single set processing |
| 13 | `fitness_engine.process_workout_session()` | Step 12, Phase 3 (xp_engine) | Session orchestration |
| 14 | `fitness_engine.process_daily_workouts()` | Step 13 | Daily workout orchestration |
| 15 | `test_fitness_engine.py` | Steps 7-14 | Fitness engine test suite |
| 16 | `nutrition_engine.calculate_calories()` | None (pure math) | Calorie formula |
| 17 | `nutrition_engine.calculate_adherence()` | None (pure math) | Symmetric adherence |
| 18 | `nutrition_engine.get_daily_meals()` | Phase 1 (notion_client) | Meal query |
| 19 | `nutrition_engine.get_nutrition_streak()` | Steps 17-18 | Consecutive adherent day count |
| 20 | `nutrition_engine.calculate_vit_xp()` | Steps 17, 19 | VIT XP with streak multiplier |
| 21 | `nutrition_engine.process_daily_nutrition()` | Steps 16-20, Phase 3 (xp_engine) | Daily nutrition orchestration |
| 22 | `test_nutrition_engine.py` | Steps 16-21 | Nutrition engine test suite |
| 23 | `conftest.py` updates | Steps 6, 15, 22 | Mock fixtures for domain engines |

**Key dependencies**:
- `financial_engine` depends on `coin_engine` (Phase 2) for Gold credits and `xp_engine` (Phase 3) for stat refresh
- `fitness_engine` depends on `xp_engine` (Phase 3) for stat refresh after session processing
- `nutrition_engine` depends on `xp_engine` (Phase 3) for stat refresh after daily processing
- All three engines depend on `config.py` (Phase 1) for configurable constants
- All three engines depend on `notion_client.py` (Phase 1) for Notion API access
- Financial engine is independent of fitness/nutrition — can be built in parallel
- Fitness and nutrition pure math functions (steps 7-9, 16-17) have zero dependencies and can be built first
