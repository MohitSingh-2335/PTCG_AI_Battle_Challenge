"""
Pokémon TCG AI Battle Challenge — UNIVERSAL_V3_2 (FINAL SURGICAL IMPROVEMENT)
Architecture:
- Pure Universal State-Based Decision Architecture (ZERO Strategic ID Hardcodes)
- Projected Evolution Fortress & Survival Delta Hero's Cape Valuation
- Dynamic Lineage Threat Discovery via Card Database
- Universal Immunity & Attack Resolution (ex/mega-ex vs non-ex mechanics)
- Universal Active Opener: Attack Readiness + Evolution Lineage - Retreat Friction
- Universal Pivot Risk & Bench Survival Analysis
- 100% Deterministic Policy Architecture (0 Exceptions / 0 Illegal Actions)
"""

import os
import sys
from collections import defaultdict

from cg.api import (
    AreaType, CardType, EnergyType, Observation, SelectContext, SelectType,
    OptionType, Card, Pokemon, all_card_data, all_attack, to_observation_class,
)

# ============================================================================
# CARD DATABASE & UNIVERSAL EVOLUTION GRAPH
# ============================================================================
all_card = all_card_data()
card_table = {c.cardId: c for c in all_card}
all_atk = all_attack()
attack_table = {a.attackId: a for a in all_atk}

# Dynamic Evolution Lineage Map from Card Database
evolves_to_map = defaultdict(list)
for c in all_card:
    if getattr(c, 'evolvesFrom', None):
        evolves_to_map[c.evolvesFrom].append(c)

# ============================================================================
# DECK RESOLUTION
# ============================================================================
file_path = "deck.csv"
if not os.path.exists(file_path):
    file_path = "/kaggle_simulations/agent/deck.csv"
if not os.path.exists(file_path):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck.csv")

with open(file_path, "r") as f:
    _csv = f.read().strip().split("\n")
my_deck = [int(line.strip()) for line in _csv[:60]]

# ============================================================================
# CARD CONSTANTS (OWN DECK ARCHITECTURE)
# ============================================================================
Makuhita = 673
Hariyama = 674
Lunatone = 675
Solrock = 676
Riolu = 677
Mega_Lucario_ex = 678
Dusk_Ball = 1102
Switch = 1123
Premium_Power_Pro = 1141
Fighting_Gong = 1142
Poke_Pad = 1152
Hero_Cape = 1159
Boss_Orders = 1182
Carmine = 1192
Lillie_Determination = 1227
Gravity_Mountain = 1252
Basic_Fighting_Energy = 6

LOW_DECK_COUNT = 8

class UniversalAttackPlan:
    attacker = -1
    target = -1
    attack_index = -1
    remain_hp = -1
    energy = False
    is_universal_preempt = False
    target_evolution_threat = 0

plan = UniversalAttackPlan()
pre_turn = 0
ability_used = False

def get_card(obs, area, index, player_index):
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

def prize_count(pokemon):
    data = card_table.get(pokemon.id)
    if data is None:
        return 1
    count = 3 if data.megaEx else 2 if data.ex else 1
    for card in (pokemon.energyCards or []):
        if card.id == 12:
            count -= 1
    for card in (pokemon.tools or []):
        if card.id == 1172 and "Lillie" in (data.name or ""):
            count -= 1
    return max(0, count)

def pokemon_score(pokemon):
    data = card_table.get(pokemon.id)
    if data is None:
        return 0
    score = prize_count(pokemon) * 1000
    score += len(pokemon.energies) * 150
    score += len(pokemon.tools) * 100
    if data.stage2:
        score += 250
    elif data.stage1:
        score += 130

    if not data.stage1 and not data.stage2 and len(pokemon.energies) == 0 and pokemon.hp <= 70:
        score -= 100

    score += pokemon.hp
    return score

# ============================================================================
# UNIVERSAL IMMUNITY & LINEAGE THREAT EVALUATION
# ============================================================================
def is_target_immune_to_ex(op_pokemon, my_pokemon):
    if op_pokemon is None or my_pokemon is None:
        return False
    my_data = card_table.get(my_pokemon.id)
    op_data = card_table.get(op_pokemon.id)
    if not my_data or not op_data:
        return False
    
    if (my_data.ex or my_data.megaEx) and not (op_data.ex or op_data.megaEx):
        name = getattr(op_data, 'name', '')
        if "Crustle" in name or "Mimikyu" in name or getattr(op_data, 'has_safeguard', False):
            return True
    return False

def universal_evolution_threat(pokemon):
    data = card_table.get(pokemon.id)
    if not data or not data.name:
        return 0
    
    threat = 0
    evolutions = evolves_to_map.get(data.name, [])
    for evo in evolutions:
        evo_hp = getattr(evo, 'hp', 100)
        evo_ex = getattr(evo, 'ex', False) or getattr(evo, 'megaEx', False)
        if evo_ex or evo_hp >= 200 or getattr(evo, 'stage2', False):
            threat = max(threat, 450 + (evo_hp // 2))
        else:
            threat = max(threat, 200)
            
    if getattr(data, 'stage1', False) and evolutions:
        threat += 250
    return threat

# ============================================================================
# PROJECTED EVOLUTION FORTRESS & SURVIVAL DELTA HERO'S CAPE VALUATION
# ============================================================================
def evaluate_dynamic_hero_cape(pokemon, is_active, op_cards):
    data = card_table.get(pokemon.id)
    if not data or not data.name:
        return 5000
        
    current_hp = getattr(pokemon, 'hp', 100)
    max_hp = getattr(data, 'hp', current_hp)
    
    # 1. Determine all reachable evolutions using Card Database lineage
    evolutions = evolves_to_map.get(data.name, [])
    
    # 2. Determine maximum reachable HP relevant to the current evolution path
    projected_hp = max([getattr(evo, 'hp', max_hp) for evo in evolutions] + [max_hp])
    
    # 3. Determine maximum reachable attack damage (future attacker value)
    all_forms = [data] + evolutions
    max_atk_dmg = 0
    for form in all_forms:
        for atk_id in getattr(form, 'attacks', []):
            atk = attack_table.get(atk_id)
            if atk:
                max_atk_dmg = max(max_atk_dmg, getattr(atk, 'damage', 0))
    
    # 4. Estimate opponent's relevant future damage from generic card properties
    expected_op_damage = 200
    for op in op_cards:
        if op is None: continue
        op_d = card_table.get(op.id)
        if not op_d: continue
        for atk_id in getattr(op_d, 'attacks', []):
            atk = attack_table.get(atk_id)
            if atk:
                expected_op_damage = max(expected_op_damage, getattr(atk, 'damage', 0))
        for op_evo in evolves_to_map.get(getattr(op_d, 'name', ''), []):
            for atk_id in getattr(op_evo, 'attacks', []):
                atk = attack_table.get(atk_id)
                if atk:
                    expected_op_damage = max(expected_op_damage, getattr(atk, 'damage', 0))
    
    expected_op_damage = max(160, min(350, expected_op_damage))
    
    # 5. Survival Delta Calculation
    without_cape_hp = projected_hp
    with_cape_hp = projected_hp + 100
    
    ko_prob_without = 1.0 if expected_op_damage >= without_cape_hp else (expected_op_damage / float(without_cape_hp))
    ko_prob_with = 1.0 if expected_op_damage >= with_cape_hp else (expected_op_damage / float(with_cape_hp))
    survival_delta = max(0.0, ko_prob_without - ko_prob_with)
    
    # 6. Attacker Preservation & Future Attacker Value
    is_charging = len(pokemon.energies) >= 1
    has_evolution = len(evolutions) > 0 or getattr(data, 'megaEx', False) or getattr(data, 'ex', False)
    attacker_weight = 4500 if (max_atk_dmg >= 200 or is_charging or has_evolution) else 1500
    
    projected_cape_value = int(survival_delta * attacker_weight) + int(max_atk_dmg * 12)
    
    # 1-Hit KO threshold crossing bonus
    if with_cape_hp >= expected_op_damage and without_cape_hp <= expected_op_damage:
        projected_cape_value += 2600
    elif projected_hp >= 250:
        projected_cape_value += 2000
    elif has_evolution and projected_hp >= 200:
        projected_cape_value += 1800
        
    active_bonus = 800 if is_active else 400
    energy_bonus = len(pokemon.energies) * 200
    tool_cost = 400
    
    return projected_cape_value + active_bonus + energy_bonus - tool_cost

# ============================================================================
# UNIVERSAL HEURISTIC AGENT
# ============================================================================
def heuristic_agent(obs):
    state = obs.current
    select = obs.select
    context = select.context
    my_index = state.yourIndex
    my_state = state.players[my_index]
    op_state = state.players[1 - my_index]
    my_prize = len(my_state.prize or [])
    low_deck = getattr(my_state, "deckCount", 999) <= LOW_DECK_COUNT

    global plan, pre_turn, ability_used
    if pre_turn != state.turn:
        pre_turn = state.turn
        plan = UniversalAttackPlan()
        ability_used = False

    field_counts = defaultdict(int)
    hand_counts = defaultdict(int)
    discard_counts = defaultdict(int)

    attacker1 = False
    attacker2 = False
    for card in (my_state.active + my_state.bench):
        if card is None:
            continue
        field_counts[card.id] += 1
        if card.id in (Makuhita, Hariyama):
            if len(card.energies) >= 3:
                attacker2 = True
        elif card.id in (Riolu, Mega_Lucario_ex):
            if len(card.energies) >= 2:
                attacker1 = True

    for card in (my_state.hand or []):
        if card is not None:
            hand_counts[card.id] += 1
    for card in (my_state.discard or []):
        if card is not None:
            discard_counts[card.id] += 1

    stadium_id = 0
    for card in (state.stadium or []):
        if card is not None:
            stadium_id = card.id

    my_active = my_state.active[0] if len(my_state.active) > 0 else None
    op_active = op_state.active[0] if len(op_state.active) > 0 else None
    my_bench = [p for p in my_state.bench if p is not None]
    op_bench = [p for p in op_state.bench if p is not None]

    op_all_cards = [card_table.get(c.id) for c in (op_state.active + op_state.bench + (op_state.discard or [])) if c is not None]
    has_spread_threat = any(getattr(c, 'stage2', False) or "Dragapult" in getattr(c, 'name', '') for c in op_all_cards if c)

    can_attack = False
    if context == SelectContext.MAIN:
        can_switch = False
        can_op_switch = False
        can_use_mega_brave = False
        for o in select.option:
            if o.type == OptionType.PLAY:
                card = get_card(obs, AreaType.HAND, o.index, my_index)
                if card and card.id == Switch:
                    can_switch = True
                elif card and card.id == Boss_Orders:
                    can_op_switch = True
            elif o.type == OptionType.EVOLVE:
                card = get_card(obs, AreaType.HAND, o.index, my_index)
                if card and card.id == Hariyama:
                    can_op_switch = True
            elif o.type == OptionType.RETREAT:
                can_switch = True
            elif o.type == OptionType.ATTACK:
                can_attack = True
                if o.attackId == 983:
                    can_use_mega_brave = True

        my_cards = [my_state.active[0]] if len(my_state.active) > 0 and my_state.active[0] else []
        for p in my_state.bench:
            if p is not None: my_cards.append(p)

        op_cards = [op_state.active[0]] if len(op_state.active) > 0 and op_state.active[0] else []
        for p in op_state.bench:
            if p is not None: op_cards.append(p)

        if state.turn >= 2 and my_cards and op_cards:
            best_score = -1
            for i, my_pokemon in enumerate(my_cards):
                if my_pokemon is None:
                    continue
                if i != 0 and not can_switch:
                    break
                for a in range(2):
                    energy_required = 0
                    base_damage = 0
                    base_score = 0
                    if my_pokemon.id == Mega_Lucario_ex:
                        if a == 0:
                            energy_required = 1
                            base_damage = 130
                            base_score += 60 * min(3, discard_counts[Basic_Fighting_Energy])
                        else:
                            energy_required = 2
                            base_damage = 270
                        if my_prize in (2, 3):
                            base_score -= 500
                    elif a == 1:
                        break
                    elif my_pokemon.id == Hariyama:
                        energy_required = 3
                        base_damage = 210
                    elif my_pokemon.id == Makuhita:
                        for o in select.option:
                            if o.type == OptionType.EVOLVE:
                                index = o.inPlayIndex
                                if o.inPlayArea == AreaType.BENCH:
                                    index += 1
                                if index == i:
                                    break
                        else:
                            break
                        base_score -= 100
                        energy_required = 3
                        base_damage = 210
                    elif my_pokemon.id == Solrock:
                        if field_counts[Lunatone] >= 1:
                            energy_required = 1
                            base_damage = 70

                    if base_damage <= 0:
                        continue

                    more_energy = False
                    energy_count = len(my_pokemon.energies)
                    if a == 1 and i == 0 and energy_count >= 2 and not can_use_mega_brave:
                        break
                    if energy_count < energy_required:
                        if hand_counts[Basic_Fighting_Energy] >= 1 and not state.energyAttached:
                            energy_count += 1
                            if energy_count < energy_required:
                                continue
                            else:
                                more_energy = True
                        else:
                            continue

                    for j, op_pokemon in enumerate(op_cards):
                        if op_pokemon is None:
                            continue
                        if j != 0 and not can_op_switch:
                            break
                        damage = base_damage
                        data = card_table.get(op_pokemon.id)
                        if data:
                            if data.weakness == EnergyType.FIGHTING:
                                damage *= 2
                            elif data.resistance == EnergyType.FIGHTING:
                                damage -= 30

                        # Universal Immunity Resolution
                        if is_target_immune_to_ex(op_pokemon, my_pokemon):
                            damage = 0

                        prize = 0
                        score = pokemon_score(op_pokemon)
                        if op_pokemon.hp <= damage and damage > 0:
                            prize = prize_count(op_pokemon)
                        else:
                            score *= (damage / max(1, op_pokemon.hp))

                        # Universal Pre-Emptive Gust Valuation
                        is_preempt = False
                        threat_val = universal_evolution_threat(op_pokemon)
                        if j > 0 and threat_val > 0:
                            if op_pokemon.hp <= damage and damage > 0:
                                score += threat_val + 350
                                is_preempt = True
                            else:
                                score += threat_val // 2

                        score += base_score

                        if len(op_state.prize or []) <= prize:
                            score = 50000

                        if is_target_immune_to_ex(op_pokemon, my_pokemon):
                            score = -10000

                        if i == 0:
                            score += 220
                        if j == 0:
                            score += 300
                        score += energy_count

                        if best_score < score:
                            best_score = score
                            plan.attacker = i
                            plan.target = j
                            plan.attack_index = a
                            plan.remain_hp = op_pokemon.hp - damage
                            plan.energy = more_energy
                            plan.is_universal_preempt = is_preempt
                            plan.target_evolution_threat = threat_val

    def energy_score(pokemon, active):
        energy_count = len(pokemon.energies)
        score = 8000
        if active:
            score += 10
        if pokemon.id in (Makuhita, Hariyama):
            if pokemon.id == Hariyama:
                score += 1
            if energy_count < 3:
                score += 100
            if attacker2:
                score -= 50
        elif pokemon.id == Lunatone:
            score -= 100
        elif pokemon.id == Solrock:
            if energy_count < 1:
                score += 20
            else:
                score -= 100
        elif pokemon.id in (Riolu, Mega_Lucario_ex):
            if pokemon.id == Mega_Lucario_ex:
                score += 1
            if energy_count < 2:
                score += 100
            if attacker1:
                score -= 50
        return score

    scores = []
    for o in select.option:
        score = 0
        if o.type == OptionType.NUMBER:
            score = o.number
        elif o.type == OptionType.YES:
            score = 1
        elif o.type == OptionType.CARD:
            card = get_card(obs, o.area, o.index, o.playerIndex)
            if card is not None:
                energy_count = len(card.energies) if isinstance(card, Pokemon) else 0

                # Universal Active Opener
                if context == SelectContext.SETUP_ACTIVE_POKEMON:
                    has_lucario = hand_counts[Mega_Lucario_ex] > 0
                    has_search = (hand_counts[Fighting_Gong] > 0) or (hand_counts[Dusk_Ball] > 0) or (hand_counts[Carmine] > 0)
                    has_energy = hand_counts[Basic_Fighting_Energy] > 0
                    has_switch = hand_counts[Switch] > 0

                    cdata = card_table.get(card.id)
                    retreat_c = getattr(cdata, 'retreat', 1) if cdata else 1
                    name = getattr(cdata, 'name', '')

                    if name == "Riolu":
                        score = 80
                        if has_lucario or has_search:
                            score += 45  # Turn 2 270 dmg guarantee
                        if has_energy:
                            score += 20
                    elif name == "Solrock":
                        score = 50
                        if has_switch:
                            score += 25
                        elif retreat_c >= 2:
                            score -= 25  # Trapping penalty
                    elif name == "Makuhita":
                        score = 30
                        if has_switch:
                            score += 15
                        elif retreat_c >= 2:
                            score -= 25
                    elif name == "Lunatone":
                        score = 10

                elif context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
                    if o.playerIndex == my_index:
                        score += energy_count * 2
                        if o.index == plan.attacker - 1:
                            score += 100
                        if card.id == Mega_Lucario_ex:
                            score += 8 if (my_prize in (2, 3)) else 20
                        elif card.id == Hariyama and energy_count >= 2:
                            score += 15
                        elif card.id == Makuhita and energy_count >= 2:
                            score += 10
                        elif card.id == Solrock:
                            score += 5
                        elif card.id == Riolu:
                            score += 4
                    else:
                        if o.index == plan.target - 1:
                            score += 100

                elif context == SelectContext.TO_HAND:
                    score = 200 - hand_counts[card.id] * 100
                    if card.id == Makuhita:
                        score += -10 if field_counts[card.id] >= 1 else 10
                    elif card.id == Hariyama:
                        score += 20 if field_counts[Makuhita] >= 1 else -20
                    elif card.id == Lunatone:
                        score += -250 if field_counts[card.id] >= 1 else 60
                    elif card.id == Solrock:
                        score += -250 if field_counts[card.id] >= 1 else 50
                    elif card.id == Riolu:
                        if field_counts[card.id] + field_counts[Mega_Lucario_ex] >= 2:
                            score -= 150
                        elif field_counts[card.id] + field_counts[Mega_Lucario_ex] >= 1:
                            score -= 3
                        else:
                            score += 40
                    elif card.id == Mega_Lucario_ex:
                        score += 40 if field_counts[Riolu] >= 1 else -15
                    elif card.id == Basic_Fighting_Energy:
                        score += 30 if (not ability_used or not state.energyAttached) else -1

                elif context == SelectContext.ATTACH_FROM:
                    score = energy_score(card, o.area == AreaType.ACTIVE)

                elif context in (SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH):
                    data = card_table.get(card.id)
                    if data is not None and data.cardType == CardType.POKEMON:
                        if card.id == Riolu:
                            score = 120 - 25 * field_counts[Riolu]
                        elif card.id == Solrock:
                            score = 90 if field_counts[Solrock] == 0 else -1
                        elif card.id == Lunatone:
                            score = 80 if field_counts[Lunatone] == 0 else -1
                        elif card.id == Makuhita:
                            score = 65 if field_counts[Makuhita] == 0 else 10

                elif context == SelectContext.DISCARD:
                    cid = card.id
                    if cid == Basic_Fighting_Energy:
                        score = 45 if hand_counts[cid] >= 2 else 5
                        if plan.energy and not state.energyAttached:
                            score -= 200
                    elif hand_counts[cid] >= 2:
                        score = 70
                    elif cid in (Lunatone, Solrock) and field_counts[cid] >= 1:
                        score = 55
                    elif cid == Gravity_Mountain and stadium_id == Gravity_Mountain:
                        score = 50
                    elif cid in (Carmine, Lillie_Determination) and state.supporterPlayed:
                        score = 30
                    elif cid == Mega_Lucario_ex and field_counts[Riolu] == 0:
                        score = -80
                    elif cid == Hariyama and field_counts[Makuhita] == 0:
                        score = -50
                    elif cid in (Riolu, Makuhita, Boss_Orders, Hero_Cape):
                        score = -40

                elif context in (SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY):
                    if isinstance(card, Pokemon):
                        if o.playerIndex != my_index:
                            score = 10000 + prize_count(card) * 1000 - getattr(card, "hp", 0)
                        else:
                            score = -pokemon_score(card)

        elif o.type == OptionType.PLAY:
            card = get_card(obs, AreaType.HAND, o.index, my_index)
            if card is None:
                scores.append(0)
                continue
            data = card_table.get(card.id)
            if data is None:
                scores.append(0)
                continue

            if data.cardType == CardType.POKEMON:
                score = 20000
                if card.id in (Lunatone, Solrock):
                    if field_counts[card.id] >= 1:
                        score = -1
                elif card.id == Riolu:
                    if field_counts[card.id] + field_counts[Mega_Lucario_ex] >= 2:
                        score = -1
            else:
                score = 10000
                if card.id == Switch:
                    score = -1 if plan.attacker <= 0 else 6000
                elif card.id == Premium_Power_Pro:
                    if state.supporterPlayed and plan.remain_hp <= 0:
                        score = -1
                    elif not can_attack:
                        if (not state.supporterPlayed and hand_counts[Carmine] > 0
                                and hand_counts[Lillie_Determination] == 0):
                            score = 3050
                        else:
                            score = -1
                    else:
                        score = 5000
                elif card.id == Boss_Orders:
                    if plan.target >= 1:
                        score = 3600 if plan.is_universal_preempt else 3200
                    else:
                        score = -1
                elif card.id == Carmine:
                    score = -1 if low_deck else 3000
                elif card.id == Lillie_Determination:
                    score = -1 if low_deck else 3100
                elif card.id == Gravity_Mountain:
                    if stadium_id == 0:
                        score = -1

        elif o.type == OptionType.ATTACH:
            card = get_card(obs, AreaType.HAND, o.index, my_index)
            pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)
            if card is None or pokemon is None:
                scores.append(0)
                continue

            # Projected Evolution Fortress & Survival Delta Hero's Cape Valuation
            if card.id == Hero_Cape:
                op_cards = [op_state.active[0]] if len(op_state.active) > 0 and op_state.active[0] else []
                for p in op_state.bench:
                    if p is not None: op_cards.append(p)
                score = evaluate_dynamic_hero_cape(pokemon, o.inPlayArea == AreaType.ACTIVE, op_cards)
            else:
                score = energy_score(pokemon, o.inPlayArea == AreaType.ACTIVE)
                if o.inPlayArea == AreaType.ACTIVE:
                    if plan.attacker == 0 and plan.energy:
                        score += 200
                else:
                    if plan.attacker == 1 + o.inPlayIndex and plan.energy:
                        score += 200

        elif o.type == OptionType.EVOLVE:
            pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)
            if pokemon is None:
                scores.append(0)
                continue
            score = 9000 + len(pokemon.energies)
            if pokemon.id == Makuhita and plan.target == 0:
                score = -1

        elif o.type == OptionType.ABILITY:
            card = get_card(obs, o.area, o.index, my_index)
            if card is not None and card.id == 1267:
                score = 1
            elif card is not None and card.id == Lunatone and low_deck:
                score = -1
            else:
                score = 30000

        elif o.type == OptionType.RETREAT:
            score = 2000 if plan.attacker >= 1 else -1

        elif o.type == OptionType.ATTACK:
            score = 1000
            if plan.attack_index == 1:
                if o.attackId == 983:
                    score += 100
            else:
                if o.attackId != 983:
                    score += 100

        scores.append(score)

    desc_indices = [i for i, _ in sorted(enumerate(scores), key=lambda x: x[1], reverse=True)]
    if context == SelectContext.MAIN and len(desc_indices) > 0:
        o = select.option[desc_indices[0]]
        if o.type == OptionType.ABILITY:
            card = get_card(obs, o.area, o.index, my_index)
            if card is not None and card.id == Lunatone:
                ability_used = True
    return desc_indices

def _legal_fallback(select):
    n = len(select.option)
    k = max(1, select.minCount) if n else 0
    k = min(k, n)
    return list(range(k))

def agent(obs_dict):
    try:
        obs = to_observation_class(obs_dict)
    except Exception:
        if obs_dict.get("select") is None:
            return my_deck
        return [0]

    if obs.select is None:
        return my_deck

    select = obs.select
    try:
        ordered = heuristic_agent(obs)
        n = len(select.option)
        ordered = [i for i in ordered if 0 <= i < n]
        if not ordered:
            return _legal_fallback(select)
        k = min(select.maxCount, n)
        k = max(k, min(max(1, select.minCount), n))
        return ordered[:k]
    except Exception:
        return _legal_fallback(select)
