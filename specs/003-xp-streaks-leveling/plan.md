# Implementation Plan: Phase 3 — XP Engine, Streaks & Leveling

**Branch**: `003-xp-streaks-leveling` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-xp-streaks-leveling/spec.md`

## Summary

Build the dual progression system for the RPG life tracker: an XP engine that calculates
experience points per stat (STR/INT/WIS/VIT/CHA) using an exponential leveling curve, a
streak engine that tracks consecutive daily check-ins with tier-based XP multipliers, and
a habit engine that orchestrates daily processing — tying habit check-ins, streak tracking,
XP calculation, HP damage, and Character stat updates into a single idempotent daily pass.
All XP is derived from Activity Log entries. Stat levels, Player Level, class bonuses, and
visual progress bars are written to the Character page after each recalculation.

Key clarifications integrated:
- Multi-stat XP split: Goals/tasks relating to multiple stats split XP equally (floor division)
- Timezone-aware: "today" = calendar day in player's local timezone (from Settings DB / .env)
- No XP penalty on streak decay: losing the multiplier is the only consequence
- Real-time stat updates: `update_character_stats()` runs after every XP event, not just daily automation
- Rank is display-only: no Activity Log entry on rank change (deferred to Phase 5 Achievements)

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv` (inherited from Phase 1)
**Storage**: Notion Activity Log (XP source), Streak Tracker DB, Character DB (display cache)
**Testing**: `pytest` with mock Notion responses (`conftest.py` from Phase 1, extended in Phase 2)
**Target Platform**: GitHub Actions (scheduled daily), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Daily habit processing < 30s; stat recalculation < 10s; real-time stat refresh after button-triggered XP < 5s
**Constraints**: All XP values are integers (floor rounding). Activity Log is append-only.
Phase 1 and Phase 2 must be complete. Notion API rate limit (3 req/sec).
Player timezone configurable via Settings DB or `.env` (`PLAYER_TIMEZONE`, default: UTC).
**Scale/Scope**: Single player, ~10-50 Activity Log entries per day, 4-10 active habits,
5 stats, 6 streak tiers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All XP/streak state stored in Notion (Activity Log, Streak Tracker). Buttons create Activity Log entries (Notion-native). Python only aggregates multi-row XP sums and writes display values back. Progress bars use Notion formulas for single-row display; Python generates the bar string for cross-row totals |
| II. Python for Complex Orchestration | PASS | `xp_engine.py` handles cross-row XP aggregation and exponential math. `streak_engine.py` handles cross-row streak detection. `habit_engine.py` orchestrates daily processing. Each tool: one concern, deterministic, independently testable |
| III. WAT Architecture | PASS | Three new tools in `tools/`. Each is a deterministic execution unit. No tool does reasoning. Each can be called independently or orchestrated by the daily automation |
| IV. Settings DB as Canonical Config | PASS | XP formula constants (B, E, L), streak tier thresholds, streak multipliers, class bonus %, domain-to-stat mapping, default habit XP, player timezone — all read from `config.py` / Settings DB. No hardcoded balance values in engine files |
| V. Idempotency | PASS | Daily processing uses date-based deduplication to prevent double XP grants. Streak updates check Last Completed date before incrementing. Stat recalculation is a pure re-sum — safe to re-run. `update_character_stats()` overwrites display cache with freshly calculated values |
| VI. Free-First | PASS | No new dependencies. Reuses Phase 1 infrastructure |

**Gate result: ALL PASS** — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-xp-streaks-leveling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── xp_engine.py         # Exponential leveling curves, per-stat aggregation, class bonus, multi-stat split
├── streak_engine.py     # Streak tracking, tier advancement, decay (no XP penalty), multipliers
├── habit_engine.py      # Daily habit processing orchestration (good + bad habits)
│
├── config.py            # (Phase 1 — already exists) XP/streak/timezone constants from Settings DB
├── logger.py            # (Phase 1 — already exists)
├── notion_client.py     # (Phase 1 — already exists)
├── hp_engine.py         # (Phase 2 — already exists) Used by habit_engine for bad habit damage
├── coin_engine.py       # (Phase 2 — already exists)
└── smoke_test.py        # (Phase 1 — already exists)

tests/
├── test_xp_engine.py    # XP formula, level calc, stat aggregation, class bonus, multi-stat split, progress bar
├── test_streak_engine.py # Streak increment, decay (no penalty), tier boundaries, multiplier calc, timezone
├── test_habit_engine.py # Daily processing, idempotency, good + bad habit orchestration, real-time triggers
├── conftest.py          # (Phase 1+2 — extend with XP/streak/habit mock fixtures)
```

**Structure Decision**: Three new tools added to the flat `tools/` directory. Tests mirror
tool names. `conftest.py` extended with Activity Log mock entries for XP and streak
scenarios, mock Streak Tracker entries, and mock Good/Bad Habit entries with domains.

## Complexity Tracking

No constitution violations. Table not required.

---

## Phase 0: Research

No NEEDS CLARIFICATION items remain after the clarify session. All decisions resolved:

### R1: XP Aggregation Strategy — Multi-Source Sum with Equal Split

**Decision**: Stat XP is the sum of all XP-granting Activity Log entries mapped to that
stat's domain. When a Goal/Task relates to multiple skills mapping to different stats,
XP is split equally among those stats (floor division; remainder dropped).
**Rationale**: Consistent with Activity Log single-source-of-truth. Equal split is fair,
avoids XP inflation from duplication, and floor division keeps all values as integers.
**Alternatives considered**: Full XP to each stat (inflationary), primary skill only
(ignores secondary domains), separate XP ledger per stat (breaks single-source principle).

### R2: Level Calculation — Iterative Threshold

**Decision**: `level_from_xp()` iterates from level 1 upward, accumulating XP thresholds
until cumulative XP exceeds the player's total. This handles multi-level jumps naturally.
**Rationale**: The exponential formula doesn't have a clean analytical inverse. Iteration
is simple, correct, and fast (players won't exceed level ~50 in practice).
**Alternatives considered**: Binary search — premature optimization. Analytical inverse — no closed form.

### R3: Streak Reset — Binary, No XP Penalty

**Decision**: Missing a day resets the streak to 0. No XP is deducted as a penalty —
losing the multiplier is the only consequence. The `STREAK_DECAY_RATE` config is
preserved for future graduated decay but not used in V5.
**Rationale**: Losing a high multiplier (e.g., 3.0x → 1.0x) is already a significant
consequence. Adding an XP penalty would double-punish and discourage re-engagement
after a broken streak.
**Alternatives considered**: Fixed XP penalty (too punitive), percentage-based penalty
(complex, discouraging).

### R4: Class Bonus Application — At Aggregation

**Decision**: The +10% class bonus is applied during `update_character_stats()`, not when
individual XP events are created. The bonus multiplies the total stat XP, not per-event.
**Rationale**: Keeps bonus logic in one place. Class changes take effect immediately.
**Alternatives considered**: Per-event application — leaks class knowledge into every source.

### R5: Daily Processing Idempotency — Date-Based Guard

**Decision**: XP grants check for existing entries for the same habit + date before
creating new ones. Stat recalculation is a pure re-sum (inherently idempotent).
**Rationale**: Consistent with Phase 2 patterns. Prevents double-counting on re-runs.
**Alternatives considered**: Processing flags on entries — too many API writes.

### R6: Streak Tracker Initialization — Lazy Creation

**Decision**: Streak Tracker rows are created on first check-in for a habit. No
pre-seeding required.
**Rationale**: New player-added habits automatically get streak tracking without migrations.
**Alternatives considered**: Pre-seeded in `seed_data.py` — breaks on new habits.

### R7: Stat Recalculation Timing — Real-Time (Clarification Q4)

**Decision**: `update_character_stats()` runs after every XP-granting event, including
Goal/Task button completions — not just during daily automation.
**Rationale**: Players expect immediate feedback when completing goals/tasks. Consistent
with Phase 2's real-time death detection pattern. Daily automation still runs the full
processing pass for streaks, but stat display is always current.
**Alternatives considered**: Daily-only (laggy UX), daily + manual CLI command (partial).

### R8: Timezone-Aware Day Boundary (Clarification Q2)

**Decision**: "Today" for streak and daily processing is the calendar day in the player's
local timezone, configured via `PLAYER_TIMEZONE` in Settings DB or `.env` (default: UTC).
**Rationale**: A player checking in at 11:55 PM should have that count for today, not
tomorrow. Timezone awareness prevents confusing streak breaks for late-night users.
**Alternatives considered**: UTC-only (timezone-unaware, confusing), automation-time cutoff
(arbitrary, penalizes late check-ins).

---

## Phase 1: Design & Contracts

### Data Model

#### XP State (derived from Activity Log)

XP per stat is calculated:

```
Stat XP = SUM(
  Activity Log entries WHERE
    XP columns (EXP + Habit, EXP + Goal, EXP + Tasks) are non-zero
    AND the entry's domain maps to this stat
)
```

For entries mapping to multiple stats (via multi-skill Goals/Tasks):
```
Per-stat share = floor(total_xp / number_of_stats)
```

XP-granting Activity Log entry types:

| Type | XP Column | Domain Source | Created By |
|------|-----------|-------------|------------|
| GOOD | EXP + (Habit) | Good Habit's Domain property | `habit_engine.process_daily_habits()` |
| GOAL | EXP + (Goal) | Goal's Related Skills → Skill's Stat | Notion button (value pre-filled) |
| TASKS | EXP + (Tasks) | Brain Dump's Related Skills → Skill's Stat | Notion button (value pre-filled) |

#### Level State (derived from XP)

```
XP_required(n) = B * n^E + L * n      (per-level cost)
Cumulative_XP(n) = SUM(XP_required(1..n))  (total to reach level n)
Stat Level = max n where Cumulative_XP(n) <= Stat XP
Player Level = floor(avg(STR Level, INT Level, WIS Level, VIT Level, CHA Level))
Total XP = STR XP + INT XP + WIS XP + VIT XP + CHA XP
```

Default formula constants from config:

| Constant | Default | Settings DB Key |
|----------|---------|-----------------|
| B (base) | 1000 | Level Base XP |
| E (exponent) | 1.8 | Level Exponent |
| L (linear mod) | 200 | (reserved) |

Reference XP table (first 10 levels, defaults):

| Level | XP Required | Cumulative XP |
|-------|-------------|---------------|
| 1 | 1200 | 1200 |
| 2 | 3882 | 5082 |
| 3 | 7686 | 12768 |
| 4 | 12431 | 25199 |
| 5 | 18012 | 43211 |
| 6 | 24361 | 67572 |
| 7 | 31422 | 98994 |
| 8 | 39152 | 138146 |
| 9 | 47513 | 185659 |
| 10 | 56474 | 242133 |

#### Streak State (Streak Tracker DB)

| Property | Type | Updated By |
|----------|------|-----------|
| Habit | Relation → Good Habit | Created on first check-in |
| Domain | Select | Copied from Good Habit on creation |
| Current Streak | Number | `streak_engine.update_streak_tracker()` |
| Best Streak | Number | `streak_engine.update_streak_tracker()` (max of current, previous best) |
| Current Tier | Select | `streak_engine.update_streak_tracker()` |
| Multiplier | Number | `streak_engine.update_streak_tracker()` |
| Last Completed | Date | `streak_engine.update_streak_tracker()` |

Streak tier thresholds (from config):

| Days | Tier | Multiplier |
|------|------|-----------|
| 0 | None | 1.0x |
| 3 | Bronze | 1.1x |
| 7 | Silver | 1.25x |
| 14 | Gold | 1.5x |
| 30 | Platinum | 2.0x |
| 60 | Diamond | 2.5x |
| 100 | Mythic | 3.0x |

Decay behavior: streak resets to 0, tier to None, multiplier to 1.0. **No XP penalty.**
Best Streak preserved (never decreases).

#### Character DB (Display Cache — Python-Written)

Properties updated by Phase 3 engines:

| Property | Updated By | When |
|----------|-----------|------|
| STR/INT/WIS/VIT/CHA XP | `xp_engine.update_character_stats()` | After every XP-granting event (real-time) |
| STR/INT/WIS/VIT/CHA Level | `xp_engine.update_character_stats()` | After every XP-granting event |
| Player Level | `xp_engine.update_character_stats()` | After every XP-granting event |
| Total XP | `xp_engine.update_character_stats()` | After every XP-granting event |
| Current Rank | `xp_engine.update_character_stats()` | After every XP-granting event (display-only, no event logged) |

Properties that remain Notion formulas (not Python-written):

| Property | Formula |
|----------|---------|
| EXP Progress | Visual bar from stat XP (single-row display) |
| Character Details | "Name | Level X | Y Coins" |

#### Domain-to-Stat Mapping (from config)

| Domain | Stat |
|--------|------|
| gym, organized | STR |
| learning | INT |
| finance | WIS |
| nutrition, habits, health | VIT |
| social, content, creativity, writing | CHA |

#### Class-to-Stat Mapping (from config)

| Class | Bonus Stat |
|-------|-----------|
| Warrior | STR |
| Ranger | WIS |
| Mage | INT |
| Paladin | VIT |
| Rogue | CHA |

Applied at aggregation time, not per-event. `floor(raw_xp * 1.1)` for matching stat.

#### Timezone Configuration

| Source | Key | Default |
|--------|-----|---------|
| Settings DB | Player Timezone | UTC |
| .env | PLAYER_TIMEZONE | UTC |

Used by: streak engine (day boundary), habit engine (daily processing date), daily automation.

### Contracts

#### xp_engine.py

```python
def xp_for_level(n: int) -> int
    """XP required from level n-1 to level n.
    Formula: floor(B * n^E + L * n). All values from config.
    Returns: integer XP cost for this level."""

def cumulative_xp_for_level(n: int) -> int
    """Total XP required to reach level n (sum of xp_for_level(1..n)).
    Returns: integer cumulative XP."""

def level_from_xp(total_xp: int) -> int
    """Current level given total XP.
    Iterates from level 1 upward until cumulative exceeds total_xp.
    Returns: integer level (minimum 1)."""

def progress_to_next_level(total_xp: int) -> float
    """Progress toward next level as 0.0–1.0.
    Returns: float (XP into current level / XP needed for next level)."""

def aggregate_stat_xp(character_id: str, stat: str) -> int
    """Sum all XP entries from Activity Log mapped to the given stat.
    For multi-stat entries (Goals/Tasks with multiple skill relations),
    split XP equally among stats (floor division).
    Returns: integer total XP for this stat (before class bonus)."""

def apply_class_bonus(base_xp: int, stat: str, character_class: str) -> int
    """Apply +10% class bonus if stat matches class mapping.
    Returns: floor(base_xp * 1.1) if match, else base_xp unchanged."""

def update_character_stats(character_id: str) -> dict
    """Recalculate all 5 stat XPs (with class bonus), stat levels, Player Level,
    Total XP, and Current Rank. Write all to Character DB.
    Called after every XP-granting event (real-time) and during daily processing.
    Rank is display-only — no Activity Log entry on rank change.
    Returns: {"stats": {stat: {"xp": int, "level": int}},
              "player_level": int, "total_xp": int, "rank": str}"""

def generate_progress_bar(current: int, target: int, segments: int = 10) -> str
    """Visual progress bar string.
    Returns: '◾◾◾◽◽◽◽◽◽◽ 400/500 | LV 2' format."""
```

#### streak_engine.py

```python
def get_today(timezone: str = None) -> str
    """Get today's date in the player's configured timezone.
    Reads PLAYER_TIMEZONE from config if not provided.
    Returns: date string 'YYYY-MM-DD'."""

def check_streaks(character_id: str, date: str) -> dict
    """For each active good habit: check if completed today (timezone-aware).
    If completed: increment streak. If missed: reset streak (no XP penalty).
    Returns: {"updated": int, "decayed": int, "details": [...]}"""

def calculate_multiplier(streak_count: int) -> float
    """XP multiplier for the given streak count.
    Uses config.STREAK_TIERS to find the highest qualifying tier.
    Returns: float multiplier (1.0 if below first tier)."""

def get_streak_tier(count: int) -> str
    """Tier name for the given streak count.
    Returns: 'None', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', or 'Mythic'."""

def apply_decay(character_id: str, habit_id: str) -> dict
    """Reset streak to 0, tier to None, multiplier to 1.0.
    No XP penalty applied. Log decay event.
    Returns: {"habit_id": str, "previous_streak": int, "previous_tier": str}"""

def update_streak_tracker(habit_id: str, completed: bool, date: str) -> dict
    """Write streak state to Streak Tracker DB.
    If completed: increment Current Streak, update Best Streak if new high,
    update tier and multiplier, set Last Completed = date.
    If not completed: apply_decay() (no XP penalty).
    Creates Streak Tracker row if none exists for this habit (lazy init).
    Returns: {"streak": int, "best": int, "tier": str, "multiplier": float}"""
```

#### habit_engine.py

```python
def get_active_habits(character_id: str) -> list
    """Query Good Habit DB for habits where Active = True.
    Returns: list of habit dicts with id, name, domain, base_xp."""

def process_daily_habits(character_id: str, date: str) -> dict
    """Idempotent daily processing (timezone-aware date):
    1. Read today's Activity Log entries (Type=GOOD)
    2. For each active habit: determine if checked in today
    3. Update streak tracker for each habit (increment or decay, no XP penalty on decay)
    4. Calculate XP per completed habit: base_xp * streak_multiplier (floor to int)
    5. Create XP Activity Log entries for completed habits (skip if already exists for habit+date)
    6. Call xp_engine.update_character_stats() (real-time stat refresh)
    Returns: {"processed": int, "xp_granted": int, "streaks_updated": int,
              "streaks_decayed": int, "already_processed": bool}"""

def process_bad_habits(character_id: str, date: str) -> dict
    """Read today's Activity Log entries (Type=BAD).
    For each: call hp_engine.apply_damage() with the bad habit's HP Damage value.
    Returns: {"processed": int, "total_damage": int, "died": bool}"""

def calculate_habit_xp(base_xp: int, multiplier: float) -> int
    """Calculate effective XP: floor(base_xp * multiplier).
    Returns: integer XP."""

def get_trailing_adherence(habit_id: str, days: int = 30) -> float
    """Percentage of last N days where habit was completed.
    Returns: float 0.0–1.0."""
```

### Quickstart

See `specs/003-xp-streaks-leveling/quickstart.md` (generated separately).

---

## Implementation Order

| Step | Tool/Function | Depends On | Deliverable |
|------|--------------|------------|-------------|
| 1 | `xp_engine.xp_for_level()`, `cumulative_xp_for_level()` | Phase 1 (config) | XP formula functions |
| 2 | `xp_engine.level_from_xp()`, `progress_to_next_level()` | Step 1 | Level calculation |
| 3 | `xp_engine.generate_progress_bar()` | Step 2 | Visual display |
| 4 | `xp_engine.apply_class_bonus()` | Phase 1 (config) | Class modifier |
| 5 | `xp_engine.aggregate_stat_xp()` | Phase 1 (notion_client) | Per-stat XP sum with multi-stat split |
| 6 | `xp_engine.update_character_stats()` | Steps 2, 4, 5 | Full stat recalculation + write (real-time) |
| 7 | `test_xp_engine.py` | Steps 1-6 | XP engine test suite |
| 8 | `streak_engine.get_today()` | Phase 1 (config — timezone) | Timezone-aware date |
| 9 | `streak_engine.calculate_multiplier()`, `get_streak_tier()` | Phase 1 (config) | Pure tier/multiplier functions |
| 10 | `streak_engine.update_streak_tracker()` | Step 9 | Streak state writes (lazy init) |
| 11 | `streak_engine.apply_decay()` | Step 10 | Streak reset (no XP penalty) |
| 12 | `streak_engine.check_streaks()` | Steps 8, 10, 11 | Full streak check orchestration |
| 13 | `test_streak_engine.py` | Steps 8-12 | Streak engine test suite |
| 14 | `habit_engine.get_active_habits()` | Phase 1 (notion_client) | Habit query |
| 15 | `habit_engine.calculate_habit_xp()` | Step 9 (multiplier) | XP calculation with streak |
| 16 | `habit_engine.process_daily_habits()` | Steps 6, 12, 15 | Daily good habit processing + real-time stat update |
| 17 | `habit_engine.process_bad_habits()` | Phase 2 (hp_engine) | Daily bad habit → HP damage |
| 18 | `habit_engine.get_trailing_adherence()` | Phase 1 (notion_client) | Adherence metric |
| 19 | `test_habit_engine.py` | Steps 14-18 | Habit engine test suite |

**Key dependencies**:
- `habit_engine` depends on `xp_engine` for `update_character_stats()` (real-time)
- `habit_engine` depends on `streak_engine` for `check_streaks()` and `calculate_multiplier()`
- `habit_engine` depends on `hp_engine` (Phase 2) for `apply_damage()` (bad habits)
- `xp_engine` and `streak_engine` are independent of each other and can be built in parallel
- `streak_engine` needs timezone support (`get_today()`) for correct day boundary

---

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Notion as Headless DB & GUI | PASS | All XP data lives in Activity Log. Buttons create entries. Python aggregates and writes display cache. Rank is display-only (no event logged) |
| II. Python for Complex Orchestration | PASS | Cross-row XP sums, exponential math, streak detection, multi-stat split — all multi-row ops. Three tools, each one concern |
| III. WAT Architecture | PASS | Deterministic tools, no reasoning in engines |
| IV. Settings DB as Canonical Config | PASS | B/E/L formula constants, streak tiers, multipliers, class mapping, domain mapping, player timezone — all from config |
| V. Idempotency | PASS | Date-based dedup for daily processing, pure re-sum for stat calculation, Last Completed date for streaks. Real-time stat updates are pure overwrites (inherently idempotent) |
| VI. Free-First | PASS | No new dependencies |

**Gate result: ALL PASS** — ready for `/speckit.tasks`.
