# Tasks: Phase 2 — HP System, Death & Economy

**Input**: Design documents from `/specs/002-hp-death-economy/`
**Prerequisites**: Phase 1 complete (all 33 databases, `db_ids.json`, seed data, config, logger, notion_client)

**Tests**: Included — the spec and constitution require pytest coverage for all tools.

**Organization**: Tasks grouped by engine (hp_engine first, then coin_engine) to respect the dependency chain: coin_engine depends on hp_engine for `is_dead()`, `apply_damage()`, `apply_recovery()`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Test Infrastructure Setup

**Purpose**: Extend Phase 1 test fixtures with HP/coin mock data for Activity Log scenarios

- [ ] T101 [P] Extend `tests/conftest.py` with Phase 2 fixtures — mock Activity Log entries for HP scenarios (initial creation +1000, BAD -10, RESPAWN +1000, DIED marker, PENALTY -100, HOTEL +50), mock Activity Log entries for coin scenarios (GOAL +50, TASKS +25, MARKET -150, HOTEL -100, BLACKMARKET -50), mock Character page with Current HP/Current Coins/Death Count/Respawn properties, mock Overdraft Penalty config row (Frequency, HP Penalty, Last Check), mock Hotel tier rows (Budget/Ordinary/Premium with prices and HP recovery), mock Market items, mock Bad Habit rows with damage values

---

## Phase 2: HP Engine — Core HP Tracking (US1: HP as Consequence)

**Purpose**: Implement HP calculation from Activity Log sum

- [ ] T102 [US1] Implement `get_current_hp()` in `tools/hp_engine.py` — query all Activity Log entries for character, sum HP columns (HP + Hotel, HP - Bad Habit, HP - Overdraft), return integer (can be negative). Use `config.py` for Activity Log DB ID from `db_ids.json`. Auto-paginate via `notion_client.query_database()`
- [ ] T103 [US1] Implement `apply_damage()` in `tools/hp_engine.py` — create BAD or PENALTY Activity Log entry with negative HP value, call `check_death()` immediately after, call `update_character_hp()`, return `{"hp_before": int, "hp_after": int, "died": bool}`
- [ ] T104 [US1] Implement `update_character_hp()` in `tools/hp_engine.py` — call `get_current_hp()`, write Current HP to Character DB page via `notion_client.update_page()`, return new HP value

**Checkpoint**: HP damage from bad habits flows through Activity Log and updates Character display

---

## Phase 3: HP Engine — Death & Respawn (US2: Death and Respawn)

**Purpose**: Implement death detection, death events, and respawn mechanism

- [ ] T105 [US2] Implement `is_dead()` in `tools/hp_engine.py` — query Activity Log for entries with Type = "DIED" or "RESPAWN", sort by date descending, return True if most recent death-related entry is DIED (no subsequent RESPAWN)
- [ ] T106 [US2] Implement `check_death()` in `tools/hp_engine.py` — return True if `get_current_hp()` <= 0 AND `is_dead()` is False (needs death event but doesn't have one yet)
- [ ] T107 [US2] Implement `trigger_death()` in `tools/hp_engine.py` — guard: only execute if `check_death()` True and `is_dead()` False. Create DIED Activity Log entry (no HP change, marker only). Read current Death Count from Character, increment by 1, write back. Return `{"death_count": int, "death_penalty_text": str}`
- [ ] T108 [US2] Implement `respawn()` in `tools/hp_engine.py` — if `is_dead()`: create RESPAWN Activity Log entry with +Starting HP (from `config.py`), clear Respawn checkbox on Character, call `update_character_hp()`, return `{"respawned": True, "new_hp": int}`. If NOT dead: clear Respawn checkbox, log notice, return `{"respawned": False, "new_hp": get_current_hp()}`
- [ ] T109 [US2] Implement `apply_recovery()` in `tools/hp_engine.py` — create HOTEL Activity Log entry with positive HP value, call `update_character_hp()`, return `{"hp_before": int, "hp_after": int}`

**Checkpoint**: Full HP lifecycle operational — damage → death detection → death event → respawn

---

## Phase 4: HP Engine Tests

**Purpose**: Comprehensive test coverage for all hp_engine functions

- [ ] T110 [US1][US2] Write tests in `tests/test_hp_engine.py`:
  - test `get_current_hp()` sums all HP entries correctly (positive + negative)
  - test `get_current_hp()` returns negative when damage exceeds starting HP
  - test `get_current_hp()` with empty Activity Log returns 0
  - test `apply_damage()` creates correct Activity Log entry with negative HP
  - test `apply_damage()` triggers death when HP drops to exactly 0
  - test `apply_damage()` triggers death when HP drops below 0
  - test `apply_damage()` does NOT trigger death when HP stays above 0
  - test `apply_damage()` while already dead: damage applied, no duplicate death event
  - test `is_dead()` returns True when last death-related entry is DIED
  - test `is_dead()` returns False when last death-related entry is RESPAWN
  - test `is_dead()` returns False when no death-related entries exist
  - test `check_death()` returns True when HP <= 0 and not yet dead
  - test `check_death()` returns False when HP > 0
  - test `check_death()` returns False when HP <= 0 but already dead
  - test `trigger_death()` creates DIED entry and increments death count
  - test `trigger_death()` guard: no-op when `is_dead()` already True
  - test `respawn()` creates RESPAWN entry with +Starting HP and clears checkbox
  - test `respawn()` while alive: clears checkbox, logs notice, no HP change
  - test `respawn()` after multiple deaths: death count preserved, HP reset
  - test `apply_recovery()` creates HOTEL entry with positive HP
  - test `update_character_hp()` writes correct value to Character DB
  - test multiple bad habits on same day: each applies independently, no daily cap

**Checkpoint**: HP engine fully tested — all US1 and US2 acceptance scenarios covered

---

## Phase 5: Coin Engine — Core Economy (US3: Earning and Spending)

**Purpose**: Implement coin balance tracking, earning, and spending with dead-state guard

- [ ] T111 [US3] Implement `get_coin_balance()` in `tools/coin_engine.py` — query all Activity Log entries for character, sum coin columns (Coins + Goal, Coins + Tasks, Coins - Market, Coins - Hotel, Coins - Black), return integer (can be negative). Pure read operation
- [ ] T112 [US3] Implement `spend_coins()` in `tools/coin_engine.py` — check `hp_engine.is_dead()` first: if dead, return `{"blocked": True, "balance_before": int, "balance_after": int}`. Otherwise create Activity Log entry with negative coins for the given entry_type (MARKET/HOTEL/BLACKMARKET), call `update_character_coins()`, return `{"blocked": False, "balance_before": int, "balance_after": int}`. Allow overdraft (negative balance)
- [ ] T113 [US3] Implement `earn_coins()` in `tools/coin_engine.py` — always allowed (even while dead). Create Activity Log entry with positive coins, call `update_character_coins()`, return `{"balance_before": int, "balance_after": int}`
- [ ] T114 [US3] Implement `update_character_coins()` in `tools/coin_engine.py` — call `get_coin_balance()`, write Current Coins to Character DB page, return balance

**Checkpoint**: Core coin operations work — earn, spend, dead-state guard, overdraft allowed

---

## Phase 6: Coin Engine — Market, Hotel & Black Market (US3 + US5)

**Purpose**: Implement specific spending flows for each shop type

- [ ] T115 [US3] Implement `process_market_purchase()` in `tools/coin_engine.py` — check `hp_engine.is_dead()` (block if dead). Read Market item price from Notion. Call `spend_coins()` with entry_type="MARKET". Mark item as purchased (update Market page: Purchased=true, Redemption Date=today). Return `{"success": bool, "balance_after": int, "blocked": bool}`
- [ ] T116 [US5] Implement `process_hotel_checkin()` in `tools/coin_engine.py` — check `hp_engine.is_dead()` (block if dead). Read hotel tier price and HP recovery from config/Hotel DB. Call `spend_coins()` with entry_type="HOTEL". Call `hp_engine.apply_recovery()` for HP gain. Return `{"success": bool, "coins_after": int, "hp_after": int, "blocked": bool}`
- [ ] T117 [US3] Implement `process_black_market()` in `tools/coin_engine.py` — check `hp_engine.is_dead()` (block if dead). Read Black Market price. Call `spend_coins()` with entry_type="BLACKMARKET". Create recovery Activity Log entry for the specific missed date. Does NOT repair streaks. Return `{"success": bool, "coins_after": int, "blocked": bool}`

**Checkpoint**: All three shops operational — Market, Hotel (with HP recovery), Black Market

---

## Phase 7: Coin Engine — Overdraft System (US4: Overdraft Penalties)

**Purpose**: Implement periodic overdraft check that bridges economy to HP system

- [ ] T118 [US4] Implement `check_overdraft()` in `tools/coin_engine.py` — return True if `get_coin_balance()` < 0
- [ ] T119 [US4] Implement `apply_overdraft_penalty()` in `tools/coin_engine.py` — read Overdraft Penalty config from Notion (Frequency, HP Penalty, Last Check date). If frequency is "Disabled", return `{"penalized": False}`. If check not due per frequency and Last Check date, return `{"penalized": False}`. If overdrawn AND check is due: call `hp_engine.apply_damage()` with penalty amount and source="OVERDRAFT". Update Last Check date on Overdraft Penalty row. Return `{"penalized": bool, "hp_damage": int, "died": bool}`

**Checkpoint**: Overdraft penalties bridge economy to HP — negative coins cause HP damage on schedule

---

## Phase 8: Coin Engine Tests

**Purpose**: Comprehensive test coverage for all coin_engine functions

- [ ] T120 [US3][US4][US5] Write tests in `tests/test_coin_engine.py`:
  - test `get_coin_balance()` sums all coin columns correctly (positive + negative)
  - test `get_coin_balance()` returns 0 with empty Activity Log
  - test `get_coin_balance()` returns negative when spending exceeds earning
  - test `spend_coins()` creates correct Activity Log entry with negative coins
  - test `spend_coins()` allows overdraft (balance goes negative)
  - test `spend_coins()` blocked when character is dead
  - test `earn_coins()` creates correct Activity Log entry with positive coins
  - test `earn_coins()` allowed while character is dead
  - test `process_market_purchase()` deducts coins and marks item purchased
  - test `process_market_purchase()` blocked while dead
  - test `process_hotel_checkin()` deducts coins AND recovers HP for Budget tier
  - test `process_hotel_checkin()` deducts coins AND recovers HP for Ordinary tier
  - test `process_hotel_checkin()` deducts coins AND recovers HP for Premium tier
  - test `process_hotel_checkin()` blocked while dead
  - test `process_hotel_checkin()` allows HP to exceed starting value (no cap)
  - test `process_black_market()` deducts coins and creates recovery entry
  - test `process_black_market()` blocked while dead
  - test `process_black_market()` does NOT repair streaks
  - test `check_overdraft()` returns True when balance negative
  - test `check_overdraft()` returns False when balance positive or zero
  - test `apply_overdraft_penalty()` applies HP damage when overdrawn and due
  - test `apply_overdraft_penalty()` skips when balance positive
  - test `apply_overdraft_penalty()` skips when frequency is "Disabled"
  - test `apply_overdraft_penalty()` skips when check not yet due (Last Check recent)
  - test `apply_overdraft_penalty()` updates Last Check date after applying
  - test `apply_overdraft_penalty()` triggers death when HP drops to 0 via penalty
  - test `update_character_coins()` writes correct value to Character DB
  - test 10+ mixed earn/spend transactions produce correct final balance (SC-004)

**Checkpoint**: Coin engine fully tested — all US3, US4, US5 acceptance scenarios covered

---

## Phase 9: Integration & Polish

**Purpose**: Cross-engine validation and documentation

- [ ] T121 [P] Write integration tests in `tests/test_hp_coin_integration.py`:
  - test overdraft penalty triggers death (coin → HP → death chain)
  - test hotel check-in recovers HP and deducts coins in single operation
  - test dead player cannot spend but CAN earn coins
  - test respawn after overdraft-caused death: HP resets, coin debt persists
  - test full lifecycle: earn coins → spend at hotel → log bad habit → die → respawn → earn → pay off overdraft
- [ ] T122 [P] Update `workflows/` with Phase 2 operational notes — HP engine usage, coin engine usage, manual verification steps from quickstart.md
- [ ] T123 Run `pytest tests/test_hp_engine.py tests/test_coin_engine.py tests/test_hp_coin_integration.py -v` and verify all tests pass
- [ ] T124 Run `pytest tests/ -v` and verify all tests pass (Phase 1 + Phase 2)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Test Infrastructure (Phase 1)**: No new dependencies — extend existing conftest.py
- **HP Core (Phase 2)**: Depends on Phase 1 project (notion_client, config, logger)
- **Death & Respawn (Phase 3)**: Depends on HP Core (get_current_hp)
- **HP Tests (Phase 4)**: Depends on Phases 2-3 (all hp_engine functions)
- **Coin Core (Phase 5)**: Depends on HP Engine (is_dead for dead-state guard)
- **Market/Hotel/Black Market (Phase 6)**: Depends on Coin Core (spend_coins, earn_coins)
- **Overdraft (Phase 7)**: Depends on Coin Core + HP Engine (apply_damage)
- **Coin Tests (Phase 8)**: Depends on Phases 5-7 (all coin_engine functions)
- **Integration (Phase 9)**: Depends on all phases complete

### Engine Dependencies

```
Phase 1 (Foundation — already complete)
  └── HP Engine (T102-T109)
        ├── hp_engine tests (T110)
        └── Coin Engine (T111-T119)
              ├── coin_engine tests (T120)
              └── Integration tests (T121)
                    └── Phase 9 Polish (T122-T124)
```

### Key Cross-Engine Dependency

`coin_engine` imports from `hp_engine`:
- `is_dead()` — to block spending while dead (T112, T115, T116, T117)
- `apply_damage()` — for overdraft HP penalties (T119)
- `apply_recovery()` — for hotel HP recovery (T116)

**HP engine MUST be complete before coin engine implementation begins.**

### Parallel Opportunities

- T101 (conftest fixtures) can run in parallel with T102-T104 (HP core)
- T121 (integration tests) + T122 (workflows) can be written in parallel
- Within HP engine: T102 → T103 + T104 can partially overlap (T104 only needs T102)
- Within coin engine: T115 + T116 + T117 can run in parallel after T111-T114

---

## Implementation Strategy

### HP Engine First (T101-T110)

1. Extend conftest.py with Phase 2 fixtures (T101)
2. Implement HP core: get_current_hp, apply_damage, update_character_hp (T102-T104)
3. Implement death/respawn: is_dead, check_death, trigger_death, respawn, apply_recovery (T105-T109)
4. Write and run HP engine tests (T110)
5. **STOP and VALIDATE**: HP damage, death, and respawn all work correctly

### Coin Engine Second (T111-T120)

6. Implement coin core: get_coin_balance, spend_coins, earn_coins, update_character_coins (T111-T114)
7. Implement shops: market, hotel, black market (T115-T117)
8. Implement overdraft: check_overdraft, apply_overdraft_penalty (T118-T119)
9. Write and run coin engine tests (T120)
10. **STOP and VALIDATE**: Full economy works, dead-state guards enforced

### Integration Last (T121-T124)

11. Write and run integration tests (T121)
12. Update workflows (T122)
13. Run full test suite (T123-T124)

---

## Notes

- All values are integers. No fractional HP or coins.
- Activity Log is append-only — no edits to existing entries.
- HP and coins are pure sums of Activity Log columns — re-reading always gives the correct value.
- Death state is derived from Activity Log event sequence, not a boolean flag.
- `is_dead()` check before every spending operation is the dead-state guard.
- Overdraft uses "Last Check" date for idempotency — safe to re-run.
- All functions use `tools/logger.py` for structured logging to stderr.
- All functions use `tools/config.py` for game balance constants (Starting HP, overdraft penalty, hotel prices).
- Commit after each task or logical group.
