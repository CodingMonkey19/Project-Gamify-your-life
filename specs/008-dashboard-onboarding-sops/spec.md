# Feature Specification: Dashboard, Onboarding & SOPs

**Feature Branch**: `008-dashboard-onboarding-sops`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Phase 8 of V5 Implementation Plan — Daily Dashboard Page Setup, Character Onboarding Flow, Workflow Documentation (SOPs)

## Clarifications

### Session 2026-03-22

- Q: Should the dashboard be created programmatically or manually via SOP? → A: Python script creates dashboard via Notion API — programmatic, reproducible, testable.
- Q: How does the onboarding script discover database IDs (Character DB, Habit DBs, etc.)? → A: Store DB IDs in `.env` or Settings DB — script reads them like other automation scripts.
- Q: What are the available character classes? → A: Warrior, Mage, Rogue, Paladin, Ranger — classic RPG archetypes. Class is flavor text only in V5 (no gameplay effects).
- Q: What are the exact default good/bad habits created during onboarding? → A: Stat-balanced defaults. Good: Exercise (STR), Read 30min (INT), Track Expenses (WIS), Eat Clean (VIT), Social Interaction (CHA). Bad: Junk Food, Doom Scrolling, Skipping Workout.
- Q: Should dashboard setup run automatically after onboarding? → A: Yes — onboarding auto-creates the dashboard at the end, giving the player a single "zero to playing" command.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Character Onboarding Flow (Priority: P1)

A new player launches the system for the first time. They run an onboarding script that walks them through creating their RPG character: choosing a name, selecting a class, defining their master objective (long-term life goal), setting minor objectives, choosing a death penalty flavor text, and answering identity questions about their strengths and weaknesses. The script creates the Character row in the Character DB with all starting stats (Level 1, 1000 HP, 0 Coins, 0 Gold, Peasant rank), creates linked Onboarding Identity rows capturing their answers, sets up a default set of good and bad habits linked to the character, and creates 8 default Vision Board categories (Health, Career, Finance, Relationships, Learning, Creativity, Adventure, Spirituality). After all records are created, the onboarding script automatically creates the Daily Dashboard page via Notion API, giving the player a complete "zero to playing" experience in a single command.

**Why this priority**: Nothing in the system works without a character. The onboarding flow is the entry point for the entire game — daily automation, weekly reports, monthly settlement, dashboard display all depend on a Character DB record existing. This is the first thing any new player must do. Without onboarding, every other feature requires manual Notion row creation.

**Independent Test**: Run `python tools/onboarding.py --parent-page-id <ID>`. Follow the interactive prompts: enter a character name, select a class, type a master objective, add 2-3 minor objectives, choose a death penalty text, answer strength/weakness questions. Verify: Character row created in Character DB with correct starting stats, Onboarding Identity rows created with answers, default good/bad habits created and linked to character, 8 Vision Board categories created. Then run `python tools/daily_automation.py --character-id <new_ID>` to confirm the character integrates with existing automation.

**Acceptance Scenarios**:

1. **Given** no character exists for this player, **When** the onboarding script runs, **Then** the player is prompted for name, class, master objective, minor objectives, death penalty, strengths, and weaknesses, and a Character row is created with Level 1, HP 1000, Coins 0, Gold 0, Rank "Peasant", all stat XPs at 0
2. **Given** the onboarding script has created a character, **When** setup_default_habits is called, **Then** 5 good habits are created: Exercise (STR), Read 30min (INT), Track Expenses (WIS), Eat Clean (VIT), Social Interaction (CHA); and 3 bad habits: Junk Food, Doom Scrolling, Skipping Workout — all linked to the new character in Good Habit DB and Bad Habit DB
3. **Given** the onboarding script has created a character, **When** setup_vision_board is called, **Then** 8 Vision Board rows are created with categories: Health, Career, Finance, Relationships, Learning, Creativity, Adventure, Spirituality — each linked to the character with empty aspiration checklists ready for the player to fill
4. **Given** the player provides invalid input (empty name, empty master objective), **When** the onboarding script validates input, **Then** the script re-prompts with a clear error message and does not create any partial records
5. **Given** a character already exists for this player (re-run scenario), **When** the onboarding script runs, **Then** it warns the player that a character already exists and asks for confirmation before proceeding (prevent accidental data duplication)

---

### User Story 2 — Daily Dashboard Page Setup (Priority: P1)

The player opens Notion and sees a Daily Dashboard page that serves as their central command center. The dashboard displays their character card at the top (avatar image, name, level, rank, HP bar, coin/gold balance, radar chart embed), followed by organized panels: a Growth panel showing today's good habits with check-in buttons, a Battle panel showing bad habits with "Crap I did..." buttons, a Quest Board showing active quests (not completed), a Tasks panel showing incomplete Brain Dump items, a Journal panel for today's entry with mood selector, and a Stats panel showing the last 7 days of Daily Snapshots. The dashboard is a Notion page with linked database views — each panel is a filtered/sorted view of the relevant database.

**Why this priority**: The dashboard is the player's daily interface. Without it, the player must navigate between 20+ separate Notion databases to interact with the system. The dashboard aggregates everything into a single page, making the game playable and enjoyable. Co-P1 with onboarding because the dashboard is useless without a character, and a character without a dashboard has no user-friendly interaction point.

**Independent Test**: After onboarding completes (which auto-creates the dashboard), open the resulting Notion page. Alternatively, run `python tools/dashboard_setup.py --character-id <ID>` independently. Verify: character card displays correct stats, Growth panel shows today's habits with check-in buttons working, Battle panel shows bad habits, Quest Board shows only active quests, Tasks panel shows incomplete items, Journal panel allows entry, Stats panel shows recent snapshots. Click a check-in button — verify Activity Log entry created.

**Acceptance Scenarios**:

1. **Given** a character exists and the dashboard page is created, **When** the player opens the dashboard, **Then** they see their character card with current avatar, name, level, rank, HP (as a visual indicator), coin balance, gold balance, and embedded radar chart
2. **Given** today's good habits exist, **When** the player views the Growth panel, **Then** they see only today's unchecked habits with Notion check-in buttons, and checking in creates an Activity Log entry
3. **Given** active quests exist in Quests DB, **When** the player views the Quest Board, **Then** only quests with Status ≠ "Completed" are displayed, sorted by deadline
4. **Given** the player has Daily Snapshots for the past 7 days, **When** they view the Stats panel, **Then** they see a table/gallery of the most recent 7 snapshots showing stat progression
5. **Given** the player opens the Journal panel, **When** they write an entry and select a mood, **Then** the journal entry is saved and the mood is recorded for today's snapshot

---

### User Story 3 — Workflow Documentation (SOPs) (Priority: P2)

The system includes a complete set of Standard Operating Procedures (SOPs) as markdown workflow files that document every operational aspect of the game: how to set up Notion databases from scratch, the daily routine workflow (what the player does each day and what automation handles), the weekly review process, how to regenerate assets (radar charts, avatars), and the onboarding process. Each SOP is written for a human operator (the player or a future Claude agent) and includes the objective, required inputs, step-by-step instructions, expected outputs, and troubleshooting guidance for common issues.

**Why this priority**: SOPs are documentation — they don't add functionality but make the system maintainable and transferable. The game works without them, but if the player forgets a step, encounters an error, or wants to set up the system on a new Notion workspace, they'd have no reference. P2 because the system is fully functional after P1 stories; SOPs add resilience and reduce the player's cognitive load.

**Independent Test**: Open each SOP file. Follow the steps described for one workflow (e.g., daily routine). Verify that each step is accurate, references the correct script/tool names, and produces the described output. Check that troubleshooting sections address the most common failure modes (API errors, missing env vars, Notion permission issues).

**Acceptance Scenarios**:

1. **Given** a new Notion workspace with no databases, **When** the player follows `workflows/setup-notion.md`, **Then** they can recreate the full database schema from scratch using the documented steps
2. **Given** the system is fully set up, **When** the player follows `workflows/daily-routine.md`, **Then** they know exactly which Notion buttons to click, what data to enter, and what the automation handles automatically
3. **Given** the weekly report has run, **When** the player follows `workflows/weekly-review.md`, **Then** they know how to interpret the report, act on coaching suggestions, and review quest progress
4. **Given** the player needs to regenerate a corrupted radar chart or avatar, **When** they follow `workflows/asset-generation.md`, **Then** they can trigger regeneration and verify the new assets display correctly
5. **Given** a new player is setting up for the first time, **When** they follow `workflows/onboarding.md`, **Then** they are guided through the complete character creation process with clear explanations of each choice

---

### Edge Cases

- What happens when onboarding is interrupted mid-flow (script crash after character created but before habits/vision board)? The script should detect partial state on re-run: if Character exists but habits don't, resume from where it left off rather than failing or duplicating.
- What happens when the dashboard page already exists and the setup script runs again? The script should detect the existing page and update it rather than creating a duplicate dashboard.
- What happens when a linked database view on the dashboard references a DB that doesn't exist yet? The dashboard SOP should specify the prerequisite: all databases must be created (Phase 1 create_databases.py) before dashboard setup.
- What happens when the player wants to customize default habits after onboarding? Default habits are regular Notion rows — the player can edit, delete, or add habits directly in Notion. No script needed for customization. Dashboard is a static Notion page created once; if player modifies habits, they must manually update dashboard views. The setup script can be re-run to reset the dashboard to default state.
- What happens when an SOP references a tool that has been renamed or removed? Each SOP should include a "Last verified" date and a version reference to the Phase it was written for. SOPs are living documents updated per the WAT self-improvement loop.
- What happens when the player changes their character name or class after onboarding? Character properties are editable in Notion directly. The name/class are display values — no engine logic depends on them, so changes are safe.
- What happens when setup_vision_board is called but Vision Board DB doesn't exist? The script should check DB existence first (similar to smoke test pattern) and provide a clear error: "Run create_databases.py first."

## Requirements *(mandatory)*

### Functional Requirements

**Character Onboarding**

- **FR-001**: System MUST prompt the player for character name, class, master objective, minor objectives, death penalty flavor text, and identity questions (strengths/weaknesses) via interactive CLI
- **FR-002**: System MUST create a Character row in Character DB with starting values: Level 1, HP 1000 (STARTING_HP from config), Coins 0, Gold 0, Rank "Peasant", all 5 stat XPs at 0
- **FR-003**: System MUST create Onboarding Identity rows linked to the character recording the player's answers to strengths (at least 1, up to 10), weaknesses (at least 1, up to 10), and objectives
- **FR-004**: System MUST call `setup_default_habits(character_id)` to create starter good habits and bad habits linked to the new character
- **FR-005**: System MUST call `setup_vision_board(character_id)` to create 8 Vision Board category rows (Health, Career, Finance, Relationships, Learning, Creativity, Adventure, Spirituality) linked to the character
- **FR-006**: System MUST validate all required inputs (name, master objective) are non-empty before creating any records
- **FR-007**: System MUST detect existing character for the same parent page and warn before proceeding (idempotency awareness)
- **FR-008**: System MUST handle partial onboarding state (character exists, habits don't) by resuming from the incomplete step
- **FR-008a**: System MUST present 5 character class options during onboarding: Warrior, Mage, Rogue, Paladin, Ranger. Each class provides a +10% XP bonus to its mapped stat (Warrior→STR, Mage→INT, Rogue→CHA, Paladin→VIT, Ranger→WIS) as defined in Phase 3 FR-008
- **FR-008b**: System MUST create the exact default habits: Good = Exercise (STR), Read 30min (INT), Track Expenses (WIS), Eat Clean (VIT), Social Interaction (CHA). Bad = Junk Food, Doom Scrolling, Skipping Workout. Domain mapping rationale: Exercise→STR (physical), Read→INT (mental), Finance→WIS (decision-making), Nutrition→VIT (health), Social→CHA (interpersonal). Player can change domains in Notion after onboarding
- **FR-008c**: System MUST read all required Notion database IDs from `.env` or Settings DB — not search by title or accept as CLI arguments. DB ID keys follow the existing automation pattern (e.g., `CHARACTER_DB_ID`, `GOOD_HABIT_DB_ID`, etc.)
- **FR-008d**: System MUST automatically create the Daily Dashboard page at the end of the onboarding flow, so the player runs a single command to go from zero to fully playable

**Daily Dashboard**

- **FR-009**: System MUST programmatically create a Notion dashboard page via the Notion API with linked database views for: Character Card, Growth panel (Good Habits), Battle panel (Bad Habits), Quest Board, Tasks panel (Brain Dump), Journal panel, Stats panel (Daily Snapshots)
- **FR-010**: Growth panel MUST embed a linked database view of Good Habit DB. A text block above the view MUST instruct the player to apply a "Date = Today" filter (Notion API cannot set view filters programmatically)
- **FR-011**: Battle panel MUST embed a linked database view of Bad Habit DB. A text block above the view MUST instruct the player to make "Crap I did..." action buttons visible
- **FR-012**: Quest Board MUST embed a linked database view of Quests DB. A text block above the view MUST instruct the player to filter Status ≠ "Completed" and sort by Deadline ascending
- **FR-013**: Tasks panel MUST embed a linked database view of Brain Dump DB. A text block above the view MUST instruct the player to filter to incomplete tasks
- **FR-014**: Stats panel MUST embed a linked database view of Daily Snapshots DB. A text block above the view MUST instruct the player to sort by Date descending and limit to 7 rows
- **FR-015**: Character Card MUST display: avatar image, character name, level, rank, HP as text (e.g., "800/1000 HP" — Notion does not support native progress bars), coin balance, gold balance, and embedded radar chart image

**Workflow Documentation (SOPs)**

- **FR-016**: System MUST provide `workflows/setup-notion.md` documenting complete database creation and configuration from a blank Notion workspace
- **FR-017**: System MUST provide `workflows/daily-routine.md` documenting what the player does each day (habit check-ins, meal logging, expense entry, journal) and what automation handles
- **FR-018**: System MUST provide `workflows/weekly-review.md` documenting how to interpret the weekly report, review coaching, and manage quests
- **FR-019**: System MUST provide `workflows/asset-generation.md` documenting how to regenerate radar charts and avatar frames manually
- **FR-020**: System MUST provide `workflows/onboarding.md` documenting the full character creation process with explanations of each field
- **FR-021**: Each SOP MUST follow the WAT workflow format: objective, required inputs, step-by-step instructions, expected outputs, troubleshooting section
- **FR-022**: Each SOP MUST reference correct tool/script names as they exist in `tools/` at the time of writing

### Key Entities

- **Character**: The player's RPG identity — name, class, level, rank, HP, coins, gold, 5 stat XPs, master objective, death penalty text. Central entity that all other systems reference. Created during onboarding.
- **Onboarding Identity**: Captures the player's character creation answers — strengths, weaknesses, objectives. Linked to Character. Used by AI coaching engine for personalized briefings.
- **Vision Board**: 8 life category rows (Health, Career, Finance, etc.) with aspiration checklists. Linked to Character. Player fills in goals and checks off achievements over time.
- **Dashboard Page**: A Notion page (not a database) containing linked database views. Serves as the player's daily interaction surface. References Character, Good/Bad Habits, Quests, Brain Dump, Journal, Daily Snapshots.
- **SOP Workflow**: A markdown file in `workflows/` documenting an operational procedure. Not a database entity — a documentation artifact that evolves with the system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new player can go from zero to a fully initialized character with habits, vision board, and dashboard in under 10 minutes by following the onboarding flow
- **SC-002**: The onboarding script creates all required records (1 Character, N Identity rows, 5+ good habits, 3+ bad habits, 8 vision board entries) in a single run without manual Notion editing
- **SC-003**: The daily dashboard displays all 7 panels (Character Card, Growth, Battle, Quest Board, Tasks, Journal, Stats) on a single Notion page with correct filters and sorts
- **SC-004**: A player can complete their entire daily routine (check-in habits, log meals/expenses, write journal, select mood) without leaving the dashboard page
- **SC-005**: Running onboarding twice on the same workspace detects the existing character and warns the player — no duplicate characters or habits created
- **SC-006**: Each SOP is self-contained: a player unfamiliar with the system can follow any SOP end-to-end without external reference and achieve the documented outcome
- **SC-007**: All 5 SOP files are complete, reference correct tool names, and include troubleshooting for at least 3 common failure modes each
- **SC-008**: The dashboard's Stats panel accurately reflects the most recent 7 days of snapshots, updating automatically as new daily automation runs add snapshots
- **SC-009**: Partial onboarding recovery works — if the script is interrupted after character creation, re-running it resumes from the missing step (habits or vision board) without duplicating the character

## Assumptions

- Phases 1-7 are complete: all databases exist, all engines are operational, daily/weekly/monthly automation runs successfully, GitHub Actions workflows are configured
- The 33 Notion databases are created via `create_databases.py` from Phase 1 before dashboard setup begins
- Good Habit DB and Bad Habit DB support linked relations to Character DB (schema from Phase 1)
- Vision Board DB exists with schema from Phase 1 (Category, Character relation, Aspirations checklist)
- Onboarding Identity DB exists with schema from Phase 1 (Character relation, Question, Answer fields)
- Journal DB exists with schema supporting Date, Entry text, Mood select, and Character relation
- Brain Dump DB exists with schema supporting Task, Status (incomplete/complete), and Character relation
- The player interacts with the onboarding script via CLI (terminal/command prompt) — not a web UI
- Notion pages support linked database views with filters and sorts (standard Notion feature)
- The radar chart image is hosted on Cloudinary (from Phase 4) and embeddable in Notion via image block
- The avatar image is hosted on Cloudinary (from Phase 5) and embeddable in Notion via image block
- CHARACTER_ID is a single-player system — onboarding creates one character per workspace

## Scope Boundaries

**In scope**: Character onboarding script (interactive CLI with auto-dashboard creation), default habit creation (stat-balanced set), vision board creation, identity question capture, daily dashboard page setup (programmatic via Notion API), 5 workflow SOP documents, partial onboarding recovery, duplicate detection

**Out of scope**: Multi-player onboarding (one character per workspace), web-based onboarding UI, dashboard theme customization, SOP auto-generation from code, automated SOP verification/testing, notification system for SOP updates, character deletion/reset flow, dashboard mobile optimization (Notion handles responsive layout natively), character class gameplay effects (class is flavor text only in V5)
