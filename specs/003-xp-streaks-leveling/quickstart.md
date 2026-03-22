# Quickstart: Phase 3 — XP Engine, Streaks & Leveling

## Prerequisites

- Phase 1 complete: all 33 databases exist, `db_ids.json` populated, seed data loaded
- Phase 2 complete: `hp_engine.py` and `coin_engine.py` operational
- `.env` configured with `NOTION_API_KEY` and `NOTION_PARENT_PAGE_ID`
- `tools/smoke_test.py` passes all checks
- Default Character row exists with Starting HP = 1000

## What Phase 3 Adds

Three new tools:

| Tool | Purpose |
|------|---------|
| `tools/xp_engine.py` | Exponential leveling curves, per-stat XP aggregation, class bonus, progress bars |
| `tools/streak_engine.py` | Streak tracking, tier advancement, decay, XP multipliers |
| `tools/habit_engine.py` | Daily habit processing orchestration (good habits → XP, bad habits → HP damage) |

## Testing

```bash
# Run Phase 3 tests
pytest tests/test_xp_engine.py tests/test_streak_engine.py tests/test_habit_engine.py -v

# Run all tests (including Phase 1 + 2)
pytest tests/ -v
```

## Manual Verification

### Test XP Calculation

1. Open **Good Habit** database in Notion
2. Click "Check-in" on a habit (creates Activity Log entry)
3. Run: `python -c "from tools.xp_engine import update_character_stats; print(update_character_stats('CHARACTER_ID'))"`
4. Check Character page — the stat mapped to the habit's domain should show increased XP

### Test Leveling

1. Grant enough XP to a stat to cross a level threshold (Level 2 = 1200 cumulative XP with defaults)
2. Run: `python -c "from tools.xp_engine import level_from_xp; print(level_from_xp(1205))"`
3. Verify output is `2`

### Test Streak Tracking

1. Check in a habit on consecutive days (or simulate via Activity Log entries)
2. Run: `python -c "from tools.streak_engine import check_streaks; print(check_streaks('CHARACTER_ID', '2026-03-22'))"`
3. Open Streak Tracker database — verify Current Streak incremented
4. After 3 consecutive days, verify tier is "Bronze" and multiplier is 1.1

### Test Streak Decay

1. Skip a day for an active habit
2. Run daily processing for the skipped day
3. Verify streak reset to 0 and tier reset to "None" in Streak Tracker

### Test Class Bonus

1. Set character's Class to "Warrior" in Character database
2. Earn 100 STR XP via habits
3. Run `update_character_stats()`
4. Verify STR XP on Character shows 110 (100 * 1.1)
5. Verify INT XP has no bonus applied

### Test Daily Processing

1. Check in multiple good habits and log one bad habit
2. Run: `python -c "from tools.habit_engine import process_daily_habits, process_bad_habits; print(process_daily_habits('CHARACTER_ID', '2026-03-22')); print(process_bad_habits('CHARACTER_ID', '2026-03-22'))"`
3. Verify: XP granted for good habits, streaks updated, HP damage for bad habit
4. Run again — verify no duplicate XP or damage (idempotent)

### Test Progress Bar

1. Run: `python -c "from tools.xp_engine import generate_progress_bar; print(generate_progress_bar(400, 1200, 10))"`
2. Verify output: `◾◾◾◽◽◽◽◽◽◽ 400/1200`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| XP not updating on Character page | Run `xp_engine.update_character_stats()` to force recalculation |
| Streak not incrementing | Check Activity Log — ensure Type=GOOD entry exists for today with the habit relation |
| Wrong stat getting XP | Verify the habit's Domain property matches the expected stat in the domain-to-stat mapping |
| Class bonus not applied | Check Character page — Class property must be one of: Warrior, Mage, Rogue, Paladin, Ranger |
| Daily processing creates duplicate XP | This is a bug — check the date-based dedup logic in `process_daily_habits()` |
| Level not changing after XP increase | XP may not have crossed the next level threshold. Check with `cumulative_xp_for_level(current_level + 1)` |
| Streak tier wrong | Verify STREAK_TIERS in Settings DB matches expected thresholds |
