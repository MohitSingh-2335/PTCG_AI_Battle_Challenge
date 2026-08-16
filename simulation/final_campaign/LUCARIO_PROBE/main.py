"""
Pokémon TCG AI Battle Challenge — Mega Lucario ex + Crustle-Aware Counter Agent
Architecture:
- High-Tempo Mega Lucario ex (270 dmg Mega Brave / 440 HP Hero's Cape)
- Crustle Anti-Wall Engine: Hariyama (210 dmg non-ex) & Solrock (70 dmg non-ex)
- 100% Deterministic Policy Architecture (0 Exceptions / 0 Fallbacks)
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
# CARD CONSTANTS
# ============================================================================
MAKUHITA = 673
HARIYAMA = 674
LUNATONE = 675
SOLROCK = 676
RIOLU = 677
MEGA_LUCARIO_EX = 678
DUSK_BALL = 1102
SWITCH = 1123
PREMIUM_POWER_PRO = 1141
FIGHTING_GONG = 1142
POKE_PAD = 1152
HERO_CAPE = 1159
BOSS_ORDERS = 1182
CARMINE = 1192
LILLIE_DETERMINATION = 1227
GRAVITY_MOUNTAIN = 1252
BASIC_FIGHTING_ENERGY = 6
CRUSTLE = 345
DWEBBLE = 344

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

def prize_count(pokemon: Pokemon) -> int:
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

def pokemon_score(pokemon: Pokemon, my_prizes_left: int = 6) -> int:
    data = card_table.get(pokemon.id)
    if data is None:
        return 0
    prizes = prize_count(pokemon)
    if prizes >= my_prizes_left:
        score = 60000
    else:
        score = prizes * 5000
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
# MAIN AGENT FUNCTION
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
    op_active = op_state.active[0] if len(op_state.active) > 0 else None

    # Field Tracking
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

    # Opponent Archetype Recognition
    op_pokes = [p.id for p in (op_state.active + op_state.bench) if p is not None]
    op_discard_ids = [c.id for c in (op_state.discard or [])]
    op_all_seen = set(op_pokes + op_discard_ids)

    is_crustle_active = op_active is not None and op_active.id == CRUSTLE
    is_crustle_threat = any(cid in (CRUSTLE, DWEBBLE) for cid in op_all_seen)

    # Active State
    active_is_lucario = my_active is not None and my_active.id == MEGA_LUCARIO_EX
    active_is_hariyama = my_active is not None and my_active.id == HARIYAMA
    active_energy = len(my_active.energies) if my_active else 0
    bench_has_hariyama = any(p is not None and p.id == HARIYAMA for p in my_state.bench)
    bench_has_solrock = any(p is not None and p.id == SOLROCK for p in my_state.bench)

    def attach_score(pokemon: Pokemon, active: bool) -> int:
        e = len(pokemon.energies)
        score = 8000
        # If Crustle is active, prioritize charging Hariyama (210 dmg non-ex) or Solrock (70 dmg non-ex)
        if is_crustle_active:
            if pokemon.id == HARIYAMA:
                score += 15000 + (3000 if e < 3 else -500)
            elif pokemon.id == MAKUHITA:
                score += 12000 + (2000 if e < 3 else -500)
            elif pokemon.id == SOLROCK:
                score += 8000 + (1000 if e < 1 else -500)
            elif pokemon.id == MEGA_LUCARIO_EX:
                score += 500
        else:
            if pokemon.id == MEGA_LUCARIO_EX:
                score += 10000
                if e < 2:
                    score += 5000
                elif e >= 2:
                    score -= 500
            elif pokemon.id == RIOLU:
                score += 4000
                if e < 2:
                    score += 2000
            elif pokemon.id == HARIYAMA:
                score += 2000
            elif pokemon.id == SOLROCK and field_counts[LUNATONE] >= 1:
                score += 1500
        return score

    def hand_score(card_id: int) -> int:
        if card_id == MEGA_LUCARIO_EX:
            return 250 if field_counts[RIOLU] >= 1 else 100
        elif card_id == RIOLU:
            return 200 if field_counts[RIOLU] + field_counts[MEGA_LUCARIO_EX] < 2 else 50
        elif card_id == HARIYAMA:
            return 300 if is_crustle_threat else 80
        elif card_id == MAKUHITA:
            return 220 if is_crustle_threat and field_counts[MAKUHITA] == 0 else 60
        elif card_id == FIGHTING_GONG:
            return 240
        elif card_id == CARMINE:
            return 230 if state.turn <= 2 else 150
        elif card_id == LILLIE_DETERMINATION:
            return 180
        elif card_id == HERO_CAPE:
            return 190
        elif card_id == PREMIUM_POWER_PRO:
            return 140
        elif card_id == BOSS_ORDERS:
            return 185
        elif card_id == SWITCH:
            return 160
        elif card_id == BASIC_FIGHTING_ENERGY:
            return 170 if hand_counts[BASIC_FIGHTING_ENERGY] == 0 else 20
        else:
            return 10

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
                hp = card.hp if isinstance(card, Pokemon) else 0
                e_cnt = len(card.energies) if isinstance(card, Pokemon) else 0

                if context == SelectContext.SETUP_ACTIVE_POKEMON:
                    if card.id == RIOLU:
                        score = 100
                    elif card.id == SOLROCK:
                        score = 80
                    elif card.id == MAKUHITA:
                        score = 60
                    elif card.id == LUNATONE:
                        score = 40
                    else:
                        score = 10

                elif context == SelectContext.SETUP_BENCH_POKEMON:
                    if card.id == RIOLU:
                        score = 100
                    elif card.id == LUNATONE and field_counts[LUNATONE] == 0:
                        score = 90
                    elif card.id == MAKUHITA and is_crustle_threat:
                        score = 95
                    elif card.id == SOLROCK:
                        score = 80
                    elif card.id == MAKUHITA:
                        score = 70
                    else:
                        score = -1

                elif context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
                    if o.playerIndex == my_index:
                        score += e_cnt * 100 + hp
                        if is_crustle_active:
                            if card.id == HARIYAMA:
                                score += 60000
                            elif card.id == SOLROCK:
                                score += 30000
                            elif card.id == MEGA_LUCARIO_EX:
                                score += 500
                        else:
                            if card.id == MEGA_LUCARIO_EX:
                                score += 50000
                            elif card.id == HARIYAMA:
                                score += 10000
                    else:
                        score = pokemon_score(card, len(my_state.prize or [])) if isinstance(card, Pokemon) else 0

                elif context == SelectContext.TO_BENCH:
                    if card.id == RIOLU:
                        score = 2500
                    elif card.id == LUNATONE and field_counts[LUNATONE] == 0:
                        score = 2200
                    elif card.id == MAKUHITA and is_crustle_threat:
                        score = 2400
                    elif card.id == SOLROCK:
                        score = 1800
                    else:
                        score = 100

                elif context == SelectContext.TO_HAND:
                    score = hand_score(card.id)

                elif context == SelectContext.DISCARD:
                    if o.area == AreaType.HAND and o.playerIndex == my_index:
                        score = -hand_score(card.id)
                    else:
                        score = 0

                elif context in (SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY, SelectContext.DAMAGE):
                    if isinstance(card, Pokemon) and hp > 0:
                        score = 100000 - 10 * hp + pokemon_score(card, len(my_state.prize or []))
                        if o.area == AreaType.ACTIVE:
                            score += 5000

                elif context == SelectContext.ATTACH_FROM:
                    if isinstance(card, Pokemon):
                        score = attach_score(card, o.area == AreaType.ACTIVE)

                elif context == SelectContext.EVOLVES_TO:
                    score = 100 if card.id == MEGA_LUCARIO_EX else (90 if card.id == HARIYAMA else 10)

                elif context == SelectContext.ATTACH_TO:
                    if isinstance(card, Pokemon) and o.playerIndex == my_index:
                        has_tool = len(getattr(card, 'tools', []) or []) > 0
                        if has_tool:
                            score = -1000
                        elif card.id == MEGA_LUCARIO_EX:
                            score = 10000
                        elif card.id == HARIYAMA:
                            score = 5000
                        else:
                            score = 100

        elif o.type in (OptionType.ENERGY_CARD, OptionType.ENERGY):
            score = 10 if o.playerIndex != my_index else 0

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
                    elif card.id == RIOLU:
                        score = 52000 if field_counts[RIOLU] + field_counts[MEGA_LUCARIO_EX] < 3 else -1
                    elif card.id == LUNATONE:
                        score = 51000 if field_counts[LUNATONE] == 0 else -1
                    elif card.id == MAKUHITA:
                        score = 53000 if is_crustle_threat else 48000
                    elif card.id == SOLROCK:
                        score = 49000
                    else:
                        score = 10000

                elif data.cardType == CardType.ITEM:
                    if card.id == FIGHTING_GONG:
                        score = 80000
                    elif card.id == DUSK_BALL:
                        score = 60000
                    elif card.id == POKE_PAD:
                        score = 40000 if len(my_state.discard or []) > 0 else -1
                    elif card.id == SWITCH:
                        if is_crustle_active and active_is_lucario and (bench_has_hariyama or bench_has_solrock):
                            score = 90000
                        elif not active_is_lucario and any(p is not None and p.id == MEGA_LUCARIO_EX and len(p.energies) >= 2 for p in my_state.bench):
                            score = 85000
                        else:
                            score = -1
                    else:
                        score = -1

                elif data.cardType == CardType.TOOL:
                    all_pokes = [p for p in (my_state.active + my_state.bench) if p is not None]
                    has_unattached = any(len(getattr(p, 'tools', []) or []) == 0 for p in all_pokes)
                    if not has_unattached:
                        score = -1
                    elif card.id == HERO_CAPE:
                        score = 75000
                    elif card.id == PREMIUM_POWER_PRO:
                        score = 65000
                    else:
                        score = 10000

                elif data.cardType == CardType.SUPPORTER:
                    if state.supporterPlayed:
                        score = -1
                    elif card.id == BOSS_ORDERS:
                        if len(op_state.bench or []) > 0:
                            if is_crustle_active and active_is_lucario:
                                score = 98000
                            else:
                                score = 96000
                        else:
                            score = -1
                    elif card.id == CARMINE:
                        score = 94000
                    elif card.id == LILLIE_DETERMINATION:
                        score = 92000
                    else:
                        score = -1

                elif data.cardType == CardType.STADIUM:
                    score = 20000
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
                score += len(pokemon.energies) * 500
                if o.inPlayArea == AreaType.BENCH:
                    score += 100

        elif o.type == OptionType.ABILITY:
            score = 85000

        elif o.type == OptionType.RETREAT:
            if is_crustle_active and active_is_lucario and (bench_has_hariyama or bench_has_solrock):
                score = 90000
            elif not active_is_lucario and any(p is not None and p.id == MEGA_LUCARIO_EX and len(p.energies) >= 2 for p in my_state.bench):
                score = 85000
            else:
                score = -1

        elif o.type == OptionType.ATTACK:
            score = 1000
            atk = attack_table.get(o.attackId)
            if atk is not None:
                effective_damage = atk.damage
                if active_is_lucario and is_crustle_active:
                    effective_damage = 0

                score += effective_damage // 10

                if op_active and op_active.hp <= effective_damage and effective_damage > 0:
                    prizes_taken = prize_count(op_active)
                    if prizes_taken >= len(my_state.prize or []):
                        score += 60000
                    else:
                        score += 30000

        elif o.type == OptionType.END:
            score = 0
        elif o.type == OptionType.DISCARD:
            score = -1
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
