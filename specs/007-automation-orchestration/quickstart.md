# Quickstart: Automation Orchestration

## Prerequisites

1. Python 3.10+ installed
2. Notion integration token with access to all game databases
3. Character record created in Character DB (need the page ID)
4. Phases 1-6 engines operational in `tools/`

## Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your values:
#   NOTION_TOKEN=secret_xxx
#   CHARACTER_ID=your-character-page-id
#   OPENAI_API_KEY=sk-xxx  (optional for daily, required for weekly)
#   NOTION_PARENT_PAGE_ID=your-parent-page-id

# 3. Verify environment
python tools/smoke_test.py --character-id YOUR_CHARACTER_ID
```

## Running Locally

```bash
# Daily automation (the main pipeline)
python tools/daily_automation.py --character-id YOUR_CHARACTER_ID

# Weekly report (runs daily first, then report)
python tools/weekly_report.py --character-id YOUR_CHARACTER_ID

# Monthly automation (Gold settlement + AI spend reset)
python tools/monthly_automation.py --character-id YOUR_CHARACTER_ID
```

## GitHub Actions Setup

1. Push workflow YAML files to `.github/workflows/`
2. Go to repo Settings → Secrets and variables → Actions
3. Add repository secrets:
   - `NOTION_TOKEN`
   - `OPENAI_API_KEY`
   - `CHARACTER_ID`
   - `NOTION_PARENT_PAGE_ID`
4. Verify: Go to Actions tab → select "Daily Automation" → "Run workflow" (manual trigger)

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_daily_automation.py -v

# Run with coverage
python -m pytest tests/ --cov=tools --cov-report=term-missing
```

## Verifying Idempotency

```bash
# Run daily twice — second run should no-op
python tools/daily_automation.py --character-id YOUR_CHARACTER_ID
python tools/daily_automation.py --character-id YOUR_CHARACTER_ID
# Expected: second run logs "already processed" per engine, no duplicates
```
