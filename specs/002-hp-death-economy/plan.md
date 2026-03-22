# Implementation Plan: Phase 2 — HP System, Death & Economy

**Branch**: `002-hp-death-economy` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-hp-death-economy/spec.md`

## Summary

Build the dual consequence/reward system for the RPG life tracker: an HP engine that
tracks damage from bad habits with real-time death detection and respawn, and a coin
engine that manages earning (goals/tasks), spending (Market, Hotels, Black Market),
and overdraft penalties. HP and coin balances are pure sums of Activity Log entries —
no separate ledger. Death blocks spending but not logging. All values are integers,
all state lives in Notion's Activity Log.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv` (inherited from Phase 1)
**Storage**: Notion Activity Log (single source of truth), Character DB (display)
**Testing**: `pytest` with mock Notion responses (`conftest.py` from Phase 1)
**Target Platform**: GitHub Actions (scheduled), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Death detection < 2s after HP-changing event; balance queries < 5s
**Constraints**: All values are integers. Activity Log is append-only (no edits). Phase 1 must be complete.
**Scale/Scope**: Single player, ~10-50 Activity Log entries per day at peak

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All HP/coin state stored in Notion Activity Log. "You Died!" displayed via Notion formula. Respawn via Notion checkbox. Buttons trigger Activity Log entries. Python only reads/writes, never replicates Notion-native features |
| II. Python for Complex Orchestration | PASS | `hp_engine.py` handles cross-row HP aggregation (sum of Activity Log). `coin_engine.py` handles cross-row coin aggregation. Both are multi-row reads — belongs in Python per constitution. One concern per tool |
| III. WAT Architecture | PASS | Each engine is a deterministic tool in `tools/`. No engine does reasoning. Each can be called independently |
| IV. Settings DB as Canonical Config | PASS | Starting HP, overdraft penalty amount, overdraft frequency, hotel tier prices/HP — all read from `config.py` / Settings DB. No hardcoded balance values in engine files |
| V. Idempotency | PASS | HP and coins are pure sums of Activity Log entries — re-reading always gives the correct value. Death detection checks for existing death event without subsequent respawn before creating a new one. Overdraft checks use "Last Check" date to avoid double-penalizing |
| VI. Free-First | PASS | No new dependencies. Reuses Phase 1 infrastructure |

**Gate result: ALL PASS** — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-hp-death-economy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── hp_engine.py         # HP tracking, damage, death detection, respawn
├── coin_engine.py       # Coin balance, spending, earning, overdraft, market/hotel/black market
│
├── config.py            # (Phase 1 — already exists) Reads HP/coin constants from Settings DB
├── logger.py            # (Phase 1 — already exists)
├── notion_client.py     # (Phase 1 — already exists)
└── smoke_test.py        # (Phase 1 — already exists)

tests/
├── test_hp_engine.py    # HP damage, death boundary, respawn, dead-state behavior
├── test_coin_engine.py  # Balance calc, overdraft, market/hotel/black market, dead-state blocks
├── conftest.py          # (Phase 1 — extend with HP/coin mock fixtures)
```

**Structure Decision**: Two new tools added to the flat `tools/` directory. No new
directories. Tests mirror tool names. `conftest.py` extended with Activity Log mock
entries for HP and coin scenarios.

## Complexity Tracking

No constitution violations. Table not required.

---

## Phase 0: Research

No NEEDS CLARIFICATION items remain after the clarify session. All decisions resolved:

### R1: HP Calculation Model — Activity Log Sum

**Decision**: HP is the sum of all HP-related entries in the Activity Log. No implicit
offset. Character creation and every respawn create an explicit positive-HP Activity
Log entry (e.g., Type=RESPAWN, HP=+1000).
**Rationale**: Pure sum is the simplest model — no special cases for "starting HP."
Every HP change is auditable as a row in the Activity Log. Makes debugging trivial:
sum the column, that's the HP.
**Alternatives considered**: Implicit offset (starting HP + sum of changes) — adds a
special case to every HP query and makes the Activity Log incomplete as a ledger.

### R2: Coin Balance Model — Pure Read

**Decision**: Coin balance is the sum of all coin columns in the Activity Log. Notion
buttons already write coin values when goals/tasks are completed or purchases made.
`coin_engine.get_coin_balance()` is a pure read — no processing, confirmation, or
state machine.
**Rationale**: Buttons are the user-facing interaction (Constitution Principle I).
The coins are already in the Activity Log the moment the button is pressed. The engine
just sums them.
**Alternatives considered**: Processing/confirmation step — adds complexity with no
benefit since buttons are the canonical input method.

### R3: Death Detection — Real-Time After Every HP Event

**Decision**: Death is checked immediately after every HP-changing operation (bad
habit damage, overdraft penalty application, hotel recovery). Not deferred to daily
automation.
**Rationale**: Immediate feedback is the core of the RPG experience. A player who
logs a bad habit that kills them should see "You Died!" right away, not hours later.
**Alternatives considered**: Daily-only check — breaks immersion, allows "ghost
actions" between death and detection.

### R4: Dead State — Partial Lockdown

**Decision**: While dead, the player can still log bad habits (HP damage stacks) and
earn coins (from completing goals/tasks). Spending actions are blocked (Market, Hotel,
Black Market). Only one death event exists per death — further damage doesn't create
duplicate death entries.
**Rationale**: Logging bad habits while dead increases the "debt" the player respawns
with (more negative HP → more recovery needed). Blocking spending prevents exploiting
hotel check-ins to auto-revive without using Respawn. Earning coins while dead lets
the player dig out of overdraft debt even when dead.
**Alternatives considered**: Full lockdown (too punitive — trapped in death with no
way to improve), no restrictions (allows hotel self-revival bypass).

### R5: Respawn Guard — No-Op While Alive

**Decision**: If the player checks Respawn while HP > 0, the system clears the
checkbox, logs a notice, and does nothing. Respawn is not a "full heal" exploit.
**Rationale**: Respawn is a death recovery mechanism, not a free heal. Allowing it
while alive would trivialize the HP system.
**Alternatives considered**: Allow always (breaks game balance), warn and allow
(same problem with an extra click).

### R6: Overdraft Penalty Scheduling

**Decision**: Overdraft check runs during scheduled automation (daily/weekly per
settings). Uses the "Last Check" date on the Overdraft Penalty config row to
determine if a check is due. Updates the date after each check.
**Rationale**: Overdraft penalties are a slow-burn consequence, not instant. Weekly
default gives the player time to earn coins and recover before the next penalty.
The "Last Check" date prevents double-penalizing on re-runs (idempotency).
**Alternatives considered**: Real-time overdraft check on every transaction (too
aggressive — player can't even buy a hotel to recover before being penalized again).

---

## Phase 1: Design & Contracts

### Data Model

#### HP State (derived from Activity Log)

HP is not stored directly. It is calculated:

```
Current HP = SUM(
  Activity Log entries WHERE
    HP columns (HP+Hotel, HP-BadHabit, HP-Overdraft, or HP grant from RESPAWN/creation)
    are non-zero
)
```

HP-changing Activity Log entry types:

| Type | HP Column | Sign | Source |
|------|-----------|------|--------|
| Initial creation | HP + (Hotel) | + Starting HP | `seed_data.py` (Phase 1) |
| RESPAWN | HP + (Hotel) | + Starting HP | `hp_engine.respawn()` |
| BAD | HP - (Bad Habit) | - damage value | `hp_engine.apply_damage()` |
| PENALTY | HP - (Overdraft) | - penalty amount | `coin_engine.apply_overdraft_penalty()` |
| HOTEL | HP + (Hotel) | + recovery amount | `coin_engine.process_hotel_checkin()` |
| DIED | (none — marker) | 0 | `hp_engine.trigger_death()` |

#### Coin State (derived from Activity Log)

```
Current Coins = SUM(
  Activity Log entries WHERE
    Coin columns (Coins+Goal, Coins+Tasks, Coins-Market, Coins-Hotel, Coins-Black)
    are non-zero
)
```

Coin-changing Activity Log entry types:

| Type | Coin Column | Sign | Source |
|------|-------------|------|--------|
| GOAL | Coins + (Goal) | + award | Notion button (pre-filled from Goal.Award Coins) |
| TASKS | Coins + (Tasks) | + award | Notion button (pre-filled from Brain Dump.Award Coins) |
| MARKET | Coins - (Market) | - price | `coin_engine.process_market_purchase()` |
| HOTEL | Coins - (Hotel) | - price | `coin_engine.process_hotel_checkin()` |
| BLACKMARKET | Coins - (Black) | - price | `coin_engine.process_black_market()` |

#### Death State (derived from Activity Log)

```
Is Dead = EXISTS(
  Activity Log entry WHERE Type = "DIED"
  AND no subsequent entry WHERE Type = "RESPAWN" exists with a later Date
)
```

No boolean flag stored. Death state is derived from the Activity Log sequence.

#### Character DB (Display — Python-Written)

| Property | Updated By | Calculation |
|----------|-----------|-------------|
| Current HP | `hp_engine.update_character_hp()` | Sum of all HP Activity Log entries |
| Current Coins | `coin_engine.update_character_coins()` | Sum of all coin Activity Log entries |
| Death Count | `hp_engine.trigger_death()` | Increment on each DIED entry |
| HP Progress | Notion formula | Visual bar from Current HP / Starting HP |
| Character Details | Notion formula | Includes coin display |

### Contracts

#### hp_engine.py

```python
def get_current_hp(character_id: str) -> int
    """Sum all HP entries in Activity Log. Returns integer (can be negative)."""

def apply_damage(character_id: str, amount: int, source: str) -> dict
    """Create BAD/PENALTY Activity Log entry. Check death immediately after.
    Args: amount = positive integer (will be stored as negative).
    Returns: {"hp_before": int, "hp_after": int, "died": bool}"""

def apply_recovery(character_id: str, amount: int, source: str) -> dict
    """Create HOTEL Activity Log entry with positive HP.
    Returns: {"hp_before": int, "hp_after": int}"""

def check_death(character_id: str) -> bool
    """True if Current HP <= 0 AND no DIED entry without subsequent RESPAWN."""

def is_dead(character_id: str) -> bool
    """True if most recent death-related entry is DIED (not RESPAWN)."""

def trigger_death(character_id: str) -> dict
    """Create DIED Activity Log entry. Increment death count on Character.
    Only called if check_death() is True and is_dead() is False.
    Returns: {"death_count": int, "death_penalty_text": str}"""

def respawn(character_id: str) -> dict
    """If is_dead(): create RESPAWN Activity Log entry with +Starting HP.
    Clear Respawn checkbox. Update Character HP.
    If NOT dead: clear checkbox, log notice, return no-op.
    Returns: {"respawned": bool, "new_hp": int}"""

def update_character_hp(character_id: str) -> int
    """Recalculate and write Current HP to Character DB. Returns new HP."""
```

#### coin_engine.py

```python
def get_coin_balance(character_id: str) -> int
    """Sum all coin columns in Activity Log. Pure read."""

def spend_coins(character_id: str, amount: int, source: str, entry_type: str) -> dict
    """Create Activity Log entry with negative coins.
    BLOCKS if is_dead() — returns error dict.
    Returns: {"balance_before": int, "balance_after": int, "blocked": bool}"""

def earn_coins(character_id: str, amount: int, source: str) -> dict
    """Create Activity Log entry with positive coins.
    Always allowed (even while dead).
    Returns: {"balance_before": int, "balance_after": int}"""

def check_overdraft(character_id: str) -> bool
    """True if coin balance < 0."""

def apply_overdraft_penalty(character_id: str) -> dict
    """If overdrawn AND check is due (per frequency setting AND Last Check date):
    Apply HP damage via hp_engine.apply_damage(). Update Last Check date.
    Returns: {"penalized": bool, "hp_damage": int, "died": bool}"""

def process_market_purchase(character_id: str, item_id: str) -> dict
    """Deduct coins, mark item purchased, set redemption date.
    BLOCKS if is_dead().
    Returns: {"success": bool, "balance_after": int, "blocked": bool}"""

def process_hotel_checkin(character_id: str, hotel_tier: str) -> dict
    """Deduct coins, recover HP via hp_engine.apply_recovery().
    BLOCKS if is_dead().
    Returns: {"success": bool, "coins_after": int, "hp_after": int, "blocked": bool}"""

def process_black_market(character_id: str, habit_id: str, missed_date: str) -> dict
    """Deduct coins, create recovery Activity Log entry for missed date.
    BLOCKS if is_dead(). Does NOT repair streaks.
    Returns: {"success": bool, "coins_after": int, "blocked": bool}"""

def update_character_coins(character_id: str) -> int
    """Recalculate and write Current Coins to Character DB. Returns balance."""
```

### Quickstart

See `specs/002-hp-death-economy/quickstart.md` (generated separately).

---

## Implementation Order

| Step | Tool/Function | Depends On | Deliverable |
|------|--------------|------------|-------------|
| 1 | `hp_engine.get_current_hp()` | Phase 1 (notion_client, config) | HP sum query |
| 2 | `hp_engine.apply_damage()` | Step 1 | Bad habit → HP damage + Activity Log entry |
| 3 | `hp_engine.check_death()`, `is_dead()` | Step 1 | Death state detection |
| 4 | `hp_engine.trigger_death()` | Steps 2, 3 | Death event creation |
| 5 | `hp_engine.respawn()` | Steps 3, 4 | Respawn with guard |
| 6 | `hp_engine.update_character_hp()` | Step 1 | Write HP to Character DB |
| 7 | `test_hp_engine.py` | Steps 1-6 | HP engine test suite |
| 8 | `coin_engine.get_coin_balance()` | Phase 1 | Coin sum query |
| 9 | `coin_engine.spend_coins()`, `earn_coins()` | Step 8, Step 3 (is_dead check) | Core coin operations with dead-state guard |
| 10 | `coin_engine.process_market_purchase()` | Step 9 | Market flow |
| 11 | `coin_engine.process_hotel_checkin()` | Steps 9, 2 (apply_recovery) | Hotel flow (coins + HP) |
| 12 | `coin_engine.process_black_market()` | Step 9 | Black market flow |
| 13 | `coin_engine.check_overdraft()`, `apply_overdraft_penalty()` | Steps 8, 2 (apply_damage) | Overdraft → HP penalty bridge |
| 14 | `coin_engine.update_character_coins()` | Step 8 | Write coins to Character DB |
| 15 | `test_coin_engine.py` | Steps 8-14 | Coin engine test suite |

**Key dependency**: `coin_engine` depends on `hp_engine` for:
- `is_dead()` — to block spending while dead
- `apply_damage()` — for overdraft HP penalties
- `apply_recovery()` — for hotel HP recovery

---

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Notion as Headless DB & GUI | PASS | All state in Activity Log. Buttons, formulas, checkbox for respawn — all Notion-native |
| II. Python for Complex Orchestration | PASS | HP/coin are multi-row sums (cross-row = Python). Two tools, each one concern |
| III. WAT Architecture | PASS | Deterministic tools, no reasoning in engines |
| IV. Settings DB as Canonical Config | PASS | Starting HP, overdraft amount/frequency, hotel prices — all from config |
| V. Idempotency | PASS | Pure sums, Last Check date for overdraft, death dedup via is_dead() check |
| VI. Free-First | PASS | No new dependencies |

**Gate result: ALL PASS** — ready for `/speckit.tasks`.
