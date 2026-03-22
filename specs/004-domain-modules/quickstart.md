# Quickstart: Phase 4 — Domain Modules (Financial, Fitness & Nutrition Engines)

**Date**: 2026-03-22
**Feature**: 004-domain-modules

## Prerequisites

- Phase 1 complete (config, logger, notion_client, databases created, seed data)
- Phase 2 complete (hp_engine, coin_engine operational)
- Phase 3 complete (xp_engine, streak_engine, habit_engine operational)
- Settings DB has MONTHLY_INCOME, DEFAULT_TDEE configured
- Budget Categories seeded with at least 1 category
- Exercise Dictionary seeded with at least 1 exercise

## Manual Verification Steps

### 1. Financial Engine — Monthly Processing

1. Create 3+ expense entries in Expense Log for a past month (e.g., Feb 2026)
2. Set MONTHLY_INCOME in Settings DB (e.g., 3000)
3. Run: `python tools/financial_engine.py --character-id <ID> --year 2026 --month 2`
4. Verify:
   - Treasury row created for "2026-02"
   - Surplus = MONTHLY_INCOME - total expenses
   - Gold = floor(max(0, surplus) / 10)
   - Activity Log entry with WIS XP
   - Coin balance increased by Gold earned
5. Re-run same command → verify no duplicates (idempotency)

### 2. Financial Engine — Budget Breach

1. Create expenses exceeding a budget category's limit
2. Run financial engine for that month
3. Verify:
   - WIS XP penalty applied (-50 per breached category)
   - Treasury row shows breached_count > 0
   - Gold earned = 0 if overall surplus is negative

### 3. Fitness Engine — Set Processing

1. Create a Workout Session for today
2. Create 3 Set Log entries (e.g., Bench Press: 100kg x 8, 100kg x 6, 90kg x 10)
3. Run: `python tools/fitness_engine.py --character-id <ID> --date today`
4. Verify per set:
   - 1RM = floor(weight * (1 + reps/30))
   - Volume = weight * reps
   - Base XP = floor(volume * exercise_modifier / 1000)
   - Set XP = floor(base_xp * RPE/10) (if RPE_XP_WEIGHT enabled)
5. Verify session total:
   - Single Activity Log entry (Type: WORKOUT) with sum of set XPs
   - STR XP updated in Character DB

### 4. Fitness Engine — Progressive Overload

1. Log a set for an exercise you've logged before (within 14 days)
2. Use a weight/rep combo that produces a higher 1RM than the previous best
3. Run fitness engine
4. Verify:
   - Progressive Delta written to Set Log row
   - Overload detected in output

### 5. Fitness Engine — Zero Weight/Rep Rejection

1. Create a set with weight=0 or reps=0
2. Run fitness engine
3. Verify: set is skipped, no XP granted, no 1RM calculated

### 6. Nutrition Engine — Daily Processing

1. Create 2-3 Meal Log entries for today (e.g., P=30 C=50 F=15, P=40 C=60 F=20)
2. Set DEFAULT_TDEE in Settings DB (e.g., 2200)
3. Run: `python tools/nutrition_engine.py --character-id <ID> --date today`
4. Verify:
   - Total calories = sum of each meal's (P*4 + C*4 + F*9)
   - Adherence = max(0, 1 - abs(total - 2200) / 2200)
   - Activity Log entry with VIT XP = floor(base * adherence * multiplier)

### 7. Nutrition Engine — Symmetric Adherence

1. Log meals totaling 2640 calories (20% over 2200 TDEE)
2. In a separate test: log meals totaling 1760 calories (20% under 2200 TDEE)
3. Verify both produce adherence = 0.8 (identical score)

### 8. Nutrition Engine — Streak Multiplier

1. Ensure 2 previous consecutive days had adherence >= 0.9
2. Log adherent meals for today (3rd consecutive day)
3. Run nutrition engine
4. Verify: VIT XP includes 1.15x multiplier

### 9. Nutrition Engine — No Meals / All-Zero Macros

1. Run nutrition engine for a day with no meals → verify no XP, no Activity Log entry
2. Create a meal with P=0, C=0, F=0 → verify it's rejected

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No Treasury row created | MONTHLY_INCOME = 0 and no expenses | Set MONTHLY_INCOME in Settings DB |
| Duplicate Activity Log entries | Idempotency guard failed | Check date/type filter in engine |
| XP not updating in Character | `xp_engine.update_character_stats()` not called | Verify engine calls stat refresh |
| Progressive delta always 0 | No prior sets within OVERLOAD_WINDOW_DAYS | Log sets over multiple days first |
| Adherence always 1.0 | TDEE = 0 or not set | Set DEFAULT_TDEE in Settings DB |
| Streak multiplier not activating | Fewer than 3 consecutive adherent days | Check previous days' adherence >= 0.9 |
| Set XP = 0 | Weight or reps = 0, or volume too low | Check set data, verify exercise modifier > 0 |
| Gold not credited | Overall surplus <= 0 | Check MONTHLY_INCOME vs total expenses |
| RPE weighting has no effect | RPE_XP_WEIGHT = False in Settings | Set RPE_XP_WEIGHT = True |
