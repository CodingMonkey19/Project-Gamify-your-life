# Quickstart: End-to-End Verification

## Prerequisites

1. Python 3.10+ installed
2. All engine files exist in `tools/` (Phases 1-8 complete)
3. `pip install -r requirements.txt` (includes pytest)
4. For integration tests: configured `.env` with Notion API credentials

## Running Unit Tests

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run a specific engine's tests
python -m pytest tests/test_xp_engine.py -v
python -m pytest tests/test_hp_engine.py -v

# Run with short traceback (CI style)
python -m pytest tests/ -v --tb=short

# Run and stop on first failure
python -m pytest tests/ -x -v
```

**Expected output**: All tests pass, 0 failures, 0 errors, completes in <30 seconds.

## Running Loot Box Statistical Test

```bash
# Standard run (seeded for reproducibility)
python -m pytest tests/test_loot_box.py -v

# Run 3 consecutive times to rule out flakiness (SC-005)
python -m pytest tests/test_loot_box.py -v && \
python -m pytest tests/test_loot_box.py -v && \
python -m pytest tests/test_loot_box.py -v
```

## Running Integration Smoke Tests

```bash
# Step 0: Verify environment
python tools/smoke_test.py

# Then follow tests/integration/smoke_test_checklist.md step by step
# Each step has a clear action and verification checkpoint
# Use a TEST Notion workspace — not production
```

**Important**: Integration tests are manual and sequential. Do not skip steps — each builds on the previous.

## Manual User Verification

After all automated and integration tests pass:

1. Open `checklists/manual_verification.md`
2. Work through all 8 items in your live Notion workspace
3. Mark each item pass/fail with notes
4. Spend 15-30 minutes with realistic data entry

## CI Pipeline

The CI pipeline runs automatically on every push and PR:

```yaml
# .github/workflows/tests.yml triggers:
# - All pushes to any branch
# - All pull requests

# To verify CI catches failures:
# 1. Break a test intentionally (change an assertion)
# 2. Push to a branch
# 3. Verify the CI run fails
# 4. Revert the change
# 5. Verify the CI run passes
```

## Verifying Idempotency (SC-006)

```bash
# Run daily automation twice
python tools/daily_automation.py --character-id YOUR_ID
python tools/daily_automation.py --character-id YOUR_ID

# Check for duplicates: query Activity Log for today's date
# Expected: same number of entries before and after second run
```

## Verifying Test Coverage (SC-008)

```bash
# Every engine file should have a corresponding test file
# tools/xp_engine.py → tests/test_xp_engine.py
# tools/hp_engine.py → tests/test_hp_engine.py
# etc.

# Quick check:
ls tools/*_engine.py tools/loot_box.py tools/chart_renderer.py
ls tests/test_*_engine.py tests/test_loot_box.py tests/test_chart_renderer.py
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'tools'` | Run pytest from project root: `python -m pytest tests/` |
| `NOTION_TOKEN not configured` | Unit tests don't need it — check you're not running integration tests |
| Loot box test flaky | Re-run once. Two consecutive failures = real bug |
| CI fails but local passes | Check Python version (3.10+) and requirements.txt is up to date |
| `ImportError` for an engine | Engine file may not exist yet — complete Phases 1-8 first |
