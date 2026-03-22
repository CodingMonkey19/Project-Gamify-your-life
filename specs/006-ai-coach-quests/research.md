# Research: Phase 6 — OpenAI Cognitive Coach & Quest Engine

**Date**: 2026-03-22
**Feature**: 006-ai-coach-quests

## R1: Structured JSON Output from OpenAI

**Decision**: Use OpenAI's JSON mode via `response_format={"type": "json_object"}` combined with explicit schema definitions in the system prompt.
**Rationale**: JSON mode guarantees syntactically valid JSON output, eliminating parse failures from free-text responses. The system prompt describes the exact schema (field names, types, valid values), and JSON mode enforces compliance. This is simpler than function calling / tool use for this use case since we just need structured data, not tool invocation.
**Alternatives considered**: Function calling / tool use (overkill — we're not dispatching actions, just extracting structured data), free-text with regex parsing (fragile, violates FR-021), Pydantic model validation of free-text (still requires valid JSON first), structured outputs with JSON schema enforcement (newer API feature, adds schema definition overhead — JSON mode + prompt instructions is sufficient for 3-5 field objects).

## R2: gpt-4o-mini Pricing and Budget Analysis

**Decision**: Use `gpt-4o-mini` as the default model. Pricing: ~$0.15/1M input tokens, ~$0.60/1M output tokens. Calculate cost from the API response's `usage` field (prompt_tokens, completion_tokens).
**Rationale**: Per-call cost estimates for Phase 6 use cases:
- Coaching briefing: ~1200 input tokens (system prompt + weekly metrics) + 1500 output tokens (max) = ~$0.00108/call
- Quest generation: ~1000 input tokens (system prompt + player context) + 800 output tokens (3 quests JSON) = ~$0.00063/call
- Weekly total: 1 coaching + 1 quest gen = ~$0.00171/week ≈ $0.007/month
- Monthly cap of $1.00 allows ~580+ calls — far exceeding the 8 calls/month requirement (4 weeks × 2 calls)
- Even at 10x the estimated token usage, monthly spend stays under $0.10

**Alternatives considered**: gpt-4o (higher quality but ~10x cost — $2.50/1M input, $10/1M output — would consume budget faster with no meaningful quality gain for structured quest/coaching output), gpt-3.5-turbo (deprecated path, gpt-4o-mini is the successor with better quality at similar price).

## R3: Token Counting — Post-Call from API Response

**Decision**: Use `response.usage.prompt_tokens` and `response.usage.completion_tokens` from the OpenAI API response object. Do not pre-estimate tokens with tiktoken.
**Rationale**: The API response contains exact token counts, making pre-flight estimation unnecessary overhead. Cost is calculated after each call using `(input_tokens * input_price + output_tokens * output_price)`. The `max_tokens` parameter caps output length (default: 1500). Pre-flight budget check uses a conservative estimate (max possible cost = max_tokens * output_price + estimated_input * input_price) to decide whether to proceed.
**Alternatives considered**: tiktoken for pre-flight token counting (adds dependency, adds latency, approximate anyway — the API response is authoritative), fixed cost per call (too imprecise, doesn't account for variable prompt sizes).

## R4: Domain-Matched Streak Multiplier for Quest XP

**Decision**: Query the Streak Tracker DB filtered by Domain matching the quest's Domain. Take the highest multiplier from all matching streaks. If no domain-matched streaks exist, multiplier = 1.0.
**Rationale**: This is consistent with how streaks work in Phase 3. A player might have multiple habits in the same domain (e.g., two STR habits: "Gym" and "Push-ups"), each with its own streak. Using the *highest* multiplier rewards the player's best consistency in that domain. The Streak Tracker DB already stores Domain (copied from the habit) and Multiplier (calculated from tier).
**Alternatives considered**: Average of all domain-matched multipliers (penalizes having multiple habits — a broken streak on one habit drags down the average), multiplier from the specific habit that triggered the quest (quests aren't linked to specific habits), flat multiplier from player level (disconnected from streak mechanic).

## R5: Coaching Persona System Prompts — Constants in Engine

**Decision**: Store the three persona system prompts as string constants in `coaching_engine.py`. Persona rotation state (LAST_COACH_PERSONA) is tracked in the Settings DB.
**Rationale**: System prompts are behavioral templates, not game balance constants. They define tone and focus ("be direct and action-oriented" vs "analyze patterns and data"), which is fundamentally different from numeric tuning values. Putting them in Settings DB or config.py would suggest they're frequently adjusted, but they're designed once and rarely changed. Constants in the engine file are simpler, version-controlled, and testable.
**Alternatives considered**: Settings DB (system prompts are long text, poorly suited to Notion properties — would need a separate "Prompts" DB, adding complexity), config.py (mixes behavioral templates with numeric constants), external markdown files (adds file I/O for every coaching call, fragile path management).

## R6: OpenAI Error Handling Strategy

**Decision**: Wrap all OpenAI API calls in try-except. On failure: log warning with error details, return None/empty result, do not crash. Apply exponential backoff with jitter for rate limit errors (max 3 retries, consistent with constitution's error handling mandate). Set a 30-second request timeout.
**Rationale**: The spec requires graceful degradation (FR-016, edge cases). Quest completion works without AI. Coaching and quest generation are weekly — a single failure is recoverable next week. The OpenAI Python SDK raises specific exceptions (`openai.APIError`, `openai.RateLimitError`, `openai.APIConnectionError`) that can be caught granularly.
**Alternatives considered**: Crash on failure (violates spec requirements), queue and retry later (adds state management for marginal benefit at 1 call/week), fallback to a different model (adds complexity — better to just skip and retry next week).

## R7: Weakest Stat Determination for Domain-less Quests

**Decision**: Read all 5 stat XP values (STR, INT, WIS, VIT, CHA) from Character DB, return the stat with the lowest XP. Tie-breaking: alphabetical order (CHA < INT < STR < VIT < WIS) for deterministic results.
**Rationale**: FR-009 requires defaulting domain-less quests to the player's weakest stat. Using raw XP (not level) gives finer granularity. Alphabetical tie-breaking ensures the same result on re-runs (idempotency). This function is also reused by the AI quest generator (FR-015) to ensure at least one generated quest targets the weakest area.
**Alternatives considered**: Use stat levels instead of XP (coarser — many stats could be the same level), random selection among tied stats (non-deterministic, violates idempotency spirit), user-configurable priority (over-engineering for an edge case).

## R8: OpenAI Python SDK Version and Import Pattern

**Decision**: Use `openai` Python SDK (v1.x+). Import pattern: `from openai import OpenAI; client = OpenAI()`. API key read from environment variable `OPENAI_API_KEY` (auto-detected by SDK).
**Rationale**: The v1.x SDK is the current stable release with full typing support, structured response handling, and usage statistics in the response object. The client auto-reads `OPENAI_API_KEY` from the environment (consistent with .env loading via python-dotenv in Phase 1). No need to pass the key explicitly.
**Alternatives considered**: Direct HTTP requests (loses SDK error handling, typing, retry logic), older openai v0.x (deprecated, different API surface), httpx (lower-level, no OpenAI-specific helpers).
