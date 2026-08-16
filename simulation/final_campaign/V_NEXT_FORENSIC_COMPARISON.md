# 🔬 FORENSIC COMPARISON REPORT: CURRENT CHAMPION vs V_NEXT

## 1. Artifact Verification & Randomness Audit
- **Target File**: `simulation/final_campaign/V_NEXT/main.py`
- **Keyword Scan**:
  - `random`: 0 occurrences
  - `random.sample`: 0 occurrences
  - `random.choice`: 0 occurrences
  - `randint`: 0 occurrences
  - `shuffle`: 0 occurrences
  - `fallback`: 0 occurrences
  - `except Exception`: Line 90 (`get_card` boundary check only)
- **Random Fallback Status**: `RANDOM_FALLBACK_PRESENT=NO`

---

## 2. Differential Code Analysis (Champion vs V_NEXT)

| Dimension | Champion Behavior | V_NEXT Behavior | Measured Effect & Failure Mode |
| :--- | :--- | :--- | :--- |
| **A. Prime Catcher Timing** | Played whenever opponent has a bench Pokemon (`score = 88,000`). | Gated behind `has_lethal_gust` (`score = 99,000`) or `need_switch`. | **Failure Mode**: V_NEXT held Prime Catcher (0.39/game vs 0.43/game), missing early tempo disruption in mirrors. |
| **B. Boss's Orders Timing** | Proactive gust on any high-value target (`score = 96,000-97,000`). | Strict lethality check (`score = 99,500`), lower base score otherwise. | **Failure Mode**: V_NEXT played Boss less often (0.64/game vs 0.74/game), allowing mirror opponent to charge undisturbed. |
| **C. Switch Activation** | `score = 65,000` when `need_switch`. | `score = 85,000` when `need_switch`. | **Effect**: Higher 230 Gale Thrust activation (1.16/game vs 1.00/game), but consumed switches rapidly. |
| **D. Guaranteed KO Scoring** | `+5,000` base KO priority. | `+30,000` base KO priority. | **Effect**: Zero missed lethal attacks; strong vs Lucario (+3.0%) and Crustle (+10.7%). |
| **E. Exception Handling** | Swallowed loop errors with `random.sample`. | 100% Deterministic legal output list. | **Effect**: Eliminates non-reproducible random errors. |

---

## 3. Matchup-Level Head-to-Head Comparison (300 Games Each)

```text
=========================================================================================================
=== 🥊 300-GAME MATCHUP COMPARISON: CURRENT CHAMPION vs V_NEXT ===
=========================================================================================================
Archetype Matchup                   | Current Champion Record | V_NEXT Candidate Record | Delta (V_NEXT vs Champ)
------------------------------------|-------------------------|-------------------------|------------------------
1. Mega Lucario ex (Fighting)       | 266 / 300 (88.7% Win)   | 275 / 300 (91.7% Win)   | 🟢 +3.0% Improvement
2. Crustle ex-Immunity Wall         | 124 / 300 (41.3% Win)   | 156 / 300 (52.0% Win)   | 🟢 +10.7% Improvement
3. Archaludon ex (Metal Fortress)   | 298 / 300 (99.3% Win)   | 300 / 300 (100.0% Win)  | 🟢 +0.7% Improvement
4. Alakazam ex (Psychic Disruption) | 300 / 300 (100.0% Win)  | 300 / 300 (100.0% Win)  | ⚪ +0.0% (Parity)
5. Dragapult ex (Spread Damage)     | 300 / 300 (100.0% Win)  | 299 / 300 (99.7% Win)   | ⚪ -0.3% (Parity)
6. Iono Bellibolt ex (ChatGPT)      | 263 / 300 (87.7% Win)   | 259 / 300 (86.3% Win)   | ⚪ -1.3% (Parity)
7. Mega Starmie ex (Water Turbo)    | 245 / 300 (81.7% Win)   | 239 / 300 (79.7% Win)   | 🔴 -2.0% (Slight drop)
8. Lopunny Symmetrical Mirror       | 167 / 300 (55.7% Win)   | 143 / 300 (47.7% Win)   | 🔴 -8.0% (Mirror Deficit)
=========================================================================================================
```

---

## 4. Action-Level Telemetry Forensics (100 Direct Games)

- **Switch Played / Game**: Champion: **1.09** | V_NEXT: **1.15**
- **Prime Catcher Played / Game**: Champion: **0.43** | V_NEXT: **0.39** *(V_NEXT hoards ACE SPEC)*
- **Boss's Orders Played / Game**: Champion: **0.74** | V_NEXT: **0.64** *(V_NEXT hoards Supporter)*
- **Retreat Used / Game**: Champion: **3.10** | V_NEXT: **2.95**
- **230 Gale Thrust Attacks / Game**: Champion: **1.00** | V_NEXT: **1.16** *(V_NEXT triggers more 230 hits)*
- **60 Gale Thrust Attacks / Game**: Champion: **3.56** | V_NEXT: **3.54**
- **Average Prizes Taken / Game**: Champion: **3.76** | V_NEXT: **3.66**

---

## 5. Loss Classification & Delta

1. **Mirror Gust Hoarding (Top Cause of Mirror Loss)**:
   - In mirror matches, both decks have 330 HP Megas that take 2 hits to KO.
   - Champion plays Boss/Prime Catcher proactively to drag a bench Buneary/Fan Rotom for cheap 1-hit prizes.
   - V_NEXT holds Boss/Prime Catcher waiting for a "lethal game win", conceding early prize leads.
2. **Setup Parity**:
   - Both agents achieve 99.5%+ Turn 2 Mega Lopunny evolution.
3. **Crustle / Lucario Mastery**:
   - V_NEXT is demonstrably superior vs Crustle (+10.7%) and Lucario (+3.0%) due to precise damage targeting.

---

## 6. Top 3 Regressions in V_NEXT

1. **Prime Catcher Hoarding**: V_NEXT plays Prime Catcher **0.39 times/game vs Champion 0.43 times/game**, waiting for lethal game-ending conditions rather than tempo disruption.
2. **Boss's Orders Hesitation**: V_NEXT plays Boss **0.64 times/game vs Champion 0.74 times/game**, reducing pressure on the opponent's bench setup.
3. **Mirror Match Win Rate Deficit**: Direct symmetrical mirror win rate dropped to **46.6% (233W-267L)** across 500 games due to passive gusting.

---

## 7. Top 3 Useful V_NEXT Improvements

1. **Crustle Anti-Wall Scoring**: V_NEXT improved win rate against Crustle ex-immunity by **+10.7% (52.0% vs 41.3%)**.
2. **Mega Lucario Knockout Precision**: V_NEXT improved win rate against Lucario by **+3.0% (91.7% vs 88.7%)**.
3. **Zero-Randomness Runtime Safety**: 100% deterministic execution with zero stochastic fallback calls.

---

## 8. Final Recommendation
- **RECOMMENDATION**: **KEEP_CHAMPION** (Do NOT submit V_NEXT; maintain current champion in production).
