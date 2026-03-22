# Research: End-to-End Verification

**Feature**: 009-e2e-verification
**Date**: 2026-03-22

## Decision 1: Test Framework and Runner

**Decision**: pytest with unittest.mock for Notion API mocking

**Rationale**: Already mandated by constitution ("pytest covers all engines"). `unittest.mock` is stdlib — no extra dependency. `conftest.py` shared fixtures pattern established in Phase 7 spec.

**Alternatives considered**:
- `responses` library (mock HTTP): Adds dependency, overkill when we can mock at the `notion-client` level
- `pytest-mock`: Thin wrapper over `unittest.mock`, unnecessary indirection

## Decision 2: Mock Strategy for Notion API

**Decision**: Mock the `notion-client` Client object at the function level. Each test file creates fixtures that return pre-built Notion API response dicts.

**Rationale**: Engines call `client.databases.query()`, `client.pages.create()`, etc. Mocking at this level tests the engine logic without testing the Notion SDK itself. Response dicts match Notion API shape (id, properties, results array).

**Alternatives considered**:
- Mock at HTTP level (`requests_mock`): Too low-level, fragile to SDK internal changes
- Fake Notion server: Over-engineered for a single-player system
- VCR-style recording: Ties tests to specific workspace data, breaks on schema changes

## Decision 3: conftest.py Fixture Design

**Decision**: Shared `conftest.py` provides these fixtures:
- `mock_notion_client`: Patched Client with configurable return values
- `mock_character_page`: Standard character with Level 5, HP 800, 150 coins, known XP values
- `mock_settings`: Config dict matching `config.py` defaults (so tests validate against known constants)
- `mock_habit_rows`: Sample good/bad habit rows with known XP/HP impacts
- `mock_activity_log`: Empty and pre-populated activity log for idempotency tests

**Rationale**: Shared fixtures eliminate duplication across 9 test files. A single character fixture with known values makes cross-engine assertions predictable.

**Alternatives considered**:
- Per-file fixtures only: Leads to drift between test files, harder to maintain consistency
- Factory pattern (`factory_boy`): Adds dependency, overkill for ~20 fixtures

## Decision 4: Loot Box Statistical Test Approach

**Decision**: Run 10,000 samples in a single test, assert each rarity weight within ±5% of configured weight. Use `random.seed(42)` for reproducibility in CI, plus one unseeded run for real randomness validation.

**Rationale**: ±5% over 10k samples gives >99.9% statistical confidence per the spec. Seeded run ensures CI never flakes; unseeded run validates real distribution. If unseeded fails, re-run once — spec says two consecutive failures indicate a real bug.

**Alternatives considered**:
- Chi-squared test: Statistically rigorous but harder to debug failures
- Smaller sample (1000): Wider variance, more flaky results
- Property-based testing (`hypothesis`): Adds dependency, overkill for a fixed-weight distribution

## Decision 5: Integration Test Format

**Decision**: Structured markdown checklist (`smoke_test_checklist.md`) with step number, action, verification checkpoint, and pass/fail column. Not a pytest file — integration tests require a live Notion workspace and human judgment at some steps.

**Rationale**: The 15-step integration sequence is sequential and stateful (each step depends on previous). Some steps require visual verification in Notion (e.g., "seed data is visible"). A runnable doc with clear checkpoints is more practical than brittle end-to-end automation against a live API.

**Alternatives considered**:
- Full pytest integration suite: Requires test workspace provisioning, teardown, and API rate limit handling — fragile and slow
- Bash script with curl: Loses the sequential verification checkpoints
- Jupyter notebook: Adds dependency, not appropriate for a CI context

## Decision 6: CI Pipeline Configuration

**Decision**: GitHub Actions `tests.yml` workflow — triggers on push and pull_request, runs `python -m pytest tests/ -v --tb=short`, uses Python 3.10, installs from `requirements.txt`. Integration tests excluded from CI (no Notion credentials in CI environment).

**Rationale**: Constitution mandates "Tests run on every push/PR via `tests.yml`." Unit tests are mocked and fast (<30s). Integration tests require live Notion API and are manual-only. CI blocks merge on any test failure.

**Alternatives considered**:
- Include integration tests in CI with secrets: Adds Notion token to GitHub secrets, risk of rate limiting, flaky due to network
- Separate CI job for integration: Complexity not justified for single-player system
- Pre-commit hooks only: Doesn't block PRs, easy to bypass

## Decision 7: Manual Verification Checklist Format

**Decision**: Markdown checklist with 8 items, each having: item description, explicit pass/fail criteria, checkbox, and notes field. Stored in `checklists/manual_verification.md`.

**Rationale**: Spec FR-017 through FR-019 require recordable results with explicit criteria. Markdown checkboxes are git-trackable and simple. Notes field captures subjective observations (e.g., "AI coaching tone felt appropriate").

**Alternatives considered**:
- Notion database for verification tracking: Over-engineered, adds a DB just for testing
- Google Form: External dependency, not version-controlled
- JSON checklist: Harder to read and fill in manually
