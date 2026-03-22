# Research: Phase 3 — XP Engine, Streaks & Leveling

**Date**: 2026-03-22
**Feature**: 003-xp-streaks-leveling

## R1: XP Aggregation Strategy — Multi-Source Sum with Equal Split

**Decision**: Stat XP is the sum of all XP-granting Activity Log entries mapped to that
stat's domain. When a Goal/Task relates to multiple skills mapping to different stats,
XP is split equally among those stats (floor division; remainder dropped). The Activity
Log is the single source of truth, consistent with Phase 2.
**Rationale**: All value flows through the Activity Log. Equal split avoids XP inflation
while fairly rewarding cross-domain activities. Floor division keeps all values as integers.
**Alternatives considered**: Full XP to each stat (inflationary), primary skill only
(ignores secondary domains), separate XP ledger per stat (breaks single-source principle).

## R2: Level Calculation — Iterative Threshold

**Decision**: `level_from_xp()` iterates from level 1 upward, accumulating XP thresholds
until cumulative XP exceeds the player's total. Handles multi-level jumps naturally.
**Rationale**: The exponential formula `B*n^E + L*n` has no closed-form inverse for
arbitrary E. Iteration is simple, correct, and fast for realistic level ranges (~50 max).
**Alternatives considered**: Binary search on precomputed table — premature optimization.
Analytical inverse — no closed form exists.

## R3: Streak Reset — Binary, No XP Penalty

**Decision**: Missing a day resets the streak to 0. No XP is deducted as a penalty —
losing the multiplier is the only consequence. The config value `STREAK_DECAY_RATE` is
preserved for future graduated decay but not used in V5.
**Rationale**: Losing a high multiplier (e.g., 3.0x → 1.0x) is already significant.
Adding XP penalties double-punishes and discourages re-engagement after a broken streak.
**Alternatives considered**: Fixed XP penalty (too punitive), percentage-based penalty
(complex, discouraging), graduated decay (harder to reason about).

## R4: Class Bonus Application — At Aggregation

**Decision**: The +10% class bonus is applied during `update_character_stats()`, not when
individual XP events are created. The bonus multiplies the total stat XP, not per-event.
**Rationale**: Applying per-event leaks class knowledge into every XP source. Applying
at aggregation keeps the bonus in one place and makes class changes take effect immediately
without reprocessing history.
**Alternatives considered**: Per-event application — requires every XP-granting code path
to know the character's class. Class changes would need historical reprocessing.

## R5: Daily Processing Idempotency — Date-Based Guard

**Decision**: XP grants check for existing XP entries for the same habit + date before
creating new ones. Stat recalculation is a pure re-sum (inherently idempotent).
**Rationale**: Consistent with Phase 2 patterns. Prevents double-counting on re-runs.
**Alternatives considered**: Processing flags on Activity Log entries — too many API writes.
Lock file alone — doesn't prevent double-run after lock release.

## R6: Streak Tracker Initialization — Lazy Creation

**Decision**: Streak Tracker rows are created on first check-in for a habit. No
pre-seeding required.
**Rationale**: Avoids requiring seed data for every habit. New player-added habits
automatically get streak tracking without migrations.
**Alternatives considered**: Pre-seeded in `seed_data.py` — breaks when player adds new
habits, requires migration for each addition.

## R7: Stat Recalculation Timing — Real-Time

**Decision**: `update_character_stats()` runs after every XP-granting event, including
Goal/Task button completions — not just during daily automation.
**Rationale**: Players expect immediate feedback when completing goals/tasks. Consistent
with Phase 2's real-time death detection pattern. Daily automation still runs the full
processing pass for streaks, but stat display is always current.
**Alternatives considered**: Daily-only (laggy UX — player completes goal but stats don't
update until 10 PM), daily + manual CLI command (partial solution, still not real-time).

## R8: Timezone-Aware Day Boundary

**Decision**: "Today" for streak and daily processing is the calendar day in the player's
local timezone, configured via `PLAYER_TIMEZONE` in Settings DB or `.env` (default: UTC).
**Rationale**: A player checking in at 11:55 PM should have that count for today, not
tomorrow. Timezone awareness prevents confusing streak breaks for late-night users.
**Alternatives considered**: UTC-only (timezone-unaware, confusing for non-UTC players),
automation-time cutoff (arbitrary, penalizes late check-ins).
