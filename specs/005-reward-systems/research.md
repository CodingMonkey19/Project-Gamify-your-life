# Research: Phase 5 — Reward Systems (Loot Box, Achievement, Rank & Radar Chart)

**Date**: 2026-03-22
**Feature**: 005-reward-systems

## R1: Rank as High-Water Mark

**Decision**: Rank only increases, never decreases. Even if Total XP drops below the current tier's threshold (e.g., due to XP penalties), the player retains their rank.
**Rationale**: Losing a rank feels punitive and creates anxiety. The XP penalties in the system are small (-50 for budget breaches), so demotion would be a frustrating edge case rather than meaningful gameplay. Ranks celebrate cumulative progress. This also simplifies the avatar system — no need to regenerate downgraded avatars.
**Alternatives considered**: Dynamic re-evaluation (demotion possible — too punitive, creates avatar churn), soft demotion with grace period (adds complexity for marginal benefit).

## R2: Achievement Condition Evaluation — Hardcoded Dispatch

**Decision**: Each achievement condition key maps to a hardcoded Python checker function via a dispatch dictionary: `CONDITION_CHECKERS = {"first_workout": check_first_workout, ...}`.
**Rationale**: The 43 achievements span diverse domains (workouts, finances, streaks, ranks, economy) with conditions too varied for a generic query language. A dispatch map is simple, each checker is independently testable, and adding new achievements means adding one function + one dict entry. The alternative — a generic evaluator parsing condition strings — would require building a mini-DSL for marginal benefit at 43 badges.
**Alternatives considered**: Generic query-based evaluator with condition DSL (over-engineered for 43 badges, harder to test, harder to debug), hybrid approach (unnecessary complexity at this scale).

## R3: Loot Box Rewards — Coins by Rarity

**Decision**: Loot boxes award Coins scaled by rarity: Common=25, Rare=75, Epic=200, Legendary=1000. All values configurable via Settings DB / config.py as `LOOT_REWARDS`.
**Rationale**: Creates a clean Gold→Coins conversion loop. Gold is earned from financial surplus (Phase 4), spent on loot boxes, and Coins come back out. Coins are already tracked by coin_engine and used for marketplace purchases (hotels, items). No new reward type or catalog system needed. The expected value per 100 Gold spent is ~42.6 Coins (weighted average), making loot boxes a net Gold sink with occasional jackpots.
**Alternatives considered**: XP bonuses (conflicts with domain-routed XP philosophy — random XP to random stat feels arbitrary), cosmetic titles (no mechanical benefit, less motivating), mixed rewards (adds reward catalog complexity without clear benefit in V5).

## R4: Weighted PRNG — Standard Library Implementation

**Decision**: Use Python's `random.choices()` with weight parameter for rarity selection. Weights are relative (Common:70, Rare:20, Epic:8, Legendary:2 — sum to 100 but system normalizes). Pity timer overrides RNG when threshold reached.
**Rationale**: `random.choices()` is standard library, zero dependencies, well-tested, and handles weight normalization. The pity timer is a simple counter check before RNG — if `pity_counter >= threshold`, return Legendary directly. No need for a custom PRNG or seeded generator.
**Alternatives considered**: Custom weighted selection with bisect (unnecessary when stdlib handles it), numpy.random (overkill dependency for single-use RNG), guaranteed minimum drops per N pulls (more complex than a simple counter).

## R5: Radar Chart — matplotlib with Dark RPG Theme

**Decision**: matplotlib polar plot, dark background (#1a1a2e), neon cyan accent (#00d4ff), 800x800 PNG, 5-axis (STR/INT/WIS/VIT/CHA). Uploaded to Cloudinary.
**Rationale**: matplotlib is free, well-documented, already in the V5 tech stack, and produces publication-quality charts. The dark theme matches RPG aesthetics. 800x800 is large enough for Notion embeds without being oversized. The V5 plan includes sample code for this exact approach.
**Alternatives considered**: Chartbase.so (paid — violates Free-First principle), Pillow manual drawing (no polar chart support, would need custom geometry), plotly (heavier dependency, HTML-focused not PNG-focused).

## R6: Avatar Compositing — Pillow with Cloudinary Hosting

**Decision**: Pillow (`PIL.Image`) composites the player's profile picture with a rank-specific frame overlay PNG. The result is uploaded to Cloudinary free tier. Frame PNGs are stored in `assets/frames/` with filenames matching rank names (`peasant.png`, `squire.png`, etc.).
**Rationale**: Pillow is free, handles PNG alpha compositing natively, and is already in the V5 tech stack. Cloudinary free tier provides 25 monthly credits (sufficient for single-player avatar updates). Storing frames as local PNGs keeps the system simple — no need for a frame database or dynamic generation.
**Alternatives considered**: ImageMagick CLI (adds system dependency), server-side rendering API (paid, overkill), Notion-native cover images (no compositing support).

## R7: Achievement XP Routing — Domain-Based

**Decision**: Each achievement's XP bonus routes to the stat mapped by its Domain field. For example, a fitness achievement grants STR XP, a finance achievement grants WIS XP. The Activity Log entry uses the same domain→stat mapping as all other engines.
**Rationale**: Consistent with how all other XP flows in the system — financial engine → WIS, fitness engine → STR, nutrition engine → VIT. The Achievements DB already has a Domain field designed for this purpose. Splitting XP across all stats or routing to a general pool would break the domain-specific progression model.
**Alternatives considered**: General XP split across all stats (dilutes achievement impact, makes individual stat progression unpredictable), Player Level XP only (bypasses stat system entirely).
