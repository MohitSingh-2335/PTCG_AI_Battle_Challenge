# 🤖 Pokémon TCG AI Battle Challenge — Master System Guide for Claude

---

## 🎯 Welcome Claude! Project Executive Briefing

This repository contains the complete competitive AI agent codebase for the **Kaggle Pokémon Trading Card Game AI Battle Challenge**.

The agent is built around the **Mega Lopunny ex Turbo (`Buneary #848` → `Mega Lopunny ex #849`)** scoring architecture. It runs in a custom native C++ simulation sandbox with Python bindings (`cg.api`).

---

## 🗺️ Complete Repository Sitemap & Documentation Map

```
PTCG_AI_Battle_Challenge/
├── README.md                                             # Main GitHub project presentation
├── CLAUDE_PROJECT_GUIDE.md                               # Dedicated orientation guide for Claude
├── AUDIT_DOSSIER_FOR_CLAUDE.tar.gz                       # Pre-packaged audit bundle for Claude
├── submission.tar.gz                                     # 100% QA-verified production build
├── submission_v11_perfect_champion.tar.gz                # Official 84.5% tournament champion
│
├── simulation/                                           # Simulation engine & test suites
│   ├── submission/                                       # Official submission directory
│   │   ├── main.py                                       # Production agent source code
│   │   ├── deck.csv                                      # Production 60-card list
│   │   └── cg/                                           # Native C++ binaries (Windows, Linux, macOS)
│   ├── candidate_meta/                                   # Development agent directory
│   ├── automated_cross_check_suite.py                    # 10-Checkpoint automated QA test suite
│   ├── multi_meta_rigorous_evaluator.py                  # Symmetric dual-agent tournament evaluator
│   └── combinatorial_mega_sweep.py                       # 50-deck combinatorial sweep runner
│
└── docs/                                                 # Comprehensive research & audit library
    ├── CLAUDE_COMPLETE_CODEBASE_AND_AUDIT_DOSSIER.md     # Full source code, resolved bugs & review prompt
    ├── MASTER_EXHAUSTIVE_RESEARCH_AUDIT_AND_SOLUTIONS_REPORT.md # Master 15,000-match audit document
    ├── V8_TO_V13_CHRONOLOGICAL_EVOLUTION_AND_CHANGELOG.md # V8 -> V13 version evolution & changelog
    ├── MANDATORY_QUALITY_ASSURANCE_AND_CROSS_CHECK_PROTOCOL.md # The 10 Ironclad QA Checkpoints
    ├── EXHAUSTIVE_50_COMBINATIONS_MEGA_CENSUS.md          # 50-combination tournament census
    ├── RIGOROUS_DUAL_AGENT_TOURNAMENT_AUDIT.md           # Dual-agent tournament benchmarks
    ├── Rule.md                                           # Complete official Kaggle competition rules
    └── Data.md                                           # Card database attributes and specifications
```

---

## 🃏 1. Deck Recipe & Exact Card Database Verification

```
# Core Pokémon (10 cards)
4x Buneary (848)               - Basic (60 HP)
4x Mega Lopunny ex (849)       - Stage 1 Mega Evolution (330 HP, Gale Thrust: 60 / 230 damage)
2x Fan Rotom (174)             - Basic Ability Draw Engine (Assault Landing)

# Core Items & Search (14 cards)
4x Mega Signal (1145)          - Search 2 Mega Pokémon
4x Ultra Ball (1121)           - Discard 2, Search any Pokémon
1x Master Ball ACE SPEC (1125) - Search any Pokémon (No discard)
2x Buddy-Buddy Poffin (1086)   - Search 2 Basic Pokémon (<=70 HP) to Bench
4x Switch (1123)               - Switch Active with Bench
3x Night Stretcher (1097)      - Put Pokémon or Basic Energy from Discard into Hand

# Tools & Mobility (5 cards)
3x Air Balloon (1174)          - Retreat Cost -2
2x Rescue Board (1157)         - Retreat Cost -1 (Free retreat if remaining HP <= 30)

# Supporters (7 cards)
4x Hilda (1225)                - Search 1 Supporter + 1 Basic Energy
3x Lillie's Determination (1227)- Draw until you have 6 cards in hand (8 if Going Second)

# Energies (20 cards)
2x Mist Energy (11)            - Special Energy (Blocks all special attack effects & damage counter placement)
18x Basic Water Energy (3)     - Standard Energy
--------------------------------------------------
Total: Exactly 60 Cards (100% Real Database IDs)
```

---

## 🔍 2. Critical Simulator Engine Invariants & Resolved Bugs

When reviewing the code, be aware of the following solved simulator behaviors:

1. **`appearThisTurn` Native Simulator Invariant:**
   * In the native C++ engine, `pokemon.appearThisTurn` is **ONLY `True`** on the turn a Pokémon evolves or is played from hand. It is **`False`** when retreating or playing Switch.
   * *Solution:* Module-level turn tracking `_turn_state['switched_this_turn']` is synchronized with `appearThisTurn` to calculate Gale Thrust's full 230 damage.
2. **`OptionType.RETREAT` Attribute Safety:**
   * Special conditions (`asleep`, `paralyzed`) exist on `Pokemon` (`my_active`), NOT `PlayerState` (`my_state`).
   * *Solution:* Checked safely with `bool(my_active and (getattr(my_active, 'asleep', False) or getattr(my_active, 'paralyzed', False)))`.
3. **Mill-Aware Draw Suppression Threshold:**
   * In long games, drawing aggressively can lead to self-mill.
   * *Solution:* Suppress draw supporters only when `my_state.deckCount <= (12 if is_mill_threat else 8)`.
4. **`SelectContext.TO_BENCH` Isolation:**
   * Bench placement must never be penalized by cards in hand.
   * *Solution:* `SelectContext.TO_BENCH` assigns fixed high priority to Buneary (`2500`) and Fan Rotom (`2000`).

---

## 🛡️ 3. The 10-Checkpoint Mandatory Quality Assurance Protocol

Before any code modification or release, run:
```bash
python -u "simulation/automated_cross_check_suite.py"
```
This suite automatically verifies:
1. Python AST parse (0 SyntaxErrors).
2. Exactly 60 cards in `deck.csv`.
3. Dynamic path resolution (`/kaggle_simulations/agent/` & local `__file__`).
4. `appearThisTurn` + `switched_this_turn` synchronization.
5. Lethal knockout priority (+5000 score).
6. Mill-aware draw suppression.
7. Guaranteed return pivot mobility gate.
8. Multi-OS binary integrity (`cg.dll`, `libcg.so`, `libcg-arm64.so`, `libcg.dylib`).
9. 100 live sandbox battles (0 exceptions).
10. Multi-archetype meta gauntlet benchmark ($\ge 60.0\%$).

---

## 🎯 4. Suggested Next Research & Improvement Tasks for Claude

If you are reviewing this repository for further improvements, here are the top high-leverage areas to explore:

1. **Energy Management in Lopunny Mirrors:**
   * In Lopunny-vs-Lopunny mirror matches (56%–62% win rate), games are decided by 230 Gale Thrust tempo. Analyze if attaching to bench Lopunny vs active stale Lopunny can be dynamically weighted based on opponent's energy count.
2. **Boss's Orders Integration (`ID 1182`):**
   * Evaluate whether swapping 1 Basic Water Energy for 1x Boss's Orders (`1182`) with targeted lethal gust logic increases late-game prize take consistency.
3. **Multi-Select Priority Validation:**
   * Review `SelectContext.DISCARD` (Ultra Ball discarding 2 cards) and `SelectContext.TO_BENCH` (Poffin selecting 2 basics) to verify optimal index ordering.
