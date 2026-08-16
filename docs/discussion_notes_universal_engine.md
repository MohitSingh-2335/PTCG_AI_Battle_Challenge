# 🗺️ Master Roadmap: The 10 Subsystems to Make the Agent 100% Universal

---

## 1. Complete State-Tree Lookahead (1–2 Turn Simulation Engine)
* **What it is:** Instead of judging moves greedily based on the current instant, the agent simulates the next 1–2 turns (using the built-in `cg` game engine) before picking an action.
* **Current Limitation:** The agent picks the best move *right now*, but doesn't simulate if that move leaves it vulnerable to an opponent counter-attack on the next turn.
* **Universal Solution:**
  * Simulate: *"If I play Switch and attach Energy to Active, what is the opponent's maximum counter-attack damage next turn?"*
  * If the simulated outcome leads to a loss, the agent automatically pivots to an alternative move.
* **Impact:** Completely eliminates 100% of "greedy" misplays.

---

## 2. Dynamic Deck List Optimization (Poffin / Poké Pad Engine)
* **What it is:** Optimizing card distribution to eliminate opening-hand bricking.
* **Current Limitation:** Running 22 Water Energies and only 6 Basic Pokémon means that in 1 out of 25 games, drawing 8 cards with Lillie gives 5 energies and 0 basics.
* **Universal Solution:**
  * Replace 4 excess Water Energies (22 $\rightarrow$ 18) with **4 copies of `Buddy-Buddy Poffin` (ID 1086)** or **`Poké Pad` (ID 1152)**.
* **Impact:** Guarantees that every opening hand places 2 basics on Turn 1 without discards, eliminating Turn 2–3 bench-out losses.

---

## 3. Semantic Card Skill & Ability Parsing Engine
* **What it is:** A generalized text and attribute parser for all cards in the Pokémon TCG database.
* **Current Limitation:** Uses specific card IDs (58, 229, 618, 1247) and keyword lists.
* **Universal Solution:**
  * Parse all card text directly from `all_card_data()` and `all_attack()`:
    * Damage shields (*"prevent all damage from ex / Tera / Basics"*).
    * Status conditions (*"Asleep / Paralyzed / Poisoned"*).
    * Energy acceleration (*"attach 2 energies from discard/deck"*).
    * Hand disruption (*"shuffle hand and draw 4"*).
* **Impact:** The agent automatically knows how to counter ANY new card or expansion without hardcoding.

---

## 4. Proactive Hand Disruption & Reset Counterplay (Iono / Judge / Carmine)
* **What it is:** Managing hand size to minimize losses to opponent disruption cards.
* **Current Limitation:** Holds cards in hand passively; when opponent plays *Iono* or *Judge*, key pieces are shuffled away.
* **Universal Solution:**
  * If our hand has 7+ cards and opponent is close to taking prizes, dump expendable items (Balls, Tools) to the field before ending turn.
  * If our hand is clogged with dead cards, aggressively use *Ultra Ball* or *Lillie* to refresh the hand.
* **Impact:** Protects critical win conditions from opponent disruption.

---

## 5. Multi-Plan Evolution & Dynamic Branching Tactics
* **What it is:** Explicit branching strategies based on hand and board state:
  * **Plan A (Turbo Mega):** When Buneary + Mega + Energy are present $\rightarrow$ execute 230 dmg Gale Thrust rush.
  * **Plan B (Fan Rotom Setup & Filter):** When Buneary is missing $\rightarrow$ use *Fan Rotom* Fan Call / Assault Landing to tutor 3 Colorless basics into hand.
  * **Plan C (Attrition & Night Stretcher Loop):** When an active Mega is KO'd $\rightarrow$ use *Night Stretcher* to immediately revive Buneary, evolve, and attack on the same turn.
  * **Plan D (Prize-Denial Defensive Wall):** Against heavy Fighting attackers ($>300$ dmg) $\rightarrow$ feed 1-prize *Fan Rotom* (-30 Fighting resistance) to prevent 3-prize trades.
* **Impact:** The agent always has a winning path, even with the worst possible card draws.

---

## 6. Exact Mathematical Prize-Trade Clock
* **What it is:** Calculating turns-to-victory for both players.
* **Universal Solution:**
  * Calculates: $\text{Clock}_{\text{Us}} = \lceil \text{Prizes Remaining} / 2 \rceil$ vs $\text{Clock}_{\text{Opp}}$.
  * If $\text{Clock}_{\text{Us}} \le \text{Clock}_{\text{Opp}}$, stay aggressive.
  * If $\text{Clock}_{\text{Opp}} < \text{Clock}_{\text{Us}}$ (Opponent is 1 turn away from winning), execute defensive disruption (Gusting a heavy retreat target, retreating to single-prize bait, or stalling).
* **Impact:** Guarantees winning tight 1-turn endgame races.

---

## 7. Opponent Threat Meter & Intelligent Gusting (Boss's Orders)
* **What it is:** Dynamic targeting of the opponent's bench.
* **Universal Solution:**
  * **Threat Elimination:** Gust out an opponent's benched attacker before it gets fully energized.
  * **Prize Sniping:** Gust out an easy 2-prize/3-prize target (e.g., *Fezandipiti ex* or *Squawkabilly ex* at low HP) for an immediate win.
  * **Stall Trapping:** Gust a heavy 0-energy Pokémon with high retreat cost (3–4 energy) to trap it in the active spot while building our board.
* **Impact:** Unlocks high-level control strategies used by top human players.

---

## 8. Adaptive Tool & Stadium Control
* **What it is:** Smart timing for equipping tools and playing Stadiums.
* **Universal Solution:**
  * Never play a Stadium immediately if the opponent's Stadium isn't hurting us; hold our Stadium to overwrite their critical Stadium (e.g. *Neutralization Zone*, *Artazon*).
  * Hold *Air Balloon* until a Mega is placed on board rather than equipping it to a sacrificial basic.
* **Impact:** Maximizes resource efficiency.

---

## 9. Board-Wide Energy Economy & Math Engine
* **What it is:** Global energy allocation optimization.
* **Universal Solution:**
  * Calculates total energy needed across the entire field: $\text{Energy Required} = \text{Active Cost} + \text{Backup Bench Cost}$.
  * Stops attaching once all active attackers are powered, reserving remaining energies for recovery or discarding.
* **Impact:** 0% wasted energy attachments throughout the game.

---

## 10. Deck-Agnostic Modular Core
* **What it is:** Generalizing the agent so it works with any deck archetype.
* **Universal Solution:**
  * Decouple the core decision engine from specific card IDs so that whether you play *Mega Lopunny*, *Charizard ex*, *Dragapult ex*, or *Roaring Moon*, the AI dynamically reads the deck and executes the optimal game plan automatically.
* **Impact:** Universal applicability across all current and future PTCG tournament formats.

---

## 11. 🕵️ Forensic Discoveries & Habits Mined from All 145 Replays

From our deep forensic step-by-step mining of all 145 metagame replays, we uncovered 5 critical habits and tactics utilized by top leaderboard agents:

### 1. The "Bench Draw Engine" (*Dudunsparce*, *Drakloak*, *Alakazam*)
* **The Discovery:** Top players frequently search *Alakazam* (25 times), *Kadabra* (16 times), *Dudunsparce* (12 times), and *Drakloak* (7 times) to sit on the bench.
* **Why Top Players Do This:** Abilities like *Run Away Draw* (Dudunsparce) and *Recon Directive* (Drakloak) allow drawing 2–4 extra cards every turn from the bench without consuming the 1-Supporter-per-turn limit.
* **Countermeasure:** When our agent faces these engines, prioritize gusting (*Boss's Orders*) or knocking out their draw engines early before their hand snowballs.

### 2. Multi-Target Bench Sniping (*Munkidori* & *Shadow Bullet*)
* **The Discovery:** *Munkidori* (Adrena-Brain) moves 30 damage counters from their damaged Pokémon directly onto our benched Bunearys, and *Marnie's Grimmsnarl ex* (*Shadow Bullet* - 180 dmg) hits both Active and Bench simultaneously.
* **Tactical Need:** Our agent must evaluate the HP of benched basics (*Buneary* at 70 HP) and evolve them into 330 HP *Mega Lopunny ex* before they get sniped on the bench.

### 3. The 0-Cost Pivot Buffer Promotion (*Abra*, *Dunsparce*)
* **The Discovery:** When an active Pokémon is knocked out, top players promote 0-retreat or single-prize Pokémon (*Abra*, *Dunsparce*) 65% of the time, rather than their main attacker.
* **Why:** This gives them a "free look" at their top-deck draw at the start of their turn before deciding whether to retreat into Attacker A, Attacker B, or play a Supporter.

### 4. Turn 1 Setup Attacks (*Powerful Hand*, *Filch*, *Allure*)
* **The Discovery:** If unable to deal meaningful damage on Turn 1, top players use 0-damage or low-damage setup attacks that draw 2 cards (*Allure*), steal cards (*Filch*), or build hand size (*Powerful Hand*).
* **Tactical Need:** Never waste Turn 1 passing; if no KO is possible, utilize setup attacks to dig for evolution pieces.

---

## 12. ⏱️ Micro-Sequencing Tactics (Order of Operations)

* **Rule 1: Deck Thinning Before Draw:** Always play Search cards (*Mega Signal*, *Buddy-Buddy Poffin*, *Ultra Ball*) BEFORE playing Draw Supporters (*Lillie's Determination*). Removing Pokémon from the deck increases the probability of drawing critical Energy and Supporters from Lillie.
* **Rule 2: Check Discard Before Searching:** Always check if a needed card (e.g. *Mega Lopunny*) is in the Discard pile before playing *Ultra Ball*; if it's in the discard, use *Night Stretcher* instead of burning cards on Ultra Ball.
* **Rule 3: Switch Before Attach for Gale Thrust:** If active Mega Lopunny has 0 energy and hand has 1 Energy + 1 Switch:
  * **Correct Order:** Play *Switch* first $\rightarrow$ promote second Mega Lopunny $\rightarrow$ attach Energy $\rightarrow$ attack with activated +170 dmg boost (230 total dmg).
  * **Incorrect Order:** Attach energy to current active $\rightarrow$ attack deals only 60 dmg.

---

## 13. 🧪 Status Condition Mitigation & Active Recovery Engine

* **Poison & Burn Math:**
  * Poison deals 10 dmg between turns; Burn deals 20 dmg with a 50% coin flip to cure.
  * If our active Mega has 30 HP and is Poisoned/Burned, attacking will cause it to faint *at the end of our turn*, denying us a prize trade.
  * **The Fix:** Retreat or play *Switch* to cleanse the status condition before attacking.
* **Asleep & Paralyzed Lockout:**
  * Asleep/Paralyzed Pokémon cannot attack or retreat manually.
  * **The Fix:** The agent must automatically prioritize *Switch* or *Rescue Board* to instantly unlock the active spot.

---

## 14. 🏁 Prize-Mapping Matrix (Optimal Prize Paths)

To win in the minimum number of turns, the AI maps out the fastest mathematical prize path:

```
┌────────────────────────────┬─────────────────────────────┬──────────────────────────┐
│ Opponent Board Archetype   │ Optimal Prize Sequence      │ Total Turns to Win       │
├────────────────────────────┼─────────────────────────────┼──────────────────────────┤
│ Mega Ex + Standard Ex Decks│ 3 Prizes (Mega) + 2 (Ex) + 1│ 3 Attacks (Turns 2, 4, 6)│
│ Single-Prize Swarm Decks   │ 1 + 1 + 1 + 1 + 1 + 1       │ Target High-HP Anchors   │
│ Multi-Prize Hybrid         │ Gust 2-Prize Target First   │ 2 Mega KOs = 6 Prizes!   │
└────────────────────────────┴─────────────────────────────┴──────────────────────────┘
```

---

## 15. 🚀 Native C++ Monte Carlo Engine (`SearchBegin` / `SearchStep`)
* **Discovery in Codebase (`cg/sim.py`):**
  * The simulator C++ kernel includes pre-compiled C++ Monte Carlo search routines: `lib.SearchBegin`, `lib.SearchStep`, and `lib.SearchEnd`.
  * This allows running ultra-fast C++ lookahead simulations directly inside the Kaggle time limit (600s total overage buffer).
* **Impact:** Blends heuristic speed with C++ forward tree search for near-perfect tactical play.

---

## 16. 📜 Critical Simulator Ruling Nuances (Official Competition Ground Truth)
* **Gale Thrust Evolution Timing:** In the simulator, *Mega Lopunny ex* checks if *Mega Lopunny ex itself* moved from Bench to Active. Evolving Buneary on the **Bench** before switching ensures the 230 damage boost triggers 100% of the time.
* **Target Resolution in C++ Kernel:** Multi-target attacks and abilities (like *Mega Zygarde ex Nullifying Zero*) resolve automatically from left to right on the board.
* **Setup Phase Optionality:** `minCount` controls whether benching is mandatory. If `minCount == 0`, the agent can strategically hold cards in hand rather than over-bench.

---

## 17. ⚔️ Top 30 High-Damage Threat Registry (The Lethal Danger List)

Our agent's threat evaluation engine monitors these 10 highest-damage attackers in the tournament database:
1. **Pikachu ex (ID 210):** *Topaz Bolt* — **300 Dmg** (Cost: 3)
2. **Mega Latias ex (ID 754):** *Illusory Impulse* — **300 Dmg** (Cost: 3)
3. **Gouging Fire ex (ID 46):** *Blaze Blitz* — **260 Dmg** (Cost: 3)
4. **Mega Mawile ex (ID 695):** *Huge Bite* — **260 Dmg** (Cost: 3)
5. **Black Kyurem ex (ID 179):** *Black Frost* — **250 Dmg** (Cost: 4)
6. **N's Zekrom (ID 906):** *Rampaging Thunder* — **250 Dmg** (Cost: 4)
7. **Hop's Zacian ex (ID 299):** *Brave Slash* — **240 Dmg** (Cost: 4)
8. **Miraidon ex (ID 313):** *Cyber Drive* — **220 Dmg** (Cost: 3)
9. **Pikachu ex (ID 328):** *Thunder* — **220 Dmg** (Cost: 3)
10. **Zacian ex (ID 336):** *Slashing Strike* — **210 Dmg** (Cost: 3)

---

## 18. 🧰 Game-Changing Tech Cards & Counterplay Matrix

* **Briar (ID 1201):** Takes **1 extra prize card** if knocking out an active with a Tera Pokémon when opponent has 2 prizes left. (Counterplay: Never leave our active damaged at 2 prizes).
* **Hero's Cape (ID 1159):** Gives **+100 HP** to attached Pokémon. (Counterplay: Calculate extra 100 HP in lethal prediction math).
* **Gravity Mountain (ID 1252):** Gives all Stage 2 Pokémon **-30 HP**. (Counterplay: Utilize for 1-hit KOs against Stage 2 tanks).
* **Neutralization Zone (ID 1247):** Prevents all damage from Pokémon ex to non-ex. (Counterplay: Chip with non-ex basics or overwrite Stadium).

---

## 19. Codex Audit — Recommended Next Steps for This Agent

> Added after validating the submitted Mega Lopunny agent against the local simulator and replay observations. This is a decision guide, not an implementation checklist: each change must be measured against a fixed baseline before it replaces the submitted agent.

### What is already the right core strategy

The **Mega Lopunny ex + Switch cycling** plan is the strongest part of this project. It gives 230 damage for one Energy whenever *Gale Thrust* is enabled, and the current deck has direct search, recovery, and pivot tools for that plan. Do not replace this core with a generic deck-agnostic engine at the end of the competition.

### Highest-value next upgrade: accurate tactical damage and target evaluation

Improve the existing heuristic rather than adding a broad new subsystem:

1. Calculate whether each available attack is an actual knockout after weakness, resistance, tools, Stadiums, and prevention effects.
2. Score the prize value correctly: normal Pokémon = 1, Pokémon ex = 2, Mega Evolution Pokémon ex = 3.
3. Recognise attacks such as *Spiky Hopper* that ignore effects on the opponent's Active Pokémon.
4. Use the opponent's real typed Energy costs when estimating incoming damage; do not assume that any three Energy can pay a Fire-Fire-Colorless attack.

Why this matters: this directly improves attack, retreat, and promotion decisions every game without changing the deck or introducing search-time risk.

### Second priority: refine the existing bench and promotion policy

Keep at least one backup Pokémon, but do **not** blindly fill the Bench against spread decks. The desired rule is:

* Early game: establish one backup Buneary and one pivot/setup Pokémon when possible.
* Against Dragapult, Alakazam, Froslass, Munkidori, or Grimmsnarl: evolve exposed Buneary early and avoid unnecessary extra 70-HP Bench targets.
* When a Mega is likely to be knocked out for 3 prizes, promote a one-prize pivot only if it meaningfully changes the prize race and does not immediately lose to a bench-out.

This is more reliable than treating every Fighting opponent as identical.

### Third priority: evaluate one deck revision, not many card ideas at once

The notes propose Buddy-Buddy Poffin / Poké Pad. These should only be tested as a single controlled deck variant:

* Candidate: replace **2–4 Water Energy** with **2–4 Buddy-Buddy Poffin**.
* Do not add Poké Pad at the same time: it goes to hand, while Poffin puts low-HP Basics directly on the Bench and is more aligned with preventing bench-out losses.
* Keep exactly 60 cards, no more than four copies of a non-Energy card, and no more than one ACE SPEC.
* Run a matched benchmark against the current 22-Energy deck before adopting it. Track win rate, bench-out losses, deck-out losses, and average time per selection.

The current deck should remain the baseline until this proves better. A deck change is not automatically a bug fix.

### Upgrades to defer unless there is time for a controlled benchmark

* **1–2 turn C++ Monte Carlo search — defer.** Promising, but hidden-information assumptions and the 600-second budget can make an untested rollout weaker or invalid.
* **Full semantic parser for all cards — defer.** Useful long term, but broad text parsing is error-prone; implement only the prevention/damage patterns encountered in replay data.
* **Persistent adaptive memory — do not use.** It can change behavior between games without a trustworthy signal that identifies the cause of a loss. Fixed, reproducible weights are safer for competition evaluation.
* **Boss's Orders / Briar / Stadium control — deck-dependent.** These cards are not in the submitted deck; adding their logic alone provides no benefit.
* **“Guaranteed” anti-brick or “100% universal” claims — do not rely on.** Draws, prize cards, hidden information, and opponent interaction prevent guarantees.

### Concrete testing gate before every future change

1. Preserve a copy of the current working archive.
2. Make one change only.
3. Run at least 50 local games against random legal decisions for crash detection.
4. Replay-fuzz every recorded observation and require zero invalid selections.
5. Compare against the prior version on the same opponent decks/seeds; keep the change only if it improves results without errors.
6. Package only `main.py`, `deck.csv`, and `cg/`; exclude memory files and `__pycache__/`.

### Bottom line

For this competition, the best path is **a dependable Mega Lopunny specialist with accurate combat math and disciplined setup**, not a last-minute attempt at a universal Pokémon TCG engine. The proposed Poffin-only deck variant is the most worthwhile strategic experiment after those agent-level safeguards are stable.
