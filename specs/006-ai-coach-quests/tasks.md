# Tasks: OpenAI Cognitive Coach & Quest Engine

**Input**: Design documents from `/specs/006-ai-coach-quests/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md
**Task ID Range**: T501–T529 (Phase 6 — avoids collision with Phase 1: T001-T029, Phase 2: T101-T124, Phase 3: T201-T226, Phase 4: T301-T326, Phase 5: T401-T430)

**Organization**: Tasks grouped by user story. Quest Completion (US1) is the MVP — works without AI. AI Quest Generation (US2) and Weekly Coaching (US3) both depend on the shared cost tracker (Foundational phase). US2 and US3 can be built in parallel after the cost tracker is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1=Quest Completion, US2=AI Quest Generation, US3=Weekly Coaching)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Config + Dependencies)

**Purpose**: Add Phase 6 constants to config, install new dependency, seed Settings DB with AI-related settings

- [ ] T501 [P] Add Phase 6 constants to `tools/config.py`: QUEST_DIFFICULTY_REWARDS (Easy=25xp/5g, Medium=50xp/10g, Hard=100xp/25g, Epic=200xp/50g), OPENAI_MODEL ("gpt-4o-mini"), OPENAI_MONTHLY_COST_CAP_USD (1.00), OPENAI_MAX_TOKENS (1500). All readable from Settings DB with fallback defaults.
- [ ] T502 [P] Add `openai` to `requirements.txt`. Run `pip install openai`.
- [ ] T503 [P] Add Phase 6 Settings DB seed entries: AI_MONTHLY_SPEND=0, LAST_COACH_PERSONA="" (empty), OPENAI_MODEL="gpt-4o-mini", OPENAI_MONTHLY_COST_CAP_USD=1.00, OPENAI_MAX_TOKENS=1500. Add to `tools/seed_data.py` or equivalent seeding script.

**Checkpoint**: Config updated, dependency installed, Settings DB ready — all four tools can proceed.

---

## Phase 2: Foundational — AI Cost Tracker (Blocking Prerequisite)

**Purpose**: Shared cost tracking and budget enforcement that MUST be complete before any AI tool (US2, US3) can be implemented. US1 (Quest Completion) has no AI dependency and can be built in parallel with this phase.

**⚠️ CRITICAL**: AI Quest Generation (US2) and Weekly Coaching (US3) cannot begin until this phase is complete.

### Implementation

- [ ] T504 [P] Implement `estimate_cost(input_tokens, output_tokens, model)` in `tools/ai_cost_tracker.py` — pure math: calculate USD cost from token counts using MODEL_PRICING dict (gpt-4o-mini: $0.15/1M input, $0.60/1M output). Return float.
- [ ] T505 [P] Implement `get_monthly_spend()` in `tools/ai_cost_tracker.py` — read AI_MONTHLY_SPEND from Settings DB via notion_client. Return 0.0 if not set.
- [ ] T506 Implement `check_budget(estimated_input_tokens, max_output_tokens, model)` in `tools/ai_cost_tracker.py` — call estimate_cost() for worst-case, read get_monthly_spend(), compare against OPENAI_MONTHLY_COST_CAP_USD from config. Return True if within budget, False + log warning if cap would be exceeded. (Depends on T504, T505)
- [ ] T507 Implement `record_spend(usage, model, prompt_hash=None)` in `tools/ai_cost_tracker.py` — calculate actual cost from usage.prompt_tokens + usage.completion_tokens via estimate_cost(), read current spend via get_monthly_spend(), write incremented AI_MONTHLY_SPEND back to Settings DB. Log cost details (model, tokens, cost, prompt_hash) per FR-023. Return cost float. (Depends on T504, T505)
- [ ] T508 Write `tests/test_ai_cost_tracker.py` — test cases: cost estimation math (known token counts → expected USD), budget check passes when under cap, budget check rejects when at/over cap, spend recording increments correctly, edge case: cap = 0 blocks all calls, edge case: missing Settings DB key defaults to 0.

**Checkpoint**: Cost tracker ready — AI tools can now integrate budget enforcement.

---

## Phase 3: User Story 1 — Quest Completion & XP Rewards (Priority: P1) 🎯 MVP

**Goal**: Process completed quests: apply domain-matched streak multiplier, calculate Effective XP, create Activity Log entry for stat routing, credit Gold via coin_engine. No AI dependency — works even when OpenAI is unreachable.

**Independent Test**: Manually create a quest in Quests DB (domain=STR, difficulty=Medium, base_xp=50, gold_reward=10, status=Completed), run quest engine, verify Activity Log entry with Effective XP (base × multiplier) mapped to STR, Gold credited, quest row updated with Applied Multiplier and Effective XP. Re-run and verify no duplicates.

### Implementation for User Story 1

- [ ] T509 [P] [US1] Implement `get_weakest_stat(character_id)` in `tools/quest_engine.py` — read STR/INT/WIS/VIT/CHA XP from Character DB, return stat name with lowest XP. Alphabetical tie-breaking (CHA < INT < STR < VIT < WIS).
- [ ] T510 [P] [US1] Implement `get_domain_streak_multiplier(character_id, domain)` in `tools/quest_engine.py` — query Streak Tracker DB filtered by Domain matching the given domain, return highest Multiplier value. Return 1.0 if no matches or domain is None.
- [ ] T511 [P] [US1] Implement `get_pending_quests(character_id)` in `tools/quest_engine.py` — query Quests DB for rows where Status="Completed" AND Effective XP is empty (null/0), filtered by Character relation. Return list of quest dicts.
- [ ] T512 [US1] Implement `process_quest_completion(character_id, quest)` in `tools/quest_engine.py` — resolve domain (quest.domain or get_weakest_stat()), get multiplier via get_domain_streak_multiplier(), calculate Effective XP = floor(base_xp × multiplier), write Applied Multiplier + Effective XP to quest row, create Activity Log entry (Type=QUEST, domain XP), credit Gold via coin_engine if gold_reward > 0. Return result dict. (Depends on T509, T510)
- [ ] T513 [US1] Implement `process_all_quests(character_id)` in `tools/quest_engine.py` — call get_pending_quests(), iterate with process_quest_completion(), call xp_engine.update_character_stats() if any processed. Return summary `{processed, total_xp, total_gold, quests}`. (Depends on T511, T512)
- [ ] T514 [US1] Add CLI entry point to `tools/quest_engine.py` — `if __name__ == "__main__"` block with `--character-id` argument, calls process_all_quests(), prints summary.
- [ ] T515 [US1] Write `tests/test_quest_engine.py` — test cases: no-streak multiplier defaults to 1.0, streak Gold-tier multiplier 1.5x applied correctly (100 × 1.5 = 150), Effective XP uses floor(), idempotency (quest with Effective XP already set is skipped), domain-less quest defaults to weakest stat, status != Completed is skipped, Gold credited via coin_engine mock, Activity Log entry created with correct Type=QUEST and domain, multiple quests processed independently.

**Checkpoint**: Quest completion fully functional. Run quickstart steps 1-5 to verify. At this point, manually created quests can be completed with full XP/Gold rewards — the core gameplay loop works.

---

## Phase 4: User Story 2 — AI Procedural Quest Generation (Priority: P1)

**Goal**: Generate 3 personalized AI quests per week based on player stats, streaks, and weak areas. AI picks title/narrative/domain/difficulty; system calculates XP/Gold from difficulty. Quests created in Quests DB with source="AI-Generated".

**Independent Test**: Run quest generation for a character with STR=10, INT=3. Verify 3 quests created in Quests DB, at least one targeting INT (weakest), each with narrative, difficulty, base_xp, gold_reward, due date within 7 days, source="AI-Generated".

**Depends on**: Phase 2 (ai_cost_tracker), Phase 3 T509 (get_weakest_stat — reused for FR-015)

### Implementation for User Story 2

- [ ] T516 [P] [US2] Implement `build_generation_context(character_id)` in `tools/quest_generator.py` — gather: Character DB (5 stat XPs, stat levels, player level, rank), Streak Tracker (active streaks with domain/days/tier), Quests DB (recent completion count, current available count), weakest stat via quest_engine.get_weakest_stat(). Return context dict matching data-model.md schema.
- [ ] T517 [P] [US2] Implement `validate_quest(quest_data, weakest_stat)` in `tools/quest_generator.py` — validate title (non-empty), narrative (non-empty), domain (in {STR,INT,WIS,VIT,CHA} or default to weakest_stat + log warning), difficulty (in {Easy,Medium,Hard,Epic} or default to "Medium" + log warning). Return validated dict or None if title/narrative missing.
- [ ] T518 [US2] Implement `generate_quests(character_id)` in `tools/quest_generator.py` — check budget via ai_cost_tracker.check_budget(), build context via build_generation_context(), construct system prompt instructing AI to return JSON with 3 quests targeting weakest area, call OpenAI with response_format={"type": "json_object"} and max_tokens from config, record spend via ai_cost_tracker.record_spend(), parse JSON, validate each quest via validate_quest(), for each valid quest: look up base_xp/gold_reward from QUEST_DIFFICULTY_REWARDS[difficulty], create Quests DB row (status=Available, source=AI-Generated, due=today+7d). Return summary. Return None + warning on budget cap or API failure. (Depends on T516, T517, Phase 2 T506-T507)
- [ ] T519 [US2] Add CLI entry point to `tools/quest_generator.py` — `--character-id` argument, calls generate_quests(), prints summary with created quest titles.
- [ ] T520 [US2] Write `tests/test_quest_generator.py` — test cases: context building includes all required fields, valid AI response parsed into 3 quests, invalid domain defaults to weakest stat, invalid difficulty defaults to Medium, missing title → quest rejected, partial response (1-2 quests) accepted with log, malformed JSON → no quests created + warning, API failure → graceful return None, budget exceeded → no API call made, base_xp/gold_reward correctly looked up from difficulty, due date = today + 7 days. Use mocked OpenAI responses.

**Checkpoint**: AI quest generation complete. Run quickstart steps 6-8 to verify.

---

## Phase 5: User Story 3 — Weekly Coaching Briefing (Priority: P2)

**Goal**: Generate personalized weekly coaching briefings using 3 rotating AI personas (Wartime CEO, Methodical Analyst, Quest Master). Each persona produces a structured response with observations, recommendations, and encouragement in a distinctive voice.

**Independent Test**: Run coaching engine with each persona in sequence. Verify each produces structured JSON response with observations/recommendations/encouragement. Verify persona rotation persists in Settings DB. Verify cost cap blocks calls when reached.

**Depends on**: Phase 2 (ai_cost_tracker)

### Implementation for User Story 3

- [ ] T521 [P] [US3] Define PERSONAS dict and ROTATION_ORDER list in `tools/coaching_engine.py` — three entries: "wartime_ceo" (direct, action-oriented, calls out weaknesses), "methodical_analyst" (data-driven, pattern analysis, trend observation), "quest_master" (RPG narrative, hero's journey, quest framing). Each has name + system_prompt string constant. ROTATION_ORDER = ["wartime_ceo", "methodical_analyst", "quest_master"].
- [ ] T522 [US3] Implement `get_next_persona()` in `tools/coaching_engine.py` — read LAST_COACH_PERSONA from Settings DB, find index in ROTATION_ORDER, return next (wrap around). If empty or invalid, return first persona. (Depends on T521)
- [ ] T523 [P] [US3] Implement `build_coaching_context(character_id)` in `tools/coaching_engine.py` — gather: Character DB (current stats, HP, Gold, Coins, level, rank), Activity Log (7-day stat XP deltas per domain), Streak Tracker (active streaks + recently broken streaks), Quests DB (completed vs total this week). Return weekly metrics dict matching data-model.md schema.
- [ ] T524 [US3] Implement `generate_briefing(character_id)` in `tools/coaching_engine.py` — check budget via ai_cost_tracker.check_budget(), get next persona via get_next_persona(), build context via build_coaching_context(), construct prompt with persona system prompt + metrics as user message, call OpenAI with response_format={"type": "json_object"} and max_tokens from config, record spend via ai_cost_tracker.record_spend(), update LAST_COACH_PERSONA in Settings DB, parse and validate briefing JSON (greeting, observations, recommendations, encouragement), log briefing. Return `{persona, briefing, cost}`. Return None + warning on budget cap or API failure. (Depends on T522, T523, Phase 2 T506-T507)
- [ ] T525 [US3] Add CLI entry point to `tools/coaching_engine.py` — `--character-id` argument, calls generate_briefing(), prints formatted briefing with persona name.
- [ ] T526 [US3] Write `tests/test_coaching_engine.py` — test cases: persona rotation wartime→analyst→quest_master→wartime (wraps), empty LAST_COACH_PERSONA starts at wartime, context building includes all metric fields, valid briefing parsed with all 4 sections, API failure → graceful return None, budget exceeded → no API call, persona written to Settings DB after success, each persona system prompt produces distinctive response (mock). Use mocked OpenAI responses.

**Checkpoint**: Coaching engine complete. Run quickstart steps 9-10 to verify.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Shared test infrastructure, end-to-end validation, workflow integration

- [ ] T527 [P] Extend `tests/conftest.py` with Phase 6 mock fixtures — mock Quests DB responses (completed, in-progress, already-processed), mock Streak Tracker responses (domain-matched, no-match), mock OpenAI responses (valid quest JSON, valid briefing JSON, malformed JSON, API error), mock Settings DB responses (AI_MONTHLY_SPEND, LAST_COACH_PERSONA).
- [ ] T528 Run `quickstart.md` full validation — execute all 10 verification steps sequentially with a real Notion workspace (or mocked). Document any gaps or issues found.
- [ ] T529 Update `workflows/` if a quest/coaching workflow SOP is needed — document the weekly automation integration point (Phase 7 will call quest_generator.generate_quests + coaching_engine.generate_briefing + quest_engine.process_all_quests during weekly report).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1: T501-T503)**: No dependencies — can start immediately
- **Foundational (Phase 2: T504-T508)**: Depends on Setup (config needed for constants) — BLOCKS US2 and US3
- **US1 Quest Completion (Phase 3: T509-T515)**: Depends on Setup only — can be built IN PARALLEL with Phase 2 (no AI dependency)
- **US2 AI Quest Generation (Phase 4: T516-T520)**: Depends on Phase 2 (cost tracker) + Phase 3 T509 (get_weakest_stat reuse)
- **US3 Weekly Coaching (Phase 5: T521-T526)**: Depends on Phase 2 (cost tracker) only — can be built IN PARALLEL with US2
- **Polish (Phase 6: T527-T529)**: Depends on all previous phases complete

### User Story Dependencies

- **US1 (Quest Completion)**: Independent of all AI functionality. Can be completed as MVP. Only needs Phase 1 (config) + Phases 2-5 engines (xp_engine, coin_engine, streak_engine).
- **US2 (AI Quest Generation)**: Depends on cost tracker (Phase 2). Reuses quest_engine.get_weakest_stat() from US1.
- **US3 (Weekly Coaching)**: Depends on cost tracker (Phase 2). Fully independent of US1 and US2.

### Within Each User Story

- Pure functions (get_weakest_stat, estimate_cost, validate_quest) first — no Notion dependency, easy to unit test
- Notion-reading functions next (get_pending_quests, get_monthly_spend, build_context)
- Orchestrators last (process_all_quests, generate_quests, generate_briefing)
- CLI entry point after orchestrator
- Tests after all functions in the story are implemented

### Parallel Opportunities

- **Phase 1**: T501, T502, T503 can all run in parallel (different files)
- **Phase 2 + Phase 3**: Foundational cost tracker and Quest Completion can run in parallel (different files, no shared dependencies)
- **Phase 2 internals**: T504, T505 can run in parallel (independent functions)
- **Phase 3 internals**: T509, T510, T511 can run in parallel (independent functions)
- **Phase 4 + Phase 5**: AI Quest Generation and Weekly Coaching can run in parallel (different files, both depend only on Phase 2)
- **Phase 4 internals**: T516, T517 can run in parallel (independent functions)
- **Phase 5 internals**: T521, T523 can run in parallel (independent — personas definition vs context building)

---

## Parallel Example: Phase 2 + Phase 3 (Maximum Parallelism)

```text
# These two streams can execute simultaneously:

Stream A (Cost Tracker — Phase 2):
  T504: estimate_cost() in ai_cost_tracker.py
  T505: get_monthly_spend() in ai_cost_tracker.py
  T506: check_budget() in ai_cost_tracker.py (after T504, T505)
  T507: record_spend() in ai_cost_tracker.py (after T504, T505)
  T508: test_ai_cost_tracker.py

Stream B (Quest Completion — Phase 3):
  T509: get_weakest_stat() in quest_engine.py
  T510: get_domain_streak_multiplier() in quest_engine.py
  T511: get_pending_quests() in quest_engine.py
  T512: process_quest_completion() (after T509, T510)
  T513: process_all_quests() (after T511, T512)
  T514: CLI entry point
  T515: test_quest_engine.py
```

## Parallel Example: Phase 4 + Phase 5 (After Phase 2 Complete)

```text
# These two streams can execute simultaneously:

Stream A (AI Quest Generation — Phase 4):
  T516: build_generation_context() in quest_generator.py
  T517: validate_quest() in quest_generator.py
  T518: generate_quests() (after T516, T517)
  T519: CLI entry point
  T520: test_quest_generator.py

Stream B (Weekly Coaching — Phase 5):
  T521: PERSONAS + ROTATION_ORDER in coaching_engine.py
  T523: build_coaching_context() in coaching_engine.py
  T522: get_next_persona() (after T521)
  T524: generate_briefing() (after T522, T523)
  T525: CLI entry point
  T526: test_coaching_engine.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T501-T503)
2. Complete Phase 3: Quest Completion (T509-T515) — can skip Phase 2 entirely
3. **STOP and VALIDATE**: Run quickstart steps 1-5
4. At this point: players can create and complete quests with streak multipliers, XP routing, and Gold rewards. The core quest gameplay loop is functional.

### Incremental Delivery

1. Setup (Phase 1) → Config ready
2. Quest Completion (Phase 3) + Cost Tracker (Phase 2) in parallel → MVP + AI foundation ready
3. AI Quest Generation (Phase 4) → Personalized quests appear weekly
4. Weekly Coaching (Phase 5) → Motivational briefings complete the experience
5. Polish (Phase 6) → Shared fixtures, full validation

### Single Developer Flow

1. T501-T503 (Setup) — 30 min
2. T509-T515 (Quest Completion) — core gameplay loop first
3. T504-T508 (Cost Tracker) — enables AI tools
4. T516-T520 (AI Quest Generation) — adds AI quests
5. T521-T526 (Weekly Coaching) — adds coaching
6. T527-T529 (Polish) — cleanup and validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Quest Completion (US1) is deliberately AI-free — it works even if OpenAI is unreachable
- Cost tracker is in Foundational because both AI tools need it, but US1 doesn't
- Total: 29 tasks across 6 phases
- US1: 7 tasks, US2: 5 tasks, US3: 6 tasks, Setup: 3 tasks, Foundational: 5 tasks, Polish: 3 tasks
- Suggested MVP scope: Phase 1 + Phase 3 (Setup + Quest Completion) = 10 tasks
