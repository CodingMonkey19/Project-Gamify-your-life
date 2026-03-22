# Data Model: Phase 4 — Domain Modules (Financial, Fitness & Nutrition Engines)

**Date**: 2026-03-22
**Feature**: 004-domain-modules

## Core Principle: Activity Log as Single Source of Truth

Like all prior phases, XP grants from domain modules flow through the Activity Log.
The financial, fitness, and nutrition engines create Activity Log entries as their output.
`xp_engine.update_character_stats()` re-sums all entries to update stat totals.

## Financial Domain

### Budget Categories DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Category | Title | Budget category name (e.g., "Food", "Entertainment") |
| Monthly Limit | Number | Maximum monthly spend for this category |
| Type | Select | "Needs" or "Wants" classification |
| Character | Relation → Character | Links category to player |

### Expense Log DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Description | Title | What was purchased |
| Amount | Number | Cost of the expense |
| Date | Date | When the expense occurred |
| Category | Relation → Budget Categories | Links to budget category |
| Character | Relation → Character | Links to player |

### Treasury DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Month | Title | Format: "YYYY-MM" (idempotency key) |
| Income | Number | MONTHLY_INCOME from Settings DB |
| Total Expenses | Number | Sum of all expenses for the month |
| Surplus | Number | Income - Total Expenses |
| Gold Earned | Number | floor(max(0, surplus) / GOLD_CONVERSION_RATE) |
| WIS XP | Number | Positive for surplus, negative for breaches |
| Breached Categories | Number | Count of categories over budget |
| Character | Relation → Character | Links to player |

### Financial Calculation

```
Per-category surplus = category.monthly_limit - sum(expenses for category in month)
  If surplus < 0 → category is breached → WIS XP penalty = BUDGET_BREACH_XP_PENALTY (-50)

Overall surplus = MONTHLY_INCOME - sum(all expenses in month)
Gold earned = floor(max(0, overall_surplus) / GOLD_CONVERSION_RATE)

Total WIS XP = base_financial_xp - (breached_count * abs(BUDGET_BREACH_XP_PENALTY))
  where base_financial_xp = positive XP for financial discipline (configurable)
```

### Financial State Transition

```
Monthly automation triggers (1st of month)
  → financial_engine.process_monthly_finances(character_id, prev_year, prev_month)
    → Check Treasury for existing "YYYY-MM" row → if exists, SKIP (idempotent)
    → Fetch budget categories
    → Fetch all expenses for prev_month, group by category
    → Read MONTHLY_INCOME from Settings DB
    → Calculate surplus/deficit per category
    → Calculate overall surplus, Gold, WIS XP
    → Create Treasury row
    → Create Activity Log entry (Type: FINANCIAL, WIS XP amount)
    → If Gold > 0: coin_engine.add_gold(character_id, gold_earned)
    → xp_engine.update_character_stats(character_id)
```

## Fitness Domain

### Exercise Dictionary DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Exercise Name | Title | Name of the movement |
| Muscle Group | Select | Primary muscle (Chest, Back, Legs, Shoulders, Arms, Core) |
| Movement Type | Select | Compound or Isolation |
| Base XP Modifier | Number | Multiplier for XP calculation (e.g., 1.5 for compound, 1.0 for isolation) |

### Workout Sessions DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Session Name | Title | Name/label for the workout |
| Session Date | Date | When the workout occurred |
| Duration | Number | Minutes (optional, for tracking) |
| Character | Relation → Character | Links to player |

### Set Log DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Set# | Number | Set number within the session |
| Exercise | Relation → Exercise Dictionary | Which exercise |
| Session | Relation → Workout Sessions | Which session |
| Weight | Number | Weight lifted (kg) |
| Reps | Number | Repetitions completed |
| RIR | Number | Reps in Reserve (optional) |
| RPE | Number | Rate of Perceived Exertion 1-10 (default: 7 if empty) |
| Volume | Formula (Notion) | `prop("Weight") * prop("Reps")` |
| Estimated 1RM | Formula (Notion) | `prop("Weight") * (1 + prop("Reps") / 30)` |
| Progressive Delta | Number | Written by Python — absolute difference from best 1RM |
| Session XP | Number | Written by Python — XP earned for this set |

### Fitness Calculations

```
1RM (Epley) = floor(weight * (1 + reps / 30))
Volume = weight * reps
Base XP = floor(volume * exercise_base_modifier / 1000)
Set XP (RPE weighted) = floor(base_xp * (RPE / 10))   # if RPE_XP_WEIGHT enabled
Set XP (no RPE)       = base_xp                         # if RPE_XP_WEIGHT disabled
Session XP = sum(set_xp for all valid sets in session)

Progressive overload:
  best_1rm = max(1RM for exercise within OVERLOAD_WINDOW_DAYS)
  current_1rm = 1RM for this set
  overload = current_1rm > best_1rm
  delta_abs = current_1rm - best_1rm
  delta_pct = (delta_abs / best_1rm) * 100
```

### Fitness State Transition

```
Daily automation triggers (or real-time after session)
  → fitness_engine.process_daily_workouts(character_id, today)
    → Fetch all Workout Sessions for today
    → For each session:
      → fitness_engine.process_workout_session(character_id, session_id)
        → Fetch all sets for session
        → For each set:
          → Reject if weight=0 or reps=0
          → Calculate 1RM, volume, base_xp, set_xp (RPE-weighted)
          → Get best_1rm for exercise within overload window
          → Calculate progressive delta
          → Write progressive delta + session XP to Set Log row
        → Sum all set XP → total session XP
        → Check for existing Activity Log entry for session (idempotent)
        → Create Activity Log entry (Type: WORKOUT, EXP + (Workout) = total_xp, Domain: gym → STR)
        → xp_engine.update_character_stats(character_id)
```

## Nutrition Domain

### Meal Log DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Meal Name | Title | Description of the meal |
| Date | Date | When the meal was eaten |
| Protein | Number | Grams of protein |
| Carbs | Number | Grams of carbohydrates |
| Fat | Number | Grams of fat |
| Calories | Formula (Notion) | `prop("Protein")*4 + prop("Carbs")*4 + prop("Fat")*9` |
| Character | Relation → Character | Links to player |

### Ingredients Library DB Schema (Reference Only)

| Property | Type | Purpose |
|----------|------|---------|
| Name | Title | Ingredient name |
| Protein per 100g | Number | Protein content |
| Carbs per 100g | Number | Carb content |
| Fat per 100g | Number | Fat content |
| Calories per 100g | Number | Derived or entered |

Note: Ingredients Library is Notion-native convenience for meal logging. The nutrition engine
operates on meal-level macros, not individual ingredients.

### Nutrition Calculations

```
Daily calories = sum(floor((protein*4) + (carbs*4) + (fat*9)) for each meal)
  Note: Python recalculates from raw macros, does not rely on Notion formula

Adherence = max(0, 1 - abs(actual_calories - TDEE) / TDEE)
  TDEE read from Character DB or Settings DB (default: DEFAULT_TDEE = 2200)
  Adherence of 1.0 = exact match, 0.0 = 100%+ deviation

Adherent day = adherence >= (1 - MACRO_TOLERANCE_PCT / 100)
  With default tolerance 10%: adherent if adherence >= 0.9

Nutrition streak = count of consecutive adherent days ending at today
  Multiplier = NUTRITION_STREAK_MULTIPLIER (1.15) if streak >= 3, else 1.0

VIT XP = floor(base_vit_xp * adherence * multiplier)
  base_vit_xp = DEFAULT_HABIT_XP from config (default: 5)
```

### Nutrition State Transition

```
Daily automation triggers
  → nutrition_engine.process_daily_nutrition(character_id, today)
    → Fetch all meals for today
    → Reject meals with protein=0, carbs=0, fat=0 (all zero)
    → If no valid meals → return None (no XP, streak broken)
    → Sum daily calories from raw macros
    → Read TDEE from Character DB / Settings DB
    → Calculate adherence score
    → Calculate nutrition streak (query previous days)
    → Determine multiplier (1.15 if streak >= 3, else 1.0)
    → Calculate VIT XP
    → Check for existing Activity Log entry (idempotent)
    → Create Activity Log entry (Type: NUTRITION, EXP + (Nutrition) = vit_xp, Domain: nutrition → VIT)
    → xp_engine.update_character_stats(character_id)
```

## Activity Log Entry Types (Phase 4 additions)

| Type | XP Column | Domain → Stat | Created By |
|------|-----------|--------------|------------|
| FINANCIAL | EXP + (Financial) | finance → WIS | `financial_engine.process_monthly_finances()` |
| WORKOUT | EXP + (Workout) | gym → STR | `fitness_engine.process_workout_session()` |
| NUTRITION | EXP + (Nutrition) | nutrition → VIT | `nutrition_engine.process_daily_nutrition()` |

## Settings DB Additions (Phase 4)

| Setting Key | Default | Used By |
|------------|---------|---------|
| MONTHLY_INCOME | 0 | financial_engine |
| GOLD_CONVERSION_RATE | 10 | financial_engine |
| BUDGET_BREACH_XP_PENALTY | -50 | financial_engine |
| RPE_XP_WEIGHT | True | fitness_engine |
| OVERLOAD_WINDOW_DAYS | 14 | fitness_engine |
| DEFAULT_TDEE | 2200 | nutrition_engine |
| MACRO_TOLERANCE_PCT | 10 | nutrition_engine |
| NUTRITION_STREAK_MULTIPLIER | 1.15 | nutrition_engine |
