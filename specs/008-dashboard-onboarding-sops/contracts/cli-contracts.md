# CLI Contracts: Onboarding & Dashboard

## onboarding.py

```
Usage: python tools/onboarding.py --parent-page-id <NOTION_PAGE_ID>

Arguments:
  --parent-page-id  (required)  Notion page ID under which the character and dashboard will be created

Environment Variables (required):
  NOTION_TOKEN                Notion API integration token
  CHARACTER_DB_ID             Notion DB ID for Character DB
  GOOD_HABIT_DB_ID            Notion DB ID for Good Habit DB
  BAD_HABIT_DB_ID             Notion DB ID for Bad Habit DB
  VISION_BOARD_DB_ID          Notion DB ID for Vision Board DB
  ONBOARDING_IDENTITY_DB_ID   Notion DB ID for Onboarding Identity DB
  JOURNAL_DB_ID               Notion DB ID for Journal DB (for dashboard)
  BRAIN_DUMP_DB_ID            Notion DB ID for Brain Dump DB (for dashboard)
  QUESTS_DB_ID                Notion DB ID for Quests DB (for dashboard)
  DAILY_SNAPSHOTS_DB_ID       Notion DB ID for Daily Snapshots DB (for dashboard)

Interactive Prompts (in order):
  1. Character Name        (required, non-empty)
  2. Character Class       (choice: Warrior, Mage, Rogue, Paladin, Ranger)
  3. Master Objective      (required, non-empty, free text)
  4. Minor Objectives      (optional, multi-line, blank line to finish)
  5. Death Penalty Text    (required, non-empty, free text)
  6. Strengths             (required, at least 1, multi-line, blank line to finish)
  7. Weaknesses            (required, at least 1, multi-line, blank line to finish)

Execution Flow:
  1. Validate env vars (smoke test pattern)
  2. Check for existing character → warn + confirm if found
  3. Collect interactive inputs with validation
  4. Create Character row in Character DB
  5. Create Onboarding Identity rows (strengths, weaknesses, objectives)
  6. Create 5 default good habits + 3 default bad habits
  7. Create 8 Vision Board category entries
  8. Auto-create Daily Dashboard page (calls dashboard_setup internally)
  9. Print summary with character ID and dashboard URL

Exit Codes:
  0   Success — character + habits + vision board + dashboard all created
  1   Environment validation failure (missing env vars, API unreachable)
  2   User cancelled (existing character warning declined)

Stdout:
  ═══ Character Created ═══
  Name: [name]
  Class: [class]
  Character ID: [notion_page_id]
  Dashboard: [notion_page_url]

  Records created:
    ✓ Character row (Level 1, HP 1000, Peasant)
    ✓ Identity rows (N entries)
    ✓ Good habits (5)
    ✓ Bad habits (3)
    ✓ Vision Board (8 categories)
    ✓ Dashboard (7 panels)
  ════════════════════════
```

## dashboard_setup.py

```
Usage: python tools/dashboard_setup.py --character-id <NOTION_PAGE_ID> --parent-page-id <NOTION_PAGE_ID>

Arguments:
  --character-id    (required)  Notion page ID of the character
  --parent-page-id  (required)  Notion page ID under which to create the dashboard

Environment Variables (required):
  NOTION_TOKEN
  GOOD_HABIT_DB_ID
  BAD_HABIT_DB_ID
  QUESTS_DB_ID
  BRAIN_DUMP_DB_ID
  JOURNAL_DB_ID
  DAILY_SNAPSHOTS_DB_ID

Execution Flow:
  1. Validate env vars
  2. Read character data (name, level, rank, HP, coins, gold, avatar URL, chart URL)
  3. Check for existing dashboard page → update if found, create if not
  4. Build page with 7 panel blocks:
     - Character Card (callout + images + stats text)
     - Growth (heading + linked Good Habit DB)
     - Battle (heading + linked Bad Habit DB)
     - Quest Board (heading + linked Quests DB)
     - Tasks (heading + linked Brain Dump DB)
     - Journal (heading + linked Journal DB)
     - Stats (heading + linked Daily Snapshots DB)
  5. Print dashboard URL

Exit Codes:
  0   Success — dashboard page created/updated
  1   Environment validation failure
  2   Character not found

Stdout:
  Dashboard created: [notion_page_url]
  Panels: Character Card, Growth, Battle, Quest Board, Tasks, Journal, Stats
  Note: Apply filters manually for optimal view (see workflows/onboarding.md)

Idempotency:
  Checks for existing "Daily Dashboard" page under parent.
  If found, updates blocks. If not, creates new page.
```
