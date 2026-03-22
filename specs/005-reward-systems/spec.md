# Feature Specification: Reward Systems — Loot Box, Achievement, Rank & Radar Chart

**Feature Branch**: `005-reward-systems`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Phase 5 of V5 Implementation Plan — Loot Box Engine with Pity Timer, Achievement Engine (43 badges), Rank Engine with Avatar Renderer, Coded Radar Chart Renderer

## Clarifications

### Session 2026-03-22

- Q: What do loot box rewards contain? → A: Coin bonuses scaled by rarity (Common=25, Rare=75, Epic=200, Legendary=1000 Coins)
- Q: How are achievement conditions evaluated? → A: Hardcoded checker functions — a dispatch map of condition_key → Python function, each querying the relevant DB
- Q: Can rank go down (demotion)? → A: High-water mark — rank never decreases, even if Total XP drops below the threshold
- Q: Which stat does achievement XP route to? → A: Domain-routed — each achievement's XP bonus goes to its Domain stat (e.g., fitness badge → STR)
- Q: How does the player trigger a loot box open? → A: CLI command — `python tools/loot_box.py --character-id <ID>` (consistent with other WAT tools)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Rank Progression & Visual Identity (Priority: P1)

The player progresses through rank tiers (Peasant → Squire → Knight → Champion → Hero → Legend → Mythic) based on their Total XP. When a rank-up occurs, the system generates a new avatar frame compositing the player's profile picture with a rank-specific border, uploads the image to a hosting service, and updates the Character record with the new rank and avatar URL. The player sees their current rank reflected in the Character DB and their avatar updated with the corresponding rank frame.

**Why this priority**: Rank is the most visible progression indicator. It provides immediate feedback on overall effort across all stats and activities. It also feeds into the radar chart title and dashboard display. Other reward systems (achievements, loot boxes) reference rank for display.

**Independent Test**: Manually set a character's Total XP to cross a rank threshold (e.g., 1000 for Squire), run the rank engine, verify the Character DB rank field updates, an avatar frame is composited and uploaded, and the Avatar URL is written back.

**Acceptance Scenarios**:

1. **Given** a character with 999 Total XP (Peasant), **When** XP increases to 1000, **Then** rank updates to "Squire", a new avatar with the Squire frame is generated and uploaded, and Avatar URL is updated in Character DB
2. **Given** a character with 5000 Total XP (Knight), **When** rank engine runs, **Then** no rank change occurs and no new avatar is generated (idempotent)
3. **Given** a character with no profile picture set, **When** rank-up occurs, **Then** a default placeholder avatar is used with the rank frame

---

### User Story 2 — Stat Radar Chart Visualization (Priority: P1)

The player's 5-stat profile (STR, INT, WIS, VIT, CHA) is visualized as a radar/spider chart. The chart is generated as an 800x800 PNG image with a dark theme, uploaded to a hosting service, and the URL is written to the Character DB. The chart regenerates whenever stats change (typically during daily automation) so the player always sees their current stat balance.

**Why this priority**: The radar chart is the primary visual representation of the player's RPG stat balance — it's the "character sheet" visual. It's also zero-cost (code-generated), making it an easy high-impact win. It runs independently of loot/achievements and feeds into the dashboard.

**Independent Test**: Create a character with known stat levels (e.g., STR=5, INT=3, WIS=7, VIT=4, CHA=2), run the chart renderer, verify a PNG is generated with correct dimensions (800x800), 5 labeled axes, correct level values at vertices, and the image uploads successfully.

**Acceptance Scenarios**:

1. **Given** a character with stat levels STR=5, INT=3, WIS=7, VIT=4, CHA=2, **When** chart renderer runs, **Then** an 800x800 PNG is generated with 5 labeled axes, filled polygon reflecting relative stat values, player name + rank as title, and the URL is written to Radar Chart URL in Character DB
2. **Given** all stats at level 0, **When** chart renderer runs, **Then** chart generates with a collapsed polygon at center (no error)
3. **Given** chart already generated for current stat values, **When** chart renderer runs again with same values, **Then** chart is regenerated (overwrite is acceptable — charts are cheap to produce)

---

### User Story 3 — Achievement Badges (Priority: P2)

The system tracks 43 predefined achievements across all domains (fitness, finance, nutrition, habits, economy, rank, streaks). Each achievement has a condition key, description, XP bonus, and domain mapping. When a player meets an achievement condition, the system creates a Player Achievement record (linking achievement to character with unlock date) and grants the XP bonus via an Activity Log entry. Achievements are checked during daily automation.

**Why this priority**: Achievements add long-term motivation and milestone celebration but are not required for core stat progression. They depend on all domain engines being operational (Phases 2-4) to detect conditions. P2 because the player can already progress through stats and ranks without achievements.

**Independent Test**: Seed the Achievements DB with a test badge (e.g., "First Blood" — complete 1 workout), create a character with 1 completed workout session, run the achievement engine, verify a Player Achievement record is created and an Activity Log entry grants the XP bonus.

**Acceptance Scenarios**:

1. **Given** a character who has completed their first workout, **When** achievement engine checks conditions, **Then** "First Blood" (or equivalent first-workout badge) is unlocked, a Player Achievement row is created with today's date, and an Activity Log entry grants the XP bonus
2. **Given** a character who has already unlocked "First Blood", **When** achievement engine runs again, **Then** no duplicate Player Achievement is created (idempotent)
3. **Given** a character who meets multiple achievement conditions simultaneously, **When** achievement engine runs, **Then** all qualifying achievements are unlocked in a single run, each with its own Player Achievement row and Activity Log entry

---

### User Story 4 — Loot Box Rewards (Priority: P3)

The player spends Gold to open loot boxes via CLI command. Each loot box costs a fixed amount (default: 100 Gold) and produces a Coin reward with a weighted random rarity: Common (70%) = 25 Coins, Rare (20%) = 75 Coins, Epic (8%) = 200 Coins, Legendary (2%) = 1000 Coins. A pity timer ensures that after a configurable number of consecutive non-Legendary pulls (default: 50), the next pull is guaranteed Legendary. Rewards are recorded in the Loot Box Inventory DB. The pity counter is tracked on the Character record. This creates a Gold-to-Coins conversion loop — Gold is earned from financial surplus, spent on loot boxes, and Coins are the output.

**Why this priority**: Loot boxes are the Gold sink — they give earned Gold a purpose. However, Gold earning (Phase 4 financial engine) and the core progression loop work without loot boxes. This is the "fun reward" layer, not a progression requirement. P3 because the player experience is complete without it.

**Independent Test**: Give a character 200 Gold, open 2 loot boxes, verify Gold is deducted (via coin_engine), rarity distribution follows weights over many samples, Loot Box Inventory rows are created, and pity counter increments/resets appropriately.

**Acceptance Scenarios**:

1. **Given** a character with 100+ Gold, **When** player runs `python tools/loot_box.py --character-id <ID>`, **Then** Gold is deducted by LOOT_COST (100), a weighted random rarity is selected, Coins are awarded (Common=25, Rare=75, Epic=200, Legendary=1000), a Loot Box Inventory row is created, and pity counter increments by 1
2. **Given** a character with less than 100 Gold, **When** player attempts to open a loot box, **Then** the action is rejected with an insufficient Gold message
3. **Given** a character whose pity counter equals PITY_TIMER_THRESHOLD (50), **When** player opens a loot box, **Then** the reward is guaranteed Legendary regardless of RNG, and pity counter resets to 0
4. **Given** a character opens a loot box and receives a Legendary reward before hitting the pity threshold, **When** the rarity is determined, **Then** pity counter resets to 0

---

### Edge Cases

- What happens when a character has exactly 0 Total XP? Rank = "Peasant" (lowest tier), no avatar frame applied (or default/no-frame version)
- What happens when rank thresholds are updated in config after a character already has a rank? Rank engine re-evaluates from Total XP on next run but only promotes — rank is a high-water mark and never demotes
- What happens when the image hosting service (Cloudinary) is unreachable? Avatar/chart generation should complete locally, upload failure is logged as warning, Character DB URL is not updated (retried on next run)
- What happens when the Achievements DB has no seeded achievements? Achievement engine returns early with no work to do
- What happens when the player opens a loot box during a race condition (concurrent requests)? Single-player system — not applicable. Sequential processing only
- What happens when all 43 achievements are already unlocked? Achievement engine skips all conditions checks — no new Player Achievements created
- What happens when a character has no stat XP at all (all 0)? Radar chart generates with collapsed polygon at center, rank stays Peasant
- What happens when the profile picture file is missing or corrupt? Avatar renderer uses a default placeholder image
- What happens when rarity weights don't sum to 100? Rarity weights are relative
  proportions. System converts to probabilities: `probability = weight / sum(all weights)`.
  Example: weights [70, 20, 8, 2] (sum=100) → [0.70, 0.20, 0.08, 0.02].
  Weights [700, 200, 80, 20] produce identical probabilities
- What happens when LOOT_COST is set to 0 in config? Loot box is free — no Gold deducted, pity timer still operates normally

## Requirements *(mandatory)*

### Functional Requirements

**Rank Engine**

- **FR-001**: System MUST determine player rank from Total XP using configurable thresholds: 0=Peasant, 1000=Squire, 5000=Knight, 15000=Champion, 40000=Hero, 100000=Legend, 250000=Mythic. Rank always reflects the current Total XP tier; if thresholds change in config, ranks are recalculated on the next run. Rank can only move upward — once a tier is reached, it is never demoted even if XP is somehow reduced
- **FR-002**: System MUST detect rank-up by comparing calculated rank against current Character DB rank. If calculated rank is higher, update. If lower or equal, no change (high-water mark)
- **FR-003**: System MUST update the Character DB Current Rank field when a rank change is detected
- **FR-004**: System MUST be callable from daily automation to check for rank-ups after stat recalculation

**Avatar Renderer**

- **FR-005**: System MUST composite the player's profile picture with a rank-specific frame overlay to produce a combined avatar image
- **FR-006**: System MUST upload the generated avatar image to an image hosting service and return the hosted URL
- **FR-007**: System MUST write the hosted avatar URL to the Character DB Avatar URL field
- **FR-008**: System MUST use a default placeholder when no profile picture is available

**Radar Chart Renderer**

- **FR-009**: System MUST generate a 5-axis radar chart from the player's stat levels (STR, INT, WIS, VIT, CHA)
- **FR-010**: System MUST render the chart as an 800x800 PNG with a dark background, neon accent polygon, labeled axes with stat names, and level values at vertices
- **FR-011**: System MUST include the player's name and current rank as the chart title
- **FR-012**: System MUST upload the chart image to an image hosting service and write the URL to Character DB Radar Chart URL field
- **FR-013**: System MUST handle all-zero stats without error, producing a valid chart with a collapsed center polygon

**Achievement Engine**

- **FR-014**: System MUST store achievement definitions with: Badge Name, Description, Condition Key (machine-readable identifier), XP Bonus, Domain (maps to stat), and Icon URL
- **FR-015**: System MUST evaluate all achievement conditions using hardcoded checker functions dispatched by condition key (e.g., `{"first_workout": check_first_workout, ...}`). Each checker queries the relevant database to determine if the condition is met
- **FR-016**: System MUST create a Player Achievement record linking the achievement to the character with the unlock date
- **FR-017**: System MUST create an Activity Log entry for each newly unlocked achievement granting the defined XP bonus, routed to the achievement's Domain stat (e.g., a fitness achievement grants STR XP, a finance achievement grants WIS XP)
- **FR-018**: System MUST skip achievements the player has already unlocked (idempotent — no duplicate Player Achievement rows)
- **FR-019**: System MUST call xp_engine.update_character_stats() after granting achievement XP to update stat totals

**Loot Box Engine**

- **FR-020**: System MUST select a random rarity using configured weights (default: Common=70, Rare=20, Epic=8, Legendary=2) and award Coins by rarity tier (default: Common=25, Rare=75, Epic=200, Legendary=1000)
- **FR-021**: System MUST deduct LOOT_COST (default: 100) Gold from the player's balance before generating a reward
- **FR-022**: System MUST reject loot box opens when the player has insufficient Gold
- **FR-023**: System MUST increment the Character DB pity counter by 1 after each non-Legendary pull
- **FR-024**: System MUST guarantee a Legendary reward when pity counter reaches PITY_TIMER_THRESHOLD (default: 50)
- **FR-025**: System MUST reset pity counter to 0 whenever a Legendary reward is obtained (whether by RNG or pity)
- **FR-026**: System MUST create a Loot Box Inventory row recording the reward name, rarity, Coin reward amount, Gold cost, claimed status, date, and character link
- **FR-027**: System MUST use coin_engine for both Gold deduction and Coin crediting to maintain consistent balance tracking
- **FR-028**: System MUST be invocable via CLI command consistent with other WAT tools

### Key Entities

- **Rank Tier**: A named progression level (Peasant through Mythic) with a minimum Total XP threshold. Determines avatar frame and title display.
- **Avatar Frame**: A rank-specific image overlay composited with the player's profile picture. Stored as PNG assets per rank tier.
- **Radar Chart**: A generated 5-axis visualization of the player's stat levels. Regenerated on stat changes.
- **Achievement**: A predefined badge with a condition key, description, XP bonus, and domain. 43 total across all game domains.
- **Player Achievement**: A junction record linking an unlocked achievement to a character with the date of unlock. Prevents duplicate unlocks.
- **Loot Box Inventory Item**: A record of a purchased loot box reward with rarity, Gold cost, and timestamp. Linked to character.
- **Pity Counter**: A per-character counter tracking consecutive non-Legendary loot box pulls. Resets on any Legendary pull.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rank correctly maps Total XP to the appropriate tier across all 7 thresholds (verified by testing boundary values: 0, 999, 1000, 4999, 5000, etc.)
- **SC-002**: Avatar frame compositing produces a valid image file with both the profile picture and rank border visible
- **SC-003**: Radar chart generates an 800x800 PNG with exactly 5 labeled axes and values matching the character's stat levels
- **SC-004**: Loot box rarity distribution matches configured weights within ±5% tolerance over 10,000 samples
- **SC-005**: Pity timer guarantees a Legendary reward after exactly 50 consecutive non-Legendary pulls (counter starts at 0, increments to 50; the pull when counter equals PITY_TIMER_THRESHOLD is guaranteed Legendary)
- **SC-006**: Achievement engine detects and unlocks all qualifying badges in a single run without duplicating previously unlocked achievements
- **SC-007**: All reward system operations are idempotent — re-running rank check, achievement check, or chart generation produces no duplicate records or incorrect state
- **SC-008**: Loot box correctly rejects purchase when Gold balance is below LOOT_COST
- **SC-009**: All XP bonuses from achievements flow through Activity Log entries and are correctly aggregated by xp_engine into the appropriate stat

## Assumptions

- Phases 1-4 are complete: config, notion_client, xp_engine, coin_engine, and all three domain engines are operational
- Character DB already has Total XP, Current Rank, Avatar URL, Radar Chart URL, and Pity Counter fields
- Loot Box Inventory, Achievements, and Player Achievements databases exist (created in Phase 1 seed_data)
- Achievement definitions (43 badges) are seeded in the Achievements DB during Phase 1
- Rank frame PNG assets exist in `assets/frames/` (one per rank tier)
- Image hosting service (Cloudinary) credentials are configured in `.env`
- The system is single-player — no concurrent access concerns
- All balance constants (LOOT_WEIGHTS, LOOT_COST, PITY_TIMER_THRESHOLD, RANK_THRESHOLDS) are readable from Settings DB with fallback defaults in config.py

## Scope Boundaries

**In scope**: Rank calculation + avatar rendering, radar chart generation + upload, achievement condition checking + XP granting, loot box RNG + pity timer + Gold deduction + inventory recording

**Out of scope**: Quest engine (Phase 6), OpenAI coaching (Phase 6), daily/monthly automation orchestration (Phase 7), dashboard layout (Phase 8), new Notion database creation (Phase 1), achievement badge icon design (asset creation, not code)
