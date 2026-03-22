# GitHub Actions Workflow Contracts

## daily.yml

```yaml
name: Daily Automation
on:
  schedule:
    - cron: '0 20 * * *'    # 10 PM Cairo (UTC+2) = 8 PM UTC
  workflow_dispatch: {}       # Manual trigger for testing

concurrency:
  group: daily-automation
  cancel-in-progress: false   # Never kill a running pipeline

env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  CHARACTER_ID: ${{ secrets.CHARACTER_ID }}
  NOTION_PARENT_PAGE_ID: ${{ secrets.NOTION_PARENT_PAGE_ID }}

jobs:
  daily:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python tools/daily_automation.py --character-id $CHARACTER_ID
```

## weekly.yml

```yaml
name: Weekly Report
on:
  schedule:
    - cron: '0 8 * * 0'     # Sunday 10 AM Cairo = 8 AM UTC
  workflow_dispatch: {}

concurrency:
  group: weekly-report
  cancel-in-progress: false

env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  CHARACTER_ID: ${{ secrets.CHARACTER_ID }}
  NOTION_PARENT_PAGE_ID: ${{ secrets.NOTION_PARENT_PAGE_ID }}

jobs:
  weekly:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python tools/daily_automation.py --character-id $CHARACTER_ID
      - run: python tools/weekly_report.py --character-id $CHARACTER_ID
```

Note: weekly.yml runs daily_automation.py FIRST (per clarification Q8) to guarantee today's snapshot exists before delta calculation.

## monthly.yml

```yaml
name: Monthly Automation
on:
  schedule:
    - cron: '0 0 1 * *'     # 1st of month midnight UTC ≈ 2 AM Cairo
  workflow_dispatch: {}

concurrency:
  group: monthly-automation
  cancel-in-progress: false

env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  CHARACTER_ID: ${{ secrets.CHARACTER_ID }}
  NOTION_PARENT_PAGE_ID: ${{ secrets.NOTION_PARENT_PAGE_ID }}

jobs:
  monthly:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python tools/monthly_automation.py --character-id $CHARACTER_ID
```

## tests.yml

```yaml
name: Tests
on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]

concurrency:
  group: tests-${{ github.ref }}
  cancel-in-progress: true    # OK to cancel stale test runs

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -v
```

## Required GitHub Repository Secrets

| Secret | Description | Used By |
|--------|-------------|---------|
| `NOTION_TOKEN` | Notion API integration token | All workflows |
| `OPENAI_API_KEY` | OpenAI API key for coaching + quests | weekly, monthly |
| `CHARACTER_ID` | Notion page ID of the player character | All workflows |
| `NOTION_PARENT_PAGE_ID` | Parent page for Notion page creation | All workflows |
