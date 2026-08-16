# 🔬 Master Catalog: 25 Targeted Replay-Loss Experiments & Strategy Roadmap

---

## 🎯 Executive Summary

Following our forensic audit of all **210 tournament replays** and the discovery of specific failure mechanics (Grass weakness nukes, unswitched attack selection, Turn 1 first-mover supporter restrictions, and damaged active prize leaks), we have engineered **25 distinct experimental configurations** grouped into 5 strategic domains.

---

## 📋 The 25 Strategic Experiment Matrix

```
┌────┬─────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ ID │ Experiment Title                                │ Strategic Hypothesis & Tactical Counter                     │
├────┼─────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ E1 │ Spiky Hopper (160 Dmg) Knockout Gate            │ Prioritize 160 dmg over 60 unswitched Gale for lethal KOs   │
│ E2 │ Low-HP 1-Hit Kill Priority Gate                 │ Award +10,000 score bonus to any lethal attack              │
│ E3 │ Prize Denial Retreat on ≥280 Dmg Active         │ Retreat damaged Mega to deny 3 prize cards to opponent      │
│ E4 │ Boss's Orders (1220) 2-Prize Target Sniper      │ 17 Water + 2 Mist + 1 Boss: Target benched damaged ex       │
│ E5 │ Prime Catcher (1124) ACE SPEC Switch-Gust       │ Gust opponent bench + switch our attacker simultaneously    │
│ E6 │ Survival Brace (1126) 1-Hit KO Shield           │ Leave Lopunny with 10 HP surviving 400 dmg Grass nukes     │
│ E7 │ Hero's Cape (1127) 430-HP Titan                 │ Boost Mega Lopunny to 430 HP to survive all 1HKOs           │
│ E8 │ Rigid Band (1177) -30 Damage Buffer             │ Reduce incoming attack damage by 30                         │
│ E9 │ Bianca's Devotion (1222) 330-HP Full Heal       │ 17 Water + 2 Mist + 1 Bianca: Full heal Lopunny ≤50 HP      │
│ E10│ Cheren's Care (1231) Hand Scoop Recovery        │ Scoop damaged Lopunny & Energy into hand to deny 3 prizes   │
│ E11│ Carmine (1192) Turn 1 First-Mover Draw Engine   │ 18 Water + 1 Mist + 1 Carmine: Draw 5 on Turn 1 when 1st    │
│ E12│ Ciphermaniac (1188) + Rotom Deterministic Draw  │ Stack top 2 cards, Rotom Assault Landing draws them         │
│ E13│ Professor's Research (1219) 7-Card Hand Dump    │ Maximum draw velocity to dig for Switch & Energy            │
│ E14│ Pokégear 3.0 (1095) Supporter Consistency       │ Top 7 cards search for Hilda/Lillie                         │
│ E15│ Iono (1228) Late-Game Hand Reset Disruption     │ Shrink opponent hand to 1–2 cards when they have few prizes │
│ E16│ 3x Mist Energy (11) Anti-Spread Fortress        │ 17 Water + 3 Mist + 2 Poffin: Triple immunity coverage      │
│ E17│ 4x Mist Energy (11) Maximum Effect Immunity     │ 16 Water + 4 Mist + 2 Poffin: Complete status lockout       │
│ E18│ Enhanced Hammer (1080) Special Energy Stripping │ Discard opponent Special Energy (Ignition/Telepath/Mist)    │
│ E19│ Crushing Hammer (1078) Energy Denial Turbo      │ Strip basic/special energy on coin flip                     │
│ E20│ Legacy Energy (12) Prize Reduction Shield       │ Force opponent to take 1 fewer prize card on KO             │
│ E21│ Surfing Beach (1194) Universal Pivot Arena      │ Reduce retreat cost of Basic Pokémon by 1                   │
│ E22│ Jamming Tower (1196) Tool Lockout Stadium       │ Deactivate opponent Power Pro, Belt, and Tools              │
│ E23│ Artazon (1191) Turn-by-Turn Basic Search Stadium│ Free basic Pokémon bench search every turn                  │
│ E24│ 4th Night Stretcher (1097) Infinite Loop        │ 17 Water + 2 Mist + 4th Stretcher: Endless recovery         │
│ E25│ Super Rod (1110) 3-Card Deck Recycle            │ Recycle 3 Pokémon/Energies back into deck                   │
└────┴─────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Mandatory Quality Assurance Standards
All 25 experiments must strictly satisfy our 10-checkpoint QA standard:
1. Python AST Parse Validation.
2. Exact 60 Cards.
3. Robust Path Resolution.
4. Simulator State Synchronization.
5. Lethal Knockout Priority.
6. Self-Mill Suppression (Deck $\le 3$).
7. Guaranteed Return Pivot Gate.
8. Multi-OS Engine Binaries.
9. 100-Match Zero Exception Sandbox Test.
10. Multi-Archetype Meta Gauntlet Benchmark ($\ge 60.0\%$).
