# CLI Contracts: Automation Scripts

## daily_automation.py

```
Usage: python tools/daily_automation.py --character-id <UUID>

Arguments:
  --character-id  (required)  Notion page ID of the character to process

Environment Variables (required):
  NOTION_TOKEN              Notion API integration token
  CHARACTER_ID              Fallback if --character-id not provided

Environment Variables (optional):
  OPENAI_API_KEY            Required only for weekly/monthly AI features
  NOTION_PARENT_PAGE_ID     Parent page for Notion operations

Exit Codes:
  0   Success — all pipeline steps completed (some may have logged errors)
  1   Smoke test failure — no processing attempted
  2   Fatal error — unrecoverable failure

Stdout:
  Final summary block with step results:
  ═══ Daily Automation Summary ═══
  Date: 2026-03-22
  Steps completed: 14/16
  Steps failed: 2 (logged)
  Snapshot: created
  ════════════════════════════════

Stderr (via logger.py):
  Per-step structured log lines:
  2026-03-22 22:00:01 - daily_automation - INFO - ✓ Good Habits: 5 processed
  2026-03-22 22:00:02 - daily_automation - ERROR - ✗ Streak Decay: APIResponseError
```

## weekly_report.py

```
Usage: python tools/weekly_report.py --character-id <UUID>

Arguments:
  --character-id  (required)  Notion page ID of the character

Environment Variables (required):
  NOTION_TOKEN
  CHARACTER_ID              Fallback
  OPENAI_API_KEY            Required for coaching + quest generation

Exit Codes:
  0   Success — report generated (AI sections may be skipped if cost cap hit)
  1   Smoke test failure
  2   Fatal error

Stdout:
  Weekly report summary including stat deltas, streak status,
  quest completion, coaching briefing excerpt, AI cost, overdraft status.

Behavior:
  - Calls daily_automation.py first to ensure today's snapshot exists
  - If AI cost cap reached, skips coaching + quest generation with warnings
  - If coin balance < 0, applies overdraft HP penalty before report
```

## monthly_automation.py

```
Usage: python tools/monthly_automation.py --character-id <UUID>

Arguments:
  --character-id  (required)  Notion page ID of the character

Environment Variables (required):
  NOTION_TOKEN
  CHARACTER_ID              Fallback

Exit Codes:
  0   Success — Treasury row created, AI spend reset
  1   Smoke test failure
  2   Fatal error

Stdout:
  Monthly summary: surplus amount, Gold earned, WIS XP, AI spend reset confirmation.

Idempotency:
  Checks for existing Treasury row for target month before creating.
  Second run prints "already processed" and exits 0.
```

## smoke_test.py

```
Usage: python tools/smoke_test.py [--character-id <UUID>]

Arguments:
  --character-id  (optional)  If provided, also validates character exists in DB

Exit Codes:
  0   All checks passed
  1   Required check failed (NOTION_TOKEN missing, API unreachable, etc.)

Checks (required — fail = exit 1):
  - NOTION_TOKEN env var exists and non-empty
  - CHARACTER_ID env var or --character-id provided
  - Notion API reachable (notion.users.me() succeeds)

Checks (optional — warn only):
  - OPENAI_API_KEY present
  - NOTION_PARENT_PAGE_ID present
  - Character record exists in Character DB (if --character-id provided)
```
