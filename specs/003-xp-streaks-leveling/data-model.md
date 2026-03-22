# Data Model: Phase 3 — XP Engine, Streaks & Leveling

**Date**: 2026-03-22
**Feature**: 003-xp-streaks-leveling

## Core Principle: Activity Log as Single Source of Truth

XP, like HP and coins, is a **derived value** — always the sum of XP columns in the
Activity Log. The Character DB's stat XP properties are display caches written by Python
after each calculation. Streak state lives in the Streak Tracker DB and is updated by
the streak engine after each daily processing run.

## XP State

### Calculation

```
Stat XP (raw) = SUM(all XP columns in Activity Log for entries mapped to this stat's domain)

For multi-stat entries (Goals/Tasks with multiple skill relations):
  Per-stat share = floor(total_xp / number_of_stats)

Stat XP (final) = apply_class_bonus(raw, stat, character_class)
```

### XP-Granting Entry Types

| Activity Log Type | XP Column Used | Domain Source | Created By |
|-------------------|---------------|---------------|------------|
| GOOD | EXP + (Habit) | Good Habit → Domain property | `habit_engine.process_daily_habits()` |
| GOAL | EXP + (Goal) | Goal → Related Skills → Skill → Stat | Notion button |
| TASKS | EXP + (Tasks) | Brain Dump → Related Skills → Skill → Stat | Notion button |

### Domain-to-Stat Mapping

| Domain Tags | Stat |
|------------|------|
| gym, organized | STR |
| learning | INT |
| finance | WIS |
| nutrition, habits, health | VIT |
| social, content, creativity, writing | CHA |

### Class Bonus

| Class | Bonus Stat | Modifier |
|-------|-----------|----------|
| Warrior | STR | +10% |
| Ranger | WIS | +10% |
| Mage | INT | +10% |
| Paladin | VIT | +10% |
| Rogue | CHA | +10% |

Applied at aggregation time, not per-event. `floor(raw_xp * 1.1)` for matching stat.

## Level State

### Exponential Formula

```
XP_required(n) = floor(B * n^E + L * n)
Cumulative_XP(n) = SUM(XP_required(1) .. XP_required(n))
```

Defaults: B=1000, E=1.8, L=200 (configurable via Settings DB)

### Level Derivation

```
Stat Level = max n where Cumulative_XP(n) <= Stat XP
Player Level = floor(avg(STR Level, INT Level, WIS Level, VIT Level, CHA Level))
Total XP = STR XP + INT XP + WIS XP + VIT XP + CHA XP
```

### Rank Derivation

```
Current Rank = highest rank where threshold <= Total XP
```

| Threshold | Rank |
|-----------|------|
| 0 | Peasant |
| 1000 | Squire |
| 5000 | Knight |
| 15000 | Champion |
| 40000 | Hero |
| 100000 | Legend |
| 250000 | Mythic |

## Streak State

### Streak Tracker DB Schema

| Property | Type | Purpose |
|----------|------|---------|
| Habit | Relation → Good Habit | Links streak to habit |
| Domain | Select | Copied from habit's domain |
| Current Streak | Number | Consecutive days completed |
| Best Streak | Number | All-time high (never decreases) |
| Current Tier | Select | None/Bronze/Silver/Gold/Platinum/Diamond/Mythic |
| Multiplier | Number | XP multiplier for this tier |
| Last Completed | Date | Date of most recent check-in |

### Streak Tier Thresholds

| Days | Tier | Multiplier |
|------|------|-----------|
| 0 | None | 1.0x |
| 3 | Bronze | 1.1x |
| 7 | Silver | 1.25x |
| 14 | Gold | 1.5x |
| 30 | Platinum | 2.0x |
| 60 | Diamond | 2.5x |
| 100 | Mythic | 3.0x |

### Streak Lifecycle

```
Habit created → No Streak Tracker row exists yet
  → Player checks in (day 1) → Streak Tracker row created (streak=1, tier=None)
    → Player checks in (day 2) → streak=2, tier=None
      → Player checks in (day 3) → streak=3, tier=Bronze, multiplier=1.1
        → Player misses day 4 → streak=0, tier=None, multiplier=1.0 (no XP penalty)
          → Best Streak preserved (was 3)
```

Day boundary: calendar day midnight in player's local timezone (`PLAYER_TIMEZONE` from
Settings DB or `.env`, default: UTC). A check-in at 11:55 PM counts for that day.

## Character DB (Display Cache)

Properties written by Phase 3:

| Property | Updated By | When |
|----------|-----------|------|
| STR XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| INT XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| WIS XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| VIT XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| CHA XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| STR/INT/WIS/VIT/CHA Level | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| Player Level | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| Total XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| Current Rank | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |

## State Transitions

### Daily Processing Flow

```
Daily automation triggers
  → habit_engine.process_daily_habits(character_id, today)
    → Read Activity Log entries for today (Type=GOOD)
    → For each active habit:
        → Was it checked in today?
          → YES: streak_engine.update_streak_tracker(habit_id, True, today)
                 → Increment streak, update tier/multiplier/best
                 → Calculate XP: base_xp * multiplier (floor to int)
                 → Create XP Activity Log entry (if not already exists for habit+date)
          → NO: streak_engine.update_streak_tracker(habit_id, False, today)
                 → apply_decay() → streak=0, tier=None
    → xp_engine.update_character_stats(character_id)
      → For each stat: aggregate_stat_xp() + apply_class_bonus()
      → Calculate stat levels, Player Level, Total XP, Rank
      → Write all to Character DB

  → habit_engine.process_bad_habits(character_id, today)
    → Read Activity Log entries for today (Type=BAD)
    → For each: hp_engine.apply_damage(character_id, damage, source)
```

### Real-Time Stat Refresh (Goal/Task Completion)

```
Player clicks "COMPLETE" on Goal → Notion button creates Activity Log entry (Type=GOAL, EXP + Goal = N)
  → Trigger: xp_engine.update_character_stats(character_id)
    → aggregate_stat_xp() re-sums all XP entries (including new Goal XP)
    → For multi-skill Goals: XP split equally among mapped stats (floor division)
    → apply_class_bonus() on each stat
    → Recalculate levels, Player Level, Total XP, Rank (display-only, no event)
    → Write to Character DB immediately
  → Player sees updated stats without waiting for daily automation
```

### XP Flow (Single Habit Check-In)

```
Player clicks "Check-in" button → Notion creates Activity Log entry (Type=GOOD)
  → Daily processing reads entry
    → Looks up habit's domain (e.g., "gym" → STR)
    → Looks up habit's streak tracker → gets multiplier (e.g., 1.5x for Gold)
    → Calculates XP: base_xp * multiplier = 5 * 1.5 = 7 (floor)
    → Creates XP Activity Log entry: EXP + (Habit) = 7
    → aggregate_stat_xp("STR") → sums all STR-domain XP entries → e.g., 1205
    → apply_class_bonus(1205, "STR", "Warrior") → floor(1205 * 1.1) = 1325
    → level_from_xp(1325) → Level 2 (threshold was 1200)
    → Writes STR XP = 1325, STR Level = 2 to Character DB
```
