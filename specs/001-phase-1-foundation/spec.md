# Feature Specification: Phase 1 Foundation

**Feature Branch**: `001-phase-1-foundation`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Phase 1 Foundation: Config, Logging, Notion Client, Smoke Test, Database Schemas, Seed Data, and Migration Runner"

## Clarifications

### Session 2026-03-22

- Q: Are Seed Reference Data (Task 1.5) and Migration Runner (Task 1.6) in Phase 1 scope? → A: Yes, both are in Phase 1 scope.
- Q: How are existing databases identified for idempotent re-runs? → A: Store IDs as primary lookup, fall back to title match if ID lookup fails.
- Q: What happens if two automation runs overlap? → A: Lock file — second run detects it, logs a warning, and exits without executing.
- Q: Is title-based seed deduplication acceptable if a player renames a row? → A: Yes, acceptable — seed by title is good enough; player renames are their responsibility.
- Q: How should database creation handle relation dependencies across 33 databases? → A: Two-pass — create all databases first (no relations), then add all relations in a second pass.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurable Game Balance (Priority: P1)

A player can open the Settings page in their Notion workspace and adjust any game
balance value — XP rates, HP damage amounts, streak tier thresholds, hotel prices,
coin rewards — and have those values automatically apply the next time automation
runs. No code changes, no developer involvement required.

**Why this priority**: All other game systems depend on these balance values. Getting
them right is iterative — players need to tune them to match their lifestyle without
friction. This is the control panel for the entire RPG.

**Independent Test**: Can be tested by changing a value in Notion Settings, running
any automation, and verifying the new value was used. Delivers standalone value as a
configuration system even before other features are built.

**Acceptance Scenarios**:

1. **Given** a player has set "XP per habit check-in" to 10 in the Notion Settings
   page, **When** the daily automation runs, **Then** completed habits award 10 XP
   (not the default value).
2. **Given** the Notion Settings page is empty or unreachable, **When** automation
   runs, **Then** the system uses built-in default values and logs a notice that
   defaults are in use.
3. **Given** a player changes a balance value mid-day, **When** the next automation
   run begins, **Then** the updated value is picked up without any manual reset.

---

### User Story 2 - Complete Game Workspace Setup (Priority: P2)

A player runs a single setup command and gets all 33 game databases created in their
Notion workspace — fully structured with every required property, all inter-database
relationships linked, and action buttons ready to use. No manual Notion setup required.

**Why this priority**: Without the database schemas, nothing else can be built or
tested. This is the structural foundation every other feature depends on.

**Independent Test**: Can be verified by inspecting the Notion workspace and
confirming all 33 databases exist with correct properties. Delivers a functional
Notion workspace skeleton even before automation logic is added.

**Acceptance Scenarios**:

1. **Given** a player has a valid Notion integration and a parent page, **When** they
   run the setup command, **Then** all 33 game databases appear in Notion with correct
   names, properties, and relation links between databases.
2. **Given** the setup command has already been run once, **When** it is run again,
   **Then** no duplicate databases are created and existing data is preserved.
3. **Given** the player's Notion workspace, **When** they open any database, **Then**
   action buttons (e.g., "Check-in", "COMPLETE", "Buy") are present and correctly
   configured on the appropriate databases.

---

### User Story 3 - Pre-Flight System Check (Priority: P3)

Before any automation runs, the player can trigger a readiness check that confirms
all required credentials are set, all Notion connections are live, and all game
databases are accessible. The result is a clear pass/fail report — not a cryptic
error mid-run.

**Why this priority**: Silent automation failures waste time and can corrupt game
state. An explicit readiness gate catches problems before they cause damage.

**Independent Test**: Can be tested in isolation by running the check command and
verifying it correctly identifies missing credentials or unreachable databases.

**Acceptance Scenarios**:

1. **Given** all credentials are set and all databases exist, **When** the pre-flight
   check runs, **Then** it reports every check as passed within 30 seconds (measured against Notion API at standard 3 req/sec rate limit per FR-004).
2. **Given** the Notion API key is missing, **When** the pre-flight check runs,
   **Then** it fails immediately with a clear message identifying the missing
   credential by name.
3. **Given** one or more expected game databases do not exist, **When** the check
   runs, **Then** it lists each missing database by name and exits with a failure
   status so automation pipelines can detect it.

---

### User Story 4 - Resilient Automation Connectivity (Priority: P4)

When the Notion service is temporarily unavailable or rate-limited, automation
recovers automatically — retrying the operation — rather than crashing and leaving
game state in an inconsistent condition.

**Why this priority**: Automation runs unattended on a schedule. Transient failures
must not require manual intervention to resolve.

**Independent Test**: Can be simulated by observing retry behavior under rate-limit
conditions. Delivers value independently as a reliability layer.

**Acceptance Scenarios**:

1. **Given** Notion returns a rate-limit response, **When** the automation makes a
   request, **Then** it waits and retries automatically without player intervention.
2. **Given** Notion fails repeatedly beyond the retry limit, **When** automation
   gives up, **Then** it logs a clear error with the failure reason and exits cleanly
   without corrupting any game data.
3. **Given** a successful retry after an initial failure, **When** automation
   completes, **Then** the log shows the retry occurred and the final outcome.

---

### User Story 5 - Pre-Populated Reference Data (Priority: P5)

After databases are created, the system seeds all reference data — exercises, budget
categories, ingredients with macros, achievement definitions, default habits, hotel
tiers, difficulty levels, mood types, skills, a default Character row (with starting
HP), and a default Settings row (with all balance defaults). The player opens Notion
and sees a ready-to-use workspace, not 33 empty tables.

**Why this priority**: Empty databases are useless. Without seed data, the player
can't interact with the system (no habits to check in, no hotels to visit, no
difficulty levels for tasks). Seeding turns empty schemas into a playable game.

**Independent Test**: Can be tested by running the seed command after database setup
and verifying that each database contains the expected reference rows. Delivers a
functional workspace the player can immediately explore.

**Acceptance Scenarios**:

1. **Given** all 33 databases have been created, **When** the seed command runs,
   **Then** each database contains its expected reference data (e.g., 25+ exercises,
   43 achievements, 3 hotel tiers, 7 skills, 1 default Character row).
2. **Given** the seed command has already been run once, **When** it is run again,
   **Then** no duplicate rows are created — existing reference data is preserved.
3. **Given** the player has manually added custom data to a database, **When** the
   seed command is re-run, **Then** the player's custom data is not deleted or
   overwritten.

---

### User Story 6 - Schema Migration Path (Priority: P6)

When the game evolves and database schemas need to change (new properties, renamed
fields, new databases), the system applies incremental migrations rather than
requiring a destructive re-creation of the entire workspace. Each migration is
versioned and tracked so the system knows which changes have already been applied.

**Why this priority**: Without a migration path, any schema change after initial
setup risks data loss or requires manual Notion editing. A migration runner future-
proofs the system from day one.

**Independent Test**: Can be tested by defining a sample migration, running it, and
verifying the schema change was applied and recorded as completed.

**Acceptance Scenarios**:

1. **Given** a new migration is defined (e.g., "add Mood Intensity property to Mood
   database"), **When** the migration runner executes, **Then** the property is added
   and the migration is recorded as applied.
2. **Given** a migration has already been applied, **When** the migration runner runs
   again, **Then** it skips that migration and reports it as already complete.
3. **Given** multiple pending migrations, **When** the runner executes, **Then** they
   are applied in order and each is individually recorded.

---

### Edge Cases

- What happens when the Settings page exists but contains an invalid value (e.g.,
  text where a number is expected)? → System uses the default for that field and
  logs a warning identifying the invalid property by name.
- What happens when the setup command is run and some databases already exist but
  others are missing? → Existing databases are preserved; only missing ones are
  created.
- What happens when the Notion API key is valid but the parent page ID is wrong or
  inaccessible? → Pre-flight check identifies this specifically, not as a generic
  connection error.
- What happens when automation logs cannot be written (e.g., permissions issue)?
  → Error is surfaced to the process output so the automation runner can capture it.
- What happens when the seed command runs but a database it needs to populate doesn't
  exist yet? → Seeding fails with a clear error naming the missing database; it does
  not attempt to create databases (that's the setup command's job).
- What happens when a migration references a database that doesn't exist? → The
  migration fails and is not marked as applied, allowing retry after the issue is
  resolved.
- What happens when the player has manually renamed a seeded row (e.g., renamed a
  habit)? → Seed deduplication is by title at creation time. Renamed rows are not
  detected as duplicates; a new seed row with the original title would be created.
  This is acceptable — player renames are the player's responsibility.
- What happens when two automation runs overlap (e.g., cron fires while a previous
  run is still active)? → The second run detects a lock file, logs a warning, and
  exits immediately without executing any operations.
- What happens when `.automation.lock` exists but contains corrupted/invalid JSON?
  → System treats as corrupted, deletes the file, logs a warning with the raw
  contents, and proceeds as if no lock existed.
- What happens when the stored database ID mapping references a database that was
  deleted in Notion? → The ID lookup fails, the system falls back to title match.
  If title match also fails, the database is re-created and the mapping is updated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow all game balance values to be set from within the
  Notion workspace, with changes taking effect on the next automation run without
  any code changes.
- **FR-002**: The system MUST use built-in default values for any balance setting
  that is absent, invalid, or unreadable from the Notion Settings page.
- **FR-003**: The system MUST log every automation action with a timestamp, severity
  level, and the source module, in a consistent and parseable format.
- **FR-004**: The system MUST automatically retry failed Notion operations using
  exponential backoff with jitter on 429 and 5xx responses (initial delay 1 second,
  maximum 3 retries) before reporting a failure. The system MUST sustain no more
  than 3 requests per second to the Notion API.
- **FR-005**: The system MUST not exceed Notion's API request rate limits during
  normal operation, including bulk database creation.
- **FR-006**: The system MUST provide a standalone readiness check that validates all
  required credentials, Notion connectivity, and game database existence.
- **FR-007**: The readiness check MUST identify each failing dependency by name and
  signal failure in a way automation pipelines can detect.
- **FR-008**: The system MUST create all 33 game databases in a single automated
  operation, including all properties, inter-database relation links, and action
  buttons.
- **FR-009**: The database creation operation MUST be safe to re-run: no duplicate
  databases, no data loss, no broken relations on subsequent executions. The system
  MUST store a mapping of database names to Notion IDs after creation and use stored
  IDs as the primary lookup on re-runs, falling back to title match if an ID lookup
  fails.
- **FR-010**: The system MUST support all 33 game databases: Character, Activity Log,
  Good Habit, Bad Habit, Skill/Area, Streak Tracker, Goal, Brain Dump, To-do
  Difficulty, Market, My Cart, Hotel, Black Market, Overdraft Penalty, Level Setting,
  Settings, Quests, Daily Journal, Mood, Onboarding Identity, Vision Board Items,
  Budget Categories, Expense Log, Treasury, Exercise Dictionary, Workout Sessions,
  Set Log, Meal Log, Ingredients Library, Loot Box Inventory, Achievements,
  Player Achievements, and Daily Snapshots.
- **FR-011**: The system MUST seed all reference data into the appropriate databases
  after creation, including exercises, budget categories, ingredients, achievements,
  default habits (good and bad), hotel tiers, difficulty levels, mood types, skills,
  a default Character row, and a default Settings row.
- **FR-012**: The seed operation MUST be idempotent: re-running it produces no
  duplicate rows. Deduplication is by title/name match.
- **FR-013**: The system MUST NOT delete or overwrite player-created data when the
  seed command is re-run.
- **FR-014**: The system MUST support incremental schema migrations, each versioned
  and tracked, so that database changes after initial setup do not require full
  re-creation.
- **FR-015**: Each migration MUST be applied at most once. The system MUST track
  which migrations have been applied and skip them on subsequent runs.
- **FR-016**: Migrations MUST be applied in defined order, and a failed migration
  MUST NOT be recorded as applied.
- **FR-017**: The system MUST prevent concurrent automation runs using a lock file.
  If a run detects an existing lock, it MUST check the lock's age. If the lock is
  older than a configurable timeout (default: 30 minutes), it MUST be treated as
  stale — the system removes it, logs a warning, and proceeds. If the lock is fresh,
  the system MUST log a warning and exit without executing.
- **FR-018**: Database creation MUST use a two-pass approach: first create all 33
  databases (without relations), then add all inter-database relations in a second
  pass, to avoid dependency ordering issues.

### Key Entities

- **Settings Configuration**: The complete set of game balance values (XP rates, HP
  costs, coin rewards, streak multipliers, hotel prices, loot box weights, AI cost
  limits) that govern all game systems. Readable from the Notion workspace;
  falls back to built-in defaults when absent or invalid.
- **Game Database**: One of 33 structured Notion tables with defined properties,
  inter-database relationships, and optionally action buttons. Together they form the
  entire data layer of the RPG system.
- **Automation Session**: A single execution run of an automation script, identified
  by start time and source module, producing a structured log of every action taken,
  every value resolved, and any errors encountered.
- **Reference Data (Seed)**: Pre-defined rows that populate databases on first setup —
  exercises, ingredients, achievements, habits, hotels, difficulty levels, mood types,
  skills, and initial Character/Settings entries. Identified by title for deduplication.
- **Schema Migration**: A versioned, ordered change to the database schemas (add/rename
  properties, add databases). Tracked in a migration ledger to ensure each migration
  applies exactly once.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A player with no coding knowledge can change any game balance value
  from within Notion and have it reflected in the next automation run — verified
  end-to-end with zero code changes required.
- **SC-002**: The pre-flight readiness check completes in under 30 seconds and
  produces a human-readable pass/fail result for every dependency, with zero
  ambiguity about what failed and why.
- **SC-003**: All 33 game databases are created in Notion in a single automated run
  with zero manual Notion setup steps — verified by inspecting the workspace
  immediately after the run.
- **SC-004**: Re-running the database setup produces identical results to the first
  run — no duplicate databases, no missing relations, no data loss — verified by
  running the command twice and comparing workspace state.
- **SC-005**: Automation recovers from Notion rate-limit responses without manual
  intervention in 100% of cases where Notion becomes available again within the
  retry window.
- **SC-006**: Every automation run produces logs sufficient for the player to
  diagnose any failure without developer assistance — verified by a player being
  able to identify and resolve a simulated failure from logs alone.
- **SC-007**: After the seed command runs, a new player can immediately interact with
  the Notion workspace — habits to check in, hotels to visit, a Character page with
  starting HP — with zero manual data entry required.
- **SC-008**: Re-running the seed command after the player has added custom data
  produces no duplicates and does not delete or modify player-created rows —
  verified by adding a custom habit, re-running seed, and confirming both the custom
  and default habits coexist.
- **SC-009**: A schema migration adds a new property to an existing database without
  affecting existing data — verified by running a sample migration and confirming
  prior rows retain all their values.

## Assumptions

- The player has a Notion account with an active integration that has read/write
  content permissions and can read user information.
- The player can supply a Notion parent page ID where all game databases will be
  created.
- GitHub Actions is the intended scheduled automation runner; local execution for
  development and testing is also supported.
- The 33 database list is fixed for V5. Schema changes after initial setup require
  a migration path, not a full re-run of the setup command.
- OpenAI integration credentials are validated by the readiness check but not
  exercised in Phase 1.
