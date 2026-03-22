# Implementation Plan: Phase 1 Foundation

**Branch**: `001-phase-1-foundation` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-phase-1-foundation/spec.md`

## Summary

Build the complete foundation layer for the RPG-Gamified Life Tracker: a centralized
configuration system backed by a Notion Settings DB with hardcoded fallbacks, a
rate-limited Notion API client with retry logic, structured logging, a pre-flight
smoke test, automated creation of all 33 Notion database schemas (two-pass: create
then link relations), idempotent seed data population, and a versioned schema
migration runner. This phase delivers a fully functional, ready-to-use Notion
workspace with zero manual setup.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv`
**Storage**: Notion (headless database), local `.env` + `db_ids.json` (ID mapping)
**Testing**: `pytest` with mock Notion responses (`conftest.py`)
**Target Platform**: GitHub Actions (scheduled), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Smoke test < 30s; full DB creation < 5 min for 33 databases
**Constraints**: Notion API rate limit (3 req/sec max), zero paid dependencies in Phase 1
**Scale/Scope**: Single player, 33 databases, ~150 seed rows across all databases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All data stored in Notion; Python only creates schemas and seeds data, never replicates Notion-native features |
| II. Python for Complex Orchestration | PASS | Each tool handles one concern: `config.py` (config), `notion_client.py` (API), `smoke_test.py` (validation), `create_databases.py` (schemas), `seed_data.py` (seeding), `migrate.py` (migrations) |
| III. WAT Architecture | PASS | Tools in `tools/`, workflows in `workflows/`, no direct multi-step execution without SOPs |
| IV. Settings DB as Canonical Config | PASS | `config.py` reads from Settings DB first, falls back to hardcoded defaults. No engine embeds balance values directly |
| V. Idempotency | PASS | DB creation uses stored ID + title fallback (FR-009). Seed uses title dedup (FR-012). Migration tracks applied versions (FR-015). Lock file prevents concurrent runs (FR-017) |
| VI. Free-First | PASS | No paid dependencies in Phase 1. Only `notion-client` and `python-dotenv` |

**Gate result: ALL PASS** — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-1-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
tools/
├── config.py            # All balance constants + Settings DB reader
├── logger.py            # Structured logging with timestamps
├── notion_client.py     # Notion API wrapper (rate limiting, pagination, retries)
├── smoke_test.py        # Pre-flight validation
├── create_databases.py  # Two-pass: create 33 DBs, then link relations + buttons
├── seed_data.py         # Idempotent reference data population
└── migrate.py           # Schema migration runner with version tracking

tests/
├── conftest.py          # Shared fixtures (mock Notion responses)
├── test_config.py       # Settings DB reader, fallback behavior
├── test_notion_client.py # Rate limiting, retry, pagination
├── test_smoke_test.py   # Credential and DB validation
├── test_create_dbs.py   # Schema creation, idempotency, two-pass relations
├── test_seed_data.py    # Dedup, no-overwrite, expected row counts
└── test_migrate.py      # Version tracking, ordered application, failure handling

workflows/
├── setup-notion.md      # Notion integration setup SOP
└── onboarding.md        # Character creation + identity setup SOP

db_ids.json              # Stored database name → Notion ID mapping
migrations.json          # Migration version ledger
.env                     # NOTION_API_KEY, NOTION_PARENT_PAGE_ID, OPENAI_API_KEY
```

**Structure Decision**: Single-project layout following WAT architecture. All Python
tools are flat in `tools/` (one concern per file). Tests mirror tool names. No
`src/` wrapper — tools are invoked directly via `python tools/<script>.py`.

## Complexity Tracking

No constitution violations. Table not required.

---

## Phase 0: Research

All technical decisions for Phase 1 are well-defined in the V5 plan and constitution.
No NEEDS CLARIFICATION items remain after the clarify session. Research findings:

### R1: Notion API — Database Creation and Relations

**Decision**: Two-pass creation (all databases first, relations second)
**Rationale**: Notion requires both databases to exist before a relation property can
reference them. Creating all 33 databases in pass 1 guarantees all targets exist when
pass 2 adds relation properties. This is simpler and more reliable than topological
sorting.
**Alternatives considered**: Topological sort (more complex, same result), single-pass
with forward declarations (not supported by Notion API).

### R2: Idempotency Strategy — Database Identification

**Decision**: Store database IDs in `db_ids.json` after creation; use stored ID as
primary lookup, fall back to title match under parent page if ID lookup fails.
**Rationale**: Notion database IDs are stable and unique. Title matching alone is
fragile (renames break it). Dual strategy handles both normal re-runs (ID hit) and
recovery scenarios (database deleted and recreated).
**Alternatives considered**: Title-only matching (fragile), storing IDs in `.env`
(clutters env with 24 entries).

### R3: Concurrency Protection

**Decision**: Lock file created at automation start, removed on exit (including error
paths). Second run detects lock, logs warning, exits.
**Rationale**: GitHub Actions can overlap if a run exceeds the cron interval. Lock
file is the simplest mechanism that prevents data corruption from concurrent writes.
**Alternatives considered**: Queue-based (overkill for single-player), no protection
(risky).

### R4: Notion API Rate Limiting

**Decision**: Exponential backoff with jitter on 429 responses. Max 3 req/sec
sustained rate. Max 3 retries per request.
**Rationale**: Notion's documented rate limit is 3 requests/second per integration.
Backoff with jitter prevents thundering herd on retry. 3 retries covers transient
issues without hanging indefinitely.
**Alternatives considered**: Fixed delay (less efficient), no rate limiting (will fail
on bulk operations).

### R5: Seed Data Deduplication

**Decision**: Query by title before inserting. If a row with the same title exists
in the target database, skip it. Player-renamed rows are not detected as duplicates.
**Rationale**: Title is the natural human-readable identifier for reference data.
The tradeoff (renamed rows not deduplicated) is acceptable per user decision — player
renames are the player's responsibility.
**Alternatives considered**: Hidden unique ID property (adds complexity to every
database), hash-based dedup (over-engineered for ~150 rows).

### R6: Migration Ledger Format

**Decision**: `migrations.json` — a JSON file tracking applied migration IDs with
timestamps. Each migration is a Python dict defining the operation (add property,
rename, etc.) with a unique version string.
**Rationale**: JSON is human-readable, versionable in git, and trivial to parse.
No external database needed for tracking.
**Alternatives considered**: Notion-based tracking DB (circular dependency — can't
migrate the migration tracker), SQLite (unnecessary dependency).

---

## Phase 1: Design & Contracts

### Data Model

#### db_ids.json (Database ID Mapping)

```json
{
  "Character": "notion-db-id-here",
  "Activity Log": "notion-db-id-here",
  "Good Habit": "notion-db-id-here",
  ...
}
```

- Written by `create_databases.py` after each database is created
- Read by all tools that need to interact with specific databases
- 33 entries, one per database name

#### migrations.json (Migration Ledger)

```json
{
  "applied": [
    {
      "id": "001_add_mood_intensity",
      "applied_at": "2026-03-22T10:00:00Z"
    }
  ]
}
```

- Written by `migrate.py` after each successful migration
- Read before applying to determine which migrations are pending
- Ordered by `id` — migrations applied sequentially

#### Lock File (.automation.lock)

```json
{
  "pid": 12345,
  "started_at": "2026-03-22T22:00:00Z",
  "module": "daily_automation"
}
```

- Created at automation start, removed on exit
- Checked by all automation entry points before executing
- Contains enough info to diagnose stale locks

#### Settings DB Schema (Notion)

Key-value structure: each row is one setting.

| Setting Name (Title) | Value (Number/Text) | Type (Select) | Description (Text) |
|---|---|---|---|
| Starting HP | 1000 | number | HP on creation/respawn |
| Default Habit XP | 5 | number | XP per good habit |
| Overdraft Penalty | 100 | number | HP deducted on overdraft |
| Level Exponent | 1.8 | number | XP curve steepness |
| Level Base XP | 1000 | number | Base XP per level |
| ... | ... | ... | ... |

Read by `config.py` → `load_settings_from_notion()`. Fallback to hardcoded defaults
per setting if missing or invalid (non-numeric where number expected).

### Contracts

Phase 1 tools expose CLI interfaces (invoked via `python tools/<script>.py`):

#### smoke_test.py

```
Input:  (none — reads .env and db_ids.json)
Output: JSON to stdout
  {
    "status": "pass" | "fail",
    "checks": [
      {"name": "NOTION_API_KEY", "status": "pass" | "fail", "message": "..."},
      {"name": "NOTION_PARENT_PAGE_ID", "status": "pass" | "fail", "message": "..."},
      {"name": "notion_connectivity", "status": "pass" | "fail", "message": "..."},
      {"name": "db_Character", "status": "pass" | "fail", "message": "..."},
      ...
    ]
  }
Exit code: 0 if all pass, 1 if any fail
```

#### create_databases.py

```
Input:  --parent-page-id (or from .env)
Output: JSON to stdout
  {
    "created": ["Character", "Activity Log", ...],
    "skipped": ["Good Habit", ...],  // already existed
    "relations_linked": 42,
    "buttons_added": 12
  }
Side effect: writes/updates db_ids.json
Exit code: 0 on success, 1 on failure
```

#### seed_data.py

```
Input:  (none — reads db_ids.json for target databases)
Output: JSON to stdout
  {
    "seeded": {"Good Habit": 4, "Bad Habit": 3, "Hotel": 3, ...},
    "skipped": {"Good Habit": 0, "Hotel": 0, ...},  // already existed
    "total_created": 150,
    "total_skipped": 0
  }
Exit code: 0 on success, 1 if required database missing
```

#### migrate.py

```
Input:  (none — reads migrations.json and db_ids.json)
Output: JSON to stdout
  {
    "applied": ["001_add_mood_intensity"],
    "skipped": ["000_initial"],  // already applied
    "failed": [],
    "pending": 0
  }
Exit code: 0 if all applied, 1 if any failed
```

#### config.py (library, not CLI)

```python
# Usage by other tools:
from config import get_config

config = get_config(notion_client, settings_db_id)
xp_per_habit = config["DEFAULT_HABIT_XP"]  # from Notion or fallback
```

### Quickstart

See `specs/001-phase-1-foundation/quickstart.md` (generated separately).

---

## Implementation Order

| Step | Tool | Depends On | Deliverable |
|------|------|------------|-------------|
| 1 | `tools/logger.py` | — | Structured logging module |
| 2 | `tools/config.py` | logger | Constants + Settings DB reader |
| 3 | `tools/notion_client.py` | logger, config | API wrapper with rate limiting |
| 4 | `tools/smoke_test.py` | notion_client, config | Pre-flight validation |
| 5 | `tools/create_databases.py` | notion_client, config, logger | 33 DB schemas + relations + buttons |
| 6 | `tools/seed_data.py` | notion_client, config, create_databases | Reference data population |
| 7 | `tools/migrate.py` | notion_client, config, logger | Migration runner |
| 8 | `tests/*` | all tools | Full test suite |
| 9 | `workflows/setup-notion.md` | all tools | Setup SOP |

Lock file logic (FR-017) is implemented in `notion_client.py` as a shared utility
used by all automation entry points.

---

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Notion as Headless DB & GUI | PASS | All data in Notion, Python only orchestrates |
| II. Python for Complex Orchestration | PASS | 7 tools, each one concern, no embedded constants |
| III. WAT Architecture | PASS | Tools + workflows, no monolithic scripts |
| IV. Settings DB as Canonical Config | PASS | `config.py` reads Settings DB first |
| V. Idempotency | PASS | ID+title for DBs, title for seeds, version for migrations, lock for concurrency |
| VI. Free-First | PASS | Zero paid deps |

**Gate result: ALL PASS** — ready for `/speckit.tasks`.
