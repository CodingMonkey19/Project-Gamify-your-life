# Feature Specification: OpenAI Cognitive Coach & Quest Engine

**Feature Branch**: `006-ai-coach-quests`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Phase 6 of V5 Implementation Plan — Multi-Persona OpenAI Coach with Cost Controls, Quest Engine with Procedural AI Quest Generation

## Clarifications

### Session 2026-03-22

- Q: Which streak determines the quest multiplier? → A: Domain-matched — use the highest streak tier from habits in the quest's Domain (e.g., STR quest uses STR habit streaks)
- Q: Who sets base XP and Gold for AI-generated quests? → A: System calculates from difficulty — AI picks difficulty, system maps to XP/Gold using config (e.g., Easy=25/5, Medium=50/10, Hard=100/25, Epic=200/50)
- Q: Where is monthly AI spend tracked? → A: Settings DB in Notion — stored as AI_MONTHLY_SPEND, reset by monthly automation on the 1st
- Q: How is the coaching persona selected each week? → A: Round-robin rotation — cycle through Wartime CEO → Methodical Analyst → Quest Master, track last-used
- Q: Should quests award Gold or Coins? → A: Gold — quests award Gold as designed in V5 plan (second Gold source alongside financial surplus)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Quest Completion & XP Rewards (Priority: P1)

The player has a Quest Board in Notion showing available quests (both manually created and AI-generated). Each quest has a title, narrative, domain (STR/INT/WIS/VIT/CHA), difficulty (Easy/Medium/Hard/Epic), base XP, Gold reward, and due date. When the player marks a quest as "Completed", the quest engine processes it: applies a streak-based multiplier to calculate Effective XP, creates an Activity Log entry for the domain XP, credits Gold via coin_engine, and updates character stats. The player sees the quest marked complete with final XP/Gold earned.

**Why this priority**: Quest completion is the core gameplay loop that gives meaning to the quest board. Without the completion engine, quests are just a to-do list. This must work before AI generation makes sense — manually created quests must be completable first.

**Independent Test**: Manually create a quest in the Quests DB (title, domain=STR, difficulty=Medium, base_xp=50, gold_reward=10, status=Completed), run the quest engine, verify Activity Log entry with Effective XP (base * multiplier) mapped to STR, Gold credited, quest row updated with Applied Multiplier and Effective XP.

**Acceptance Scenarios**:

1. **Given** a quest with domain=STR, base_xp=50, Gold=10, and player's highest STR-domain habit streak tier gives a 1.5x multiplier, **When** quest is marked Completed and quest engine runs, **Then** Effective XP = floor(50 * 1.5) = 75 STR XP is granted via Activity Log, 10 Gold credited via coin_engine, Applied Multiplier=1.5 and Effective XP=75 written to quest row
2. **Given** a quest already processed (Effective XP field already populated), **When** quest engine runs again, **Then** no duplicate Activity Log entry is created (idempotent)
3. **Given** a quest with status "In Progress" or "Available", **When** quest engine runs, **Then** quest is skipped (only "Completed" status triggers processing)
4. **Given** a quest with status "Failed", **When** quest engine runs, **Then** quest is skipped, no XP or Gold granted

---

### User Story 2 — AI Procedural Quest Generation (Priority: P1)

During the weekly report automation, the system generates 3 new AI quests based on the player's current stats, recent activity, active streaks, and weak areas. The AI picks the title, narrative, domain, and difficulty for each quest. The system then calculates base XP and Gold reward from the difficulty tier using a configurable scale (Easy=25xp/5g, Medium=50xp/10g, Hard=100xp/25g, Epic=200xp/50g). The quests are created in the Quests DB with source="AI-Generated", status="Available", and a due date within the coming week.

**Why this priority**: AI quest generation is the unique differentiator — it creates personalized challenges that adapt to the player's current state. Without this, the quest board is static. It's co-P1 with quest completion because both are needed for the full quest loop: generate → attempt → complete → reward.

**Independent Test**: Run the quest generation with a character who has STR=10, INT=3, WIS=5 (INT is weakest stat), verify 3 quests created in Quests DB, at least one targeting INT domain, each with narrative, difficulty, base XP, Gold, due date within 7 days, source="AI-Generated".

**Acceptance Scenarios**:

1. **Given** a character with uneven stats (STR=10, INT=3), **When** AI quest generation runs, **Then** 3 quests are created in the Quests DB, at least one targets the weakest stat area (INT), each has a thematic narrative, difficulty, base XP, Gold reward, and due date within the next 7 days
2. **Given** the AI response is structured JSON, **When** quest generation parses the response, **Then** all required quest fields are extracted and validated before creating DB rows
3. **Given** the AI service is unreachable or returns an error, **When** quest generation runs, **Then** the failure is logged as a warning and no quests are created (graceful degradation, no crash)

---

### User Story 3 — Weekly Coaching Briefing (Priority: P2)

During the weekly report automation, the system sends the player's weekly metrics (stat deltas, streak status, quest completion rate, HP changes, Gold/Coin balance) to an AI coach that responds with a personalized weekly briefing. The AI coach has 3 distinct personas that rotate in round-robin order each week: the Wartime CEO (direct, action-oriented), the Methodical Analyst (data-driven, pattern-focused), and the Quest Master (narrative, gamified encouragement). The last-used persona is tracked in Settings DB. The briefing is logged for the player to review.

**Why this priority**: The coaching briefing is motivational but not mechanically required. The game loop (quests, XP, Gold) works without coaching. P2 because it enhances the experience but doesn't block any core functionality.

**Independent Test**: Provide weekly metrics (7-day stat deltas, streak counts, quest completion rate), run the coaching engine with each persona, verify each produces a structured response with observations, recommendations, and encouragement in the persona's distinctive voice.

**Acceptance Scenarios**:

1. **Given** weekly metrics showing STR XP +500, INT XP +50, 3 active streaks, 2/5 quests completed, **When** Wartime CEO persona generates a briefing, **Then** the response is direct, action-oriented, calls out the INT weakness, and suggests specific actions
2. **Given** the same metrics, **When** Methodical Analyst persona generates a briefing, **Then** the response is data-driven, highlights patterns, and provides analytical observations
3. **Given** the same metrics, **When** Quest Master persona generates a briefing, **Then** the response uses RPG narrative language, treats the player as a hero, and frames recommendations as quest objectives
4. **Given** the monthly AI cost has reached the configured cap, **When** a coaching briefing is requested, **Then** the request is rejected with a cost cap warning (no API call made)

---

### Edge Cases

- What happens when the OpenAI API key is not configured? Coach and quest generation skip gracefully with a warning, quest completion still works (no AI dependency)
- What happens when the AI returns malformed JSON for quest generation? Parse failure is logged, no quests created, no crash
- What happens when the AI returns fewer than 3 quests? Accept whatever valid quests are returned (1 or 2), log that generation was partial
- What happens when the monthly cost cap is reached mid-week? All AI operations (coaching + quest generation) are blocked until next month. Quest completion continues normally (no AI needed)
- What happens when a quest has no domain set? Default to the player's weakest stat for XP routing
- What happens when a quest has base_xp = 0? Process normally but grant 0 XP (Gold reward may still be non-zero)
- What happens when the player has no active streaks? Applied Multiplier = 1.0 (no streak bonus)
- What happens when multiple quests are completed on the same day? Each is processed independently with its own Activity Log entry
- What happens when the AI generates a quest with an invalid difficulty? Map to "Medium" as default, log warning
- What happens when the Quests DB is empty? Quest engine returns early with no work to do
- Where are coaching briefings stored after generation? The coaching JSON is returned to the weekly automation caller. Weekly automation logs it via logger.py and optionally stores the latest briefing in Settings DB (LAST_COACHING_BRIEFING field) for dashboard display. Phase 6 engines produce the briefing; Phase 7 automation persists it; Phase 8 dashboard can display it from Settings DB

## Requirements *(mandatory)*

### Functional Requirements

**Quest Engine**

- **FR-001**: System MUST process quests with status "Completed" that have not yet been processed (Effective XP field is empty)
- **FR-002**: System MUST calculate Applied Multiplier using the highest streak tier from habits matching the quest's Domain (e.g., a STR quest uses the best STR-domain habit streak). If no domain-matched streaks exist, multiplier = 1.0
- **FR-003**: System MUST calculate Effective XP as `floor(base_xp * applied_multiplier)` and write it to the quest row
- **FR-004**: System MUST create an Activity Log entry for each processed quest with Effective XP routed to the quest's Domain stat
- **FR-005**: System MUST credit the quest's Gold Reward via coin_engine if Gold > 0
- **FR-006**: System MUST call xp_engine.update_character_stats() after processing quest completions
- **FR-007**: System MUST skip quests with status other than "Completed" (Available, In Progress, Failed)
- **FR-008**: System MUST be idempotent — quests with Effective XP already populated are skipped on re-run
- **FR-009**: System MUST handle quests with no domain by defaulting to the player's weakest stat

**AI Quest Generation**

- **FR-010**: System MUST generate exactly 3 quests per weekly generation cycle
- **FR-011**: System MUST provide the AI with current player stats, recent activity summary, active streaks, and quest completion rate as context
- **FR-012**: System MUST request structured JSON responses from the AI containing: title, narrative, domain, difficulty. The system then calculates base_xp and gold_reward from difficulty using QUEST_DIFFICULTY_REWARDS config (default: Easy=25xp/5g, Medium=50xp/10g, Hard=100xp/25g, Epic=200xp/50g)
- **FR-013**: System MUST validate AI-generated quest data before creating Quests DB rows (required fields present, difficulty in valid set [Easy/Medium/Hard/Epic], domain in valid set [STR/INT/WIS/VIT/CHA])
- **FR-014**: System MUST set generated quests with source="AI-Generated", status="Available", and due date = 7 days from generation. Manually-created quests have source="Manual" (or empty if created before Phase 6)
- **FR-015**: System MUST target at least one quest toward the player's weakest stat area (lowest current XP level) to encourage balanced progression. Ties are broken alphabetically (CHA > INT > STR > VIT > WIS)
- **FR-016**: System MUST gracefully handle AI failures (unreachable, timeout, malformed response) — log warning, create no quests, do not crash

**AI Coaching**

- **FR-017**: System MUST support 3 coaching personas rotating in round-robin order: Wartime CEO (direct, action-oriented) → Methodical Analyst (data-driven) → Quest Master (narrative, RPG-themed). The last-used persona is tracked in Settings DB to persist across runs
- **FR-018**: System MUST send weekly metrics to the selected persona and receive a structured briefing response
- **FR-019**: System MUST enforce a configurable monthly cost cap (default: $1.00 USD) on all AI API calls
- **FR-020**: System MUST track cumulative monthly AI spend and reject requests when the cap is reached
- **FR-021**: System MUST use structured JSON for all AI responses to ensure parseable output. The coaching briefing JSON schema MUST contain: `greeting` (string), `observations` (array of strings), `recommendations` (array of strings), `encouragement` (string). The quest generation JSON schema MUST contain: `quests` (array of objects, each with `title`, `narrative`, `domain`, `difficulty`)
- **FR-022**: System MUST limit AI response tokens to a configurable maximum (default: 1500 tokens) per call
- **FR-023**: System MUST log all AI interactions (prompt hash, tokens used, cost estimate, persona) for cost tracking

**Cost Controls**

- **FR-024**: System MUST read OPENAI_MODEL, OPENAI_MONTHLY_COST_CAP_USD, and OPENAI_MAX_TOKENS from Settings DB / config.py
- **FR-025**: System MUST calculate per-call cost estimate: `cost = (input_tokens * OPENAI_INPUT_PRICE_PER_1M + output_tokens * OPENAI_OUTPUT_PRICE_PER_1M) / 1_000_000`. Default (gpt-4o-mini): input=$0.15/1M, output=$0.60/1M
- **FR-026**: System MUST persist cumulative monthly spend as AI_MONTHLY_SPEND in the Settings DB (Notion), reset to 0 on the 1st of each month by monthly automation

### Key Entities

- **Quest**: A challenge assigned to the player with domain, difficulty, base XP, Gold reward, and status. Can be manually created or AI-generated. Effective XP is calculated at completion time.
- **Coaching Persona**: One of 3 predefined AI personality templates (Wartime CEO, Methodical Analyst, Quest Master) that shape the tone and focus of coaching briefings.
- **Weekly Metrics**: A snapshot of the player's trailing 7-day performance (stat deltas, streak counts, quest completion rate, HP/Gold/Coin changes) used as input for coaching and quest generation.
- **Cost Tracker**: A running total of monthly AI spend used to enforce the cost cap. Resets monthly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Quest completion correctly calculates Effective XP = floor(base_xp * streak_multiplier) and routes to the correct Domain stat via Activity Log
- **SC-002**: AI quest generation produces 3 valid quests with all required fields (title, narrative, domain, difficulty, base_xp, gold_reward, due date)
- **SC-003**: At least 1 of 3 generated quests targets the player's weakest stat, promoting balanced progression
- **SC-004**: Each coaching persona produces a distinctively voiced briefing when given the same metrics input
- **SC-005**: Monthly AI cost stays within the configured cap — system blocks calls when cap is reached
- **SC-006**: All quest engine operations are idempotent — re-running produces no duplicate Activity Log entries or double Gold credits
- **SC-007**: AI failures (network, timeout, malformed response) are handled gracefully with no crash, no partial data, and appropriate warning logs
- **SC-008**: All AI responses are structured JSON that can be parsed without error

## Assumptions

- Phases 1-5 are complete: config, notion_client, xp_engine, coin_engine, streak_engine, and all domain/reward engines are operational
- Quests DB exists with schema from Phase 1 (Quest Title, Narrative, Domain, Difficulty, Status, Base XP, Applied Multiplier, Effective XP, Gold Reward, Source, Due Date, Character)
- OpenAI API key is configured in `.env` (OPENAI_API_KEY)
- Model defaults to gpt-4o-mini (cost-effective for structured responses)
- Monthly cost cap is tracked in Settings DB (AI_MONTHLY_SPEND) and resets to 0 on the 1st of each month via monthly automation
- Last-used coaching persona is tracked in Settings DB (LAST_COACH_PERSONA) for round-robin rotation
- Quest XP/Gold rewards for AI-generated quests are system-calculated from difficulty via QUEST_DIFFICULTY_REWARDS config, not AI-determined
- Quest generation happens during weekly automation (Phase 7), but the engine is independently callable via CLI
- The 3 coaching personas are predefined system prompts, not dynamically generated

## Scope Boundaries

**In scope**: Quest completion processing + XP/Gold rewards, AI procedural quest generation (3 per week), multi-persona coaching briefings, cost tracking + monthly cap enforcement, structured JSON AI responses

**Out of scope**: Daily/weekly/monthly automation orchestration (Phase 7), dashboard display of coaching briefings (Phase 8), manual quest creation UI (Notion-native — player creates rows directly), quest failure penalties (quests fail silently — no XP loss), AI model fine-tuning, conversation history (each AI call is stateless)
