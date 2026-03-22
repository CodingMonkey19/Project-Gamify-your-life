# Data Model: Phase 1 Foundation

**Date**: 2026-03-22
**Feature**: 001-phase-1-foundation

## Local Entities (File-Based)

### db_ids.json — Database ID Mapping

Stores the mapping between human-readable database names and Notion database IDs.

| Field | Type | Description |
|-------|------|-------------|
| `<database_name>` | string (Notion ID) | Notion UUID for each of 33 databases |

- Written by `create_databases.py` after each database is created or located
- Read by all tools needing database references
- 33 entries total
- Identity: database name (unique, matches the Notion database title)

### migrations.json — Migration Ledger

Tracks which schema migrations have been applied.

| Field | Type | Description |
|-------|------|-------------|
| `applied[].id` | string | Unique migration identifier (e.g., `001_add_mood_intensity`) |
| `applied[].applied_at` | ISO 8601 datetime | When the migration was applied |

- Ordered by `id` — migrations applied sequentially
- A migration not in this list is considered pending
- Identity: migration `id` (unique, never reused)

### .automation.lock — Concurrency Lock

Prevents overlapping automation runs.

| Field | Type | Description |
|-------|------|-------------|
| `pid` | integer | Process ID of the running automation |
| `started_at` | ISO 8601 datetime | When the lock was created |
| `module` | string | Which automation script holds the lock |

- Created at automation start, deleted on exit (including error paths)
- Stale lock detection: if PID is not running, lock can be overridden with warning

### .env — Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_API_KEY` | Yes | Notion integration secret |
| `NOTION_PARENT_PAGE_ID` | Yes | Notion page where databases are created |
| `OPENAI_API_KEY` | Validated, not used in Phase 1 | For future AI coaching |

## Notion Entities (33 Databases)

All 33 database schemas are defined in the V5 Implementation Plan (lines 252-560).
Phase 1 creates the schemas exactly as specified. Key structural notes:

### Creation Order (Two-Pass)

**Pass 1 — Create databases (no relations):**
All 33 databases created with their non-relation properties (Title, Number, Select,
Checkbox, Date, Text, Files, Formula, Status fields).

**Pass 2 — Add relations and rollups:**
All inter-database Relation and Rollup properties added. This requires all target
databases to already exist.

### Databases with Buttons

| Database | Button Name | Action |
|----------|-------------|--------|
| Good Habit | Check-in | Creates Activity Log entry (Type=GOOD) |
| Bad Habit | "Crap, I did..." | Creates Activity Log entry (Type=BAD) |
| Goal | COMPLETE | Creates Activity Log entry (Type=GOAL) |
| Brain Dump | COMPLETED / REDO | Creates Activity Log entry (Type=TASKS) |
| Market | Add to Cart / Buy | Cart relation / Activity Log entry (Type=MARKET) |
| Hotel | HOTEL CHECK-IN | Creates Activity Log entry (Type=HOTEL) |
| Black Market | Buy | Creates Activity Log entry (Type=BLACKMARKET) |

### Databases with Formulas

| Database | Formula Property | Computation |
|----------|-----------------|-------------|
| Character | EXP Progress | Visual bar `◾◾◾◽◽ 400/500` |
| Character | HP Progress | Visual bar + "You Died!" if HP ≤ 0 |
| Character | Character Details | "Name ▪ Level X ▪ Y Coins" |
| Good Habit | Check-in Status | ✅/❌ based on today's Activity Log |
| Good Habit | Heat Map | Calendar visualization |
| Bad Habit | Check-in Status | ✅ clean / ❌ failed today |
| Skill | Level Progress | `◾◾◾◽◽ 400/500 ▪ LV 1` |
| Market | T.Price | "1500 Coins" formatted |
| Hotel | Color Bar / Details | Tier indicator + price/HP display |
| Activity Log | Activities / Status / Totals | Human-readable summaries |
| My Cart | Holding Coins / Message | Balance + summary |

### Seed Data Counts

| Database | Seed Rows | Dedup Key |
|----------|-----------|-----------|
| Exercise Dictionary | 25+ | Title |
| Budget Categories | 8+ | Title |
| Ingredients Library | 40+ ingredients | Title |
| Achievement definitions | 43 | Title |
| Good Habit | 4 defaults | Title |
| Bad Habit | 3 defaults | Title |
| Hotel | 3 tiers | Title |
| To-do Difficulty | 3 levels | Title |
| Mood (types) | 7 types | Title |
| Skill/Area | 7 domains | Title |
| Character | 1 default | Title |
| Settings | ~15 defaults | Title |
| Vision Board Items | 8 categories | Title |

**Total**: ~160+ seed rows across 13 databases.

## State Transitions

### Database Setup Lifecycle

```
No databases → create_databases.py → 33 empty DBs with schemas
                                     → db_ids.json written
33 empty DBs → seed_data.py → populated workspace ready for play
```

### Migration Lifecycle

```
New migration defined → migrate.py reads migrations.json
  → migration not in applied list → execute migration → record in ledger
  → migration already applied → skip
  → migration fails → do NOT record, allow retry
```

### Lock Lifecycle

```
Automation start → check for .automation.lock
  → lock exists + PID running → log warning, exit
  → lock exists + PID dead → override with warning, proceed
  → no lock → create lock → run → remove lock (finally block)
```
