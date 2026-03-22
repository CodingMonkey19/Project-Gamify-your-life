# Quickstart: Dashboard, Onboarding & SOPs

## Prerequisites

1. Python 3.10+ installed
2. Notion integration token with access to all game databases
3. All 33 Notion databases created (Phase 1 `create_databases.py`)
4. Phases 1-7 engines operational in `tools/`
5. `.env` file configured with all DB IDs

## Environment Setup

```bash
# 1. Install dependencies (if not already done)
pip install -r requirements.txt

# 2. Add new DB ID env vars to .env (append to existing):
#   CHARACTER_DB_ID=<your-character-db-id>
#   GOOD_HABIT_DB_ID=<your-good-habit-db-id>
#   BAD_HABIT_DB_ID=<your-bad-habit-db-id>
#   VISION_BOARD_DB_ID=<your-vision-board-db-id>
#   ONBOARDING_IDENTITY_DB_ID=<your-identity-db-id>
#   JOURNAL_DB_ID=<your-journal-db-id>
#   BRAIN_DUMP_DB_ID=<your-brain-dump-db-id>
#   QUESTS_DB_ID=<your-quests-db-id>
#   DAILY_SNAPSHOTS_DB_ID=<your-daily-snapshots-db-id>

# 3. Find DB IDs: Open each Notion DB → Share → Copy link
#    URL format: notion.so/<workspace>/<DB_ID>?v=...
#    The DB_ID is the 32-char hex string before the ?v= parameter
```

## Running Onboarding (First Time)

```bash
# Single command: creates character + habits + vision board + dashboard
python tools/onboarding.py --parent-page-id YOUR_PARENT_PAGE_ID

# Follow the interactive prompts:
#   1. Enter character name
#   2. Choose class (1-5: Warrior, Mage, Rogue, Paladin, Ranger)
#   3. Type master objective
#   4. Add minor objectives (blank line to finish)
#   5. Write death penalty flavor text
#   6. List strengths (blank line to finish)
#   7. List weaknesses (blank line to finish)

# Output: Character ID + Dashboard URL
# Total time: ~5-10 minutes including input
```

## Running Dashboard Setup (Standalone)

```bash
# If you need to recreate/update the dashboard separately:
python tools/dashboard_setup.py \
  --character-id YOUR_CHARACTER_ID \
  --parent-page-id YOUR_PARENT_PAGE_ID
```

## Post-Onboarding: Apply Dashboard Filters

After onboarding creates the dashboard, open it in Notion and apply these filters:

1. **Growth panel**: Filter → Date = Today
2. **Quest Board**: Filter → Status ≠ Completed, Sort → Deadline ascending
3. **Tasks panel**: Filter → Status = Incomplete
4. **Journal panel**: Filter → Date = Today
5. **Stats panel**: Sort → Date descending, Limit → 7 rows

(These filters persist in Notion once set — you only do this once.)

## Verifying Onboarding

```bash
# Check character integrates with daily automation
python tools/daily_automation.py --character-id YOUR_NEW_CHARACTER_ID

# Run onboarding again — should detect existing character and warn
python tools/onboarding.py --parent-page-id YOUR_PARENT_PAGE_ID
# Expected: "Character already exists" warning, no duplicates
```

## Testing

```bash
# Run onboarding + dashboard tests
python -m pytest tests/test_onboarding.py tests/test_dashboard_setup.py -v

# Run full test suite
python -m pytest tests/ -v
```

## SOP Files

After implementation, verify SOPs exist and are accurate:

```bash
ls workflows/
# Expected: setup-notion.md, daily-routine.md, weekly-review.md,
#           asset-generation.md, onboarding.md
```

Open each SOP and follow one workflow end-to-end to verify accuracy.
