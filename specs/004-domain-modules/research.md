# Research: Phase 4 — Domain Modules (Financial, Fitness & Nutrition Engines)

**Date**: 2026-03-22
**Feature**: 004-domain-modules

## R1: RPE-to-XP Weighting — Linear Scaling

**Decision**: Linear scaling: `set_xp = floor(base_xp * (RPE / 10))`. RPE 10 = 100% of base,
RPE 5 = 50%. Default RPE = 7 when not provided by player.
**Rationale**: Simple, predictable, easy to explain to the player. RPE 8 earns 80% — the
mapping is immediately intuitive. No lookup tables or complex curves needed.
**Alternatives considered**: Exponential `(RPE/10)^2` (too punitive at low RPE, unintuitive),
tiered brackets (arbitrary cutoffs, harder to test), flat XP per set (ignores effort entirely).

## R2: Base Set XP — Volume-Based with Exercise Modifier

**Decision**: `base_xp = floor(volume * exercise_base_modifier / 1000)` where
volume = weight x reps. The Exercise Dictionary's Base XP Modifier property scales XP by
exercise type (compound lifts have higher modifiers than isolation).
**Rationale**: Ties XP directly to physical effort — heavier weight and more reps always
earn more. The /1000 scaling keeps XP values in a reasonable single-digit to low-double-digit
range per set, consistent with habit XP (5 per check-in). Exercise modifier rewards compound
movements that train more muscle groups.
**Alternatives considered**: Flat per set (ignores volume difference between 50kg x 5 and
150kg x 10), difficulty-tiered (arbitrary categories, loses granularity).

## R3: Symmetric Adherence Score — Linear Formula

**Decision**: `adherence = max(0, 1 - abs(actual - target) / target)`. Produces a 0-1 score.
Over-eating by 20% and under-eating by 20% both produce 0.8. Score of 0 at 100%+ deviation.
**Rationale**: Simple, symmetric, no discontinuities. Maps directly to XP percentage. Player
can mentally calculate their score. Max(0, ...) prevents negative scores at extreme deviations.
**Alternatives considered**: Binary threshold (too harsh — 1.0 or 0.0), Gaussian bell curve
(more complex, harder to explain, diminishing returns close to target are unintuitive),
asymmetric scoring (over-eating penalized more than under — adds game design complexity
without clear benefit in V5).

## R4: Nutrition Streak Threshold — 3 Consecutive Days

**Decision**: The 1.15x nutrition streak multiplier activates after 3 consecutive adherent
days. An adherent day = adherence score >= (1 - MACRO_TOLERANCE_PCT / 100), i.e., >= 0.9
with default 10% tolerance.
**Rationale**: Aligns with the habit streak system where Bronze tier (first multiplier) also
activates at 3 days. Consistent thresholds across systems reduce cognitive load. 3 days is
attainable but still requires commitment — not so easy it's meaningless, not so hard it's
discouraging.
**Alternatives considered**: 2 days (too easy), 5 days (discouraging for beginners), 7 days
(full week — too long for first reward), tiered nutrition streaks (adds complexity —
deferred to future version if needed).

## R5: Income Source — Settings DB Single Value

**Decision**: Monthly income is read from `MONTHLY_INCOME` in the Settings DB. Same value
applies to every month until the player manually updates it. Default: 0 (no Treasury row
created if income is 0 and no expenses).
**Rationale**: Most players have a roughly stable monthly income. Per-month income entry
would require a new database or manual Treasury pre-population. A single config value is
consistent with how TDEE and other player parameters are stored. The player can update it
at any time and the next monthly run uses the new value.
**Alternatives considered**: Income per Treasury row (requires manual pre-population each
month), separate Income Log database (overkill for a single monthly value), no income
tracking at all (loses Gold conversion for the overall surplus picture).

## R6: Progressive Overload Window — Configurable Default 14 Days

**Decision**: `OVERLOAD_WINDOW_DAYS = 14` configurable via Settings DB. The fitness engine
compares current 1RM against the best 1RM for the same exercise within this rolling window.
**Rationale**: 14 days captures 2-3 sessions per muscle group for typical training splits
(push/pull/legs, upper/lower). Too short (7 days) might miss the comparison session if
training frequency varies. Too long (30+ days) would compare against stale data that doesn't
reflect current capacity.
**Alternatives considered**: Fixed 7-day window (misses sessions for 3-4 day splits),
30-day window (comparison becomes meaningless — too much variance), all-time comparison
(would eventually make overload impossible as lifetime PR diverges from working sets).

## R7: Financial Engine Timing — Complete Months Only

**Decision**: The financial engine only processes complete months. It runs during monthly
automation (1st of month, processing the previous month). Mid-month triggers are no-ops.
**Rationale**: Partial month data would produce misleading surplus/deficit numbers. A player
who spent $50 on day 1 of a $500 budget category would show $450 surplus — meaningless.
Monthly processing aligns with how budgets are naturally structured.
**Alternatives considered**: Real-time surplus updates (misleading partial data), weekly
partial calculations (over-complex for marginal benefit), daily budget tracking (too
granular, doesn't match monthly budgeting mental model).
