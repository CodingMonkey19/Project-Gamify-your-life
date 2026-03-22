# Data Model: Dashboard, Onboarding & SOPs

**Date**: 2026-03-22 | **Feature**: 008-dashboard-onboarding-sops

## Entities

### Character (Notion DB — already exists from Phase 1)

Central player identity. Created during onboarding with starting values.

| Field | Type | Default (Onboarding) | Validation |
|-------|------|---------------------|------------|
| Name | Title | Player input (required) | Non-empty string |
| Class | Select | Player choice from: Warrior, Mage, Rogue, Paladin, Ranger | Must be one of 5 options |
| Level | Number | 1 | >= 1 |
| Rank | Select | "Peasant" | From RANK_THRESHOLDS |
| HP | Number | 1000 (STARTING_HP from config) | 0 to STARTING_HP |
| Coins | Number | 0 | Can be negative (overdraft) |
| Gold | Number | 0 | >= 0 |
| STR XP | Number | 0 | >= 0 |
| INT XP | Number | 0 | >= 0 |
| WIS XP | Number | 0 | >= 0 |
| VIT XP | Number | 0 | >= 0 |
| CHA XP | Number | 0 | >= 0 |
| Master Objective | Rich Text | Player input (required) | Non-empty string |
| Minor Objectives | Rich Text | Player input (optional, multi-line) | Can be empty |
| Death Penalty | Rich Text | Player input (required) | Non-empty string |
| Avatar URL | URL | Default placeholder or empty | Valid URL or empty |
| Radar Chart URL | URL | Empty (generated on first daily run) | Valid URL or empty |

**State transitions**: Created → Active (immediately usable by all engines).

### Onboarding Identity (Notion DB — already exists from Phase 1)

Captures character creation answers for AI coaching personalization.

| Field | Type | Source | Validation |
|-------|------|--------|------------|
| Character | Relation → Character DB | Linked during creation | Must reference valid Character |
| Question | Select or Text | Preset categories: "Strength", "Weakness", "Objective" | Non-empty |
| Answer | Rich Text | Player input | Non-empty string |

**Cardinality**: N rows per Character (typically 4-6: 2+ strengths, 2+ weaknesses, objectives).

### Good Habit (Notion DB — already exists from Phase 1)

Default habits created during onboarding. Player can customize after.

| Field | Type | Default Value | Stat Domain |
|-------|------|---------------|-------------|
| Name | Title | See below | — |
| Character | Relation → Character DB | Linked during creation | — |
| Domain | Select | Mapped to stat | — |

**Default good habits (5)**:

| Habit Name | Domain | Stat |
|------------|--------|------|
| Exercise | gym | STR |
| Read 30min | learning | INT |
| Track Expenses | finance | WIS |
| Eat Clean | nutrition | VIT |
| Social Interaction | social | CHA |

### Bad Habit (Notion DB — already exists from Phase 1)

Default bad habits created during onboarding.

**Default bad habits (3)**:

| Habit Name | HP Damage |
|------------|-----------|
| Junk Food | DEFAULT_BAD_HABIT_HP (-10) |
| Doom Scrolling | DEFAULT_BAD_HABIT_HP (-10) |
| Skipping Workout | DEFAULT_BAD_HABIT_HP (-10) |

### Vision Board (Notion DB — already exists from Phase 1)

8 life category rows with aspiration checklists.

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| Category | Title | One of 8 categories | Non-empty |
| Character | Relation → Character DB | Linked during creation | Must reference valid Character |
| Aspirations | Rich Text / Checklist | Empty (player fills in) | Can be empty |

**Default categories (8)**: Health, Career, Finance, Relationships, Learning, Creativity, Adventure, Spirituality

### Dashboard Page (Notion Page — NOT a database)

A Notion page with child blocks forming the dashboard layout.

| Block | Type | Content |
|-------|------|---------|
| Character Card | Callout + Image + Paragraph | Avatar, name, level, rank, HP, coins, gold, radar chart |
| Growth | Heading + Linked DB | Good Habit DB (filter: today's habits) |
| Battle | Heading + Linked DB | Bad Habit DB (all entries) |
| Quest Board | Heading + Linked DB | Quests DB (filter: Status ≠ Completed) |
| Tasks | Heading + Linked DB | Brain Dump DB (filter: incomplete) |
| Journal | Heading + Linked DB | Journal DB (filter: today) |
| Stats | Heading + Linked DB | Daily Snapshots DB (sort: date desc, limit: 7) |

**Note**: Linked DB views are created via Notion API. Filters must be set manually by the player on first view (API limitation). The SOP documents which filters to apply.

### SOP Workflow (Markdown files — NOT a database entity)

5 files in `workflows/` following WAT format.

| File | Purpose |
|------|---------|
| `setup-notion.md` | Database creation from scratch |
| `daily-routine.md` | Daily player workflow |
| `weekly-review.md` | Weekly report interpretation |
| `asset-generation.md` | Radar chart + avatar regeneration |
| `onboarding.md` | Character creation walkthrough |

## Relationships

```
Character DB (1) ←── (many) Onboarding Identity rows
Character DB (1) ←── (5) Default Good Habits
Character DB (1) ←── (3) Default Bad Habits
Character DB (1) ←── (8) Vision Board entries
Character DB (1) ←── (1) Dashboard Page (via parent_page_id)

Dashboard Page ──references──→ Good Habit DB (linked view)
Dashboard Page ──references──→ Bad Habit DB (linked view)
Dashboard Page ──references──→ Quests DB (linked view)
Dashboard Page ──references──→ Brain Dump DB (linked view)
Dashboard Page ──references──→ Journal DB (linked view)
Dashboard Page ──references──→ Daily Snapshots DB (linked view)
```

## Idempotency Keys

| Entity | Key | Check Query |
|--------|-----|-------------|
| Character | Parent Page ID | Query Character DB: any row linked to this parent page |
| Onboarding Identity | Character + Question type | Query Identity DB: rows linked to character_id |
| Good Habits | Character + Habit Name | Query Good Habit DB: rows linked to character_id |
| Bad Habits | Character + Habit Name | Query Bad Habit DB: rows linked to character_id |
| Vision Board | Character + Category | Query Vision Board DB: rows linked to character_id |
| Dashboard Page | Parent Page + Title "Daily Dashboard" | Search pages under parent with matching title |

## Environment Variables (New for Phase 8)

| Key | Description | Required |
|-----|-------------|----------|
| `CHARACTER_DB_ID` | Notion DB ID for Character DB | Yes |
| `GOOD_HABIT_DB_ID` | Notion DB ID for Good Habit DB | Yes |
| `BAD_HABIT_DB_ID` | Notion DB ID for Bad Habit DB | Yes |
| `VISION_BOARD_DB_ID` | Notion DB ID for Vision Board DB | Yes |
| `ONBOARDING_IDENTITY_DB_ID` | Notion DB ID for Identity DB | Yes |
| `JOURNAL_DB_ID` | Notion DB ID for Journal DB | Yes (for dashboard) |
| `BRAIN_DUMP_DB_ID` | Notion DB ID for Brain Dump DB | Yes (for dashboard) |
| `QUESTS_DB_ID` | Notion DB ID for Quests DB | Yes (for dashboard) |
| `DAILY_SNAPSHOTS_DB_ID` | Notion DB ID for Daily Snapshots DB | Yes (for dashboard) |
