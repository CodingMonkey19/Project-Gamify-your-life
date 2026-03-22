# Data Model: End-to-End Verification

**Feature**: 009-e2e-verification
**Date**: 2026-03-22

> Phase 9 is a verification phase — it does not introduce new database entities. This document defines the **test fixture data structures** used across all test files.

## Test Fixture Entities

### Mock Character Page

Standard test character used across engine tests.

| Field | Test Value | Source |
|-------|-----------|--------|
| Name | "TestHero" | Fixed |
| Class | "Warrior" | Fixed |
| Level | 5 | Fixed |
| HP | 800 | Fixed (below STARTING_HP to test recovery) |
| Max HP | 1000 | From config.py STARTING_HP |
| Coins | 150 | Fixed |
| Gold | 10 | Fixed |
| Rank | "Squire" | From config.py rank thresholds |
| STR_XP | 500 | Fixed |
| INT_XP | 300 | Fixed |
| WIS_XP | 200 | Fixed |
| VIT_XP | 400 | Fixed |
| CHA_XP | 100 | Fixed |
| Total_XP | 1500 | Sum of stat XPs |
| Streak_Days | 7 | Fixed (at tier 2 threshold) |

### Mock Settings

Mirrors `config.py` defaults to validate engines use config values, not hardcoded numbers.

| Setting | Test Value | Maps To |
|---------|-----------|---------|
| STARTING_HP | 1000 | config.STARTING_HP |
| XP_BASE | 100 | config.XP_BASE |
| XP_EXPONENT | 1.5 | config.XP_EXPONENT |
| STREAK_TIERS | [3, 7, 14, 30, 60, 100] | config.STREAK_TIERS |
| HOTEL_COSTS | {1: 50, 2: 100, 3: 200} | config.HOTEL_COSTS |
| HOTEL_RECOVERY | {1: 200, 2: 400, 3: 800} | config.HOTEL_RECOVERY |
| LOOT_WEIGHTS | {Common: 70, Rare: 20, Epic: 8, Legendary: 2} | config.LOOT_WEIGHTS |
| PITY_TIMER_THRESHOLD | 50 | config.PITY_TIMER_THRESHOLD |
| GOLD_CONVERSION_RATE | 100 | config.GOLD_CONVERSION_RATE |
| CLASS_BONUSES | {Warrior: "STR", Mage: "INT", ...} | config.CHARACTER_CLASSES |

### Mock Notion API Response Shape

All mock fixtures return dicts matching the Notion API response format:

```python
# Database query response
{
    "results": [
        {
            "id": "page-uuid",
            "properties": {
                "Name": {"title": [{"plain_text": "value"}]},
                "HP": {"number": 800},
                "Date": {"date": {"start": "2026-03-22"}},
                # ... property-specific shapes
            }
        }
    ],
    "has_more": False
}

# Page create/update response
{
    "id": "new-page-uuid",
    "url": "https://notion.so/new-page-uuid",
    "properties": { ... }
}
```

### Mock Activity Log (for idempotency tests)

| Field | Type | Purpose |
|-------|------|---------|
| Date | date | Idempotency key — one entry per date |
| Engine | text | Which engine created the entry |
| Action | text | What was done (e.g., "daily_xp_award") |
| Value | number | Numeric result |

## Relationships

```
conftest.py
├── mock_notion_client ──→ used by ALL 9 test files
├── mock_character_page ──→ used by xp, hp, coin, streak, chart tests
├── mock_settings ──→ used by ALL 9 test files (validates config sourcing)
├── mock_habit_rows ──→ used by streak, xp tests
├── mock_activity_log ──→ used by idempotency integration tests
├── mock_workout_rows ──→ used by fitness tests
├── mock_meal_rows ──→ used by nutrition tests
└── mock_expense_rows ──→ used by financial tests
```

## No New Databases

Phase 9 reads from existing databases only. No schema changes, no new tables, no migrations.
