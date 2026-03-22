# Feature Specification: Phase 2 — HP System, Death & Economy

**Feature Branch**: `002-hp-death-economy`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Phase 2: HP System, Death and Economy"

## Clarifications

### Session 2026-03-22

- Q: When does death detection run? → A: Immediately after every HP-changing event (bad habit, overdraft penalty) — real-time death detection.
- Q: Can the player act while dead? → A: Dead players can still log bad habits (HP damage stacks) and earn coins, but cannot spend coins (no market/hotel/black market) until respawn.
- Q: How is starting HP represented? → A: Explicit Activity Log entry — on character creation and every respawn, an entry is created with starting HP as positive value. Current HP = sum(all HP entries).
- Q: Who processes button-created coin Activity Log entries? → A: Coin balance is a pure read — get_coin_balance() sums all coin columns in Activity Log. Buttons already write the coins, no further processing needed.
- Q: What happens if player checks Respawn while alive (HP > 0)? → A: No-op — system ignores Respawn flag if HP > 0, clears the checkbox, logs a notice.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - HP as Consequence for Bad Habits (Priority: P1)

A player's character has a Health Points (HP) pool that starts at a configurable
value (default: 1000). Every time the player logs a bad habit — smoking, doomscrolling,
skipping a workout — their character takes HP damage. The player sees their HP bar
drop in Notion and feels the weight of the consequence. HP is the stick to XP's carrot:
it makes bad choices visible and costly.

**Why this priority**: Without a consequence system, the RPG has no tension. XP alone
is all reward and no risk. HP introduces stakes — the possibility of losing — which
is what makes the game feel real.

**Independent Test**: Can be tested by logging a bad habit and verifying that the
character's HP decreases by the correct amount. Delivers standalone value as a
consequence tracker even before death or economy features exist.

**Acceptance Scenarios**:

1. **Given** a character with 1000 HP and a bad habit that costs 10 HP, **When** the
   player logs that bad habit, **Then** the character's HP drops to 990 and the HP
   progress bar in Notion updates accordingly.
2. **Given** a character with 15 HP and a bad habit that costs 20 HP, **When** the
   player logs that bad habit, **Then** the character's HP drops to -5 (below zero
   is allowed — death is checked separately).
3. **Given** multiple bad habits logged on the same day, **When** HP is recalculated,
   **Then** each bad habit's damage is applied independently and the total reflects
   all incidents.
4. **Given** a bad habit that would push HP to exactly 0, **When** the damage is
   applied, **Then** death is detected immediately after that event — not deferred
   to the next daily automation run.

---

### User Story 2 - Death and Respawn (Priority: P2)

When the character's HP reaches zero or below, the character "dies." The player sees
a "You Died!" message in Notion along with a Death Penalty — a real-world consequence
they defined during onboarding (e.g., "No Netflix for a week"). Death is dramatic but
recoverable: the player can check a Respawn checkbox in Notion to reset their HP to
the starting value and continue playing. Death count is tracked permanently.

**Why this priority**: Death gives HP meaning. Without a death state, HP is just a
number that goes down. With death, the player has a real boundary they're trying to
stay above, creating genuine motivation to avoid bad habits.

**Independent Test**: Can be tested by reducing HP to zero and verifying the death
event fires, the "You Died!" message appears, and respawn resets HP correctly.

**Acceptance Scenarios**:

1. **Given** a character whose HP has just dropped to 0 or below, **When** the system
   checks for death, **Then** a death event is recorded, the death count increments
   by 1, and the HP progress bar displays "You Died!".
2. **Given** a dead character, **When** the player checks the Respawn checkbox in
   Notion, **Then** the character's HP resets to the configured starting value and
   the Respawn checkbox is cleared.
3. **Given** a character with HP above zero, **When** the system checks for death,
   **Then** no death event is recorded and the character continues normally.
4. **Given** a character who has died 3 times previously, **When** they die again,
   **Then** the death count reads 4 and all previous death events remain in the
   activity history.
5. **Given** a dead character, **When** the player logs a bad habit, **Then** the HP
   damage is still applied (stacking further negative) but no additional death event
   is created (already dead).
6. **Given** a dead character, **When** the player tries to buy a Market item or
   check into a Hotel, **Then** the purchase is blocked and the player sees that
   they must respawn first.
7. **Given** a player checks the Respawn checkbox while HP is still positive,
   **When** the system processes the flag, **Then** it is treated as a no-op — the
   checkbox is cleared, HP is unchanged, and a notice is logged.

---

### User Story 3 - Coin Economy: Earning and Spending (Priority: P3)

The player earns Coins by completing goals and tasks. They spend Coins in the Market
(buying real-world rewards they've defined), at Hotels (recovering HP), or on the
Black Market (buying back missed habit check-ins). The coin balance is tracked on the
Character page. Spending more than the player has is allowed — but comes with
consequences (see Story 4).

**Why this priority**: Coins create a resource management layer. The player must
decide: spend coins on a reward now, or save them for HP recovery later? This
tension makes every completed task feel valuable and every purchase feel meaningful.

**Independent Test**: Can be tested by simulating coin earnings from a completed goal,
then a market purchase, and verifying the balance changes correctly. Delivers a
functional economy even without overdraft penalties.

**Acceptance Scenarios**:

1. **Given** a player completes a goal worth 50 Coins, **When** the system processes
   the completion, **Then** 50 Coins are added to their balance and the transaction
   appears in the activity history.
2. **Given** a player with 200 Coins buys a Market item costing 150 Coins, **When**
   the purchase is processed, **Then** their balance drops to 50 Coins, the item is
   marked as purchased, and the redemption date is set.
3. **Given** a player with 100 Coins checks into the Premium Hotel (300 Coins),
   **When** the check-in is processed, **Then** the balance drops to -200 Coins
   (overdraft) and the character recovers the hotel's HP amount.
4. **Given** a player who missed a habit check-in, **When** they buy a Check-in
   Recovery from the Black Market (50 Coins), **Then** the missed check-in is
   retroactively counted and the coins are deducted.

---

### User Story 4 - Overdraft Penalties (Priority: P4)

When a player's coin balance is negative (overdrawn), the system applies periodic HP
penalties — a configurable amount (default: 100 HP) at a configurable frequency
(default: weekly). This creates urgency to earn coins and get out of debt. If
overdraft penalties push HP to zero, death occurs normally.

**Why this priority**: Without overdraft consequences, negative coin balances have no
teeth. Players could overspend freely. Overdraft penalties connect the economy to the
HP system, creating a debt spiral that motivates responsible coin management.

**Independent Test**: Can be tested by setting a character's coin balance to negative,
running the overdraft check, and verifying HP damage is applied.

**Acceptance Scenarios**:

1. **Given** a character with a coin balance of -200 and the overdraft check is set to
   weekly, **When** the weekly automation runs, **Then** the character takes the
   configured HP penalty (default: 100 HP damage) and the penalty is logged in the
   activity history.
2. **Given** a character with a positive coin balance, **When** the overdraft check
   runs, **Then** no penalty is applied.
3. **Given** a character with -50 coins and 80 HP remaining, **When** the overdraft
   penalty of 100 HP is applied, **Then** HP drops to -20 and a death event is
   triggered.
4. **Given** the overdraft check frequency is set to "Disabled" in settings, **When**
   automation runs, **Then** no overdraft check occurs regardless of coin balance.

---

### User Story 5 - Hotel HP Recovery (Priority: P5)

When a player's HP is getting dangerously low, they can spend coins at a Hotel to
recover HP. Three tiers exist — Budget (cheap, small recovery), Ordinary (moderate),
and Premium (expensive, large recovery). This gives the player an escape valve before
death, at the cost of their coin reserves.

**Why this priority**: Without a recovery mechanism, low HP is a death sentence with
no agency. Hotels give the player a strategic choice: spend now to survive, or risk
it and save coins for rewards.

**Independent Test**: Can be tested by checking into each hotel tier and verifying
the correct HP recovery and coin deduction. Delivers a standalone HP recovery feature.

**Acceptance Scenarios**:

1. **Given** a character with 300 HP and 200 coins, **When** they check into the
   Budget Hotel (100 coins, +50 HP), **Then** their HP becomes 350 and their coin
   balance becomes 100.
2. **Given** a character with 100 HP, **When** they check into the Premium Hotel
   (300 coins, +500 HP), **Then** their HP becomes 600 regardless of whether they
   had enough coins (overdraft is allowed).
3. **Given** a character at full HP (1000), **When** they check into a hotel, **Then**
   HP increases beyond the starting value (no cap on HP recovery).

---

### Edge Cases

- What happens when a player logs the same bad habit multiple times in one day?
  → Each instance deals damage independently. There is no daily cap on HP damage.
- What happens when a player tries to respawn but still has negative coins?
  → Respawn resets HP only. Coin debt persists and overdraft penalties will resume.
- What happens when overdraft penalty and bad habit damage occur on the same day
  and both push HP below zero?
  → Only one death event is recorded per automation run. The first check that
  finds HP ≤ 0 triggers death.
- What happens when a player changes the overdraft frequency setting mid-cycle?
  → The new frequency takes effect on the next check. No retroactive penalties.
- What happens when the Black Market purchase references a habit check-in from a
  previous day? → The recovery applies to the specific missed date. If the habit
  engine already processed that day, the recovery is still logged but the streak
  is not retroactively repaired (streaks are calculated forward-only).
- What happens if the player checks Respawn while HP > 0? → No-op. Checkbox is
  cleared, HP unchanged, notice logged. Respawn is not a "full heal" exploit.
- What happens if Respawn is checked twice rapidly (while respawn() is still
  processing)? → Idempotency: if a RESPAWN Activity Log entry for today already
  exists, the function returns without creating a duplicate.
- What happens if the player tries to buy a Market item while dead? → Purchase is
  blocked. Player must respawn first.
- What happens when a dead player logs another bad habit? → HP damage stacks further
  negative, but no duplicate death event is created.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST track a character's HP as the sum of all HP entries
  in the activity history. On character creation and every respawn, an explicit
  Activity Log entry MUST be created with the starting HP as a positive value.
  Current HP = sum(all HP entries in Activity Log).
- **FR-002**: The system MUST deduct HP when a bad habit is logged, using the
  damage value defined on that specific bad habit.
- **FR-003**: The system MUST check for death immediately after every HP-changing
  event (bad habit damage, overdraft penalty, hotel recovery). If HP ≤ 0, a death
  event MUST be triggered in real time — not deferred to a scheduled run.
- **FR-004**: A death event MUST record the death in the Activity Log (Type=DIED),
  increment the Death Count on the Character page, and ensure the player's Death
  Penalty text is visible via the Character page's HP Progress formula (which shows
  the text when HP ≤ 0). "Death Penalty" refers to the flavor-text consequence the
  player defined during onboarding; "Overdraft Penalty" refers to periodic HP damage
  from negative coin balance (FR-008).
- **FR-005**: The system MUST allow the player to respawn by checking a Respawn
  control in Notion, which creates a new Activity Log entry with the starting HP
  as a positive value and clears the respawn flag. If the Respawn flag is checked
  while HP > 0, the system MUST treat it as a no-op (clear the flag, log a notice,
  do not change HP).
- **FR-006**: The system MUST track a character's coin balance as the sum of all
  coin columns in the activity history. Coin balance is a pure read operation —
  Notion buttons write coin values to Activity Log entries, and the system sums
  them without additional processing or confirmation steps.
- **FR-007**: The system MUST allow coin spending even when the balance would go
  negative (overdraft is permitted).
- **FR-008**: The system MUST apply periodic HP penalties to characters with negative
  coin balances, at a frequency and amount defined in the game settings.
- **FR-009**: The system MUST support Market purchases that deduct coins, mark items
  as purchased, and record a redemption date.
- **FR-010**: The system MUST support Hotel check-ins that deduct coins and recover
  HP, with three tiers offering different price/recovery ratios.
- **FR-011**: The system MUST support Black Market transactions that allow purchasing
  a retroactive check-in recovery for a missed habit day.
- **FR-012**: All HP changes, coin transactions, deaths, and purchases MUST be
  recorded in the central activity history with the appropriate event type.
- **FR-013**: The overdraft check MUST be disableable via settings without requiring
  code changes.
- **FR-014**: While a character is dead (HP ≤ 0, not yet respawned), the system MUST
  block coin-spending actions (Market purchases, Hotel check-ins, Black Market buys).
  Bad habit logging and coin earning MUST continue normally.
- **FR-015**: Only one death event MUST be recorded per HP-changing event. If the
  character is already dead (prior death event exists without a subsequent respawn),
  further HP damage MUST be applied but no additional death event created.

### Key Entities

- **Health Points (HP)**: A numeric resource representing the character's vitality.
  Calculated as the sum of all HP entries in the Activity Log (including the initial
  grant entry). Reduced by bad habits and overdraft penalties; recovered by hotel
  check-ins. Reaching zero triggers immediate death. On respawn, a new positive HP
  entry is created in the Activity Log.
- **Death Event**: A recorded state when HP reaches zero. Displays the player's
  self-defined real-world penalty. Recoverable via manual respawn.
- **Coin Balance**: An in-game currency earned through goals and tasks, spent at
  the Market, Hotels, and Black Market. Can go negative (overdraft).
- **Overdraft Penalty**: A periodic HP deduction applied to characters with negative
  coin balances. Configurable frequency and severity. Connects the economy to the
  HP system.
- **Hotel**: An HP recovery mechanism with three price/recovery tiers (Budget,
  Ordinary, Premium). Costs coins to use.
- **Black Market**: A special shop offering retroactive check-in recovery for
  missed habits. Costs coins to use.
- **Market Purchase**: A player-defined reward item that costs coins. Represents
  real-world treats the player grants themselves.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every bad habit logged by the player results in an immediate,
  visible HP decrease on the character page — verified by logging 3 different
  bad habits and confirming each produces the correct HP change.
- **SC-002**: Death triggers reliably at exactly HP ≤ 0 with zero false positives
  (no death when HP > 0) and zero missed deaths (no survival when HP ≤ 0) —
  verified by testing boundary values at HP = 1, HP = 0, and HP = -1.
- **SC-003**: Respawn resets HP to exactly the configured starting value in 100%
  of cases — verified by respawning after deaths at different HP levels (-5, -100,
  0).
- **SC-004**: Coin balance is always the exact sum of all transactions — verified
  by performing 10+ mixed earn/spend transactions and confirming the final balance
  matches the arithmetic total.
- **SC-005**: Overdraft penalties apply on the correct schedule (weekly/biweekly)
  and only when the balance is negative — verified by running the check across
  multiple cycles with positive and negative balances.
- **SC-006**: Hotel check-ins correctly deduct coins and recover HP for all three
  tiers — verified by testing each tier and confirming both the coin deduction and
  HP recovery match the tier's configured values.

## Assumptions

- Phase 1 (Foundation) is complete: all 33 databases exist, the Notion client is
  operational, the config/settings system is functional, and structured logging is
  available.
- HP and coin values are integers. No fractional HP or fractional coins.
- The activity history (Activity Log database) is the single source of truth for
  all HP changes and coin transactions. No separate ledger exists. Both HP and coin
  balances are pure sums of their respective Activity Log columns.
- Death is not permanent. There is no limit on the number of times a player can
  die and respawn.
- The starting HP value is the same for every respawn (no scaling with level or
  death count).
- Black Market check-in recovery does not repair broken streaks — streaks are
  handled by the streak engine in Phase 3.
