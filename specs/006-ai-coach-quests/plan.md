# Implementation Plan: Phase 6 — OpenAI Cognitive Coach & Quest Engine

**Branch**: `006-ai-coach-quests` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-ai-coach-quests/spec.md`

## Summary

Build a quest completion engine, AI-powered procedural quest generator, and multi-persona coaching system with cost controls. The quest engine processes completed quests by applying domain-matched streak multipliers to calculate Effective XP, creating Activity Log entries for stat routing, and crediting Gold via coin_engine — following the same patterns established in Phases 2-5. The AI quest generator uses OpenAI's gpt-4o-mini with JSON mode to produce 3 personalized quests per week based on player stats, streaks, and weak areas; the system calculates XP/Gold rewards from difficulty via a configurable scale. The coaching engine rotates 3 personas (Wartime CEO, Methodical Analyst, Quest Master) in round-robin order to deliver structured weekly briefings. All AI operations share a cost tracker that enforces a configurable monthly spend cap ($1.00 default) with pre-flight budget checks and post-call spend recording.

Key research decisions:
- Structured JSON output via OpenAI JSON mode (`response_format={"type": "json_object"}`)
- Cost tracking from API response `usage` field (no tiktoken dependency)
- Domain-matched streak multiplier: highest multiplier from all streaks matching quest domain
- Persona system prompts as constants in engine file (not config — they're behavioral templates, not balance values)
- Graceful degradation: all AI failures log warnings and skip without crashing

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `notion-client`, `python-dotenv` (inherited from Phase 1), `openai` (new — OpenAI Python SDK v1.x+)
**Storage**: Notion — Quests DB (existing), Activity Log (existing), Character DB (existing), Streak Tracker (existing), Settings DB (existing). No new databases.
**Testing**: `pytest` with mock Notion responses (`conftest.py` from Phases 1-5, extended) + mocked OpenAI responses
**Target Platform**: GitHub Actions (scheduled weekly), local CLI (development)
**Project Type**: CLI tools / automation scripts
**Performance Goals**: Quest processing < 5s per quest; AI call < 30s (timeout); full weekly run (3 quest gen + 1 coaching + quest completion) < 120s
**Constraints**: All XP/Gold values are integers (floor rounding). Activity Log is append-only. Phases 1-5 must be complete. Notion API rate limit (3 req/sec). OpenAI monthly cost cap ($1.00 default). Single player. AI responses must be structured JSON.
**Scale/Scope**: Single player, 3 AI-generated quests per week, 1 coaching briefing per week, 5 stat domains, 4 difficulty tiers, 3 coaching personas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Notion as Headless DB & GUI | PASS | All data stored in Notion (Quests DB, Activity Log, Settings DB). Quest completion involves cross-row aggregation (streak lookup across Streak Tracker, XP calculation from Activity Log). Notion-native: players create manual quests directly as DB rows, mark quests as Completed via Status property. Python handles: multi-DB queries (streak lookup), XP calculation with multiplier, AI integration, cost tracking |
| II. Python for Complex Orchestration | PASS | Four new tools in `tools/`, each handling one concern: `quest_engine.py` (quest completion processing), `quest_generator.py` (AI quest generation), `coaching_engine.py` (AI coaching briefings), `ai_cost_tracker.py` (spend tracking + budget enforcement). No tool does reasoning. Quest engine is deterministic math. AI tools delegate reasoning to OpenAI and parse structured responses. All constants from config.py / Settings DB |
| III. WAT Architecture | PASS | Four new tools added to `tools/`. Each is a deterministic execution unit callable independently via CLI. Quest engine has no AI dependency. AI tools use shared cost tracker. No embedded reasoning — tools call OpenAI and parse responses |
| IV. Settings DB as Canonical Config | PASS | All new constants sourced from Settings DB / config.py: QUEST_DIFFICULTY_REWARDS, OPENAI_MODEL, OPENAI_MONTHLY_COST_CAP_USD, OPENAI_MAX_TOKENS, AI_MONTHLY_SPEND, LAST_COACH_PERSONA. No hardcoded balance values in engine files. Persona system prompts are constants in coaching_engine.py but are behavioral templates, not balance values (see R5 in research.md) |
| V. Idempotency | PASS | Quest engine: checks Effective XP field before processing — populated means already processed, skip. Activity Log entries are created only when Effective XP was empty. Re-running creates no duplicates. AI quest generation: non-idempotent by design (each run creates new quests) but safe — creates Available quests, no side effects. Coaching: non-idempotent (each run produces a new briefing) but safe — persona rotation advances, spend accumulates correctly |
| VI. Free-First | PASS | Only paid dependency is OpenAI gpt-4o-mini at ~$0.007/month for expected usage. Hard monthly cost cap ($1.00 default) enforced before every API call. Estimated monthly spend is 100x below cap. No other paid services added. `openai` Python SDK is free/open-source |

**Post-design re-check**: All principles still hold. No new violations introduced by data model or contracts.

## Project Structure

### Documentation (this feature)

```text
specs/006-ai-coach-quests/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
tools/
├── quest_engine.py       # Quest completion: streak multiplier, Effective XP, Activity Log, Gold
├── quest_generator.py    # AI quest generation: OpenAI call, validation, Quests DB row creation
├── coaching_engine.py    # AI coaching: persona rotation, weekly metrics, structured briefings
├── ai_cost_tracker.py    # Shared cost tracking: budget check, spend recording, cap enforcement
│
├── config.py             # (Phase 1 — extend) QUEST_DIFFICULTY_REWARDS, OPENAI_*, AI cost settings
├── logger.py             # (Phase 1 — already exists)
├── notion_client.py      # (Phase 1 — already exists)
├── xp_engine.py          # (Phase 3 — already exists) Called after quest XP grants
├── coin_engine.py        # (Phase 2 — already exists) Gold crediting for quest rewards
├── streak_engine.py      # (Phase 3 — already exists) Streak Tracker queries for multiplier

tests/
├── test_quest_engine.py       # Completion processing, multiplier calc, idempotency, domain default
├── test_quest_generator.py    # AI response parsing, validation, DB row creation, error handling
├── test_coaching_engine.py    # Persona rotation, briefing parsing, metrics context building
├── test_ai_cost_tracker.py    # Budget check, spend recording, cap enforcement, cost calculation
├── conftest.py                # (Phases 1-5 — extend with quest/AI mock fixtures)
```

**Structure Decision**: Flat `tools/` layout consistent with Phases 1-5. Quest engine is separate from AI quest generator because quest completion has zero AI dependency — it works even when OpenAI is unreachable. Cost tracker is a shared module imported by both AI tools, not a standalone CLI tool (it has no independent CLI use case). Tests mirror engine files 1:1.

## Contracts

### quest_engine.py

```python
def get_pending_quests(character_id: str) -> list:
    """Query Quests DB for quests with Status='Completed' and Effective XP empty.
    Filters by Character relation matching character_id.
    Returns: list of quest dicts with all Quests DB properties."""

def get_domain_streak_multiplier(character_id: str, domain: str) -> float:
    """Query Streak Tracker DB for all rows matching the given domain.
    Returns the highest Multiplier value found.
    Returns 1.0 if no domain-matched streaks exist or domain is None."""

def get_weakest_stat(character_id: str) -> str:
    """Read all 5 stat XP values from Character DB.
    Returns the stat name with the lowest XP value.
    Tie-breaking: alphabetical (CHA < INT < STR < VIT < WIS)."""

def process_quest_completion(character_id: str, quest: dict) -> dict:
    """Process a single completed quest.
    1. Resolve domain (quest domain or weakest stat default via get_weakest_stat)
    2. Get streak multiplier via get_domain_streak_multiplier()
    3. Calculate Effective XP = floor(base_xp * multiplier)
    4. Write Applied Multiplier and Effective XP to quest row
    5. Create Activity Log entry (Type=QUEST, domain XP)
    6. Credit Gold via coin_engine if gold_reward > 0
    Returns: {"quest_id": str, "domain": str, "multiplier": float,
              "effective_xp": int, "gold_awarded": int}"""

def process_all_quests(character_id: str) -> dict:
    """Orchestrator: process all pending completed quests.
    1. get_pending_quests()
    2. For each: process_quest_completion()
    3. Call xp_engine.update_character_stats() if any quests processed
    Returns: {"processed": int, "total_xp": int, "total_gold": int,
              "quests": list[dict]}"""
```

### quest_generator.py

```python
def build_generation_context(character_id: str) -> dict:
    """Gather player context for AI quest generation prompt.
    Reads: Character DB (stats, level, rank), Streak Tracker (active streaks),
    Quests DB (recent completion count, available quest count).
    Identifies weakest stat.
    Returns: context dict matching AI input schema (see data-model.md)."""

def validate_quest(quest_data: dict, weakest_stat: str) -> dict:
    """Validate a single AI-generated quest dict.
    Checks: title (non-empty), narrative (non-empty),
    domain (in valid set, default to weakest_stat), difficulty (in valid set, default Medium).
    Returns: validated quest dict with corrections applied.
    Returns None if quest is invalid (missing title or narrative)."""

def generate_quests(character_id: str) -> dict:
    """Full AI quest generation pipeline.
    1. ai_cost_tracker.check_budget() → reject if over cap
    2. Build player context via build_generation_context()
    3. Call OpenAI with quest generation system prompt + JSON mode
    4. ai_cost_tracker.record_spend()
    5. Parse JSON response, validate each quest via validate_quest()
    6. For each valid quest: calculate base_xp/gold from difficulty, create Quests DB row
    Returns: {"quests_created": int, "quests_rejected": int,
              "cost": float, "quest_ids": list[str]}
    Returns None with warning if budget exceeded or API fails."""
```

### coaching_engine.py

```python
PERSONAS = {
    "wartime_ceo": {"name": "Wartime CEO", "system_prompt": "..."},
    "methodical_analyst": {"name": "Methodical Analyst", "system_prompt": "..."},
    "quest_master": {"name": "Quest Master", "system_prompt": "..."},
}
ROTATION_ORDER = ["wartime_ceo", "methodical_analyst", "quest_master"]

def get_next_persona() -> str:
    """Read LAST_COACH_PERSONA from Settings DB.
    Return the next persona in ROTATION_ORDER.
    If LAST_COACH_PERSONA is empty or invalid, start with first persona.
    Returns: persona key (e.g., 'wartime_ceo')."""

def build_coaching_context(character_id: str) -> dict:
    """Gather weekly metrics for coaching input.
    Reads: Character DB (current stats, HP, Gold, Coins, level, rank),
    Activity Log (7-day XP deltas per stat),
    Streak Tracker (active + recently broken streaks),
    Quests DB (completed vs total this week).
    Returns: weekly metrics dict matching coaching input schema (see data-model.md)."""

def generate_briefing(character_id: str) -> dict:
    """Full coaching briefing pipeline.
    1. ai_cost_tracker.check_budget() → reject if over cap
    2. Determine next persona via get_next_persona()
    3. Build weekly metrics via build_coaching_context()
    4. Call OpenAI with persona system prompt + metrics + JSON mode
    5. ai_cost_tracker.record_spend()
    6. Update LAST_COACH_PERSONA in Settings DB
    7. Parse and validate briefing JSON
    8. Log briefing
    Returns: {"persona": str, "briefing": dict, "cost": float}
    Returns None with warning if budget exceeded or API fails."""
```

### ai_cost_tracker.py

```python
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # USD per 1M tokens
}

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """Calculate estimated cost for a given token count.
    Returns: cost in USD (float)."""

def check_budget(estimated_input_tokens: int, max_output_tokens: int,
                 model: str = "gpt-4o-mini") -> bool:
    """Pre-flight budget check before making an AI call.
    1. Read AI_MONTHLY_SPEND from Settings DB
    2. Read OPENAI_MONTHLY_COST_CAP_USD from config
    3. Calculate worst-case cost from estimated input + max output tokens
    4. Return True if spend + worst_case <= cap, False otherwise.
    Logs warning when rejecting."""

def record_spend(usage: dict, model: str = "gpt-4o-mini") -> float:
    """Record actual spend after a successful AI call.
    1. Calculate cost from usage.prompt_tokens and usage.completion_tokens
    2. Read current AI_MONTHLY_SPEND from Settings DB
    3. Write AI_MONTHLY_SPEND + cost back to Settings DB
    4. Log cost details (model, tokens, cost)
    Returns: cost for this call (float)."""

def get_monthly_spend() -> float:
    """Read current AI_MONTHLY_SPEND from Settings DB.
    Returns: cumulative spend in USD (float). Returns 0.0 if not set."""
```

## Implementation Order

| Step | Function/File | Depends On | Delivers |
|------|--------------|------------|----------|
| 1 | `config.py` updates | Phase 1 config | New constants: QUEST_DIFFICULTY_REWARDS, OPENAI_MODEL, OPENAI_MONTHLY_COST_CAP_USD, OPENAI_MAX_TOKENS |
| 2 | `ai_cost_tracker.estimate_cost()` | Step 1 (config) | Pure math: tokens → USD |
| 3 | `ai_cost_tracker.get_monthly_spend()` | Phase 1 (notion_client) | Settings DB read |
| 4 | `ai_cost_tracker.check_budget()` | Steps 2-3 | Pre-flight budget gate |
| 5 | `ai_cost_tracker.record_spend()` | Steps 2-3 | Post-call spend recording |
| 6 | `test_ai_cost_tracker.py` | Steps 2-5 | Cost tracker test suite |
| 7 | `quest_engine.get_weakest_stat()` | Phase 1 (notion_client) | Stat comparison |
| 8 | `quest_engine.get_domain_streak_multiplier()` | Phase 3 (streak_engine) | Domain-matched multiplier lookup |
| 9 | `quest_engine.get_pending_quests()` | Phase 1 (notion_client) | Quests DB query |
| 10 | `quest_engine.process_quest_completion()` | Steps 7-9, Phase 2 (coin_engine) | Single quest processing |
| 11 | `quest_engine.process_all_quests()` | Step 10, Phase 3 (xp_engine) | Full quest orchestration |
| 12 | `test_quest_engine.py` | Steps 7-11 | Quest engine test suite |
| 13 | `quest_generator.build_generation_context()` | Phase 1 (notion_client) | Player context for AI |
| 14 | `quest_generator.validate_quest()` | Step 1 (config) | Quest validation logic |
| 15 | `quest_generator.generate_quests()` | Steps 4-5, 13-14, Step 1 (config), openai SDK | Full AI quest generation |
| 16 | `test_quest_generator.py` | Steps 13-15 | Quest generator test suite |
| 17 | `coaching_engine.get_next_persona()` | Phase 1 (notion_client) | Persona rotation |
| 18 | `coaching_engine.build_coaching_context()` | Phase 1 (notion_client) | Weekly metrics gathering |
| 19 | `coaching_engine.generate_briefing()` | Steps 4-5, 17-18, openai SDK | Full coaching pipeline |
| 20 | `test_coaching_engine.py` | Steps 17-19 | Coaching engine test suite |
| 21 | `conftest.py` updates | Steps 6, 12, 16, 20 | Mock fixtures for Phase 6 engines |

**Key dependencies**:
- `quest_engine` has zero AI dependency — can be built and tested independently of OpenAI
- `ai_cost_tracker` is a shared utility — must be built first before both AI tools
- `quest_generator` and `coaching_engine` both depend on `ai_cost_tracker` but are independent of each other — can be built in parallel
- `quest_engine.get_weakest_stat()` is reused by `quest_generator` (for FR-015 weakest stat targeting) — build quest_engine first
- All engines depend on `config.py` (Phase 1) for configurable constants
- Pure functions (`estimate_cost`, `get_weakest_stat`, `get_domain_streak_multiplier`, `validate_quest`) have zero Notion dependency — can be unit tested without mocks

## Complexity Tracking

No constitution violations — table not needed.
