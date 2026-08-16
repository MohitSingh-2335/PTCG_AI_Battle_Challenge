# ⚡ Pokémon TCG AI Battle Challenge — Championship Engine

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-blue.svg)](https://python.org)
[![Tournament Win Rate](https://img.shields.io/badge/Tournament%20Meta%20Win%20Rate-65.20%25-brightgreen.svg)]()
[![Matches Simulated](https://img.shields.io/badge/Matches%20Benchmarked-31%2C000%2B-orange.svg)]()
[![Status](https://img.shields.io/badge/Kaggle%20Submission-Verified%20%26%20Ready-success.svg)]()

A high-performance heuristic & simulation-optimized AI battle engine for the **Kaggle Pokémon Trading Card Game (PTCG) AI Battle Challenge**.

Built upon empirical analysis of **193 real tournament match replays** and calibrated across **39 rigorous experiments (>31,000 simulated games)**, this agent achieves a **65.20% aggregate tournament win rate** across all major competitive archetypes.

---

## 🏆 Tournament Performance Matrix

Evaluated across canonical multi-archetype gauntlet matches against the top winning deck formations in the competition:

| Opponent Archetype Formation | Matchup Status | Win Rate | Key Tactical Counter |
|:---|:---:|:---:|:---|
| **Mega Lucario ex** *(Fighting Weakness Threat)* | 👑 **DOMINANT** | **97.0% – 100.0%** | Gale Thrust 230-dmg tempo + Bench buffer |
| **Mega Starmie ex** *(Water Turbo Acceleration)* | 🏆 **DOMINANT** | **63.0%** | Mist Energy effect shield & Poffin setup |
| **Alakazam ex** *(Hammer & Status Disruption)* | 🏆 **DOMINANT** | **57.0%** | Mist Energy blocks special attack effects |
| **Archaludon ex** *(Metal Fortress Bulk)* | 🏆 **POSITIVE** | **56.0%** | Free-pivot Gale Thrust 2-turn cycle |
| **Mirror Baseline 519** *(Pure Lopunny ex)* | 🏆 **POSITIVE** | **53.0%** | Poffin bench routing & zero mulligan rate |
| **⭐ OVERALL COMPETITIVE FIELD AVERAGE** | 👑 **CHAMPION** | **65.20%** | **326 Wins / 500 Matches** |

---

## 🔬 Core Strategy & Architecture

```
                               ┌────────────────────────────────┐
                               │   Turn 1: Setup & Formation    │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
             ┌──────────────────────────────────────────────────────────────────┐
             │  Buddy-Buddy Poffin (1086) ──> Buneary (848) + Fan Rotom (174)    │
             │  Rotom "Assault Landing"   ──> Free card draw & deck shuffle     │
             └─────────────────────────────────┬────────────────────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │  Turn 2+: Evolution & Mobility │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
             ┌──────────────────────────────────────────────────────────────────┐
             │  Master Ball (1125)        ──> Guaranteed Mega Lopunny ex (849)  │
             │  Air Balloon (1174) / Tool ──> Guaranteed 0-Cost Return Pivot    │
             │  Mist Energy (11)          ──> Immune to attack effects/counters │
             └─────────────────────────────────┬────────────────────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │  Continuous 230-Damage Tempo   │
                               │  Switch Pivot ──> Gale Thrust  │
                               └────────────────────────────────┘
```

### 🔑 The 5 Empirical Laws of the Format
1. **The Poffin Density Sweet Spot (Exactly 2 Copies):** Eliminates lone-active bench-outs on Turn 1 while preventing dead draws on Turns 4–8.
2. **The 6-Basic Minimum (4 Buneary + 2 Fan Rotom):** Prevents opening-hand mulligans and early bench-out defeats.
3. **Master Ball (`1125`) ACE SPEC Supremacy:** Outperforms all other ACE SPECs by guaranteeing Turn 2 Mega evolution.
4. **Draw Supporter Velocity (Hilda 94k & Lillie 93k):** Leads hand sequencing to supply continuous Switch cards and basic energies.
5. **The 5-Tool Mobility Fortress (3 Air Balloon + 2 Rescue Board):** Guarantees zero-cost retreat for every benched Pokémon.

---

## 🎴 Optimized 60-Card Tournament Deck List (`v10`)

```text
Pokémon (10):
  4x Buneary (848)
  4x Mega Lopunny ex (849)
  2x Fan Rotom (174)

Trainers & Items (30):
  4x Mega Signal (1145)
  4x Ultra Ball (1121)
  1x Master Ball ACE SPEC (1125)
  4x Switch (1123)
  3x Night Stretcher (1097)
  3x Air Balloon (1174)
  2x Rescue Board (1157)
  4x Hilda (1225)
  3x Lillie's Determination (1227)
  2x Buddy-Buddy Poffin (1086)

Energy (20):
  2x Mist Energy (11) [Special Energy - Blocks Effects]
  18x Basic Water Energy (3)
```

---

## 📦 Project Structure

```
PTCG_AI_Battle_Challenge/
├── README.md                                  # Comprehensive project documentation
├── submission_v10_mist_poffin_master.tar.gz   # 👑 Official Verified Kaggle Package (65.20% Win Rate)
├── submission_v9_poffin_master.tar.gz         # 🥈 Mirror Peak Package (50.20% Win Rate)
├── submission_v8.tar.gz                       # 🛡️ Protected Golden Baseline (512 Elo)
├── submission_full_eval_package.tar.gz        # Complete standalone evaluation bundle
│
├── docs/                                      # Master Research Reports & Knowledge Bases
│   ├── COMPREHENSIVE_193_REPLAY_META_REPORT.md# Forensic audit of 193 tournament replays
│   ├── COMPREHENSIVE_EXPERIMENTS_CATALOG.md   # Catalog of all 39 experiments benchmarked
│   ├── MEGA_EXPERIMENT_SUITE_REPORT.md        # 10-experiment automated gauntlet report
│   ├── FUTURE_EXPERIMENTS_AND_STRATEGY.md     # Strategy notes and future micro-tuning roadmap
│   ├── ALL_ARCHETYPES_DECK_FORMATIONS.md      # Deck lists of all 5 tournament archetypes
│   ├── MASTER_REPLAY_LOSS_AUDIT.md            # Root-cause analysis of match losses
│   └── Rule.md                                # Official simulation engine rule book
│
├── simulation/                                # Simulation & Benchmark Engine
│   ├── candidate_meta/                        # Isolated candidate sandbox environment
│   │   ├── main.py                            # Production heuristic scoring agent
│   │   ├── deck.csv                           # 60-card candidate list
│   │   └── cg/                                # Native C++ battle simulation engine
│   ├── submission/                            # Protected golden baseline build
│   ├── baseline_519.py                        # Reference mirror baseline agent
│   ├── agent_lucario.py                       # Mega Lucario ex reference agent
│   └── Data/                                  # Replay datasets & match logs
│
└── archive/                                   # Historical Submissions & Deprecated Builds
    └── historical_submissions/                # Deprecated submission archives (v1–v7)
```

---

## ⚡ How to Run Simulations Locally

### Prerequisites
- Python 3.10+ (Tested on Windows, Linux, and macOS)
- Standard library dependencies (`collections`, `tarfile`, `time`, `json`, `math`)

### 1. Run a 1,000-Game Mirror Benchmark:
```bash
cd simulation/candidate_meta
python test_advanced_experiments.py
```

### 2. Run the Full Multi-Archetype Tournament Gauntlet:
```bash
python -u "simulation/candidate_meta/multi_meta_tournament_evaluator.py"
```

### 3. Verify Submission Archive Pre-Flight:
```bash
python -u "simulation/final_preflight_v10.py"
```

---

## 📄 License & Attribution
Developed for the **Kaggle Pokémon TCG AI Battle Challenge**. Built with the `cg` simulation engine bindings.