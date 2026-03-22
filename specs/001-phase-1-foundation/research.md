# Research: Phase 1 Foundation

**Date**: 2026-03-22
**Feature**: 001-phase-1-foundation

## R1: Notion API — Database Creation and Relations

**Decision**: Two-pass creation (all databases first, relations second)
**Rationale**: Notion requires both databases to exist before a relation property can
reference them. Creating all 33 databases in pass 1 guarantees all targets exist when
pass 2 adds relation properties.
**Alternatives considered**:
- Topological sort: More complex, same result since all DBs need to exist anyway
- Single-pass with forward declarations: Not supported by Notion API

## R2: Idempotency Strategy — Database Identification

**Decision**: Store database IDs in `db_ids.json`; use stored ID as primary lookup,
fall back to title match under parent page if ID lookup fails.
**Rationale**: Notion database IDs are stable and unique. Title matching alone is
fragile (renames break it). Dual strategy handles normal re-runs (ID hit) and
recovery scenarios (database deleted and recreated).
**Alternatives considered**:
- Title-only: Fragile — player could rename in Notion
- Store in `.env`: Clutters env with 24 entries, harder to read

## R3: Concurrency Protection

**Decision**: Lock file (`.automation.lock`) created at start, removed on exit.
Second run detects lock, logs warning, exits.
**Rationale**: GitHub Actions can overlap if a run exceeds cron interval. Lock file
is the simplest mechanism preventing concurrent write corruption.
**Alternatives considered**:
- Queue-based: Overkill for single-player automation
- No protection: Risk of data corruption from parallel writes

## R4: Notion API Rate Limiting

**Decision**: Exponential backoff with jitter on 429 responses. Max 3 req/sec
sustained. Max 3 retries per request.
**Rationale**: Notion's rate limit is 3 requests/second per integration. Backoff
with jitter prevents thundering herd. 3 retries covers transient issues.
**Alternatives considered**:
- Fixed delay: Less efficient, wastes time when API recovers quickly
- No limiting: Will fail on bulk operations (24 DBs × multiple properties)

## R5: Seed Data Deduplication

**Decision**: Query by title before inserting. Skip if exists. Player renames not
tracked.
**Rationale**: Title is the natural identifier for reference data. ~150 rows total,
so query-before-insert is fast enough.
**Alternatives considered**:
- Hidden UUID property: Adds complexity to every database schema
- Hash-based: Over-engineered for the row count

## R6: Migration Ledger Format

**Decision**: `migrations.json` — JSON file tracking applied migration IDs with
timestamps.
**Rationale**: Human-readable, versionable in git, trivial to parse. No external
dependency.
**Alternatives considered**:
- Notion-based tracking DB: Circular dependency — can't migrate the tracker
- SQLite: Unnecessary dependency for a simple ordered list

## R7: Notion Button Properties

**Decision**: Buttons are created as Notion button properties via the API where
supported. For databases where buttons need custom logic (e.g., "Check-in" creating
an Activity Log entry), the button is configured to create a new page in Activity Log
with pre-filled relations.
**Rationale**: Notion buttons are the user-facing interaction mechanism per
Constitution Principle I. They keep all user actions inside Notion.
**Note**: Notion API button support may require specific API version. The
`notion_client.py` wrapper will target the latest stable API version.
