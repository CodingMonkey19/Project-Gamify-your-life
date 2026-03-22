# Data Model: Phase 6 — OpenAI Cognitive Coach & Quest Engine

**Date**: 2026-03-22
**Feature**: 006-ai-coach-quests

## Core Principle: Quest Engine Follows Existing XP/Gold Patterns

Quest completion mirrors the same pattern used by all other engines: process events → create Activity Log entries → call xp_engine.update_character_stats(). Gold rewards flow through coin_engine (same as loot box). The quest engine adds no new databases — it reads from Quests DB (created in Phase 1) and writes to Activity Log and Character DB (existing). AI components (coaching, quest generation) are additive — the quest completion engine works without them.

## Quest Completion Domain

### Quests DB Schema (existing — created in Phase 1)

| Property | Type | Purpose |
|----------|------|---------|
| Quest Title | Title | Quest name |
| Narrative | Text | Story/description of the quest |
| Domain | Select | STR / INT / WIS / VIT / CHA — determines which stat receives XP |
| Difficulty | Select | Easy / Medium / Hard / Epic |
| Status | Status | Available / In Progress / Completed / Failed |
| Base XP | Number | XP value before multiplier (system-set from difficulty for AI quests) |
| Applied Multiplier | Number | Streak multiplier applied at completion (written by quest_engine) |
| Effective XP | Number | floor(Base XP × Applied Multiplier) — written by quest_engine |
| Gold Reward | Number | Gold awarded on completion (system-set from difficulty for AI quests) |
| Source | Select | Manual / AI-Generated |
| Due Date | Date | Quest deadline |
| Character | Relation → Character | Which player owns this quest |

### Quest Processing Rules

- **Trigger**: Status = "Completed" AND Effective XP is empty (null/0)
- **Skip conditions**: Status ≠ "Completed", OR Effective XP already populated (idempotency)
- **Domain default**: If Domain is empty, default to player's weakest stat (lowest XP value)
- **Multiplier source**: Highest multiplier from Streak Tracker rows where Domain matches quest Domain
- **No-streak default**: If no domain-matched streaks exist, Applied Multiplier = 1.0

### Quest Difficulty → Reward Mapping (from config.py / Settings DB)

| Difficulty | Base XP | Gold Reward |
|------------|---------|-------------|
| Easy | 25 | 5 |
| Medium | 50 | 10 |
| Hard | 100 | 25 |
| Epic | 200 | 50 |

Config key: `QUEST_DIFFICULTY_REWARDS` — dictionary mapping difficulty to `{"xp": int, "gold": int}`.

### Quest Completion Calculation

```
Applied Multiplier = max(multiplier FROM Streak Tracker WHERE domain == quest.domain)
                     OR 1.0 if no domain-matched streaks

Effective XP = floor(base_xp * applied_multiplier)

Gold Reward = quest.gold_reward (no multiplier applied to Gold)
```

### Activity Log Entry (Quest Completion)

| Property | Value |
|----------|-------|
| Type | QUEST |
| Date | Today |
| EXP + (Quest) | Effective XP value |
| Domain | Quest's Domain (or weakest stat default) |
| Character | Quest's Character relation |
| Source | Quest Title reference |

Note: New Activity Log entry type "QUEST" is added alongside existing types (GOOD, BAD, GOAL, TASKS, ACHIEVEMENT, MARKET, HOTEL, BLACKMARKET).

## AI Quest Generation Domain

### AI Request/Response Schema

**Input context sent to OpenAI** (built by quest_generator):

```json
{
  "player_stats": {"STR": 1205, "INT": 340, "WIS": 890, "VIT": 567, "CHA": 210},
  "stat_levels": {"STR": 2, "INT": 1, "WIS": 1, "VIT": 1, "CHA": 1},
  "weakest_stat": "CHA",
  "active_streaks": [{"habit": "Gym", "domain": "STR", "streak": 14, "tier": "Gold"}],
  "recent_quests_completed": 3,
  "total_quests_available": 2,
  "player_rank": "Squire",
  "player_level": 1
}
```

**Expected AI response** (structured JSON):

```json
{
  "quests": [
    {
      "title": "The Mage's Trial",
      "narrative": "Ancient texts await in the library. Study a new topic for 30 minutes.",
      "domain": "INT",
      "difficulty": "Medium"
    },
    {
      "title": "Social Expedition",
      "narrative": "Reach out to a friend you haven't spoken to in a while.",
      "domain": "CHA",
      "difficulty": "Easy"
    },
    {
      "title": "Iron Will Challenge",
      "narrative": "Complete an extra workout session beyond your routine.",
      "domain": "STR",
      "difficulty": "Hard"
    }
  ]
}
```

### AI-Generated Quest Validation Rules

| Field | Validation | On Failure |
|-------|-----------|------------|
| title | Non-empty string | Reject quest |
| narrative | Non-empty string | Reject quest |
| domain | Must be in {STR, INT, WIS, VIT, CHA} | Default to weakest stat, log warning |
| difficulty | Must be in {Easy, Medium, Hard, Epic} | Default to "Medium", log warning |

After validation, the system calculates `base_xp` and `gold_reward` from difficulty using `QUEST_DIFFICULTY_REWARDS` config.

### Generated Quest Row (written to Quests DB)

| Property | Value |
|----------|-------|
| Quest Title | AI-provided title |
| Narrative | AI-provided narrative |
| Domain | AI-provided (validated) |
| Difficulty | AI-provided (validated) |
| Status | Available |
| Base XP | From QUEST_DIFFICULTY_REWARDS[difficulty].xp |
| Gold Reward | From QUEST_DIFFICULTY_REWARDS[difficulty].gold |
| Source | AI-Generated |
| Due Date | Today + 7 days |
| Character | Current character relation |
| Applied Multiplier | (empty — set at completion) |
| Effective XP | (empty — set at completion) |

## AI Coaching Domain

### Coaching Personas

| Persona | Style | Focus | Rotation Order |
|---------|-------|-------|----------------|
| Wartime CEO | Direct, commanding, action-oriented | Weaknesses, accountability, urgency | 1 |
| Methodical Analyst | Data-driven, calm, pattern-focused | Trends, correlations, anomalies | 2 |
| Quest Master | Narrative, RPG-themed, encouraging | Hero's journey, quests as adventures | 3 |

Rotation: Round-robin tracked by `LAST_COACH_PERSONA` in Settings DB. Values: "wartime_ceo", "methodical_analyst", "quest_master". Next persona = next in sequence after last-used.

### Weekly Metrics Input (built by coaching_engine)

```json
{
  "stat_deltas_7d": {"STR": 150, "INT": 25, "WIS": 80, "VIT": 40, "CHA": 10},
  "current_stats": {"STR": 1205, "INT": 340, "WIS": 890, "VIT": 567, "CHA": 210},
  "active_streaks": [{"habit": "Gym", "domain": "STR", "days": 14, "tier": "Gold"}],
  "broken_streaks": [{"habit": "Reading", "domain": "INT", "was_days": 5}],
  "quests_completed": 3,
  "quests_total": 5,
  "hp_current": 85,
  "hp_max": 100,
  "gold_balance": 250,
  "coin_balance": 1500,
  "player_level": 1,
  "player_rank": "Squire"
}
```

### Expected Coaching Response (structured JSON)

```json
{
  "greeting": "Commander. Let's review the battlefield.",
  "observations": [
    "STR dominance continues — 150 XP this week, dwarfing other stats.",
    "CHA is critically neglected at only 10 XP gained."
  ],
  "recommendations": [
    "Dedicate 2 days this week to a CHA-focused activity.",
    "Your Gold reserves are building — consider strategic loot box investment."
  ],
  "encouragement": "You're holding the line, soldier. But a balanced army wins wars."
}
```

## Cost Tracking Domain

### Settings DB Fields (AI Cost Tracking)

| Setting Key | Type | Default | Purpose |
|-------------|------|---------|---------|
| AI_MONTHLY_SPEND | Number | 0 | Cumulative USD spent on AI calls this month |
| LAST_COACH_PERSONA | Text | (empty) | Last-used coaching persona identifier |
| OPENAI_MODEL | Text | gpt-4o-mini | OpenAI model for all AI calls |
| OPENAI_MONTHLY_COST_CAP_USD | Number | 1.00 | Hard monthly spending limit |
| OPENAI_MAX_TOKENS | Number | 1500 | Maximum output tokens per AI call |

### Cost Calculation

```
call_cost = (prompt_tokens / 1_000_000 * INPUT_PRICE) + (completion_tokens / 1_000_000 * OUTPUT_PRICE)

MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60}  # per 1M tokens
}

Pre-flight budget check:
  estimated_max_cost = (estimated_input_tokens / 1M * input_price) + (max_tokens / 1M * output_price)
  if AI_MONTHLY_SPEND + estimated_max_cost > OPENAI_MONTHLY_COST_CAP_USD → REJECT

Post-call recording:
  actual_cost = calculated from response.usage
  AI_MONTHLY_SPEND += actual_cost → written back to Settings DB
```

### AI Interaction Log (appended to existing logging)

Each AI call logs:
- Timestamp
- Persona (for coaching) or "quest_generation"
- Model used
- Prompt tokens / Completion tokens
- Estimated cost
- Success/failure status

This uses the existing `logger.py` infrastructure — no new database needed.

### Monthly Reset

`AI_MONTHLY_SPEND` is reset to 0 on the 1st of each month by the monthly automation (Phase 7). Phase 6 does not implement the reset — it only reads and increments the value.

## State Transitions

### Quest Completion Flow

```
Quest marked "Completed" in Notion (by player)
  → quest_engine.process_all_quests(character_id)
    → Query Quests DB: Status = "Completed" AND Effective XP is empty
    → For each pending quest:
      → Resolve domain (quest.domain OR weakest stat default)
      → Query Streak Tracker: domain-matched → highest multiplier (or 1.0)
      → Calculate: Effective XP = floor(base_xp * multiplier)
      → Write to quest row: Applied Multiplier, Effective XP
      → Create Activity Log entry: Type=QUEST, domain XP = Effective XP
      → If gold_reward > 0: coin_engine.add_gold(character_id, gold_reward)
    → xp_engine.update_character_stats(character_id)
    → Return summary
```

### AI Quest Generation Flow

```
Weekly automation (or manual CLI trigger)
  → quest_generator.generate_quests(character_id)
    → ai_cost_tracker.check_budget(estimated_cost) → proceed or reject
    → Build player context (stats, streaks, recent activity, weakest stat)
    → Call OpenAI with quest generation prompt + JSON mode
    → ai_cost_tracker.record_spend(response.usage, model)
    → Parse JSON response → validate each quest
    → For each valid quest:
      → Look up base_xp and gold_reward from QUEST_DIFFICULTY_REWARDS[difficulty]
      → Create Quests DB row (status=Available, source=AI-Generated, due=today+7d)
    → Return summary (quests created, any validation warnings)
```

### Coaching Briefing Flow

```
Weekly automation (or manual CLI trigger)
  → coaching_engine.generate_briefing(character_id)
    → ai_cost_tracker.check_budget(estimated_cost) → proceed or reject
    → Determine next persona (read LAST_COACH_PERSONA → rotate)
    → Build weekly metrics context
    → Call OpenAI with persona system prompt + metrics + JSON mode
    → ai_cost_tracker.record_spend(response.usage, model)
    → Update LAST_COACH_PERSONA in Settings DB
    → Parse and validate briefing JSON
    → Log briefing for player review
    → Return briefing + persona used
```

### Cost Cap Enforcement Flow

```
Any AI call requested
  → ai_cost_tracker.check_budget(estimated_max_cost)
    → Read AI_MONTHLY_SPEND from Settings DB
    → Read OPENAI_MONTHLY_COST_CAP_USD from config
    → If spend + estimated_cost > cap → return False (reject)
    → Else → return True (proceed)

After successful AI call
  → ai_cost_tracker.record_spend(response.usage, model)
    → Calculate actual cost from token counts
    → Read current AI_MONTHLY_SPEND from Settings DB
    → Write AI_MONTHLY_SPEND + actual_cost back to Settings DB
    → Log cost details
```
