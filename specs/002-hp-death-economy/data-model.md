# Data Model: Phase 2 — HP System, Death & Economy

**Date**: 2026-03-22
**Feature**: 002-hp-death-economy

## Core Principle: Activity Log as Single Source of Truth

Both HP and coin balances are **derived values** — they are never stored independently.
They are always the sum of their respective columns in the Activity Log. The Character
DB's "Current HP" and "Current Coins" properties are display caches written by Python
after each calculation.

## HP State

### Calculation

```
Current HP = SUM(all HP-related columns in Activity Log for this character)
```

### HP-Changing Entry Types

| Activity Log Type | HP Column Used | Sign | Created By |
|-------------------|---------------|------|------------|
| (initial creation) | HP + (Hotel) | + Starting HP | `seed_data.py` |
| RESPAWN | HP + (Hotel) | + Starting HP | `hp_engine.respawn()` |
| BAD | HP - (Bad Habit) | - damage value | `hp_engine.apply_damage()` |
| PENALTY | HP - (Overdraft) | - penalty amount | `coin_engine.apply_overdraft_penalty()` |
| HOTEL | HP + (Hotel) | + recovery amount | `coin_engine.process_hotel_checkin()` |
| DIED | (no HP change) | 0 | `hp_engine.trigger_death()` |

### Death State

Derived from Activity Log event sequence:

```
Is Dead = EXISTS(Type="DIED" entry) AND NOT EXISTS(Type="RESPAWN" entry after it)
```

- No boolean flag. Fully derivable from the log.
- Only one DIED entry per death cycle (check `is_dead()` before creating).
- RESPAWN entry resets the death state.

### Respawn Rules

| Condition | Behavior |
|-----------|----------|
| HP ≤ 0, is_dead = false | `trigger_death()` → creates DIED entry |
| is_dead = true, Respawn checkbox = true | `respawn()` → creates RESPAWN entry (+Starting HP), clears checkbox |
| is_dead = false, Respawn checkbox = true | No-op → clears checkbox, logs notice |
| is_dead = true, bad habit logged | Damage applied (HP goes more negative), no new DIED entry |
| is_dead = true, spending attempted | BLOCKED — must respawn first |

## Coin State

### Calculation

```
Current Coins = SUM(all coin columns in Activity Log for this character)
```

### Coin-Changing Entry Types

| Activity Log Type | Coin Column Used | Sign | Created By |
|-------------------|-----------------|------|------------|
| GOAL | Coins + (Goal) | + award | Notion button |
| TASKS | Coins + (Tasks) | + award | Notion button |
| MARKET | Coins - (Market) | - price | `coin_engine.process_market_purchase()` |
| HOTEL | Coins - (Hotel) | - price | `coin_engine.process_hotel_checkin()` |
| BLACKMARKET | Coins - (Black) | - price | `coin_engine.process_black_market()` |

### Overdraft State

```
Is Overdrawn = (Current Coins < 0)
```

Overdraft Penalty Config (from Overdraft Penalty DB):

| Property | Type | Purpose |
|----------|------|---------|
| Frequency | Select: Weekly / Biweekly / Disabled | How often to check |
| HP Penalty | Number (default: 100) | HP deducted per check |
| Last Check | Date | When overdraft was last checked (idempotency key) |

### Dead-State Spending Guard

All spending functions check `hp_engine.is_dead()` before executing:

| Action | Allowed While Dead? |
|--------|-------------------|
| Log bad habit (HP damage) | Yes — damage stacks |
| Earn coins (goal/task completion) | Yes — via Notion buttons |
| Market purchase | **NO** — blocked |
| Hotel check-in | **NO** — blocked |
| Black Market buy | **NO** — blocked |
| Respawn | Yes — this is the exit from death |

## Character DB (Display Cache)

Properties updated by Phase 2 engines:

| Property | Updated By | When |
|----------|-----------|------|
| Current HP | `hp_engine.update_character_hp()` | After every HP change |
| Current Coins | `coin_engine.update_character_coins()` | After every coin change |
| Death Count | `hp_engine.trigger_death()` | Incremented on each death |
| Respawn (checkbox) | `hp_engine.respawn()` | Cleared after processing |

Properties that remain Notion formulas (not Python-written):

| Property | Formula |
|----------|---------|
| HP Progress | `if(prop("Current HP") <= 0, "⚰️ You Died! " + prop("Death Penalty"), <visual bar from Current HP / Starting HP>)` |
| Character Details | "Name ▪ Level X ▪ Y Coins" |

## State Transitions

### HP Lifecycle

```
Character Created → Seed creates Activity Log entry (+1000 HP)
  → Player logs bad habit → apply_damage() → Activity Log entry (-N HP)
    → check_death() → HP > 0? → continue
    → check_death() → HP ≤ 0? → trigger_death() → DIED entry
      → Player checks Respawn → respawn() → Activity Log entry (+1000 HP)
        → Continue playing
```

### Coin Lifecycle

```
Player completes goal → Notion button → Activity Log entry (+N coins)
  → Player buys market item → spend_coins() → Activity Log entry (-N coins)
    → Balance < 0? → Overdraft state
      → Weekly check → apply_overdraft_penalty() → HP damage
        → HP ≤ 0? → Death (via hp_engine)
```

### Death ↔ Economy Interaction

```
                    ┌─────────────┐
                    │  ALIVE      │
                    │  HP > 0     │
                    └──────┬──────┘
                           │ Bad habit / Overdraft penalty
                           ▼
                    ┌─────────────┐
              ┌─────│  HP ≤ 0     │
              │     │  DIED entry │
              │     └──────┬──────┘
              │            │
              │     ┌──────▼──────┐
              │     │  DEAD       │
              │     │  Can log    │───→ HP goes more negative
              │     │  Can earn   │───→ Coins increase
              │     │  Can't spend│───→ BLOCKED
              │     └──────┬──────┘
              │            │ Respawn checkbox
              │     ┌──────▼──────┐
              └─────│  RESPAWN    │
                    │  +1000 HP   │
                    │  ALIVE again│
                    └─────────────┘
```
