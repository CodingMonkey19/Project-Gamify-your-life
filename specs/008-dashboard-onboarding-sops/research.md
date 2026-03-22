# Research: Dashboard, Onboarding & SOPs

**Date**: 2026-03-22 | **Feature**: 008-dashboard-onboarding-sops

## R1: Notion API — Programmatic Page Creation with Linked Database Views

**Decision**: Use the Notion API `pages.create` endpoint with child blocks to build the dashboard page programmatically.

**Rationale**: The Notion API supports creating pages with rich child content blocks including:
- `heading_2` blocks for panel section headers
- `embed` blocks for images (avatar, radar chart from Cloudinary URLs)
- `child_database` blocks — however, **linked database views** (showing an existing DB inline) require the `link_to_page` or `synced_block` approach, or more practically, `linked_database` block type (available since Notion API v2022-06-28).
- `callout` blocks for the Character Card display
- `divider` blocks between panels

Key limitation: Notion API linked database views don't support setting **view filters programmatically** via the API as of 2025. The linked DB will embed, but filters (e.g., "Status ≠ Completed") must be set manually by the player on first view, or the script can create a **pre-filtered database view** by using the Notion internal API for view configuration (undocumented, fragile).

**Practical approach**: Create the dashboard page with all linked databases embedded. Add a text block above each panel noting the expected filter (e.g., "Filter: Status ≠ Completed"). Include filter setup instructions in `workflows/onboarding.md` SOP. This is the most reliable pattern — programmatic structure, manual filter polish.

**Alternatives considered**:
- Fully manual SOP-only → rejected per clarification Q1 (user chose programmatic)
- Notion internal API for filters → rejected: undocumented, breaks on API changes, violates "reliable" WAT principle
- Template page duplication → rejected: requires a pre-existing template page, not reproducible from scratch

## R2: Interactive CLI Input — Best Practices for Python

**Decision**: Use Python's built-in `input()` for simple prompts, with a thin wrapper for validation and re-prompting.

**Rationale**: The onboarding flow is a one-time setup with ~8 interactive prompts. No need for a TUI framework. Pattern:
```python
def prompt_required(question: str) -> str:
    while True:
        answer = input(f"{question}: ").strip()
        if answer:
            return answer
        print("This field is required. Please try again.")

def prompt_choice(question: str, options: list[str]) -> str:
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        choice = input(f"{question} (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print(f"Please enter a number between 1 and {len(options)}.")
```

**Alternatives considered**:
- `click` / `typer` CLI framework → rejected: adds dependency for 8 prompts, overkill
- `inquirer` / `questionary` → rejected: adds dependency, not in authorized stack
- `argparse` for all inputs → rejected: onboarding is inherently conversational, not flag-based

## R3: Partial Onboarding Recovery — State Detection Pattern

**Decision**: Check each onboarding step's output before executing it. Use Notion DB queries to detect existing records.

**Rationale**: The onboarding flow has 5 sequential steps:
1. Create Character row
2. Create Onboarding Identity rows
3. Create default habits
4. Create Vision Board entries
5. Create Dashboard page

For recovery, before each step:
- Step 1: Query Character DB for existing character linked to parent page
- Step 2: Query Identity DB for existing rows linked to character
- Step 3: Query Good Habit DB for existing habits linked to character
- Step 4: Query Vision Board DB for existing entries linked to character
- Step 5: Check if a page titled "Daily Dashboard" exists under parent page

If a step's output already exists, skip it with a log message. This makes the entire flow idempotent and resumable.

**Alternatives considered**:
- Local state file tracking progress → rejected: file can be lost, doesn't survive across machines
- Single "onboarding_complete" flag in Settings DB → rejected: too coarse, can't detect which step failed
- Always recreate everything → rejected: violates idempotency principle (Constitution V)

## R4: Dashboard Linked Database Block Types

**Decision**: Use `child_database` reference blocks with descriptive headings indicating expected filters.

**Rationale**: The Notion API (as of 2025) supports these relevant block types for dashboards:
- `heading_2`: Panel section titles ("Growth", "Battle", "Quest Board", etc.)
- `callout`: Character Card with icon + stats text
- `image`: Avatar and radar chart from Cloudinary URLs
- `linked_database` (type: `child_database` with database_id): Embeds an existing database inline

The 7 panels map to:
1. **Character Card**: `callout` block + `image` blocks (avatar, radar chart) + `paragraph` blocks (stats)
2. **Growth**: `heading_2` + `child_database` → Good Habit DB
3. **Battle**: `heading_2` + `child_database` → Bad Habit DB
4. **Quest Board**: `heading_2` + `child_database` → Quests DB
5. **Tasks**: `heading_2` + `child_database` → Brain Dump DB
6. **Journal**: `heading_2` + `child_database` → Journal DB
7. **Stats**: `heading_2` + `child_database` → Daily Snapshots DB

**Alternatives considered**:
- Separate Notion pages per panel → rejected: defeats the purpose of a single dashboard
- Notion synced blocks → rejected: designed for cross-page sync, not inline views

## R5: SOP Format — WAT Workflow Standard

**Decision**: Each SOP follows a consistent WAT workflow template.

**Rationale**: Per Constitution III and FR-021, SOPs must follow:
```markdown
# [Workflow Name]

## Objective
What this workflow accomplishes.

## Required Inputs
- Input 1: description
- Input 2: description

## Prerequisites
- What must be true before starting

## Steps
1. Step description
2. Step description
   - Sub-step if needed

## Expected Outputs
- What should exist when done

## Troubleshooting
### Problem: [common issue]
**Cause**: [why it happens]
**Fix**: [how to resolve]

## Last Verified
Phase: 8 | Date: YYYY-MM-DD
```

This format ensures SOPs are actionable, testable, and maintainable.

**Alternatives considered**:
- Free-form prose → rejected: not actionable, hard to follow step-by-step
- Video/screenshot tutorials → rejected: can't be version-controlled, not accessible to Claude agents
