# 🛡️ Mandatory Quality Assurance & Cross-Check Protocol

---

## 🎯 Purpose & Scope

This document defines the **Non-Negotiable Verification Protocol** that must be executed every time a change, heuristic update, deck modification, or submission packaging is performed. 

Every rule in this protocol was born from an empirical discovery, simulation pitfall, or replay loss audit. **No code may be submitted or merged without 100% compliance with this checklist.**

---

## 📋 The 10 Ironclad Engineering Checkpoints

```
┌──────┬───────────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Step │ Verification Category                     │ Required Automated Check                                    │
├──────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│  1   │ Python Syntax & AST Validation            │ ast.parse() with ZERO SyntaxErrors or undefined tokens       │
│  2   │ Exact 60-Card Deck Compliance             │ Exactly 60 integers in deck.csv (No missing/extra cards)    │
│  3   │ Dynamic Path Resolution Safety            │ Both Kaggle (/kaggle_simulations/) & Local __file__ fallback│
│  4   │ Simulator State Invariant: appearThisTurn │ NEVER use appearThisTurn alone; MUST check switched_turn    │
│  5   │ Lethal Damage & Knockout Priority         │ Full 230 Gale Thrust + Spiky Hopper lethal prize check      │
│  6   │ Mill-Aware Draw Suppression               │ Suppress all draw supporters/abilities when deckCount ≤ 3   │
│  7   │ Guaranteed Pivot Retreat Gate             │ Verify bench has free retreat tool before executing switch  │
│  8   │ Multi-OS Native Binary Integrity          │ Verify cg.dll, libcg.so, libcg-arm64.so, libcg.dylib exist  │
│  9   │ Sandbox Live Decision Stress Test         │ Run 100 live sandbox battles with 0 exceptions or timeouts  │
│ 10   │ Multi-Archetype Meta Gauntlet Benchmark   │ Benchmark against full 5-deck meta (Mirror, Lucario, etc.)  │
└──────┴───────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Protocol Instructions

### Checkpoint 1: Python AST & Syntax Validation
- **Requirement:** Run `ast.parse(code)` on `main.py` before any packaging.
- **Rule:** Zero syntax errors, zero trailing semicolons, and clean standard imports.

### Checkpoint 2: Exact 60-Card Deck Audit
- **Requirement:** Parse `deck.csv` line by line.
- **Rule:** `len(deck) == 60` is strictly enforced. Card counts must adhere to format limits (Max 4 of any card, Max 1 ACE SPEC).

### Checkpoint 3: Multi-Environment Path Resolution
- **Requirement:** Deck loading must use the tri-level path resolver:
  ```python
  file_path = "deck.csv"
  if not os.path.exists(file_path):
      file_path = "/kaggle_simulations/agent/deck.csv"
  if not os.path.exists(file_path):
      file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck.csv")
  ```

### Checkpoint 4: Simulator State Invariant (`appearThisTurn`)
- **Historical Error Discovered:** In the engine, `appearThisTurn` is **ONLY True** when a Pokémon is played/evolved from hand, **NOT when it switches or retreats**.
- **Mandatory Implementation:**
  ```python
  switched = _turn_state.get('switched_this_turn', False) or (my_active is not None and my_active.appearThisTurn)
  if switched:
      effective_damage = atk.damage + 170
  ```

### Checkpoint 5: Lethal Damage & Knockout Priority Gate
- **Requirement:** When calculating `OptionType.ATTACK`:
  ```python
  if op_active and op_active.hp <= effective_damage:
      score += 5000  # Highest priority to seal guaranteed prize takes
  ```

### Checkpoint 6: Mill-Aware Draw Suppression
- **Requirement:** When `my_state.deckCount <= 3`, set `no_draw = True`.
- **Rule:** Score Hilda, Lillie, and Fan Rotom ability as `-1` to prevent losing to empty deck.

### Checkpoint 7: Guaranteed Return Pivot Safety
- **Requirement:** Before switching out an active Mega Lopunny ex, check:
  ```python
  def is_guaranteed_return_pivot(p: Pokemon) -> bool:
      if not has_retreated:
          has_tool = any(getattr(t, 'id', None) in (AIR_BALLOON, RESCUE_BOARD) for t in getattr(p, 'tools', []))
          if has_tool or len(p.energies) >= 1:
              return True
      return False
  ```

### Checkpoint 8: Multi-OS Native Binary Packaging
- **Requirement:** Archives must include all four native simulator builds inside `cg/`:
  * `cg.dll` (Windows x64)
  * `libcg.so` (Linux x64 - Kaggle environment)
  * `libcg-arm64.so` (Linux ARM64)
  * `libcg.dylib` (macOS)

### Checkpoint 9: Live Sandbox Stress Test (100 Matches)
- **Requirement:** Run 100 consecutive matches against itself in sandbox.
- **Rule:** Must complete in `< 5.0 seconds` with **ZERO crashes, ZERO invalid actions, and ZERO unhandled exceptions**.

### Checkpoint 10: Multi-Archetype Meta Gauntlet Benchmark
- **Requirement:** Every candidate build must be tested against all 5 tournament archetypes:
  1. Mirror Baseline 519
  2. Mega Lucario ex (Fighting Power Pro)
  3. Alakazam ex (Psychic Disruption)
  4. Mega Starmie ex (Water Turbo)
  5. Archaludon ex (Metal Fortress)
- **Passing Threshold:** Aggregate Win Rate $\ge 60.0\%$.

---

## ⚡ Automated Execution Command

To execute this entire 10-checkpoint protocol automatically in one command:
```bash
python -u "D:\Project\PTCG_AI_Battle_Challenge\simulation\automated_cross_check_suite.py"
```
