# Quickstart: Phase 2 — HP System, Death & Economy

## Prerequisites

- Phase 1 complete: all 33 databases exist, `db_ids.json` populated, seed data loaded
- `.env` configured with `NOTION_API_KEY` and `NOTION_PARENT_PAGE_ID`
- `tools/smoke_test.py` passes all checks
- Default Character row exists with Starting HP = 1000

## What Phase 2 Adds

Two new tools:

| Tool | Purpose |
|------|---------|
| `tools/hp_engine.py` | HP tracking, damage from bad habits, death detection, respawn |
| `tools/coin_engine.py` | Coin balance, Market/Hotel/Black Market purchases, overdraft penalties |

## Testing

```bash
# Run Phase 2 tests
pytest tests/test_hp_engine.py tests/test_coin_engine.py -v

# Run all tests (including Phase 1)
pytest tests/ -v
```

## Manual Verification

### Test HP Damage

1. Open **Bad Habit** database in Notion
2. Click "Crap, I did..." on any bad habit (creates Activity Log entry)
3. Run: `python -c "from tools.hp_engine import get_current_hp; print(get_current_hp('CHARACTER_ID'))"`
4. Verify HP decreased by the habit's damage value

### Test Death

1. Log enough bad habits to push HP to 0 or below
2. Check Character page — "HP Progress" formula should show "You Died!"
3. Death Count should have incremented

### Test Respawn

1. Check the **Respawn** checkbox on Character page
2. Run: `python -c "from tools.hp_engine import respawn; print(respawn('CHARACTER_ID'))"`
3. Verify HP reset to 1000, Respawn checkbox cleared

### Test Coin Economy

1. Complete a Goal in Notion (click COMPLETE button)
2. Run: `python -c "from tools.coin_engine import get_coin_balance; print(get_coin_balance('CHARACTER_ID'))"`
3. Verify coins increased by the Goal's award amount

### Test Market Purchase

1. Click "Buy" on a Market item
2. Verify coin balance decreased by item price
3. Verify item marked as purchased with redemption date

### Test Hotel Recovery

1. Click "HOTEL CHECK-IN" on any hotel tier
2. Verify coins decreased by hotel price AND HP increased by recovery amount

### Test Overdraft

1. Spend enough coins to go negative
2. Wait for weekly automation (or run manually)
3. Verify HP penalty applied and logged in Activity Log

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Character is dead" when trying to buy | Respawn first (check Respawn checkbox, run respawn) |
| HP not updating on Character page | Run `hp_engine.update_character_hp()` to sync |
| Overdraft penalty not applying | Check Settings DB — overdraft frequency may be "Disabled" |
| Death not detected after bad habit | Ensure `apply_damage()` is called (not just the button) |
| Coins not reflecting Goal completion | Buttons write directly to Activity Log — run `get_coin_balance()` to verify |
