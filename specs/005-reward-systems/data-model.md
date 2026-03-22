# Data Model: Phase 5 — Reward Systems (Loot Box, Achievement, Rank & Radar Chart)

**Date**: 2026-03-22
**Feature**: 005-reward-systems

## Core Principle: Reward Systems Write to Existing Infrastructure

Rank, avatar, and chart engines write results back to the Character DB (existing fields). Achievement engine writes to Activity Log (same pattern as all other XP sources). Loot box engine writes to Loot Box Inventory DB and uses coin_engine for balance changes. No new database creation — all DBs are created in Phase 1.

## Rank Domain

### Character DB Fields (existing — written by rank_engine)

| Property | Type | Written By |
|----------|------|------------|
| Current Rank | Select | `rank_engine.check_rank_up()` — Peasant/Squire/Knight/Champion/Hero/Legend/Mythic |
| Total XP | Number | `xp_engine.update_character_stats()` — input to rank calculation |
| Avatar URL | URL | `avatar_renderer.update_character_avatar()` — Cloudinary-hosted composited image |
| Radar Chart URL | URL | `chart_renderer.update_character_chart()` — Cloudinary-hosted radar PNG |

### Rank Thresholds (from config.py / Settings DB)

| Threshold | Rank |
|-----------|------|
| 0 | Peasant |
| 1,000 | Squire |
| 5,000 | Knight |
| 15,000 | Champion |
| 40,000 | Hero |
| 100,000 | Legend |
| 250,000 | Mythic |

### Rank Calculation

```
rank = highest threshold where threshold <= total_xp
High-water mark: new_rank applied ONLY IF rank_tier(new_rank) > rank_tier(current_rank)
If total_xp drops below current threshold → rank unchanged (no demotion)
```

### Rank State Transition

```
Daily automation or manual trigger
  → rank_engine.check_rank_up(character_id)
    → Read Total XP and Current Rank from Character DB
    → Calculate rank from Total XP via get_rank_from_xp()
    → If calculated rank tier > current rank tier → rank-up detected
      → Update Character DB Current Rank
      → Call avatar_renderer.update_character_avatar(character_id)
        → Fetch profile picture from Character DB
        → Download profile picture (or use placeholder)
        → Load rank frame from assets/frames/{rank}.png
        → Composite profile + frame via Pillow
        → Upload to Cloudinary → get URL
        → Write Avatar URL to Character DB
    → If no rank change → return (no action)
```

## Chart Domain

### Radar Chart Specification

| Property | Value |
|----------|-------|
| Dimensions | 800x800 PNG |
| Background | Dark (#1a1a2e) |
| Polygon fill | Neon cyan (#00d4ff) at 25% opacity |
| Polygon outline | Neon cyan (#00d4ff) at 2px |
| Axes | 5: STR, INT, WIS, VIT, CHA |
| Labels | White, stat name + level value at each vertex |
| Title | "{Player Name} · {Rank}" in white |
| Edge case | All stats = 0 → collapsed polygon at center (valid output) |

### Chart State Transition

```
Daily automation or manual trigger
  → chart_renderer.update_character_chart(character_id)
    → Read 5 stat levels + player name + rank from Character DB
    → Generate radar chart via matplotlib polar plot
    → Save to assets/charts/{character_id}.png
    → Upload to Cloudinary → get URL
    → Write Radar Chart URL to Character DB
```

## Achievement Domain

### Achievements DB Schema (existing — seeded in Phase 1)

| Property | Type | Purpose |
|----------|------|---------|
| Badge Name | Title | Achievement name (e.g., "First Blood") |
| Description | Text | Human-readable description |
| Condition Key | Text | Machine-readable key for dispatch (e.g., "first_workout") |
| XP Bonus | Number | XP granted on unlock |
| Domain | Select | STR/INT/WIS/VIT/CHA — determines which stat receives XP |
| Icon URL | URL | Badge icon image |

### Player Achievements DB Schema (existing — created in Phase 1)

| Property | Type | Purpose |
|----------|------|---------|
| Achievement | Relation → Achievements | Which badge was unlocked |
| Character | Relation → Character | Who unlocked it |
| Date Unlocked | Date | When the achievement was earned |
| Notified | Checkbox | Whether the player has been notified (for future dashboard use) |

### Achievement Condition Dispatch

```
CONDITION_CHECKERS = {
    "first_workout": check_first_workout,       # 1+ workout session completed
    "first_budget":  check_first_budget,         # 1+ monthly budget processed
    "streak_3":      check_streak_3,             # Any habit streak >= 3 days
    "streak_7":      check_streak_7,             # Any habit streak >= 7 days
    "streak_30":     check_streak_30,            # Any habit streak >= 30 days
    "rank_squire":   check_rank_squire,          # Reached Squire rank
    "rank_knight":   check_rank_knight,          # Reached Knight rank
    ...                                          # 43 total conditions
}

Each checker: fn(character_id: str) -> bool
  Queries the relevant DB(s) to determine if the condition is met
  Returns True/False — no side effects
```

### Achievement State Transition

```
Daily automation or manual trigger
  → achievement_engine.check_all_achievements(character_id)
    → Fetch all achievement definitions from Achievements DB
    → Fetch already-unlocked achievement IDs from Player Achievements DB
    → For each not-yet-unlocked achievement:
      → Dispatch condition_key to checker function
      → If checker returns True:
        → Create Player Achievement row (achievement + character + today's date)
        → Create Activity Log entry:
          Type: ACHIEVEMENT
          Domain: achievement's Domain field
          XP: achievement's XP Bonus
        → Log unlock
    → If any newly unlocked:
      → xp_engine.update_character_stats(character_id)
    → Return summary
```

## Loot Box Domain

### Loot Box Inventory DB Schema (existing — created in Phase 1)

| Property | Type | Purpose |
|----------|------|---------|
| Reward Name | Title | Generated name (e.g., "Rare Coin Pouch") |
| Rarity | Select | Common / Rare / Epic / Legendary |
| Coins Awarded | Number | Coin reward amount for this rarity |
| Gold Cost | Number | LOOT_COST at time of purchase |
| Claimed | Checkbox | Whether reward has been collected (always True on creation) |
| Date | Date | When the loot box was opened |
| Character | Relation → Character | Who opened it |

### Character DB Fields (existing — written by loot_box)

| Property | Type | Written By |
|----------|------|------------|
| Pity Counter | Number | `loot_box.open_loot_box()` — increments or resets to 0 |
| Gold | Number | `coin_engine` — deducted by LOOT_COST |
| Current Coins | Number | `coin_engine` — credited by rarity reward |

### Loot Box Configuration (from config.py / Settings DB)

| Key | Default | Purpose |
|-----|---------|---------|
| LOOT_WEIGHTS | {"Common": 70, "Rare": 20, "Epic": 8, "Legendary": 2} | Rarity selection weights |
| LOOT_COST | 100 | Gold cost per loot box |
| PITY_TIMER_THRESHOLD | 50 | Guaranteed Legendary after N non-Legendary pulls |
| LOOT_REWARDS | {"Common": 25, "Rare": 75, "Epic": 200, "Legendary": 1000} | Coin reward per rarity |

### Loot Box Calculation

```
Expected value per 100 Gold:
  (0.70 * 25) + (0.20 * 75) + (0.08 * 200) + (0.02 * 1000)
  = 17.5 + 15.0 + 16.0 + 20.0
  = 68.5 Coins per 100 Gold

Pity timer: counter starts at 0
  Each non-Legendary pull: counter += 1
  If counter >= 50: next pull guaranteed Legendary, counter resets to 0
  If Legendary by RNG before counter reaches 50: counter resets to 0
```

### Loot Box State Transition

```
Player runs CLI command: python tools/loot_box.py --character-id <ID>
  → loot_box.open_loot_box(character_id)
    → Read Gold balance + Pity Counter from Character DB
    → If Gold < LOOT_COST → reject, return error
    → Deduct LOOT_COST Gold via coin_engine
    → Roll rarity (pass pity_counter to roll_rarity())
      → If pity_counter >= PITY_TIMER_THRESHOLD → Legendary (guaranteed)
      → Else → weighted random from LOOT_WEIGHTS
    → Look up Coin reward from LOOT_REWARDS
    → Credit Coins via coin_engine
    → Update Pity Counter in Character DB:
      → If rarity == Legendary → reset to 0
      → Else → increment by 1
    → Create Loot Box Inventory row
    → Return result
```

## Activity Log Entry Types (Phase 5 additions)

| Type | XP Column | Domain → Stat | Created By |
|------|-----------|---------------|------------|
| ACHIEVEMENT | EXP + (Achievement) | Per-badge Domain field | `achievement_engine.check_all_achievements()` |

Note: Loot box does NOT create Activity Log entries — it creates Loot Box Inventory rows and modifies Gold/Coins via coin_engine. Rank and chart engines update Character DB directly without Activity Log entries.

## Settings DB Additions (Phase 5)

| Setting Key | Default | Used By |
|-------------|---------|---------|
| LOOT_WEIGHTS | {"Common": 70, "Rare": 20, "Epic": 8, "Legendary": 2} | loot_box |
| LOOT_COST | 100 | loot_box |
| PITY_TIMER_THRESHOLD | 50 | loot_box |
| RANK_THRESHOLDS | {0: "Peasant", 1000: "Squire", ...} | rank_engine |
| LOOT_REWARDS | {"Common": 25, "Rare": 75, "Epic": 200, "Legendary": 1000} | loot_box |

Note: RANK_THRESHOLDS already exists in config.py from V5 plan. LOOT_WEIGHTS and LOOT_COST already exist. LOOT_REWARDS and PITY_TIMER_THRESHOLD are new additions.
