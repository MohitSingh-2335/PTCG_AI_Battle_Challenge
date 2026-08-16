"""
Pokémon TCG AI Battle Challenge — V_NEXT Tactical Champion Agent
Strategy: Mega Lopunny ex Turbo with Tactical Lookahead & Guaranteed KO Engine

Architecture:
- Layer 1: Tactical Priority & 230-Gale-Thrust Sequencing Engine
- Layer 2: Opponent Threat Classifier & Defensive Adaptation
- Layer 3: Single-Pass Deterministic Heuristic Scoring
"""

import os
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
# DECK RESOLUTION
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

# Track active movement across turn steps for Gale Thrust 230 bonus
_turn_state = {'turn': -1, 'player': -1, 'active_serial': -1, 'switched_this_turn': False}

# ============================================================================
# HELPERS
# ============================================================================
def get_card(obs: Observation, area: AreaType, index: int, player_index: int) -> Pokemon | Card | None:
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

    score -= pokemon.hp // 2
    return score

# ============================================================================
# MAIN AGENT LOGIC
# ============================================================================
def agent(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs is None or obs.current is None or obs.select is None:
        return []

    state = obs.current
    select = obs.select
    options = select.option
    if not options:
        return []

    context = select.context
    my_index = state.yourIndex
    my_state = state.players[my_index]
    op_state = state.players[1 - my_index]

    my_active = my_state.active[0] if len(my_state.active) > 0 else None
    
    # Field count tracking
    field_counts = defaultdict(int)
    for p in (my_state.active + my_state.bench):
        if p is not None:
            field_counts[p.id] += 1

    hand_counts = defaultdict(int)
    for card in (my_state.hand or []):
        if card is not None:
            hand_counts[card.id] += 1

    discard_counts = defaultdict(int)
    for card in (my_state.discard or []):
        if card is not None:
            discard_counts[card.id] += 1

    # Active & Bench State
    active_is_mega = my_active is not None and my_active.id == MEGA_LOPUNNY_EX
    active_serial = getattr(my_active, 'serial', -1) if my_active else -1
    bench_has_mega = any(p is not None and p.id == MEGA_LOPUNNY_EX for p in my_state.bench)
    bench_mega_with_energy = any(p is not None and p.id == MEGA_LOPUNNY_EX and len(p.energies) >= 1 for p in my_state.bench)

    # Opponent Active
    op_active = None
    op_active_hp = 10000
    if len(op_state.active) > 0 and op_state.active[0] is not None:
        op_active = op_state.active[0]
        op_active_hp = op_active.hp

    # ========================================================================
    # OPPONENT THREAT & ARCHETYPE RECOGNITION
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

    # ========================================================================
    # GALE THRUST SWITCH SYNCHRONIZATION
    # ========================================================================
    switched_this_turn = False
    if context == SelectContext.MAIN:
        if state.turn == 1 or state.turn != _turn_state['turn'] or my_index != _turn_state['player']:
            _turn_state['turn'] = state.turn
            _turn_state['player'] = my_index
            _turn_state['active_serial'] = active_serial
            _turn_state['switched_this_turn'] = False
        elif active_serial != _turn_state['active_serial']:
            _turn_state['active_serial'] = active_serial
            _turn_state['switched_this_turn'] = True
        switched_this_turn = _turn_state['switched_this_turn']

    active_already_fresh = active_is_mega and (my_active is not None and my_active.appearThisTurn or switched_this_turn)
    need_switch = (bench_mega_with_energy and not active_already_fresh) or (not active_is_mega and bench_mega_with_energy)

    # Free Pivot / Cycling Check
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

    # ========================================================================
    # CARD SCORING HANDLERS
    # ========================================================================
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
            return 200 if need_switch else 60
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
                return 170
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
                if not active and want_cycling:
                    score += 2000
            elif e >= 1:
                score -= 200

            if active and want_cycling and not bench_mega_with_energy:
                score -= 500
            if active and bench_mega_with_energy:
                score -= 100

            # Mist Energy Shielding
            if energy_card is not None and getattr(energy_card, 'id', None) == MIST_ENERGY:
                has_mist = any(getattr(ec, 'id', None) == MIST_ENERGY for ec in getattr(pokemon, 'energyCards', []))
                if not has_mist:
                    score += 3500 if is_dragapult_threat else 1800
                else:
                    score -= 500

        elif pokemon.id == BUNEARY:
            score += 50
            if e >= 1:
                score -= 300
            if energy_card is not None and getattr(energy_card, 'id', None) == MIST_ENERGY:
                score -= 200
        elif pokemon.id == FAN_ROTOM:
            score -= 100
        return score

    # ========================================================================
    # OPTION SCORING PASS (DETERMINISTIC EVALUATION)
    # ========================================================================
    scores = []
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
                energy_count = len(card.energies) if isinstance(card, Pokemon) else 0
                hp = card.hp if isinstance(card, Pokemon) else 0

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
                        score += energy_count * 100 + hp
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
                        score = 100000 - 10 * hp + pokemon_target_score(card, context == SelectContext.DAMAGE, len(my_state.prize or []))
                        if o.area == AreaType.ACTIVE:
                            score += 5000

                elif context in (SelectContext.HEAL, SelectContext.REMOVE_DAMAGE_COUNTER):
                    if isinstance(card, Pokemon) and o.playerIndex == my_index:
                        damage_taken = card.maxHp - card.hp
                        score = damage_taken * 100 + (5000 if card.id == MEGA_LOPUNNY_EX else 0)

                elif context == SelectContext.ATTACH_FROM:
                    if isinstance(card, Pokemon):
                        score = attach_score(card, o.area == AreaType.ACTIVE)

                elif context == SelectContext.EVOLVES_TO:
                    score = 100 if card.id == MEGA_LOPUNNY_EX else 10

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

                elif context == SelectContext.ATTACH_TO:
                    if isinstance(card, Pokemon) and o.playerIndex == my_index:
                        has_tool = any(getattr(t, 'id', None) in (AIR_BALLOON, RESCUE_BOARD) for t in (getattr(card, 'tools', []) or []))
                        if has_tool:
                            score = -1000  # Do not attach duplicate tool!
                        elif card.id == MEGA_LOPUNNY_EX:
                            score = 10000
                        elif card.id == BUNEARY:
                            score = 1000
                        else:
                            score = 100

        elif o.type in (OptionType.ENERGY_CARD, OptionType.ENERGY):
            score = 10 if o.playerIndex != my_index else 0
            if o.playerIndex != my_index and o.area == AreaType.ACTIVE:
                score += 5

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
                        score = 46000 if field_counts[MEGA_LOPUNNY_EX] < 2 else -1

                    elif card.id == ULTRA_BALL:
                        score = 44000 if (hand_counts.get(WATER_ENERGY, 0) >= 1 or my_state.handCount >= 4) else -1

                    elif card.id == MASTER_BALL:
                        score = 47000

                    elif card.id == PRIME_CATCHER:
                        # Priority 1: Check for instant game winning prize gust
                        has_lethal_gust = any(p is not None and prize_count(p, True) >= len(my_state.prize or []) and p.hp <= 230 for p in op_state.bench)
                        if has_lethal_gust and active_is_mega:
                            score = 99000
                        elif need_switch or len(op_state.bench or []) > 0:
                            score = 88000
                        else:
                            score = -1

                    elif card.id == SWITCH:
                        # Resource Preservation: DO NOT switch if active is already fresh and can hit for 230!
                        if need_switch:
                            score = 85000  # High priority to activate Gale Thrust 230
                        else:
                            score = -1     # Preserve switch!

                    elif card.id == NIGHT_STRETCHER:
                        if discard_counts.get(MEGA_LOPUNNY_EX, 0) > 0 or discard_counts.get(BUNEARY, 0) > 0:
                            score = 42000
                        elif discard_counts.get(WATER_ENERGY, 0) > 0 and hand_counts.get(WATER_ENERGY, 0) == 0 and not getattr(state, 'energyAttached', False):
                            score = 41000
                        else:
                            score = -1
                    else:
                        score = -1

                elif data.cardType == CardType.TOOL:
                    all_pokes = [p for p in (my_state.active + my_state.bench) if p is not None]
                    has_unattached = any(len(getattr(p, 'tools', []) or []) == 0 for p in all_pokes)
                    if not has_unattached:
                        score = -1
                    elif card.id == AIR_BALLOON and field_counts[MEGA_LOPUNNY_EX] >= 1:
                        score = 60000
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
                        if len(op_state.bench or []) > 0:
                            # 1. Instant match-winning gust
                            has_lethal_win = any(p is not None and prize_count(p, True) >= len(my_state.prize or []) and p.hp <= 230 for p in op_state.bench)
                            has_ogerpon = any(p is not None and p.id == 96 for p in op_state.bench)
                            has_target = any(p is not None and (p.hp <= 230 or prize_count(p, True) >= 2) for p in op_state.bench)
                            
                            if has_lethal_win and active_is_mega:
                                score = 99500  # Highest priority to seal match victory!
                            elif has_ogerpon and is_bolt_ogerpon_threat and active_is_mega:
                                score = 97000  # Snipe Ogerpon to shut down energy acceleration!
                            elif has_target and active_is_mega:
                                score = 96000  # Priority gust on vulnerable target
                            else:
                                score = 70000
                        else:
                            score = -1

                    elif card.id == HILDA:
                        score = -1 if no_draw else 94000

                    elif card.id == LILLIES_DETERMINATION:
                        score = -1 if no_draw else 93000

                    else:
                        score = -1

                elif data.cardType == CardType.STADIUM:
                    score = 1000
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
                score = 10000
            elif (not active_is_mega or is_statused) and bench_has_mega and not is_asleep_or_paralyzed:
                score = 9500
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
                        score += 60000  # Tactical Priority A: Instant Match-Winning Knockout!
                    else:
                        score += 30000  # Tactical Priority A: Guaranteed Knockout!

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
        output = list(range(min(select.maxCount, max(1, select.minCount))))

    return output
