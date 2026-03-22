# Quickstart: Phase 6 — OpenAI Cognitive Coach & Quest Engine

**Date**: 2026-03-22
**Feature**: 006-ai-coach-quests

## Prerequisites

- Phase 1 complete (config, logger, notion_client, databases created, Quests DB with schema)
- Phase 2 complete (hp_engine, coin_engine operational)
- Phase 3 complete (xp_engine, streak_engine, habit_engine operational)
- Phase 4 complete (financial_engine, fitness_engine, nutrition_engine operational)
- Phase 5 complete (achievement_engine, rank_engine, loot_box operational)
- Quests DB exists with schema: Quest Title, Narrative, Domain, Difficulty, Status, Base XP, Applied Multiplier, Effective XP, Gold Reward, Source, Due Date, Character
- Streak Tracker DB populated with at least one streak entry
- OpenAI API key in `.env` (`OPENAI_API_KEY`)
- Settings DB has: AI_MONTHLY_SPEND=0, OPENAI_MONTHLY_COST_CAP_USD=1.00, OPENAI_MAX_TOKENS=1500, OPENAI_MODEL=gpt-4o-mini
- `pip install openai` (new dependency for Phase 6)

## Manual Verification Steps

### 1. Quest Engine — Basic Completion (No Streak)

1. Create a quest manually in Quests DB:
   - Quest Title: "Test Quest Alpha"
   - Domain: STR
   - Difficulty: Medium
   - Base XP: 50
   - Gold Reward: 10
   - Status: Completed
   - Source: Manual
   - Character: (link to your character)
   - Leave Applied Multiplier and Effective XP empty
2. Ensure no STR-domain streaks exist in Streak Tracker (or all are at 0 days)
3. Run: `python tools/quest_engine.py --character-id <ID>`
4. Verify:
   - Quest row: Applied Multiplier = 1.0, Effective XP = 50
   - Activity Log: new entry with Type=QUEST, EXP + (Quest) = 50, Domain = STR
   - Character DB: STR XP increased by 50 (after stat refresh)
   - Gold balance: increased by 10

### 2. Quest Engine — Streak Multiplier Applied

1. Ensure a STR-domain habit has a Gold-tier streak (14+ days) in Streak Tracker (Multiplier = 1.5)
2. Create a quest: Domain=STR, Difficulty=Hard, Base XP=100, Gold Reward=25, Status=Completed
3. Run: `python tools/quest_engine.py --character-id <ID>`
4. Verify:
   - Applied Multiplier = 1.5
   - Effective XP = floor(100 × 1.5) = 150
   - Activity Log: EXP + (Quest) = 150, Domain = STR
   - Gold: +25

### 3. Quest Engine — Idempotency

1. Run the quest engine again on the same character
2. Verify:
   - No new Activity Log entries created
   - No duplicate Gold credits
   - Quest rows from steps 1-2 are unchanged (Effective XP already populated → skipped)

### 4. Quest Engine — Domain Default to Weakest Stat

1. Create a quest with **no Domain** set, Base XP=25, Gold Reward=5, Status=Completed
2. Run: `python tools/quest_engine.py --character-id <ID>`
3. Verify:
   - Quest row Domain was filled with the character's weakest stat (lowest XP)
   - Activity Log entry routes XP to that stat
   - Effective XP calculated with that stat's streak multiplier

### 5. Quest Engine — Skip Non-Completed

1. Create two quests: one with Status="Available", one with Status="Failed"
2. Run: `python tools/quest_engine.py --character-id <ID>`
3. Verify: Neither quest was processed (no Activity Log entries, no Effective XP written)

### 6. AI Quest Generation — Happy Path

1. Ensure OPENAI_API_KEY is set in `.env`
2. Ensure AI_MONTHLY_SPEND = 0 in Settings DB
3. Run: `python tools/quest_generator.py --character-id <ID>`
4. Verify:
   - 3 new quests created in Quests DB
   - Each has: title, narrative, domain (valid), difficulty (valid), base_xp, gold_reward
   - Each has: Status=Available, Source=AI-Generated, Due Date = today + 7 days
   - At least 1 quest targets the character's weakest stat
   - AI_MONTHLY_SPEND in Settings DB is now > 0 (tiny amount, e.g., $0.0006)

### 7. AI Quest Generation — Cost Cap Enforcement

1. Set AI_MONTHLY_SPEND in Settings DB to a value just below OPENAI_MONTHLY_COST_CAP_USD (e.g., $0.9999)
2. Run: `python tools/quest_generator.py --character-id <ID>`
3. Verify:
   - No API call made
   - Warning logged: "Monthly AI cost cap reached"
   - No quests created
   - AI_MONTHLY_SPEND unchanged

### 8. AI Quest Generation — API Failure Graceful Degradation

1. Set OPENAI_API_KEY to an invalid value in `.env`
2. Run: `python tools/quest_generator.py --character-id <ID>`
3. Verify:
   - Warning logged with error details
   - No quests created
   - No crash
   - AI_MONTHLY_SPEND unchanged (no cost recorded for failed call)

### 9. Coaching Briefing — Persona Rotation

1. Clear LAST_COACH_PERSONA in Settings DB (or set to empty)
2. Run: `python tools/coaching_engine.py --character-id <ID>`
3. Verify:
   - Briefing generated with Wartime CEO persona (first in rotation)
   - LAST_COACH_PERSONA updated to "wartime_ceo" in Settings DB
   - Response contains greeting, observations, recommendations, encouragement
   - AI_MONTHLY_SPEND incremented
4. Run again: `python tools/coaching_engine.py --character-id <ID>`
5. Verify:
   - Briefing generated with Methodical Analyst persona (second in rotation)
   - LAST_COACH_PERSONA updated to "methodical_analyst"
6. Run again:
7. Verify: Quest Master persona used, LAST_COACH_PERSONA = "quest_master"
8. Run again:
9. Verify: Wartime CEO again (rotation wraps around)

### 10. Cost Tracker — Monthly Spend Accumulation

1. Reset AI_MONTHLY_SPEND to 0 in Settings DB
2. Run quest_generator.py (1 call)
3. Note AI_MONTHLY_SPEND value (e.g., $0.0006)
4. Run coaching_engine.py (1 call)
5. Note AI_MONTHLY_SPEND value (e.g., $0.0017 — cumulative)
6. Verify: spend is cumulative, not overwritten
