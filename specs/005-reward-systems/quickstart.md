# Quickstart: Phase 5 — Reward Systems (Loot Box, Achievement, Rank & Radar Chart)

**Date**: 2026-03-22
**Feature**: 005-reward-systems

## Prerequisites

- Phase 1 complete (config, logger, notion_client, databases created, seed data including achievements)
- Phase 2 complete (hp_engine, coin_engine operational)
- Phase 3 complete (xp_engine, streak_engine, habit_engine operational)
- Phase 4 complete (financial_engine, fitness_engine, nutrition_engine operational)
- Achievements DB seeded with 43 badge definitions
- Rank frame PNGs in `assets/frames/` (peasant.png through mythic.png)
- Cloudinary credentials in `.env` (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
- `pip install Pillow matplotlib numpy cloudinary`

## Manual Verification Steps

### 1. Rank Engine — Threshold Mapping

1. Set a character's Total XP to 999
2. Run: `python tools/rank_engine.py --character-id <ID>`
3. Verify: rank = "Peasant" (999 < 1000 threshold)
4. Set Total XP to 1000
5. Run rank engine again
6. Verify:
   - Character DB Current Rank = "Squire"
   - Avatar updated with Squire frame
   - Avatar URL written to Character DB

### 2. Rank Engine — High-Water Mark

1. With character at Squire rank (Total XP = 1000)
2. Manually reduce Total XP to 500 (simulating XP penalty)
3. Run rank engine
4. Verify: rank remains "Squire" (no demotion)

### 3. Avatar Renderer — Profile Picture Compositing

1. Ensure character has a profile picture set
2. Run rank engine to trigger avatar generation
3. Verify:
   - Composited image shows profile picture inside rank frame
   - Image uploaded to Cloudinary
   - Avatar URL in Character DB points to new Cloudinary URL
4. Test with no profile picture → verify default placeholder used

### 4. Radar Chart — Stat Visualization

1. Set character stats: STR=5, INT=3, WIS=7, VIT=4, CHA=2
2. Run: `python tools/chart_renderer.py --character-id <ID>`
3. Verify:
   - PNG generated at assets/charts/{id}.png
   - Dimensions = 800x800
   - 5 labeled axes (STR, INT, WIS, VIT, CHA)
   - Level values at each vertex
   - Title shows player name + rank
   - Dark background with neon polygon
4. Check Cloudinary upload succeeded
5. Verify Radar Chart URL written to Character DB

### 5. Radar Chart — All-Zero Stats

1. Set all stats to 0
2. Run chart renderer
3. Verify: chart generates without error, polygon collapsed at center

### 6. Achievement Engine — Badge Unlock

1. Create a character with 1 completed workout session
2. Ensure "first_workout" achievement exists in Achievements DB
3. Run: `python tools/achievement_engine.py --character-id <ID>`
4. Verify:
   - Player Achievement row created (linked to achievement + character + today's date)
   - Activity Log entry created with XP bonus routed to achievement's Domain stat
   - xp_engine.update_character_stats() called
5. Re-run same command → verify no duplicate Player Achievement (idempotent)

### 7. Achievement Engine — Multiple Unlocks

1. Set up character meeting 3+ achievement conditions
2. Run achievement engine
3. Verify: all qualifying badges unlocked in single run, each with own Player Achievement row and Activity Log entry

### 8. Loot Box — Basic Purchase

1. Give character 200 Gold
2. Run: `python tools/loot_box.py --character-id <ID>`
3. Verify:
   - Gold deducted by 100 (LOOT_COST)
   - Rarity selected (Common/Rare/Epic/Legendary)
   - Coins awarded matching rarity tier (25/75/200/1000)
   - Loot Box Inventory row created
   - Pity Counter incremented by 1 (or reset if Legendary)

### 9. Loot Box — Insufficient Gold

1. Set character Gold to 50 (below LOOT_COST of 100)
2. Run loot box command
3. Verify: rejected with insufficient Gold message, no Gold deducted, no inventory row

### 10. Loot Box — Pity Timer

1. Set character Pity Counter to 50 (= PITY_TIMER_THRESHOLD)
2. Give character 100+ Gold
3. Run loot box command
4. Verify:
   - Rarity = Legendary (guaranteed)
   - Coins awarded = 1000
   - Pity Counter reset to 0

### 11. Loot Box — Rarity Distribution

1. Run loot box 100+ times (scripted loop)
2. Tally rarity counts
3. Verify distribution approximately matches weights:
   - Common ≈ 70% (±10% at 100 samples)
   - Rare ≈ 20%
   - Epic ≈ 8%
   - Legendary ≈ 2% (plus pity guarantees)

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Rank not updating | Total XP hasn't crossed next threshold | Check Total XP vs RANK_THRESHOLDS |
| Rank demoted | Bug — rank should be high-water mark | Verify check_rank_up() compares tier ordering, not XP |
| Avatar URL not updating | Cloudinary upload failed | Check CLOUDINARY credentials in .env, check network |
| Chart has wrong dimensions | DPI or figsize mismatch | Verify figsize=(8,8), dpi=100 → 800x800 |
| Chart shows wrong stats | Stat levels not refreshed | Run xp_engine.update_character_stats() before chart renderer |
| Achievement not unlocking | Condition checker not in dispatch map | Verify condition_key matches a key in CONDITION_CHECKERS |
| Duplicate Player Achievement | Idempotency guard failed | Check get_unlocked_achievements() filter |
| Loot box gives 0 Coins | LOOT_REWARDS missing rarity key | Verify LOOT_REWARDS has all 4 rarity tiers |
| Pity timer not resetting | Counter not written back on Legendary | Verify open_loot_box() updates Pity Counter to 0 |
| Gold not deducted | coin_engine not called | Verify open_loot_box() calls coin_engine before RNG |
