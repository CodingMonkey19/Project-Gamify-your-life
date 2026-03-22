# Data Model: Automation Orchestration

**Date**: 2026-03-22 | **Feature**: 007-automation-orchestration

## Entities

### Daily Snapshot (Notion DB — already exists from Phase 1)

Point-in-time capture of all character state. One row per day per character.

| Field | Type | Source | Validation |
|-------|------|--------|------------|
| Date | Date | `date.today()` at pipeline start | Unique per Character. Idempotency key. |
| Character | Relation → Character DB | CLI arg `--character-id` | Must exist in Character DB |
| STR XP | Number | `character_db.STR_XP` | >= 0 |
| INT XP | Number | `character_db.INT_XP` | >= 0 |
| WIS XP | Number | `character_db.WIS_XP` | >= 0 |
| VIT XP | Number | `character_db.VIT_XP` | >= 0 |
| CHA XP | Number | `character_db.CHA_XP` | >= 0 |
| Level | Number | `character_db.Level` | >= 1 |
| Gold | Number | `character_db.Gold` | >= 0 |
| Coins | Number | `character_db.Coins` | Can be negative (overdraft) |
| HP | Number | `character_db.HP` | 0 to STARTING_HP |
| Rank | Select | `character_db.Rank` | One of RANK_THRESHOLDS values |
| Active Streaks | Number | Count from Streak Tracker where active=true | >= 0 |
| Mood | Select | Last mood entry or "Neutral" | One of MOOD_TYPES |

**State transitions**: None — snapshots are immutable after creation. No updates, only inserts.

### Treasury Row (Notion DB — already exists from Phase 1)

Monthly financial summary. One row per month per character.

| Field | Type | Source | Validation |
|-------|------|--------|------------|
| Month | Text | `YYYY-MM` format | Unique per Character. Idempotency key. |
| Character | Relation → Character DB | CLI arg `--character-id` | Must exist |
| Income | Number | Sum of income entries in Expense Log for month | >= 0 |
| Expenses | Number | Sum of expense entries in Expense Log for month | >= 0 |
| Surplus | Number | Income - Expenses | Can be negative (deficit) |
| Gold Earned | Number | `max(0, surplus) / GOLD_CONVERSION_RATE` | >= 0 (no penalty for deficit) |
| WIS XP | Number | Calculated based on financial discipline | >= 0 |

**State transitions**: None — Treasury rows are immutable after creation.

### Weekly Report (Computed — not persisted to DB)

Transient summary logged via logger.py and stdout. Not a Notion DB entity.

| Field | Type | Source |
|-------|------|--------|
| Period | Text | `{start_date} to {end_date}` |
| Stat Deltas | Dict[str, float] | `snapshot[today] - snapshot[7_days_ago]` per stat |
| HP Delta | Number | Same calculation |
| Gold Delta | Number | Same calculation |
| Coins Delta | Number | Same calculation |
| Streaks Active | Number | Count from Streak Tracker |
| Streaks Broken | Number | Count recently broken |
| Quests Completed | Number | Count from quest_engine |
| Quests Generated | Number | Always 3 (from quest_generator) |
| Coaching Persona | Text | Rotating persona from coaching_engine |
| Coaching Briefing | Text | AI-generated text |
| AI Cost | Float | Tokens used * model pricing |
| Overdraft Status | Text | "clear" / "penalized {amount} HP" |

### Pipeline Context (In-memory only)

Passed between pipeline steps. Not persisted.

| Field | Type | Purpose |
|-------|------|---------|
| character_id | str | Target character UUID |
| run_date | date | Captured once at start (cross-midnight safety) |
| settings | dict | Merged config from Settings DB + defaults |
| notion_client | NotionClient | Authenticated API client |
| results | dict[str, Any] | Accumulator for per-step results |
| errors | list[str] | Accumulator for per-step errors |

## Relationships

```
Character DB (1) ←── (many) Daily Snapshots
Character DB (1) ←── (many) Treasury Rows
Character DB (1) ←── (many) Activity Log entries
Character DB (1) ←── (many) Streak Tracker entries
Character DB (1) ←── (many) Quest entries

Daily Snapshots (7) ──→ Weekly Report (computed, 1)
Expense Log (month) ──→ Treasury Row (1)
Settings DB ──→ Pipeline Context (runtime config)
```

## Idempotency Keys

| Entity | Key | Check Query |
|--------|-----|-------------|
| Daily Snapshot | `Date + Character` | Filter: `Date == run_date AND Character == character_id` |
| Treasury Row | `Month + Character` | Filter: `Month == YYYY-MM AND Character == character_id` |
| Activity Log | `Date + Habit + Type` | Each engine queries before insert |
| Streak Tracker | `Last Processed Date` | Engine checks before updating |
| AI Monthly Spend | `AI_MONTHLY_SPEND` in Settings | Read before write; reset only on 1st of month |
