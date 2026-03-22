<!-- SYNC IMPACT REPORT
Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
Modified principles: All (template placeholders → concrete project principles)
Added sections: Core Principles (6), Tech Stack & Constraints, Development Workflow, Governance
Removed sections: None
Templates requiring updates:
  ✅ .specify/memory/constitution.md (this file)
  ⚠ .specify/templates/plan-template.md (verify Constitution Check alignment)
  ⚠ .specify/templates/spec-template.md (verify scope section alignment)
  ⚠ .specify/templates/tasks-template.md (verify task categories match principles)
Deferred TODOs:
  - TODO(RATIFICATION_DATE): Set once owner confirms adoption date. Using 2026-03-22.
-->

# RPG-Gamified Life Tracker Constitution

## Core Principles

### I. Notion as Headless Database and GUI

Notion is the **single source of truth** for all data storage and user-facing interaction.
Native Notion capabilities — formulas, buttons, relations, rollups — MUST handle all
single-row computation and all user-triggered actions. Python MUST NOT replicate what
Notion can do natively.

Notion-native (examples): `Calories = Protein*4 + Carbs*4 + Fat*9`, visual progress
bars, check-in status formulas, heat maps, button-triggered Activity Log entries.

Python-only (examples): multi-row aggregation, cross-database XP/HP/Coin rollups,
exponential leveling curves, streak multipliers, AI coaching, radar chart rendering,
avatar frame compositing.

### II. Python for Complex Orchestration Only

Python tools in `tools/` handle **exactly one concern** each and are deterministic,
independently testable, and stateless by default. Tools MUST NOT embed game balance
constants directly — all magic numbers are sourced from `config.py` or the Notion
Settings DB. No tool does reasoning; tools execute and return structured output.

Engine boundary rule: if logic requires reading more than one database row or
comparing historical state, it belongs in Python. If it operates on a single row's
properties, it belongs in a Notion formula.

### III. WAT Architecture — Separation of Concerns (NON-NEGOTIABLE)

The project follows the **Workflows → Agents → Tools** architecture:

- **Workflows** (`workflows/`): Markdown SOPs defining what to do, required inputs,
  expected outputs, and edge case handling. These are living documents — updated when
  constraints are discovered.
- **Agents** (Claude): Orchestrate decisions, read the workflow, call tools in sequence,
  handle failures, and ask clarifying questions. Agents MUST NOT attempt direct
  execution of multi-step tasks without a workflow.
- **Tools** (`tools/`): Python scripts for deterministic execution. API calls, math,
  file operations. Fast, consistent, testable.

Before building any new tool, check `tools/` first. Create new scripts only when
nothing exists for the task. When a tool fails, fix-verify-document before moving on.

### IV. Settings DB as Canonical Config

All game balance constants (XP curves, HP values, streak tiers, hotel costs, loot
weights, OpenAI limits, rank thresholds) MUST be readable from the **Notion Settings
DB**. `tools/config.py` provides hardcoded fallback defaults — never the primary source.

No engine file (`xp_engine.py`, `hp_engine.py`, etc.) may contain numeric game balance
values directly. All constants are imported from `config.py` or resolved via
`load_settings_from_notion()`.

### V. Idempotency and Safe Re-Runs

All GitHub Actions automation scripts (`daily_automation.py`, `weekly_report.py`,
`monthly_automation.py`) MUST be safe to re-run without double-counting, duplicate
entries, or corrupted state. Required patterns:

- Check-before-write: query for existing records before creating
- Deduplication by date: use `Date` properties as idempotency keys
- No side effects from reruns: HP/XP/Coin changes applied only once per event

If a script cannot guarantee idempotency for a given operation, it MUST log a warning
and skip rather than risk data corruption.

### VI. Free-First, Cost-Controlled AI

Prefer zero-cost solutions at every decision point:

- Radar charts: `matplotlib` (free) over paid charting services
- Avatar frames: `Pillow` compositing (free) over design APIs
- Image hosting: Cloudinary free tier

OpenAI usage MUST enforce hard monthly cost caps (`OPENAI_MONTHLY_COST_CAP_USD`).
Responses MUST be structured JSON. Model defaults to `gpt-4o-mini`. No paid
third-party dependency may be added without explicit user approval.

## Tech Stack and Constraints

**Authorized stack:** Notion API (`notion-client`), OpenAI API (`gpt-4o-mini`),
GitHub Actions, Python 3.10+, `Pillow`, `matplotlib`, `pytest`, `python-dotenv`,
Cloudinary (free tier).

**Architecture tier:** V5 follows Architecture A (Notion-only headless DB). A future
V6 may migrate to Architecture B (Next.js + FastAPI + Supabase). No V6 scope creep
into V5.

**Credentials:** All API keys and secrets MUST live in `.env`. Credentials MUST be
listed in `.gitignore`. The `.claude/` folder and any token files (`credentials.json`,
`token.json`) MUST NOT be committed.

**Deliverables:** Final outputs go to Notion (cloud). `.tmp/` is disposable — all
intermediate processing files may be deleted and regenerated. Local files are not
deliverables.

**Notion formula limitation:** Notion formulas operate on a single row only. The
following are always Python-calculated and written back via API:
- Player Level, Stat Levels, Total XP (aggregated across DBs)
- Applied Multiplier / Effective XP in Quests (depends on Streak Tracker)
- Progressive Delta in Set Log (cross-row historical comparison)
- Adherence Score in Meal Log (depends on TDEE target in Character DB)

## Development Workflow

**Build sequence:** Foundation (config, logger, Notion client, smoke test) → Database
schemas → Seed data → Engines (XP, HP, streak, coin, financial, fitness, nutrition,
habit, quest, loot box, achievement, rank, avatar, chart, snapshot, coaching) →
Automation (daily, weekly, monthly) → Tests.

**Testing:** `pytest` covers all engines. Test files mirror engine files
(`test_xp_engine.py` ↔ `xp_engine.py`). `conftest.py` provides shared mock Notion
responses. Tests run on every push/PR via `tests.yml`. No engine ships without tests.

**Self-improvement loop:** Failure → fix tool → verify fix works → update workflow
with new constraint → commit. Workflows evolve; they are not disposable after one use.

**Error handling:** On API failure: log full trace, apply exponential backoff with
jitter (max 3 retries, max 3 req/sec). If paid API involved (OpenAI, Notion), confirm
with user before retrying. Never silently swallow errors.

## Governance

This constitution supersedes all other project practices. Amendments require:
1. A documented reason (what changed and why)
2. A version bump following semantic versioning:
   - MAJOR: backward-incompatible principle removal or redefinition
   - MINOR: new principle or section added
   - PATCH: clarification, wording, typo fix
3. Propagation review across all `.specify/templates/` files
4. A commit message of the form: `docs: amend constitution to vX.Y.Z (<summary>)`

All implementation work MUST be verifiable against these principles. If a proposed
change conflicts with a principle, the conflict MUST be surfaced before implementation,
not discovered after.

**Version**: 1.0.0 | **Ratified**: 2026-03-22 | **Last Amended**: 2026-03-22
