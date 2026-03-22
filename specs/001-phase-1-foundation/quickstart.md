# Quickstart: Phase 1 Foundation Setup

## Prerequisites

1. Python 3.10+ installed
2. A Notion account with a workspace
3. A Notion integration created at https://www.notion.so/my-integrations
   - Capabilities: Read content, Update content, Insert content, Read user info
4. A parent page in Notion where game databases will be created
   - The integration must be shared with this page

## Setup Steps

### 1. Clone and install dependencies

```bash
cd "Project Gamify your life"
pip install notion-client python-dotenv pytest
```

### 2. Configure environment

Create `.env` in the project root:

```env
NOTION_API_KEY=secret_your_integration_token
NOTION_PARENT_PAGE_ID=your_parent_page_id
OPENAI_API_KEY=sk-your-key-here  # validated but not used in Phase 1
```

### 3. Run smoke test

```bash
python tools/smoke_test.py
```

Expected output: JSON with pass/fail for each check. All credential checks should
pass. Database checks will fail (databases not created yet — that's expected).

### 4. Create all 33 databases

```bash
python tools/create_databases.py
```

This runs two passes:
- Pass 1: Creates 33 databases with non-relation properties
- Pass 2: Adds all inter-database relations and rollup properties

Output: JSON summary of created/skipped databases. Also writes `db_ids.json`.

### 5. Seed reference data

```bash
python tools/seed_data.py
```

Populates databases with default data (habits, exercises, achievements, hotels,
difficulty levels, skills, character, settings, etc.). ~160 rows total.

### 6. Run smoke test again

```bash
python tools/smoke_test.py
```

All checks should now pass, including database existence checks.

### 7. Run tests

```bash
pytest tests/ -v
```

## Verification

After setup, your Notion workspace should contain:

- **Character** page with starting HP (1000), all stat fields at 0
- **Good Habit** database with 4 default habits (Wake up 5am, Workout, etc.)
- **Bad Habit** database with 3 defaults (Scrolling, Smoking, Drinking)
- **Hotel** with 3 tiers (Budget/Ordinary/Premium) and working buttons
- **Settings** with all balance defaults pre-filled
- **33 total databases** with all relations linked and buttons configured

## Re-Running Safely

All commands are idempotent:
- `create_databases.py` — skips existing databases (by stored ID or title match)
- `seed_data.py` — skips existing rows (by title match)
- `migrate.py` — skips already-applied migrations

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "NOTION_API_KEY not set" | Check `.env` file exists and has the correct key |
| "Parent page not accessible" | Share the page with your Notion integration |
| Rate limit errors | Script retries automatically (3x with backoff) |
| Duplicate databases | Check `db_ids.json` — delete stale entries if needed |
| Lock file blocks run | Check if another run is active; delete `.automation.lock` if stale |
