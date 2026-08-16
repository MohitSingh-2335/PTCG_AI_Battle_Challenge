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





def pokemon_target_score(pokemon: Pokemon, is_attack_damage: bool = True) -> int:

    """Evaluate how valuable it is to target this opponent pokemon."""

    data = card_table.get(pokemon.id)

    if data is None:

        return 0

    score = prize_count(pokemon, is_attack_damage) * 1000

    score += len(pokemon.energies) * 150

    score += len(pokemon.tools) * 100

    if data.stage2:

        score += 250

    elif data.stage1:

        score += 130

    if pokemon.id in (173, 174, 190, 1071):

        score -= 200

    score += pokemon.hp

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



    is_mill_threat = len(op_state.discard or []) >= 10 and my_state.deckCount < 15
    no_draw = my_state.deckCount <= (12 if is_mill_threat else 8)

    # Track whether active Mega was switched in THIS turn.

    # appearThisTurn does NOT track retreat/switch moves, only play/evolve.

    # So we use our own module-level tracking.

    active_serial = my_active.serial if my_active else -1

    switched_this_turn = False

    if context == SelectContext.MAIN:

        if state.turn != _turn_state['turn'] or my_index != _turn_state['player']:

            # New turn for this player: reset tracking

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

    has_retreated = bool(getattr(state, 'retreatCount', 0))
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

        elif card_id == MASTER_BALL:

            return 90

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

        elif card_id == WATER_ENERGY:

            return 10

        else:

            return 5



    def attach_score(pokemon: Pokemon, active: bool) -> int:

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

        elif pokemon.id == BUNEARY:

            score += 50

            if e >= 1:

                score -= 300

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

                            score = pokemon_target_score(card, True) if isinstance(card, Pokemon) else 0



                    elif context in (SelectContext.TO_BENCH, SelectContext.TO_HAND):

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



                    elif context == SelectContext.ATTACH_TO:

                        # Tool attachment target: Air Balloon on Mega Lopunny

                        if isinstance(card, Pokemon):

                            if card.id == MEGA_LOPUNNY_EX:

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

                            if field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] >= 3:

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

                            if len(my_state.bench) >= my_state.benchMax or (field_counts[BUNEARY] + field_counts[MEGA_LOPUNNY_EX] >= 3 and field_counts[FAN_ROTOM] >= 1):

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

                        elif card.id == SWITCH:

                            if need_switch:

                                score = 65000

                            else:

                                score = -1

                        elif card.id == NIGHT_STRETCHER:

                            if discard_counts.get(MEGA_LOPUNNY_EX, 0) > 0 or discard_counts.get(BUNEARY, 0) > 0:

                                score = 42000

                            else:

                                score = -1

                        else:

                            score = -1

                    elif data.cardType == CardType.TOOL:

                        if card.id == AIR_BALLOON and field_counts[MEGA_LOPUNNY_EX] >= 1:

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

                        elif card.id == HILDA:

                            if no_draw:

                                score = -1

                            elif field_counts[MEGA_LOPUNNY_EX] == 0:

                                score = 94000

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

                        score = -1

                    elif data.cardType == CardType.BASIC_ENERGY or data.cardType == CardType.SPECIAL_ENERGY:

                        score = -1

                    else:

                        score = -1



            elif o.type == OptionType.ATTACH:

                pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)

                if pokemon is not None and isinstance(pokemon, Pokemon):

                    score = attach_score(pokemon, o.inPlayArea == AreaType.ACTIVE)

                else:

                    score = 8000



            elif o.type == OptionType.EVOLVE:

                pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)

                score = 70000

                if pokemon is not None and isinstance(pokemon, Pokemon):

                    score += len(pokemon.energies)

                    if o.inPlayArea == AreaType.BENCH:

                        score += 100



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

                if need_switch and not (my_state.asleep or my_state.paralyzed):

                    score = 10000

                elif not active_is_mega and bench_has_mega:

                    score = 9000

                else:

                    score = -1



            elif o.type == OptionType.ATTACK:

                score = 1000

                atk = attack_table.get(o.attackId)

                if atk is not None:

                    effective_damage = atk.damage

                    if atk.name and "Gale" in atk.name:

                        my_active = my_state.active[0] if my_state.active else None

                        if my_active is not None and my_active.appearThisTurn:

                            effective_damage = atk.damage + 170

                    score += effective_damage // 10

                    if op_active and op_active.hp <= effective_damage:

                        score += 500



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

