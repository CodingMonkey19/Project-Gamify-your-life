# Research: Phase 2 — HP System, Death & Economy

**Date**: 2026-03-22
**Feature**: 002-hp-death-economy

## R1: HP Calculation Model — Activity Log Sum

**Decision**: HP = sum of all HP entries in Activity Log. No implicit offset.
Character creation and respawn create explicit positive-HP entries.
**Rationale**: Pure sum is simplest. Every HP change is auditable. No special cases.
**Alternatives considered**: Implicit offset (Starting HP + sum of changes) — adds
special case to every HP query, makes Activity Log incomplete as a ledger.

## R2: Coin Balance Model — Pure Read

**Decision**: Coin balance = sum of all coin columns in Activity Log. Notion buttons
write coin values at the moment of action. Engine just sums.
**Rationale**: Buttons are canonical input (Constitution Principle I). Coins exist
in the log the instant the button is pressed.
**Alternatives considered**: Processing/confirmation step — no benefit, adds complexity.

## R3: Death Detection — Real-Time

**Decision**: Death checked immediately after every HP-changing event.
**Rationale**: Immediate feedback is core RPG experience. "You Died!" should appear
right after the fatal bad habit, not hours later.
**Alternatives considered**: Daily-only — breaks immersion, allows ghost actions.

## R4: Dead State — Partial Lockdown

**Decision**: Dead players can log bad habits (damage stacks) and earn coins. Spending
blocked (Market, Hotel, Black Market). Only one death event per death.
**Rationale**: Stacking damage increases respawn debt. Blocking spending prevents
hotel self-revival bypass. Earning while dead allows overdraft recovery.
**Alternatives considered**: Full lockdown (too punitive), no restrictions (exploitable).

## R5: Respawn Guard

**Decision**: Respawn while alive = no-op. Clear checkbox, log notice.
**Rationale**: Respawn is death recovery, not a free heal.
**Alternatives considered**: Allow always (trivializes HP system).

## R6: Overdraft Penalty Scheduling

**Decision**: Runs during scheduled automation. Uses "Last Check" date for idempotency.
Weekly default.
**Rationale**: Slow-burn consequence, not instant. Gives player time to recover.
"Last Check" date prevents double-penalizing on re-runs.
**Alternatives considered**: Real-time on every transaction (too aggressive — can't
buy hotel before penalty hits again).

## R7: Death State Derivation

**Decision**: Death state is derived from Activity Log — most recent death-related
entry is DIED (with no subsequent RESPAWN). No boolean flag stored on Character.
**Rationale**: Keeps Activity Log as single source of truth. No flag to get out of
sync. Derivable from the event log at any time.
**Alternatives considered**: Boolean flag on Character — requires sync, can drift.
