# PTCG AI Agent Development Instructions

> **CRITICAL RULE: The agent is NEVER perfect. There WILL be bugs. Never assume it is ready.**
> **Always test, always verify, always look for edge cases that crash it.**
> **After EVERY code change: run 50+ games. If ANY game crashes → fix before moving on.**

---

## Architecture: Scoring System (NOT Priority Chain)

### THE RULE
All 5 reference notebooks (Dragapult, Iono, Abomasnow, Lucario, RL+MCTS) use the **same architecture**:
1. Score EVERY option in a single pass
2. Sort by score descending
3. Return top `maxCount` options
4. Negative scores are skipped when `minCount` allows

```python
scores = []
for o in select.option:
    score = 0
    # ... compute score based on o.type, context, game state ...
    scores.append(score)

desc_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
output = []
for i in range(select.maxCount):
    if desc_indices[i][1] >= 0 or select.minCount > i:
        output.append(desc_indices[i][0])
return output
```

> **WHY**: Our current `return [i]` priority chain ONLY returns 1 option.
> When `maxCount > 1` (bench setup, discard, damage counters), this BREAKS.

### Score Magnitude Convention (from reference agents)
| Action | Score Range |
|--------|-----------|
| EVOLVE | 70,000 - 110,000 |
| Play Basic Pokemon | 51,000 - 100,000 |
| Stadium (opponent's) | 80,000 |
| Unfair Stamp (after KO) | 80,000 |
| Rare Candy (with target) | 75,000 |
| Search Items (Poffin, Ultra Ball) | 44,000 - 80,000 |
| ABILITY | 30,000 - 50,000 |
| Supporters | 25,000 - 55,000 |
| Tools | 7,000 - 60,000 |
| ATTACH energy | 5,000 - 22,000 |
| Switch / Retreat | 2,000 - 10,000 |
| ATTACK | 1,000 - 1,100 |
| END turn | 0 |
| Skip / Unnecessary | -1 |
| NEVER do this | -10,000,000 |

---

## Required Helper: `get_card()`

Present in ALL 5 reference notebooks. Must be used to safely extract cards:

```python
def get_card(obs, area, index, player_index):
    ps = obs.current.players[player_index]
    match area:
        case AreaType.DECK: return obs.select.deck[index]
        case AreaType.HAND: return ps.hand[index]
        case AreaType.DISCARD: return ps.discard[index]
        case AreaType.ACTIVE: return ps.active[index]
        case AreaType.BENCH: return ps.bench[index]
        case AreaType.PRIZE: return ps.prize[index]
        case AreaType.STADIUM: return obs.current.stadium[index]
        case AreaType.LOOKING: return obs.current.looking[index]
        case _: return None
```

---

## SelectContext Handling (ALL must be covered)

### Contexts that need CARD scoring:
- `SETUP_ACTIVE_POKEMON` → Pick best starter
- `SETUP_BENCH_POKEMON` → Pick best bench setup (can skip with score -1)
- `SWITCH` / `TO_ACTIVE` → Pick attacker with most energy
- `TO_BENCH` / `TO_HAND` → Prioritize key missing cards
- `DISCARD` → Pick lowest-value cards (invert hand_score)
- `DAMAGE_COUNTER` / `DAMAGE_COUNTER_ANY` → Target low HP or high-value opponents
- `ATTACH_FROM` → Pick pokemon that needs energy most

### Contexts that need YES/NO:
- `IS_FIRST` → Usually go second (draw + attack first)
- `ACTIVATE` → Usually yes
- `MULLIGAN` → Usually no

---

## Safety Rules

### Must NEVER crash:
1. **Wrap everything in try/except** → fallback to random legal selection
2. **Check for None** before accessing `.id`, `.hp`, `.energies`
3. **Check list bounds** before indexing (`me.hand`, `me.bench`, etc.)
4. **Check `select.minCount`** → sometimes you MUST select even if all scores are negative
5. **Never return empty list** when `minCount > 0`
6. **Never return duplicates** in the output list
7. **Never return index >= len(options)**

### Deckout Protection:
```python
no_draw = (my_state.deckCount <= 8)
# If no_draw: score draw supporters = -1, score search items = -1
```

### Special Conditions Block Actions:
```python
if my_state.asleep or my_state.paralyzed:
    # Can't attack or retreat!
    # Score RETREAT and ATTACK = -1
```

---

## Testing Protocol

### After EVERY code change:
1. Run `test_agent.py` (50 games vs random) → must NOT crash
2. Check win rate ≥ 90%
3. Check 0 deckouts
4. Check 0 errors

### Before submission:
1. Run 200 games vs random → 0 crashes
2. Run 50 games vs V1 (Gouging Fire) → win rate ≥ 60%
3. Review all DISCARD, TO_HAND, DAMAGE_COUNTER contexts manually
4. Verify deck.csv has exactly 60 cards

---

## Common Crash Points (from experience)

| Crash | Fix |
|-------|-----|
| `me.hand[opt.index]` IndexError | Check `opt.index < len(me.hand)` |
| `me.bench[opt.inPlayIndex]` IndexError | Check `opt.inPlayIndex < len(me.bench)` |
| `get_card_data(opt.cardId)` KeyError | Check `opt.cardId is not None` and `opt.cardId in card_table` |
| `options[i].area` AttributeError | Some options don't have `.area` |
| `me.active[0]` None | Active can be None (facedown) |
| Division by zero in scoring | Check denominators |
| `len(options) == 0` | Return empty list |
| `select.deck` is None | Only available when searching deck |

---

## Deck Rules

- Exactly 60 cards
- Max 4 copies of any non-energy card
- Max 1 ACE SPEC card total
- Must have at least 1 Basic Pokemon
- Basic Energy cards have no copy limit
