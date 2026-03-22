# Feature Specification: Phase 3 — XP Engine, Streaks & Leveling

**Feature Branch**: `003-xp-streaks-leveling`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Phase 3: XP Engine, Streaks and Leveling"

## Clarifications

### Session 2026-03-22

- Q: When a Goal or Task relates to multiple skills mapping to different stats, how should XP be distributed? → A: Split equally among stats (e.g., 10 XP across 2 stats = 5 each, floor on odd splits).
- Q: What counts as "today" for streak check-in purposes? → A: Calendar day midnight in player's local timezone (configured via Settings DB or .env).
- Q: Should streak decay also deduct XP as a penalty? → A: No XP penalty — losing the streak multiplier is the only consequence of a broken streak.
- Q: When does `update_character_stats()` run? → A: After every XP-granting event (real-time), not just during daily automation. Goal/task button completions trigger immediate stat recalculation.
- Q: Should rank changes trigger a special event? → A: Display only — rank updates silently on Character page, no Activity Log entry logged. Rank events deferred to Phase 5 (Achievements).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exponential XP Progression (Priority: P1)

Every action the player takes — checking in a good habit, completing a goal, finishing a
task — earns Experience Points (XP). XP accumulates per stat (STR, INT, WIS, VIT, CHA)
based on the domain of the activity. Each stat has its own level, calculated from an
exponential curve: `XP_required(n) = B * n^E + L * n` (defaults: B=1000, E=1.8, L=200).
The player's overall Level is the average of their 5 stat levels. The player sees their
current level, XP progress bar, and XP-to-next-level on their Character page in Notion.

**Why this priority**: XP is the core reward loop. Without it, the player has no sense
of growth or progression. Every other system (streaks, ranks, achievements) builds on
top of XP. This is the carrot to HP's stick.

**Independent Test**: Can be tested by granting XP to a stat and verifying the level
calculation matches the exponential formula. Delivers standalone value as a visible
progression system even without streaks or class bonuses.

**Acceptance Scenarios**:

1. **Given** a character with 0 STR XP, **When** the player checks in a gym habit that
   awards 5 XP in the STR domain, **Then** STR XP increases to 5 and STR Level remains
   1 (threshold not yet reached).
2. **Given** a character with 1195 STR XP (just below Level 2 threshold of 1200), **When**
   the player earns 10 more STR XP, **Then** STR Level increases from 1 to 2 and the
   progress bar resets to show progress toward Level 3.
3. **Given** a character with stat levels STR=3, INT=2, WIS=1, VIT=4, CHA=2, **When**
   the system recalculates Player Level, **Then** Player Level = 2 (average of 5 stat
   levels, rounded down).
4. **Given** XP earned from multiple sources (habits, goals, tasks) across different
   domains, **When** the system aggregates stat XP, **Then** each stat's XP total is
   the sum of all XP-granting Activity Log entries mapped to that stat's domain.
5. **Given** any level number, **When** XP required is calculated, **Then** the result
   matches the formula `B * n^E + L * n` using the values from the Settings DB (or
   defaults if Settings DB is unavailable).

---

### User Story 2 - Streak Tracking and Multipliers (Priority: P2)

When a player checks in a good habit on consecutive days, they build a streak. Streaks
advance through tiers — Bronze (3 days), Silver (7), Gold (14), Platinum (30),
Diamond (60), Mythic (100) — each granting a progressively higher XP multiplier (1.1x
to 3.0x). Missing a day resets the streak to zero and applies a decay penalty. The
Streak Tracker database shows the player's current streak, best streak, tier, and
multiplier for each habit.

**Why this priority**: Streaks create daily engagement. The fear of losing a streak is
one of the strongest behavioral motivators. Combined with XP multipliers, streaks
reward consistency with exponentially more XP over time, making long-term habits feel
increasingly valuable.

**Independent Test**: Can be tested by simulating consecutive check-ins and verifying
streak counts, tier assignments, and multiplier values. Delivers a visible streak
tracking system even without the XP engine integrated.

**Acceptance Scenarios**:

1. **Given** a habit with a current streak of 2, **When** the player checks in on
   day 3, **Then** the streak increases to 3 and the tier advances to Bronze (1.1x
   multiplier).
2. **Given** a habit with a 7-day streak (Silver tier, 1.25x), **When** the player
   misses a day, **Then** the streak resets to 0, the tier drops to None (1.0x), and
   a decay event is logged.
3. **Given** a habit with a current streak of 14 and a best streak of 14, **When** the
   player checks in on day 15, **Then** the current streak becomes 15 and the best
   streak updates to 15.
4. **Given** a habit with a best streak of 30, **When** the streak resets to 0, **Then**
   the best streak remains 30 (never decreases).
5. **Given** a habit with a 60-day streak (Diamond, 2.5x multiplier), **When** the
   player checks in and earns 5 base XP, **Then** the effective XP is 12 (5 * 2.5,
   rounded down to integer).

---

### User Story 3 - Daily Habit Processing (Priority: P3)

When the daily automation runs, the system reads all Activity Log entries for today,
identifies which habits were checked in, calculates XP for each (base XP * streak
multiplier), updates streak trackers, processes bad habit entries as HP damage via the
HP engine, and writes all stat XP totals back to the Character page. This is the core
daily loop that ties habits, streaks, XP, and HP together.

**Why this priority**: This is the orchestration layer that connects the individual
engines. Without daily processing, the player would have to manually trigger every
calculation. This automation makes the game "just work" — the player checks in habits,
and the system handles the rest.

**Independent Test**: Can be tested by creating mock Activity Log entries for a day and
running the daily processor, then verifying that streak counts, XP grants, HP damage,
and Character stats all updated correctly.

**Acceptance Scenarios**:

1. **Given** a player has checked in 3 good habits today, **When** daily processing
   runs, **Then** each habit's XP (base * streak multiplier) is calculated and the
   corresponding stat XP totals are updated on the Character page.
2. **Given** a player has logged 2 bad habits today, **When** daily processing runs,
   **Then** HP damage is applied for each via the HP engine and the Character's HP
   is updated.
3. **Given** a player did NOT check in a habit that was active, **When** daily
   processing runs, **Then** that habit's streak is reset to 0 and a decay event
   is recorded.
4. **Given** daily processing has already run for today, **When** it runs again,
   **Then** no duplicate XP or HP changes are created (idempotent).

---

### User Story 4 - Class Bonus and Stat Aggregation (Priority: P4)

Each character has a Class (Warrior, Mage, Rogue, Paladin, Ranger) that provides a
+10% XP bonus to the stat mapped to that class. When stat XP is aggregated from all
sources (habits, goals, tasks, quests), the class bonus is applied to the matching
stat before writing to the Character page. The player sees their total XP per stat,
stat levels, Player Level, and Total XP — all recalculated whenever stats are updated.

**Why this priority**: Class bonuses add strategic depth — the player's class choice
affects their progression rate in specific stats, encouraging them to lean into their
strengths or deliberately challenge themselves. Stat aggregation is the mechanism that
pulls XP from every source into a unified character sheet.

**Independent Test**: Can be tested by granting XP to a stat that matches a character's
class and verifying the 10% bonus is applied. Delivers personalized progression that
makes class selection meaningful.

**Acceptance Scenarios**:

1. **Given** a Warrior class character (STR gets +10%), **When** the system aggregates
   100 base STR XP, **Then** the final STR XP written to Character is 110.
2. **Given** a Warrior class character, **When** the system aggregates INT XP, **Then**
   no class bonus is applied (INT is not the Warrior's mapped stat).
3. **Given** a character with stat XPs aggregated from habits, goals, tasks, and quests,
   **When** the system recalculates, **Then** Total XP equals the sum of all 5 stat XPs
   and Player Level equals the average of the 5 stat levels (rounded down).
4. **Given** XP sources spanning multiple databases (Activity Log for habits, Goal
   completions, Brain Dump completions), **When** stat XP is aggregated, **Then** all
   sources contribute to the correct stat based on their domain mapping.

---

### User Story 5 - Visual Progress Display (Priority: P5)

The player's Character page displays visual progress indicators: an XP progress bar
per stat showing current XP / XP-to-next-level (e.g., `◾◾◾◽◽ 400/500 | LV 2`),
the Player Level, Total XP, and Current Rank. These are updated every time stats are
recalculated, giving the player an at-a-glance view of their progression.

**Why this priority**: Visualization makes abstract numbers feel tangible. Seeing a
progress bar creep toward the next level is more motivating than seeing a raw number.
This story completes the feedback loop — the player's actions produce visible, rewarding
changes on their character sheet.

**Independent Test**: Can be tested by setting specific XP values and verifying the
progress bar string matches the expected format with correct fill segments and numbers.

**Acceptance Scenarios**:

1. **Given** a stat with 400 XP out of 500 needed for the next level, **When** the
   progress bar is generated with 10 segments, **Then** the output is
   `◾◾◾◾◾◾◾◾◽◽ 400/500 | LV 2`.
2. **Given** a stat with 0 XP at Level 1, **When** the progress bar is generated,
   **Then** all segments are empty: `◽◽◽◽◽◽◽◽◽◽ 0/1200 | LV 1`.
3. **Given** a stat that just leveled up (XP exactly at threshold), **When** the
   progress bar is generated, **Then** it shows 0 progress toward the next level.

---

### Edge Cases

- What happens when a habit has no domain assigned (Domain field is empty/null)?
  → XP is not granted. The system logs a warning identifying the habit by name and
  skips it during XP processing. The habit still counts for streak tracking (streak
  increments) but produces 0 XP. The player can manually assign a Domain in Notion.
- What happens when the streak tier config is changed mid-streak?
  → The new tier thresholds take effect immediately. If the current streak count now
  qualifies for a different tier, the multiplier updates on the next processing run.
- What happens when a player earns XP in a stat that would push them past multiple
  levels at once?
  → The system correctly calculates the final level by iterating the cumulative XP
  formula. Multi-level jumps are allowed and all intermediate levels are counted.
- What happens when daily processing runs but no Activity Log entries exist for today?
  → For good habits: every active habit without a check-in today has its streak reset
  (decay applied). For bad habits: no damage applied. For XP: no new XP granted.
  Character stats are still recalculated (to pick up any corrections).
- What happens when a player changes their class?
  → The class bonus is recalculated on the next stat aggregation. Previous XP is NOT
  retroactively adjusted — only future aggregations use the new class bonus.
- What happens when the Settings DB changes the XP formula constants (B, E, L)?
  → Level thresholds recalculate on next run using the new constants. This can cause
  a player's displayed level to change without earning any new XP. Existing XP totals
  are not modified — only the interpretation of what level those totals represent.
- What happens when two habits in the same domain are both checked in on the same day?
  → Both contribute XP independently. Each habit has its own streak tracker. The XP
  from both is summed into the stat total for that domain.
- What happens when `apply_decay()` runs but the player is dead?
  → Streak decay still occurs (streaks are independent of death state). Death does not
  freeze streak tracking. (No XP penalty is applied on decay — only the multiplier
  is lost.)
- What happens when a player's rank changes (e.g., Peasant → Squire)?
  → Rank updates silently on the Character page as a display value. No Activity Log
  entry is created for rank changes in Phase 3. Rank-up events and notifications are
  deferred to Phase 5 (Achievements/Badges).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST calculate XP required for each level using the formula
  `XP_required(n) = B * n^E + L * n` where B, E, and L are read from the Settings DB
  (falling back to defaults B=1000, E=1.8, L=200).
- **FR-002**: The system MUST track XP per stat (STR, INT, WIS, VIT, CHA) by summing
  all XP-granting Activity Log entries mapped to each stat's domain. Domain-to-stat
  mapping is defined in config (e.g., gym→STR, learning→INT, finance→WIS,
  nutrition/habits/health→VIT, social/content/creativity/writing→CHA). When a Goal
  or Task relates to multiple skills mapping to different stats, the XP MUST be split
  equally among those stats (floor division; remainder XP is dropped).
- **FR-003**: The system MUST calculate each stat's level from its cumulative XP using
  the exponential formula. Player Level MUST equal the average of the 5 stat levels
  (rounded down to integer).
- **FR-004**: The system MUST track streaks per habit in the Streak Tracker database,
  incrementing on consecutive daily check-ins and resetting to 0 on a missed day.
  "Today" is defined as the calendar day in the player's local timezone (configured
  via Settings DB or .env). A check-in at 11:55 PM counts for that calendar day.
- **FR-005**: The system MUST assign streak tiers based on configurable thresholds
  (default: Bronze=3, Silver=7, Gold=14, Platinum=30, Diamond=60, Mythic=100) and
  apply the corresponding XP multiplier (default: 1.1x to 3.0x) to all XP earned
  from that habit.
- **FR-006**: The system MUST apply streak decay when a habit is missed: reset the
  streak count to 0, drop the tier to None, and log a decay event in the Activity Log.
  No XP penalty is applied on decay — losing the streak multiplier is the only
  consequence.
- **FR-007**: The system MUST track the best (all-time highest) streak per habit
  separately from the current streak. The best streak MUST never decrease.
- **FR-008**: The system MUST apply a class bonus of +10% XP to the stat mapped to
  the character's selected class (Warrior→STR, Mage→INT, Rogue→CHA, Paladin→VIT,
  Ranger→WIS). The bonus applies during stat aggregation, not at the point of earning.
- **FR-009**: The system MUST process all daily habit activity in a single idempotent
  pass: read today's Activity Log entries, calculate XP per habit (base * streak
  multiplier), update streaks, process bad habits as HP damage, and write stat totals
  to the Character page.
- **FR-010**: The system MUST generate visual progress bars in the format
  `◾◾◾◽◽ X/Y | LV Z` for each stat, showing current progress toward the next level.
- **FR-011**: The system MUST update the Character page with: all 5 stat XP totals,
  all 5 stat levels, Player Level (average), Total XP (sum), and Current Rank after
  every XP-granting event. `update_character_stats()` is called at the end of every
  engine invocation (CLI or automation) that grants XP. Notion buttons create Activity
  Log entries which are processed on the next engine run — stat updates occur when
  the engine processes those entries, not as a real-time push from Notion.
- **FR-012**: The system MUST support XP from multiple sources: good habit check-ins,
  goal completions, task/brain dump completions, and quest completions. All sources
  feed into the same per-stat XP totals.
- **FR-013**: Daily processing MUST be idempotent — running it twice for the same date
  MUST NOT produce duplicate XP grants, streak changes, or HP damage. The system MUST
  use date-based deduplication to detect already-processed entries.
- **FR-014**: All XP values MUST be integers. Fractional XP from multiplier calculations
  MUST be rounded down (floor).
- **FR-015**: The system MUST read all game balance constants (XP formula parameters,
  streak tier thresholds, streak multipliers, class bonus percentage, domain-to-stat
  mapping) from the Settings DB via config, with hardcoded defaults as fallback.

### Key Entities

- **Experience Points (XP)**: A numeric reward earned through positive actions (habits,
  goals, tasks, quests). Tracked per stat (STR/INT/WIS/VIT/CHA). Determines stat
  levels via an exponential curve. All XP values are integers.
- **Stat Level**: A derived value calculated from cumulative stat XP using the
  exponential formula. Each of the 5 stats has its own level. Player Level is the
  average of all 5 stat levels.
- **Streak**: A consecutive-day counter per habit. Advances through tiers that grant
  XP multipliers. Resets to 0 on a missed day. Best streak is tracked separately
  and never decreases.
- **Streak Tier**: A rank assigned to a streak based on its length (Bronze through
  Mythic). Each tier provides a specific XP multiplier applied to all XP earned
  from that habit.
- **Class Bonus**: A +10% XP modifier applied to one stat based on the character's
  chosen class. Affects aggregation, not individual XP events.
- **Domain**: A category tag on habits, goals, and tasks (e.g., gym, learning, finance)
  that maps to one of the 5 RPG stats. Determines which stat receives the XP.
- **Daily Processor**: The orchestration routine that ties together habit check-ins,
  streak tracking, XP calculation, HP damage from bad habits, and Character stat
  updates into a single idempotent daily pass.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: XP calculations match the exponential formula exactly for levels 1
  through 50 — verified by comparing engine output against a precomputed reference
  table for at least 10 level values.
- **SC-002**: Streak tiers advance and reset correctly across all 6 tier boundaries
  — verified by simulating streak sequences that cross each threshold (3, 7, 14,
  30, 60, 100 days) and checking tier/multiplier assignments.
- **SC-003**: XP multipliers from streaks produce correct effective XP (base * multiplier,
  rounded down) — verified by testing each tier's multiplier with at least 3 different
  base XP values.
- **SC-004**: Class bonus applies exactly +10% to the matching stat and 0% to all
  others — verified by testing all 5 class/stat combinations.
- **SC-005**: Daily processing is fully idempotent — verified by running it twice for
  the same date and confirming zero differences in XP totals, streak counts, HP values,
  and Character stats between the first and second run.
- **SC-006**: Player Level correctly reflects the average of 5 stat levels after
  mixed XP grants across all stats — verified by setting specific stat XPs, computing
  expected levels, and checking the Character page.
- **SC-007**: Visual progress bars render correctly at boundaries (0%, 50%, 100% fill)
  — verified by generating bars for at least 3 different XP/threshold combinations.

## Assumptions

- Phase 1 (Foundation) and Phase 2 (HP System, Death & Economy) are both complete.
  All 33 databases exist, `db_ids.json` is populated, seed data is loaded, and
  `hp_engine.py` / `coin_engine.py` are operational.
- The Activity Log database already contains the EXP columns (EXP + Habit, EXP + Goal,
  EXP + Tasks) from the Phase 1 database schema creation.
- Good Habit and Bad Habit databases already have Domain (Select) properties from
  Phase 1 schema.
- The Streak Tracker database exists from Phase 1 with Current Streak, Best Streak,
  Current Tier, Multiplier, Last Completed, and Habit relation properties.
- Notion buttons on Good Habit ("Check-in") and Bad Habit ("Crap, I did...") already
  create Activity Log entries. The engines read these entries — they do not create them.
- XP values are always integers. The exponential formula may produce floats but the
  result is always floored to an integer.
- The streak decay rate from config (default: 0.05) is available but not currently
  used for graduated decay — V5 uses binary reset (streak goes to 0 on miss). The
  config value is reserved for a potential future graduated decay system.
- Class-to-stat mapping: Warrior→STR, Mage→INT, Rogue→CHA, Paladin→VIT, Ranger→WIS.
  This mapping is stored in config, not hardcoded in the XP engine.
- Player timezone is configurable via Settings DB or `.env` (e.g.,
  `PLAYER_TIMEZONE=Asia/Tokyo`). Used for determining "today" in streak tracking and
  daily processing. Defaults to UTC if not set. System MUST validate against Python's
  `pytz.all_timezones`; invalid values cause a smoke test failure with message:
  "Invalid PLAYER_TIMEZONE: {value}".
- Rank changes are display-only in Phase 3. No Activity Log events or notifications
  for rank-ups. This will be handled by Phase 5 (Achievements).
