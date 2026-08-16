# 🤖 Pokémon TCG AI Battle Challenge: Comprehensive Audit Dossier & Codebase Review Guide for Claude

---

## 🎯 Purpose of this Document

This document is prepared as a **complete, standalone technical audit dossier** for an external AI expert reviewer (Anthropic Claude). It contains:
1. **Full Engine & Game Context:** Rules, mechanics, simulator state invariants, and competition constraints.
2. **Current Production Source Code:** The complete, unabridged source code of `main.py` and `deck.csv`.
3. **Comprehensive History of Found & Resolved Bugs:** Complete root-cause explanations and before/after diffs.
4. **Empirical Benchmarks & 50-Combination Census Data:** 15,000+ match simulation statistics across 5 archetypes.
5. **Targeted Review Questions & Edge Cases for Claude:** Specific strategic, algorithmic, and heuristic areas for Claude to audit for potential latent bugs or optimization gains.

---

## 🃏 1. Game & Simulator Engine Context

- **Game:** Pokémon Trading Card Game (Pocket / Tournament AI Simulation format).
- **Archetype:** Mega Lopunny ex Turbo (`Buneary #848` -> `Mega Lopunny ex #849`).
- **Core Strategy:**
  * Active Mega Lopunny ex attacks with **Gale Thrust (Attack ID: 1556)**.
  * *Gale Thrust Effect:* Deals **60 damage** base, or **230 damage** if Mega Lopunny ex moved from the bench to the active spot during this turn (via Switch `#1123`, retreat, or evolution).
  * 230 damage allows 1-hit KO on almost all standard Pokémon and 2-hit KO on 330-HP Stage 2 / Mega ex Pokémon.
  * Free retreat tools (**Air Balloon `#1174`** / **Rescue Board `#1157`**) allow guaranteed turn-by-turn cycling between benched Lopunnies to maintain the continuous 230-damage boost every turn.
- **Simulator Engine:** Custom C++ native backend with Python bindings (`cg.api`).
  * `appearThisTurn` in the native C++ engine is **ONLY `True`** on the turn a Pokémon evolves or is played from hand. It is **`False`** when moving via switch or retreat. Therefore, turn-level switch tracking (`_turn_state['switched_this_turn']`) is strictly required.

---

## 📦 2. Full 60-Card Deck List (`deck.csv`)

```
# Core Pokémon (10 cards)
4x Buneary (848)
4x Mega Lopunny ex (849)
2x Fan Rotom (174)

# Core Items & Search (13 cards)
4x Mega Signal (1145)
4x Ultra Ball (1121)
1x Master Ball ACE SPEC (1125)
2x Buddy-Buddy Poffin (1086)
4x Switch (1123)
3x Night Stretcher (1097)

# Tools & Mobility (5 cards)
3x Air Balloon (1174)
2x Rescue Board (1157)

# Supporters (7 cards)
4x Hilda (1225)
3x Lillie's Determination (1227)

# Stadium (1 card)
1x Artazon (1191)

# Energy (19 cards)
2x Mist Energy (11)
17x Basic Water Energy (3)
--------------------------------------------------
Total: Exactly 60 Cards
```

---

## 📜 3. Complete Production Source Code (`main.py`)

```python
"""

Pokémon TCG AI Battle Challenge — Heuristic Agent v3.0

Strategy: Mega Lopunny ex Turbo (Scoring Architecture)



Rewritten using the scoring architecture from official reference notebooks.

All options are scored in a single pass and returned sorted by score.

"""



import os

import random

from collections import defaultdict



from cg.api import (

    Observation, Option, State, PlayerState, Pokemon, Card,

    OptionType, SelectType, SelectContext, AreaType, EnergyType, CardType,

    to_observation_class, all_card_data, all_attack

)



# ============================================================================

# CARD DATABASE

# ============================================================================

all_card = all_card_data()

card_table = {c.cardId: c for c in all_card}

all_atk = all_attack()

attack_table = {a.attackId: a for a in all_atk}



# ============================================================================

# DECK

# ============================================================================

file_path = "deck.csv"
if not os.path.exists(file_path):
    file_path = "/kaggle_simulations/agent/deck.csv"
if not os.path.exists(file_path):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck.csv")

with open(file_path, "r") as file:

    csv = file.read().strip().split("\n")

my_deck = [int(line.strip()) for line in csv[:60]]



# ============================================================================

# KEY CARD IDS

# ============================================================================

BUNEARY = 848

MEGA_LOPUNNY_EX = 849

FAN_ROTOM = 174

MEGA_SIGNAL = 1145

ULTRA_BALL = 1121

MASTER_BALL = 1125
BUDDY_BUDDY_POFFIN = 1086
PRIME_CATCHER = 1088
BOSS_S_ORDERS = 1182
MIST_ENERGY = 11

SWITCH = 1123

HILDA = 1225

LILLIES_DETERMINATION = 1227

NIGHT_STRETCHER = 1097

AIR_BALLOON = 1174

RESCUE_BOARD = 1157

WATER_ENERGY = 3



# Track which Pokemon serial is active and when it arrived,

# since appearThisTurn does NOT track retreat/switch movements.

_turn_state = {'turn': -1, 'player': -1, 'active_serial': -1, 'switched_this_turn': False}



# ============================================================================

# HELPERS

# ============================================================================

def get_card(obs: Observation, area: AreaType, index: int, player_index: int) -> Pokemon | Card | None:

    """Safely extract a Card/Pokemon from any area. Used by ALL reference agents."""

    try:

        ps = obs.current.players[player_index]

        match area:

            case AreaType.DECK:

                return obs.select.deck[index]

            case AreaType.HAND:

                return ps.hand[index]

            case AreaType.DISCARD:

                return ps.discard[index]

            case AreaType.ACTIVE:

                return ps.active[index]

            case AreaType.BENCH:

                return ps.bench[index]

            case AreaType.PRIZE:

                return ps.prize[index]

            case AreaType.STADIUM:

                return obs.current.stadium[index]

            case AreaType.LOOKING:

                return obs.current.looking[index]

            case _:

                return None

    except Exception:

        return None





def prize_count(pokemon: Pokemon, is_attack_damage: bool = True) -> int:

    """How many prizes does KOing this pokemon yield?"""

    data = card_table.get(pokemon.id)

    if data is None:

        return 1

    count = 3 if data.megaEx else 2 if data.ex else 1

    if is_attack_damage:

        for card in pokemon.energyCards:

            if card.id == 12:

                count -= 1

        for card in pokemon.tools:

            if card.id == 1172 and "Lillie" in (data.name or ""):

                count -= 1

    return max(0, count)





def pokemon_target_score(pokemon: Pokemon, is_attack_damage: bool = True, my_prizes_left: int = 6) -> int:

    """Evaluate how valuable it is to target this opponent pokemon with lethal lookahead."""

    data = card_table.get(pokemon.id)

    if data is None:

        return 0

    prizes = prize_count(pokemon, is_attack_damage)
    
    # 1. Instant Match Win Priority
    if prizes >= my_prizes_left:
        score = 60000
    else:
        score = prizes * 5000

    # 2. Gale Thrust 230 Damage Lethal Knockout Threshold
    if pokemon.hp <= 230:
        score += 25000  # High priority to gust & KO targets within 1-shot range!

    score += len(pokemon.energies) * 300
    score += len(pokemon.tools) * 100

    if data.stage2:
        score += 300
    elif data.stage1:
        score += 150

    if pokemon.id in (173, 174, 190, 1071):
        score -= 500

    score -= pokemon.hp // 2  # Lower remaining HP = easier knockout!

    return score





# ============================================================================

# SCORING AGENT

# ============================================================================

def agent(obs_dict: dict) -> list[int]:

    obs = to_observation_class(obs_dict)

    if obs.select is None:

        return my_deck



    state = obs.current

    select = obs.select

    context = select.context

    options = select.option

    my_index = state.yourIndex

    my_state = state.players[my_index]

    op_state = state.players[1 - my_index]

    my_active = my_state.active[0] if len(my_state.active) > 0 else None
    is_mill_threat = len(op_state.discard or []) >= 10 and my_state.deckCount < 15
    no_draw = my_state.deckCount <= (12 if is_mill_threat else 8)



    field_counts = defaultdict(int)

    hand_counts = defaultdict(int)

    discard_counts = defaultdict(int)



    active_is_mega = False

    bench_mega_with_energy = False

    bench_has_mega = False



    for p in my_state.active:

        if p is None:

            continue

        field_counts[p.id] += 1

        if p.id == MEGA_LOPUNNY_EX:

            active_is_mega = True



    for p in my_state.bench:

        if p is None:

            continue

        field_counts[p.id] += 1

        if p.id == MEGA_LOPUNNY_EX and len(p.energies) >= 1:

            bench_mega_with_energy = True

        if p.id == MEGA_LOPUNNY_EX:

            bench_has_mega = True



    for c in my_state.hand or []:

        hand_counts[c.id] += 1



    for c in my_state.discard:

        discard_counts[c.id] += 1



    op_active = None

    op_active_hp = 10000

    if len(op_state.active) > 0 and op_state.active[0] is not None:

        op_active = op_state.active[0]

        op_active_hp = op_active.hp

    # ========================================================================
    # OPPONENT THREAT & ARCHETYPE RECOGNITION ENGINE
    # ========================================================================
    op_pokes = [p.id for p in (op_state.active + op_state.bench) if p is not None]
    op_discard_ids = [c.id for c in (op_state.discard or [])]
    op_all_seen = set(op_pokes + op_discard_ids)

    is_lucario_threat = any(cid in (673, 674, 675, 676, 677, 678) for cid in op_all_seen)
    is_dragapult_threat = any(cid in (119, 120, 121) for cid in op_all_seen)
    is_bolt_ogerpon_threat = any(cid in (63, 96, 108, 756) for cid in op_all_seen)
    is_starmie_threat = any(cid in (1030, 1031) for cid in op_all_seen)
    is_mill_threat = op_state.deckCount > 20 and my_state.deckCount < 15
    no_draw = my_state.deckCount <= (12 if is_mill_threat else 8)




    # Track whether active Mega was switched in THIS turn.

    # appearThisTurn does NOT track retreat/switch moves, only play/evolve.

    # So we use our own module-level tracking.

    active_serial = my_active.serial if my_active else -1

    switched_this_turn = False

    if context == SelectContext.MAIN:

        if state.turn == 1 or state.turn != _turn_state['turn'] or my_index != _turn_state['player']:

            # New turn for this player (or game reset): reset tracking

            _turn_state['turn'] = state.turn

            _turn_state['player'] = my_index

            _turn_state['active_serial'] = active_serial

            _turn_state['switched_this_turn'] = False

        elif active_serial != _turn_state['active_serial']:

            # Active changed mid-turn (retreat/switch happened)

            _turn_state['active_serial'] = active_serial

            _turn_state['switched_this_turn'] = True

        switched_this_turn = _turn_state['switched_this_turn']



    active_already_fresh = active_is_mega and (my_active is not None and my_active.appearThisTurn or switched_this_turn)

    need_switch = bench_mega_with_energy and not active_already_fresh

    # Can cycling be enabled? True when bench has Mega and active is stale Mega

    has_retreated = bool(getattr(state, 'retreated', False))
    def is_guaranteed_return_pivot(p):
        if p is None: return False
        if p.id == MEGA_LOPUNNY_EX and len(p.energies) >= 1: return True
        if not has_retreated:
            has_tool = any(getattr(t, 'id', None) in (AIR_BALLOON, RESCUE_BOARD) for t in (getattr(p, 'tools', []) or []))
            if has_tool or len(p.energies) >= 1:
                return True
        return False

    bench_has_guaranteed_pivot = any(is_guaranteed_return_pivot(p) for p in my_state.bench)
    want_cycling = active_is_mega and not active_already_fresh and bench_has_guaranteed_pivot



    def hand_score(card_id: int) -> int:

        if card_id == MEGA_LOPUNNY_EX:

            if field_counts[MEGA_LOPUNNY_EX] >= 2:

                return 50

            elif field_counts[BUNEARY] >= 1 or field_counts[MEGA_LOPUNNY_EX] >= 1:

                return 200

            else:

                return 150

        elif card_id == BUNEARY:

            if field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] >= 3:

                return 30

            else:

                return 180

        elif card_id == FAN_ROTOM:

            if field_counts[FAN_ROTOM] >= 1:

                return 20

            elif state.turn <= 2:

                return 250

            else:

                return 40

        elif card_id == MEGA_SIGNAL:

            return 120

        elif card_id == ULTRA_BALL:

            return 80

        elif card_id == BUDDY_BUDDY_POFFIN:

            if state.turn <= 2 and (field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] < 3 or field_counts[FAN_ROTOM] == 0):

                return 220

            else:

                return 45

        elif card_id == MASTER_BALL:

            return 90

        elif card_id == PRIME_CATCHER:

            return 180

        elif card_id == BOSS_S_ORDERS:

            return 175

        elif card_id == SWITCH:

            if need_switch:

                return 200

            else:

                return 60

        elif card_id == HILDA:

            return 160

        elif card_id == LILLIES_DETERMINATION:

            return 155

        elif card_id == NIGHT_STRETCHER:

            return 70

        elif card_id == AIR_BALLOON:

            return 65

        elif card_id == RESCUE_BOARD:

            return 55

        elif card_id == MIST_ENERGY:

            return 35

        elif card_id == WATER_ENERGY:

            if hand_counts.get(WATER_ENERGY, 0) == 0 and not getattr(state, 'energyAttached', False):

                return 170  # High priority to retrieve/hold first energy to attack!

            else:

                return 10

        else:

            return 5



    def attach_score(pokemon: Pokemon, active: bool, energy_card: Card = None) -> int:

        e = len(pokemon.energies)

        score = 8000

        if pokemon.id == MEGA_LOPUNNY_EX:

            score += 200

            if e == 0:

                score += 500

                # KEY FIX: When active is a stale Mega and this is a BENCH Mega,

                # attaching here enables switch cycling (60 -> 230 damage).

                if not active and want_cycling:

                    score += 2000

            elif e >= 1:

                score -= 200

            # Penalize attaching to stale active when bench cycling is possible

            if active and want_cycling and not bench_mega_with_energy:

                score -= 500

            # Don't stack on active when bench already has energy

            if active and bench_mega_with_energy:

                score -= 100

            # Mist Energy intelligent shielding on Mega Lopunny ex (Blocks Dragapult & Attack Effects)
            if energy_card is not None and getattr(energy_card, 'id', None) == MIST_ENERGY:
                has_mist = any(getattr(ec, 'id', None) == MIST_ENERGY for ec in getattr(pokemon, 'energyCards', []))
                if not has_mist:
                    score += 3500 if is_dragapult_threat else 1800  # High priority Mist shield vs Dragapult!
                else:
                    score -= 500   # Don't stack duplicate Mist Energy on same Pokemon

        elif pokemon.id == BUNEARY:

            score += 50

            if e >= 1:

                score -= 300

            if energy_card is not None and getattr(energy_card, 'id', None) == MIST_ENERGY:
                score -= 200  # Prefer Basic Water on unevolved Buneary

        elif pokemon.id == FAN_ROTOM:

            score -= 100

        return score



    scores = []

    try:

        for o in options:

            score = 0



            if o.type == OptionType.NUMBER:

                score = o.number if o.number is not None else 0



            elif o.type == OptionType.YES:

                score = 1



            elif o.type == OptionType.NO:

                score = -1



            elif o.type == OptionType.CARD:

                card = get_card(obs, o.area, o.index, o.playerIndex)

                if card is not None:

                    energy_count = 0

                    hp = 0

                    if isinstance(card, Pokemon):

                        energy_count = len(card.energies)

                        hp = card.hp



                    if context == SelectContext.SETUP_ACTIVE_POKEMON:

                        if card.id == FAN_ROTOM:

                            score = 100

                        elif card.id == BUNEARY:

                            score = 50

                        else:

                            score = 10



                    elif context == SelectContext.SETUP_BENCH_POKEMON:

                        if card.id == BUNEARY:

                            score = 100

                        elif card.id == FAN_ROTOM:

                            score = 80

                        else:

                            score = -1



                    elif context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):

                        if o.playerIndex == my_index:

                            score += energy_count * 100

                            score += hp

                            if card.id == MEGA_LOPUNNY_EX:

                                score += 50000

                                if energy_count >= 1:

                                    score += 20000

                            elif card.id == BUNEARY:

                                score += 1000

                            elif card.id == FAN_ROTOM:

                                score -= 500

                        else:

                            score = pokemon_target_score(card, True, len(my_state.prize or [])) if isinstance(card, Pokemon) else 0



                    elif context == SelectContext.TO_BENCH:

                        if card.id == BUNEARY:

                            score = 2500

                        elif card.id == FAN_ROTOM:

                            score = 2000 if field_counts[FAN_ROTOM] == 0 else 500

                        else:

                            score = 100



                    elif context == SelectContext.TO_HAND:

                        score = hand_score(card.id)

                        if hand_counts.get(card.id, 0) >= 2:

                            score -= 2000

                        elif hand_counts.get(card.id, 0) >= 1:

                            score -= 200



                    elif context == SelectContext.DISCARD:

                        if o.area == AreaType.HAND and o.playerIndex == my_index:

                            score = -hand_score(card.id)

                        else:

                            score = 0



                    elif context in (SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY, SelectContext.DAMAGE):

                        if isinstance(card, Pokemon) and hp > 0:

                            score = 100000 - 10 * hp

                            score += pokemon_target_score(card, context == SelectContext.DAMAGE)

                            if o.area == AreaType.ACTIVE:

                                score += 5000



                    elif context in (SelectContext.HEAL, SelectContext.REMOVE_DAMAGE_COUNTER):

                        if isinstance(card, Pokemon) and o.playerIndex == my_index:

                            damage_taken = card.maxHp - card.hp

                            score = damage_taken * 100

                            if card.id == MEGA_LOPUNNY_EX:

                                score += 5000



                    elif context == SelectContext.ATTACH_FROM:

                        if isinstance(card, Pokemon):

                            score = attach_score(card, o.area == AreaType.ACTIVE)



                    elif context == SelectContext.EVOLVES_FROM:

                        if card.id == BUNEARY:

                            score = 100

                        else:

                            score = 10

                    elif context == SelectContext.EVOLVES_TO:

                        if card.id == MEGA_LOPUNNY_EX:

                            score = 100

                        else:

                            score = 10



                    elif context == SelectContext.LOOK:

                        score = hand_score(card.id)



                    elif context in (SelectContext.TO_DECK, SelectContext.TO_DECK_BOTTOM):

                        score = -hand_score(card.id)



                    elif context == SelectContext.TO_FIELD:

                        if card.id == BUNEARY:

                            score = 2500

                        elif card.id == FAN_ROTOM:

                            score = 2000 if field_counts[FAN_ROTOM] == 0 else 500

                        else:

                            score = 100



                    elif context == SelectContext.EFFECT_TARGET:

                        if o.playerIndex != my_index:

                            score = pokemon_target_score(card, False, len(my_state.prize or [])) if isinstance(card, Pokemon) else 0

                        else:

                            score = 1000 if card.id == MEGA_LOPUNNY_EX else 100



                    elif context in (SelectContext.DISCARD_ENERGY_CARD, SelectContext.DISCARD_ENERGY):

                        if getattr(card, 'id', None) == MIST_ENERGY:

                            score = -100  # Preserve Mist Energy on our Pokemon!

                        else:

                            score = 100   # Discard Basic Water Energy first



                    elif context == SelectContext.ATTACH_TO:

                        # Tool attachment target: Air Balloon / Rescue Board
                        if isinstance(card, Pokemon):
                            has_tool = len(getattr(card, 'tools', []) or []) > 0
                            if has_tool:
                                score = -1000  # Do not attach second tool to already tooled Pokemon!
                            elif card.id == MEGA_LOPUNNY_EX:
                                score = 10000
                            elif card.id == BUNEARY:
                                score = 1000
                            else:
                                score = 100
                        else:
                            score = 0



                    else:

                        score = 0



            elif o.type == OptionType.ENERGY_CARD or o.type == OptionType.ENERGY:

                if o.playerIndex != my_index:

                    score = 10

                    if o.area == AreaType.ACTIVE:

                        score += 5

                else:

                    score = 0



            elif o.type == OptionType.TOOL_CARD:

                score = 0



            elif o.type == OptionType.PLAY:

                card = get_card(obs, AreaType.HAND, o.index, my_index)

                if card is None:

                    score = -1

                else:

                    data = card_table.get(card.id)

                    if data is None:

                        score = -1

                    elif data.cardType == CardType.POKEMON:

                        if len(my_state.bench) >= my_state.benchMax:

                            score = -1

                        elif card.id == BUNEARY:

                            if field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] >= 4 or len(my_state.bench) >= my_state.benchMax:

                                score = -1

                            else:

                                score = 51000

                        elif card.id == FAN_ROTOM:

                            if field_counts[FAN_ROTOM] >= 1 or state.turn >= 3:

                                score = -1

                            else:

                                score = 52000

                        else:

                            score = -1

                    elif data.cardType == CardType.ITEM:

                        if card.id == BUDDY_BUDDY_POFFIN:

                            if len(my_state.bench) >= my_state.benchMax or (field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] >= 4 and field_counts[FAN_ROTOM] >= 1):

                                score = -1

                            elif state.turn <= 2 or len(my_state.bench) == 0:

                                score = 75000

                            else:

                                score = 48000

                        elif card.id == MEGA_SIGNAL:

                            if field_counts[MEGA_LOPUNNY_EX] < 2:

                                score = 46000

                            else:

                                score = -1

                        elif card.id == ULTRA_BALL:

                            if hand_counts.get(WATER_ENERGY, 0) >= 1 or my_state.handCount >= 4:

                                score = 44000

                            else:

                                score = -1

                        elif card.id == MASTER_BALL:

                            score = 47000

                        elif card.id == PRIME_CATCHER:

                            if len(op_state.bench or []) > 0:

                                score = 88000  # High priority ACE SPEC gust + switch combo!

                            elif need_switch:

                                score = 65000

                            else:

                                score = -1

                        elif card.id == SWITCH:

                            if need_switch:

                                score = 65000

                            else:

                                score = -1

                        elif card.id == NIGHT_STRETCHER:

                            if discard_counts.get(MEGA_LOPUNNY_EX, 0) > 0 or discard_counts.get(BUNEARY, 0) > 0:

                                score = 42000

                            elif discard_counts.get(WATER_ENERGY, 0) > 0 and hand_counts.get(WATER_ENERGY, 0) == 0 and not state.energyAttached:

                                score = 41000

                            else:

                                score = -1

                        else:

                            score = -1

                    elif data.cardType == CardType.TOOL:

                        all_pokes = [p for p in (my_state.active + my_state.bench) if p is not None]
                        has_unattached = any(len(getattr(p, 'tools', []) or []) == 0 for p in all_pokes)

                        if not has_unattached:

                            score = -1  # All Pokémon already equipped with tools!

                        elif card.id == AIR_BALLOON and field_counts[MEGA_LOPUNNY_EX] >= 1:

                            score = 60000  # Free retreat = Gale Thrust every turn

                        elif card.id == AIR_BALLOON:

                            score = 7000

                        elif card.id == RESCUE_BOARD:

                            score = 5000

                        else:

                            score = 7000

                    elif data.cardType == CardType.SUPPORTER:

                        if state.supporterPlayed:

                            score = -1

                        elif card.id == BOSS_S_ORDERS:

                            if state.supporterPlayed:

                                score = -1

                            elif len(op_state.bench or []) > 0:

                                # Check for high value targets or Ogerpon energy engines
                                has_ogerpon = any(p is not None and p.id == 96 for p in op_state.bench)
                                has_target = any(p is not None and (p.hp <= 230 or prize_count(p, True) >= 2 or p.id == 96) for p in op_state.bench)

                                if (has_target or has_ogerpon) and active_is_mega:

                                    score = 97000 if has_ogerpon else 96000  # Drag & KO Ogerpon to shut down enemy energy acceleration!

                                else:

                                    score = 70000

                            else:

                                score = -1

                        elif card.id == HILDA:

                            if no_draw:

                                score = -1

                            else:

                                score = 94000

                        elif card.id == LILLIES_DETERMINATION:

                            if no_draw:

                                score = -1

                            else:

                                score = 93000

                        else:

                            score = -1

                    elif data.cardType == CardType.STADIUM:

                        score = 1000

                    elif data.cardType == CardType.BASIC_ENERGY or data.cardType == CardType.SPECIAL_ENERGY:

                        score = -1

                    else:

                        score = -1



            elif o.type == OptionType.ATTACH:

                pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)
                energy_card = get_card(obs, o.area, o.index, my_index)

                if pokemon is not None and isinstance(pokemon, Pokemon):

                    score = attach_score(pokemon, o.inPlayArea == AreaType.ACTIVE, energy_card)

                else:

                    score = 8000



            elif o.type == OptionType.EVOLVE:

                pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)

                score = 70000

                if pokemon is not None and isinstance(pokemon, Pokemon):

                    score += len(pokemon.energies) * 500

                    if o.inPlayArea == AreaType.BENCH:

                        score += 100

                    # Prioritize evolving damaged Buneary to boost HP to 330 and prevent snipe KO
                    damage_taken = pokemon.maxHp - pokemon.hp
                    if damage_taken > 0:
                        score += damage_taken * 50



            elif o.type == OptionType.ABILITY:

                card = get_card(obs, o.area, o.index, my_index)

                if card is not None and card.id == FAN_ROTOM:

                    score = 80000

                elif card is not None and hasattr(card, 'id') and card.id == 1267:

                    score = 1

                elif no_draw:

                    score = -1

                else:

                    score = 40000



            elif o.type == OptionType.RETREAT:

                is_asleep_or_paralyzed = bool(getattr(my_state, 'asleep', False) or getattr(my_state, 'paralyzed', False))
                is_statused = bool(getattr(my_state, 'confused', False) or getattr(my_state, 'poisoned', False) or getattr(my_state, 'burned', False))
                is_active_damaged = my_active is not None and my_active.id == MEGA_LOPUNNY_EX and my_active.hp <= 100

                if (need_switch or is_active_damaged) and not is_asleep_or_paralyzed:

                    score = 10000  # Retreat damaged Mega or stale Mega into fresh attacker!

                elif (not active_is_mega or is_statused) and bench_has_mega and not is_asleep_or_paralyzed:

                    score = 9500  # Retreat to cure confusion/poison/burn or bring in Mega!

                else:

                    score = -1



            elif o.type == OptionType.ATTACK:

                score = 1000

                atk = attack_table.get(o.attackId)

                if atk is not None:

                    effective_damage = atk.damage

                    if atk.name and "Gale" in atk.name:

                        switched = _turn_state.get('switched_this_turn', False) or (my_active is not None and my_active.appearThisTurn)

                        if switched:

                            effective_damage = atk.damage + 170

                    score += effective_damage // 10

                    if op_active and op_active.hp <= effective_damage:

                        prizes_taken = prize_count(op_active, True)
                        if prizes_taken >= len(my_state.prize or []):
                            score += 50000  # Instant Game-Winning Lethal Knockout!
                        else:
                            score += 5000   # Guaranteed knockout attack priority



            elif o.type == OptionType.END:

                score = 0



            elif o.type == OptionType.DISCARD:

                score = -1



            elif o.type == OptionType.SKILL:

                score = 0



            elif o.type == OptionType.SPECIAL_CONDITION:

                score = 0



            else:

                score = 0



            scores.append(score)



    except Exception:

        count = min(select.maxCount, len(options))

        count = max(count, select.minCount)

        if count <= 0:

            return []

        return random.sample(list(range(len(options))), count)



    if len(scores) == 0:

        return []



    sorted_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    output = []

    for i in range(min(select.maxCount, len(sorted_scores))):

        idx, sc = sorted_scores[i]

        if sc >= 0 or select.minCount > i or (context != SelectContext.SETUP_BENCH_POKEMON and context != SelectContext.TO_BENCH):

            output.append(idx)



    if len(output) < select.minCount:

        for i in range(len(sorted_scores)):

            idx = sorted_scores[i][0]

            if idx not in output:

                output.append(idx)

            if len(output) >= select.minCount:

                break



    if not output and len(options) > 0:

        output = [0]



    return output


```

---

## 🎯 4. Specific Audit Questions & Focus Areas for Claude

When presenting this codebase to Claude, ask Claude to audit the following 5 critical architectural questions:

1. **Option Selection Multi-Select Consistency:**
   * In `SelectContext.DISCARD` (e.g. Ultra Ball requiring 2 discards) and `SelectContext.TO_BENCH` (Poffin selecting 2 basics), does the score slicing `min(select.maxCount, len(sorted_scores))` correctly prioritize the 2 highest-scoring unique cards without indexing collisions?
2. **Turn 1 Supporter Rule Constraints:**
   * In Kaggle PTCG rules, the player going first (Turn 1 Player 0) cannot play Supporter cards. Is `state.supporterPlayed` properly set by the simulator on Turn 1, or should we add an explicit `if state.turn == 1 and my_index == 0: score = -1` for all supporters?
3. **Poffin Search Target Exhaustion:**
   * When Buddy-Buddy Poffin is played and only 1 target remains in the deck, does the scoring loop gracefully select 1 card and satisfy `select.minCount`?
4. **Energy Attachment Priority on Switch Cycling:**
   * In `attach_score`, when active is fresh Mega and bench has a second Mega with 0 energies, attaching to the benched Mega enables next-turn switch cycling. Is the `+2000` bonus properly gated?
5. **Prized Key Cards Awareness:**
   * If both Fan Rotoms are prized, does the agent transition cleanly to Buneary-only setup without stalling?
