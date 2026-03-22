# Test Contracts: End-to-End Verification

## Unit Test File Contract

Each test file MUST follow this structure:

```
File: tests/test_{engine_name}.py
Mirrors: tools/{engine_name}.py

Imports:
  - pytest
  - unittest.mock (patch, MagicMock)
  - The engine module under test (from tools.{engine_name} import ...)
  - Shared fixtures from conftest.py

Structure:
  class Test{EngineName}:
      def test_{specific_behavior}(self, mock_notion_client, mock_settings):
          # Arrange: set up mock responses
          # Act: call engine function
          # Assert: verify expected output

Naming Convention:
  test_{what}_{condition}_{expected}
  Example: test_xp_award_warrior_class_bonus_applied

Assertions:
  - Use pytest assertions (assert x == y), not unittest-style (assertEqual)
  - Include descriptive assertion messages for failures
  - One logical assertion per test (multiple asserts OK if testing same behavior)
```

## Per-Engine Test Requirements

### test_xp_engine.py
```
Required tests:
  - test_xp_for_level_non_linear_curve: verify XP = XP_BASE * level^XP_EXPONENT
  - test_level_from_xp_roundtrip: level_from_xp(xp_for_level(N)) == N for levels 1-50
  - test_class_bonus_applies_correct_stat: Warrior gets STR bonus, Mage gets INT, etc.
  - test_class_bonus_multiplier_value: bonus XP matches config multiplier
```

### test_hp_engine.py
```
Required tests:
  - test_apply_damage_reduces_hp: HP decreases by damage amount
  - test_death_triggers_at_zero: HP <= 0 triggers death event
  - test_death_triggers_below_zero: HP going negative still triggers death
  - test_respawn_resets_to_starting_hp: after death, HP = STARTING_HP
  - test_hotel_recovery_by_tier: tier 1/2/3 restore correct HP amounts
  - test_hotel_recovery_caps_at_max: HP cannot exceed STARTING_HP after recovery
```

### test_coin_engine.py
```
Required tests:
  - test_overdraft_detection: balance < 0 after deduction flagged
  - test_market_purchase_deducts_coins: coins decrease by item cost
  - test_hotel_checkin_cost_by_tier: correct coin deduction per hotel tier
  - test_insufficient_coins_rejected: purchase blocked when balance too low
```

### test_streak_engine.py
```
Required tests:
  - test_streak_increment: consecutive day increases streak by 1
  - test_streak_reset_on_miss: missed day resets streak to 0
  - test_decay_penalty_calculation: penalty = configured decay rate * streak tier
  - test_tier_advancement_thresholds: tier changes at exactly 3, 7, 14, 30, 60, 100 days
  - test_tier_stays_within_bounds: streak of 1000 doesn't exceed max tier
```

### test_financial_engine.py
```
Required tests:
  - test_surplus_calculation: surplus = income - expenses
  - test_gold_conversion_rate: Gold = surplus / GOLD_CONVERSION_RATE
  - test_budget_breach_penalty: negative surplus applies XP penalty
  - test_zero_expenses_full_surplus: no expenses = income becomes full surplus
```

### test_fitness_engine.py
```
Required tests:
  - test_epley_1rm_accuracy: 1RM = weight * (1 + reps/30), verify to 2 decimal places
  - test_rpe_weighted_xp: higher RPE = more XP per set
  - test_progressive_overload_detection: 1RM increase over 14-day window detected
  - test_no_overload_stable_weight: same weight over 14 days = no overload flag
```

### test_nutrition_engine.py
```
Required tests:
  - test_symmetric_adherence_under: 80% of target penalized same as 120%
  - test_symmetric_adherence_over: overshoot penalized equally to undershoot
  - test_streak_multiplier_applies: consecutive adherent days multiply XP
  - test_negative_xp_on_significant_overshoot: >130% target = negative XP
  - test_perfect_adherence_max_xp: 100% target = maximum XP award
```

### test_loot_box.py
```
Required tests:
  - test_weight_distribution_10k_samples: over 10k draws, each rarity within ±5% of config weight
  - test_pity_timer_triggers: after PITY_TIMER_THRESHOLD draws without Legendary, next draw is guaranteed Legendary
  - test_pity_timer_resets_after_legendary: pity counter resets to 0 after Legendary drop
  - test_seeded_reproducibility: same seed produces same sequence
```

### test_chart_renderer.py
```
Required tests:
  - test_output_file_created: radar chart file exists after generation
  - test_correct_dimensions: image width/height match expected (e.g., 800x800)
  - test_five_axes_rendered: chart has exactly 5 axes (STR, INT, WIS, VIT, CHA)
  - test_zero_stats_no_crash: all stats at 0 produces valid chart
```

## conftest.py Fixture Contract

```
File: tests/conftest.py

Required fixtures (scope="function" unless noted):
  @pytest.fixture
  mock_notion_client → MagicMock with configurable .databases.query() and .pages.create()

  @pytest.fixture
  mock_character_page → dict matching Notion page response shape (Level 5, HP 800, 150 coins)

  @pytest.fixture
  mock_settings → dict matching config.py defaults

  @pytest.fixture
  mock_habit_rows → list of dicts (5 good habits, 3 bad habits)

  @pytest.fixture
  mock_workout_rows → list of dicts (3 workout entries with weight/reps/RPE)

  @pytest.fixture
  mock_meal_rows → list of dicts (3 meal entries with macros)

  @pytest.fixture
  mock_expense_rows → list of dicts (5 expense entries)

  @pytest.fixture
  mock_activity_log → list of dicts (empty by default, populated variant for idempotency)
```

## CI Workflow Contract

```
File: .github/workflows/tests.yml

Trigger: push (all branches), pull_request (all branches)
Runner: ubuntu-latest
Python: 3.10

Steps:
  1. Checkout code
  2. Set up Python 3.10
  3. Install dependencies: pip install -r requirements.txt
  4. Run tests: python -m pytest tests/ -v --tb=short
  5. Exit code 0 = all pass, non-zero = block merge

Environment:
  - No NOTION_TOKEN (unit tests are mocked)
  - No OPENAI_API_KEY
  - No .env file needed

Branch protection rule (manual setup):
  - Require status check "test" to pass before merge
```

## Integration Smoke Test Contract

```
File: tests/integration/smoke_test_checklist.md

Format: Numbered markdown checklist
Each step:
  ## Step N: [Title]
  **Action**: [What to do]
  **Verification**: [What to check]
  **Pass criteria**: [Specific measurable outcome]
  - [ ] Pass / Fail
  **Notes**: ___

Total: 15 steps, sequential, each depends on previous
Prerequisites: Live Notion workspace, configured .env, all tools/ scripts functional
```

## Manual Verification Contract

```
File: checklists/manual_verification.md

Format: Numbered markdown checklist
Each item:
  ## Item N: [Title]
  **Action**: [What to do in Notion]
  **Pass criteria**: [Explicit, non-subjective where possible]
  - [ ] Pass / Fail
  **Notes**: ___

Total: 8 items
Prerequisites: All automated tests pass, live Notion workspace with game data
```
