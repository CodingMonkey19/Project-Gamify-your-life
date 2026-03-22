# Implementation Plan: Phase 5 — Reward Systems (Loot Box, Achievement, Rank & Radar Chart)

**Branch**: `005-reward-systems` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-reward-systems/spec.md`

## Summary

Build four reward system engines that provide visual feedback and reward loops for the player's RPG progression. The rank engine determines tier (Peasant→Mythic) from Total XP as a high-water mark and triggers avatar frame compositing via the avatar renderer (Pillow + Cloudinary). The radar chart renderer generates 5-axis stat visualizations (matplotlib, 800x800 PNG, dark theme) and uploads to Cloudinary. The achievement engine evaluates 43 predefined badge conditions via hardcoded checker functions dispatched by condition key, creates Player Achievement records, and grants domain-routed XP bonuses. The loot box engine provides a Gold-to-Coins conversion loop with weighted PRNG (Common/Rare/Epic/Legendary) and a pity timer guaranteeing Legendary after 50 consecutive non-Legendary pulls. All engines are idempotent, read config from Settings DB, and integrate with existing coin_engine and xp_engine.

Key clarifications integrated:
- Loot box rewards: Coin bonuses by rarity (Common=25, Rare=75, Epic=200, Legendary=1000)
- Achievement evaluation: hardcoded checker functions dispatched by condition key
- Rank progression: high-water mark — never demotes
- Achievement XP: domain-routed (fitness badge → STR, finance badge → WIS, etc.)
- Loot box trigger: CLI command consistent with WAT architecture

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv` (inherited from Phase 1), `Pillow` (avatar compositing), `matplotlib` + `numpy` (radar chart), `cloudinary` (image hosting)
**Storage**: Notion — Loot Box Inventory, Achievements, Player Achievements, Character DB, Activity Log, Settings DB
**Testing**: `pytest` with mock Notion responses (`conftest.py` from Phases 1-4, extended)
**Target Platform**: GitHub Actions (scheduled daily), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Rank check < 5s; chart generation < 10s; achievement check < 15s (43 conditions); loot box < 5s per pull
**Constraints**: All XP/Coin/Gold values are integers (floor rounding). Activity Log is append-only. Phases 1-4 must be complete. Notion API rate limit (3 req/sec). Cloudinary free tier limits (25 credits/month). Rank is high-water mark only. Single player.
**Scale/Scope**: Single player, 43 achievements, 7 rank tiers, 4 loot rarity tiers, 5 stat axes on radar chart

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All data stored in Notion (Loot Box Inventory, Achievements, Player Achievements). Character DB stores Rank, Avatar URL, Radar Chart URL, Pity Counter. Python handles cross-row aggregation (achievement condition checks across multiple DBs), image generation (radar chart, avatar compositing), and weighted RNG (loot box). Notion-native: buttons could trigger loot box opens in future Phase 7 |
| II. Python for Complex Orchestration | PASS | Four new tools in `tools/`, each handling one concern: `rank_engine.py` (rank from XP threshold), `avatar_renderer.py` (Pillow compositing + Cloudinary upload), `chart_renderer.py` (matplotlib radar chart), `achievement_engine.py` (condition dispatch + XP grant), `loot_box.py` (weighted PRNG + pity timer + Coin reward). No tool does reasoning. All are deterministic and independently testable |
| III. WAT Architecture | PASS | Five new tools added to `tools/`. Each is a deterministic execution unit callable independently via CLI or via daily automation (Phase 7). No embedded reasoning |
| IV. Settings DB as Canonical Config | PASS | LOOT_WEIGHTS, LOOT_COST, PITY_TIMER_THRESHOLD, RANK_THRESHOLDS, LOOT_REWARDS — all read from `config.py` / Settings DB. No hardcoded balance values in engine files |
| V. Idempotency | PASS | Achievement engine checks for existing Player Achievement records before creating. Rank engine only updates on rank-up (high-water mark). Chart/avatar are regenerated (overwrite, no duplicate records). Loot box is intentionally non-idempotent (each call is a new purchase) but safe — Gold is deducted atomically via coin_engine |
| VI. Free-First | PASS | Pillow (free), matplotlib (free), Cloudinary free tier. No paid dependencies added. New pip dependencies: Pillow, matplotlib, numpy, cloudinary — all free/open-source |

## Project Structure

### Documentation (this feature)

```text
specs/005-reward-systems/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── rank_engine.py       # Rank tier from Total XP (high-water mark), rank-up detection
├── avatar_renderer.py   # Pillow frame compositing, Cloudinary upload, Character DB update
├── chart_renderer.py    # Radar chart generation (matplotlib), Cloudinary upload
├── achievement_engine.py # Condition dispatch, badge unlock, domain-routed XP grant
├── loot_box.py          # Weighted PRNG, pity timer, Gold→Coin conversion, inventory
│
├── config.py            # (Phase 1 — already exists) Reward system constants from Settings DB
├── logger.py            # (Phase 1 — already exists)
├── notion_client.py     # (Phase 1 — already exists)
├── xp_engine.py         # (Phase 3 — already exists) Called after achievement XP grants
├── coin_engine.py       # (Phase 2 — already exists) Gold deduction + Coin crediting for loot box

assets/
├── frames/              # Rank frame PNGs (one per tier: peasant.png, squire.png, etc.)
└── charts/              # Generated radar chart PNGs (output dir)

tests/
├── test_rank_engine.py       # Threshold mapping, high-water mark, boundary values
├── test_avatar_renderer.py   # Compositing output, placeholder fallback, upload mock
├── test_chart_renderer.py    # PNG dimensions, 5 axes, all-zero stats, title content
├── test_achievement_engine.py # Condition dispatch, idempotency, domain XP routing
├── test_loot_box.py          # Weight distribution ±5%, pity timer, Gold deduction, Coin credit
├── conftest.py               # (Phases 1-4 — extend with reward system mock fixtures)
```

**Structure Decision**: Flat `tools/` layout consistent with Phases 1-4. Each engine is a single file with clear boundaries. Tests mirror engine files 1:1. `avatar_renderer.py` and `chart_renderer.py` are separate from `rank_engine.py` because rendering is a distinct concern from rank calculation.

## Contracts

### rank_engine.py

```python
def get_rank_from_xp(total_xp: int) -> str:
    """Determine rank tier from Total XP using RANK_THRESHOLDS from config.
    Finds the highest threshold <= total_xp.
    Returns: rank name (e.g., 'Peasant', 'Squire', 'Knight', etc.)"""

def check_rank_up(character_id: str) -> dict:
    """Check if character has earned a rank-up (high-water mark).
    1. Read Total XP and Current Rank from Character DB
    2. Calculate rank from Total XP
    3. Compare: if calculated rank is higher tier than current → rank-up
    4. If rank-up: update Character DB Current Rank, trigger avatar_renderer
    5. If no change: return without action
    Returns: {"character_id": str, "previous_rank": str, "current_rank": str,
              "rank_changed": bool}"""
```

### avatar_renderer.py

```python
def composite_avatar(profile_picture_path: str, rank: str, output_path: str) -> str:
    """Composite player profile picture with rank-specific frame overlay.
    Loads frame from assets/frames/{rank.lower()}.png.
    Uses default placeholder if profile_picture_path is None or missing.
    Returns: output_path of composited image."""

def upload_image(image_path: str) -> str:
    """Upload image to Cloudinary, return hosted URL.
    Returns: URL string. Raises on upload failure."""

def update_character_avatar(character_id: str) -> dict:
    """Full pipeline: fetch profile picture URL from Character DB, download it,
    read current rank, composite with frame, upload, write Avatar URL back.
    Returns: {"character_id": str, "rank": str, "avatar_url": str}
    Returns None if upload fails (logged as warning, retried next run)."""
```

### chart_renderer.py

```python
def generate_radar_chart(stats: dict, player_name: str, rank: str, output_path: str) -> str:
    """Generate 5-axis radar chart (STR, INT, WIS, VIT, CHA).
    Dark background (#1a1a2e), neon accent polygon (#00d4ff), labeled axes,
    level values at vertices, player name + rank as title.
    Output: 800x800 PNG at output_path.
    Handles all-zero stats (collapsed center polygon).
    Returns: output_path."""

def upload_chart(image_path: str) -> str:
    """Upload chart image to Cloudinary, return hosted URL.
    Returns: URL string. Raises on upload failure."""

def update_character_chart(character_id: str) -> dict:
    """Full pipeline: read stat levels from Character DB, generate radar chart,
    upload to Cloudinary, write Radar Chart URL to Character DB.
    Returns: {"character_id": str, "stats": dict, "chart_url": str}
    Returns None if upload fails (logged as warning, retried next run)."""
```

### achievement_engine.py

```python
def get_all_achievements() -> list:
    """Fetch all achievement definitions from Achievements DB.
    Returns: [{"id": str, "name": str, "condition_key": str,
               "xp_bonus": int, "domain": str, "icon_url": str}, ...]"""

def get_unlocked_achievements(character_id: str) -> set:
    """Fetch all achievement IDs already unlocked by this character.
    Queries Player Achievements DB.
    Returns: set of achievement IDs."""

def check_condition(condition_key: str, character_id: str) -> bool:
    """Dispatch condition_key to the appropriate checker function.
    Uses CONDITION_CHECKERS dispatch map: {"first_workout": check_first_workout, ...}
    Returns: True if condition is met, False otherwise.
    Returns False for unknown condition keys (logged as warning)."""

def check_all_achievements(character_id: str) -> dict:
    """Orchestrator: evaluate all achievement conditions for a character.
    1. Fetch all achievements
    2. Fetch already-unlocked achievement IDs
    3. For each not-yet-unlocked achievement: check_condition()
    4. For each newly qualifying: create Player Achievement row, create Activity Log
       entry with XP bonus routed to achievement's Domain stat
    5. Call xp_engine.update_character_stats() if any achievements unlocked
    Returns: {"checked": int, "newly_unlocked": list[str], "total_xp_granted": int}"""
```

### loot_box.py

```python
def roll_rarity(pity_counter: int) -> str:
    """Select random rarity using LOOT_WEIGHTS from config.
    If pity_counter >= PITY_TIMER_THRESHOLD: return 'Legendary' (guaranteed).
    Otherwise: weighted random selection.
    Returns: rarity name ('Common', 'Rare', 'Epic', 'Legendary')."""

def get_coin_reward(rarity: str) -> int:
    """Look up Coin reward for a rarity tier from LOOT_REWARDS config.
    Default: Common=25, Rare=75, Epic=200, Legendary=1000.
    Returns: Coin amount (int)."""

def open_loot_box(character_id: str) -> dict:
    """Full loot box purchase pipeline.
    1. Read Gold balance and Pity Counter from Character DB
    2. Check Gold >= LOOT_COST → reject if insufficient
    3. Deduct Gold via coin_engine
    4. Roll rarity (passing current pity_counter)
    5. Get Coin reward for rarity
    6. Credit Coins via coin_engine
    7. Update Pity Counter: reset to 0 if Legendary, else increment by 1
    8. Create Loot Box Inventory row
    Returns: {"rarity": str, "coins_awarded": int, "gold_spent": int,
              "pity_counter": int, "inventory_id": str}
    Returns None with error message if insufficient Gold."""
```

## Implementation Order

| Step | Function/File | Depends On | Delivers |
|------|--------------|------------|----------|
| 1 | `config.py` updates | Phase 1 config | New constants: LOOT_WEIGHTS, LOOT_COST, PITY_TIMER_THRESHOLD, RANK_THRESHOLDS, LOOT_REWARDS |
| 2 | `rank_engine.get_rank_from_xp()` | Step 1 (config) | Pure math: XP → rank tier |
| 3 | `rank_engine.check_rank_up()` | Step 2, Phase 1 (notion_client) | Rank-up detection + Character DB update |
| 4 | `avatar_renderer.composite_avatar()` | Pillow | Frame compositing |
| 5 | `avatar_renderer.upload_image()` | Cloudinary | Image upload |
| 6 | `avatar_renderer.update_character_avatar()` | Steps 3-5 | Full avatar pipeline |
| 7 | `test_rank_engine.py` + `test_avatar_renderer.py` | Steps 2-6 | Rank + avatar test suites |
| 8 | `chart_renderer.generate_radar_chart()` | matplotlib, numpy | Chart generation |
| 9 | `chart_renderer.upload_chart()` | Cloudinary | Chart upload |
| 10 | `chart_renderer.update_character_chart()` | Steps 8-9, Phase 1 (notion_client) | Full chart pipeline |
| 11 | `test_chart_renderer.py` | Steps 8-10 | Chart test suite |
| 12 | `achievement_engine.get_all_achievements()` | Phase 1 (notion_client) | Achievement query |
| 13 | `achievement_engine.get_unlocked_achievements()` | Phase 1 (notion_client) | Unlocked set query |
| 14 | `achievement_engine.check_condition()` | Hardcoded checkers | Condition dispatch |
| 15 | `achievement_engine.check_all_achievements()` | Steps 12-14, Phase 3 (xp_engine) | Full achievement orchestration |
| 16 | `test_achievement_engine.py` | Steps 12-15 | Achievement test suite |
| 17 | `loot_box.roll_rarity()` | Step 1 (config) | Weighted PRNG + pity timer |
| 18 | `loot_box.get_coin_reward()` | Step 1 (config) | Rarity → Coin lookup |
| 19 | `loot_box.open_loot_box()` | Steps 17-18, Phase 2 (coin_engine), Phase 1 (notion_client) | Full loot box pipeline |
| 20 | `test_loot_box.py` | Steps 17-19 | Loot box test suite |
| 21 | `conftest.py` updates | Steps 7, 11, 16, 20 | Mock fixtures for reward engines |

**Key dependencies**:
- `rank_engine` depends on `notion_client` (Phase 1) for Character DB reads/writes
- `avatar_renderer` depends on `Pillow` (new dependency) and `cloudinary` (new dependency)
- `chart_renderer` depends on `matplotlib` + `numpy` (new dependencies) and `cloudinary`
- `achievement_engine` depends on `xp_engine` (Phase 3) for stat refresh after XP grants
- `loot_box` depends on `coin_engine` (Phase 2) for Gold deduction and Coin crediting
- All engines depend on `config.py` (Phase 1) for configurable constants
- Rank engine and chart renderer are independent of each other — can be built in parallel
- Achievement engine is independent of loot box — can be built in parallel
- `rank_engine.get_rank_from_xp()` and `loot_box.roll_rarity()` + `get_coin_reward()` are pure functions with zero dependencies — can be built first
