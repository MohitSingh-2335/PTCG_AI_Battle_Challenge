"""
Pokémon TCG AI Battle Challenge — Heuristic Agent v2.0
Strategy: Mega Lopunny ex Turbo

Key insight from #1 leaderboard player:
- Mega Lopunny ex (330 HP) has Gale Thrust: 230 dmg for 1 Colorless energy
  IF it moved from Bench to Active this turn.
- By using Switch/Retreat every turn, it consistently deals 230 dmg.
- Colorless type = any energy works.
- Mega evolves directly from Buneary (70 HP Basic) — no Stage 1 needed.
- Fan Rotom's Fan Call ability on T1 searches for up to 3 Colorless ≤100HP Pokémon (finds Buneary).

Turn sequence:
1. Play Buneary + Fan Rotom on turn 1 to fill bench
2. Use Mega Signal / Hilda / Ultra Ball to find Mega Lopunny ex
3. Evolve Buneary -> Mega Lopunny ex (Mega counts as evolution)
4. Attach 1 energy, Switch from bench to active => Gale Thrust 230!
5. Next turn: retreat/switch back, then switch in again => 230 again
"""

import os
import random
from cg.api import (
    Observation, SelectData, Option, State, PlayerState, Pokemon, Card, CardData, Attack,
    OptionType, SelectType, SelectContext, AreaType, EnergyType, CardType,
    to_observation_class, all_card_data, all_attack
)

# ============================================================================
# CARD DATABASE
# ============================================================================
_card_data: dict[int, CardData] = {}
_attack_data: dict[int, Attack] = {}

def _ensure_db():
    global _card_data, _attack_data
    if not _card_data:
        for c in all_card_data():
            _card_data[c.cardId] = c
        for a in all_attack():
            _attack_data[a.attackId] = a

# ============================================================================
# DECK
# ============================================================================
def read_deck_csv() -> list[int]:
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/" + file_path
    with open(file_path, "r") as file:
        csv = file.read().strip().split("\n")
    return [int(line.strip()) for line in csv[:60]]

# ============================================================================
# KEY CARD IDS
# ============================================================================
BUNEARY = 848
MEGA_LOPUNNY_EX = 849
FAN_ROTOM = 174
MEGA_SIGNAL = 1145
ULTRA_BALL = 1121
MASTER_BALL = 1125
SWITCH = 1123
HILDA = 1225
LILLIES_DETERMINATION = 1227
NIGHT_STRETCHER = 1097
AIR_BALLOON = 1174
RESCUE_BOARD = 1157

# Gale Thrust attack ID
GALE_THRUST_ID = None  # Will be resolved dynamically

# ============================================================================
# HELPERS
# ============================================================================
def get_card_data(card_id: int) -> CardData | None:
    _ensure_db()
    return _card_data.get(card_id)

def get_attack_data(attack_id: int) -> Attack | None:
    _ensure_db()
    return _attack_data.get(attack_id)

def get_my_state(state: State) -> PlayerState:
    return state.players[state.yourIndex]

def get_opp_state(state: State) -> PlayerState:
    return state.players[1 - state.yourIndex]

def get_active(player: PlayerState) -> Pokemon | None:
    if player.active and len(player.active) > 0 and player.active[0] is not None:
        return player.active[0]
    return None

def count_energy(pokemon: Pokemon) -> int:
    return len(pokemon.energies)

def is_mega_lopunny(card_id: int) -> bool:
    return card_id == MEGA_LOPUNNY_EX

def is_buneary(card_id: int) -> bool:
    return card_id == BUNEARY

def is_our_pokemon(card_id: int) -> bool:
    return card_id in (BUNEARY, MEGA_LOPUNNY_EX, FAN_ROTOM)

def pokemon_has_energy(pokemon: Pokemon) -> bool:
    return len(pokemon.energies) > 0

def can_attack(pokemon: Pokemon) -> bool:
    """Check if pokemon has at least 1 energy (all our attacks need just 1)."""
    cd = get_card_data(pokemon.id)
    if cd is None:
        return False
    for aid in cd.attacks:
        atk = get_attack_data(aid)
        if atk and len(atk.energies) <= len(pokemon.energies):
            return True
    return False

def score_attack(option: Option, state: State) -> float:
    """Score an attack option."""
    atk = get_attack_data(option.attackId)
    if atk is None:
        return 0.0
    
    score = float(atk.damage)
    
    # Gale Thrust base is 60, but if we switched in this turn it does 230
    # The engine handles the bonus automatically, so we score based on expected damage
    if atk.name and "Gale" in atk.name:
        score = 230  # Assume we switched in (which our strategy ensures)
    
    # Bonus for KO potential
    opp = get_opp_state(state)
    opp_active = get_active(opp)
    if opp_active:
        effective_dmg = score
        # Check weakness (Mega Lopunny is Colorless, weak to Fighting)
        opp_cd = get_card_data(opp_active.id)
        # If we can KO
        if opp_active.hp <= effective_dmg:
            score += 500
    
    # Spiky Hopper ignores effects on opponent - good against protected pokemon
    if atk.text and "isn't affected by any effects" in atk.text:
        score += 20
    
    return score

# ============================================================================
# MAIN SELECTION LOGIC
# ============================================================================
def handle_main(obs: Observation) -> list[int]:
    state = obs.current
    select = obs.select
    options = select.option
    me = get_my_state(state)
    opp = get_opp_state(state)
    my_active = get_active(me)
    
    # Classify options
    play_opts = []
    attach_opts = []
    evolve_opts = []
    ability_opts = []
    attack_opts = []
    retreat_opts = []
    end_opts = []
    
    for i, opt in enumerate(options):
        if opt.type == OptionType.PLAY: play_opts.append(i)
        elif opt.type == OptionType.ATTACH: attach_opts.append(i)
        elif opt.type == OptionType.EVOLVE: evolve_opts.append(i)
        elif opt.type == OptionType.ABILITY: ability_opts.append(i)
        elif opt.type == OptionType.ATTACK: attack_opts.append(i)
        elif opt.type == OptionType.RETREAT: retreat_opts.append(i)
        elif opt.type == OptionType.END: end_opts.append(i)
    
    # Check bench state
    has_bench_mega_with_energy = any(
        is_mega_lopunny(bp.id) and pokemon_has_energy(bp) for bp in me.bench
    )
    has_bench_mega = any(is_mega_lopunny(bp.id) for bp in me.bench)
    active_is_mega = my_active and is_mega_lopunny(my_active.id)
    active_can_attack = my_active and can_attack(my_active)
    
    # === P0: Use Fan Rotom ability (search for Buneary) ===
    for i in ability_opts:
        opt = options[i]
        if opt.cardId == FAN_ROTOM:
            return [i]
    
    # === P1: EVOLVE Buneary -> Mega Lopunny ex ===
    if evolve_opts:
        bench_evolves = [i for i in evolve_opts if options[i].inPlayArea == AreaType.BENCH]
        active_evolves = [i for i in evolve_opts if options[i].inPlayArea == AreaType.ACTIVE]
        if bench_evolves:
            return [bench_evolves[0]]
        if active_evolves:
            return [active_evolves[0]]
    
    # === P2: CRITICAL — Switch cycling for Gale Thrust bonus ===
    # If active is NOT Mega Lopunny, but we have one on bench with energy: SWITCH NOW
    # If active IS Mega Lopunny and we have another on bench with energy: swap for fresh Gale Thrust
    if has_bench_mega_with_energy:
        # Try Switch item first
        for i in play_opts:
            opt = options[i]
            if me.hand is None: continue
            if opt.index >= len(me.hand): continue
            hand_card = me.hand[opt.index]
            if hand_card is None: continue
            if hand_card.id == SWITCH:
                return [i]
        # Try retreat if we can't switch
        if retreat_opts and my_active and not active_is_mega:
            return [retreat_opts[0]]
        # If active is Mega Lopunny but hasn't attacked yet, retreat to swap
        if retreat_opts and active_is_mega and active_can_attack:
            # Only retreat if we have another Mega Lopunny on bench that can attack
            for bp in me.bench:
                if is_mega_lopunny(bp.id) and pokemon_has_energy(bp):
                    return [retreat_opts[0]]
    
    # === P3: Attach energy to Mega Lopunny that needs it ===
    if attach_opts and not state.energyAttached:
        best_i, best_score = None, -1
        for i in attach_opts:
            opt = options[i]
            score = 0
            if opt.inPlayArea == AreaType.ACTIVE:
                act = get_active(me)
                if act and is_mega_lopunny(act.id):
                    score = 300 if count_energy(act) == 0 else 50
                elif act:
                    score = 10
            elif opt.inPlayArea == AreaType.BENCH:
                if opt.inPlayIndex is not None and opt.inPlayIndex < len(me.bench):
                    bp = me.bench[opt.inPlayIndex]
                    if is_mega_lopunny(bp.id) and count_energy(bp) == 0:
                        score = 250
                    elif is_mega_lopunny(bp.id):
                        score = 40
                    elif is_buneary(bp.id):
                        score = 20
                    else:
                        score = 5
            if score > best_score:
                best_score = score
                best_i = i
        if best_i is not None:
            return [best_i]
    
    # === P4: Play search Items (Mega Signal, Ultra Ball, Master Ball) ===
    for i in play_opts:
        opt = options[i]
        if me.hand is None: continue
        if opt.index >= len(me.hand): continue
        hand_card = me.hand[opt.index]
        if hand_card is None: continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.ITEM:
            if hand_card.id == MEGA_SIGNAL:
                return [i]
            if hand_card.id in (ULTRA_BALL, MASTER_BALL):
                return [i]
            if hand_card.id == NIGHT_STRETCHER:
                return [i]
    
    # === P5: Play Supporters (search/draw) ===
    if not state.supporterPlayed:
        for i in play_opts:
            opt = options[i]
            if me.hand is None: continue
            if opt.index >= len(me.hand): continue
            hand_card = me.hand[opt.index]
            if hand_card is None: continue
            cd = get_card_data(hand_card.id)
            if cd and cd.cardType == CardType.SUPPORTER:
                if hand_card.id == HILDA:
                    return [i]
                if hand_card.id == LILLIES_DETERMINATION:
                    return [i]
    
    # === P6: Play Tools (Air Balloon, Rescue Board) on Mega Lopunny ===
    for i in play_opts:
        opt = options[i]
        if me.hand is None: continue
        if opt.index >= len(me.hand): continue
        hand_card = me.hand[opt.index]
        if hand_card is None: continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.TOOL:
            return [i]
    
    # === P7: Play Basic Pokemon to bench ===
    for i in play_opts:
        opt = options[i]
        if me.hand is None: continue
        if opt.index >= len(me.hand): continue
        hand_card = me.hand[opt.index]
        if hand_card is None: continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.POKEMON and cd.basic:
            if len(me.bench) < me.benchMax:
                return [i]
    
    # === P8: Retreat if active can't attack but benched can ===
    if retreat_opts and my_active:
        if not active_can_attack:
            for bp in me.bench:
                if can_attack(bp):
                    return [retreat_opts[0]]
    
    # === P9: Attack! ===
    if attack_opts:
        best_i, best_score = 0, -1
        for i in attack_opts:
            score = score_attack(options[i], state)
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # === P10: End turn ===
    if end_opts:
        return [end_opts[0]]
    
    return random.sample(list(range(len(options))), select.maxCount)


def handle_card(obs: Observation) -> list[int]:
    select = obs.select
    state = obs.current
    options = select.option
    context = select.context
    me = get_my_state(state)
    opp = get_opp_state(state)
    
    # --- SETUP: Active pokemon ---
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        # Prefer Buneary (will evolve into Mega Lopunny), or Fan Rotom
        for i, opt in enumerate(options):
            if opt.cardId == FAN_ROTOM:
                return [i]  # Fan Rotom as active = can use Fan Call T1
        for i, opt in enumerate(options):
            if opt.cardId == BUNEARY:
                return [i]
        return [0]
    
    # --- SETUP: Bench pokemon ---
    if context == SelectContext.SETUP_BENCH_POKEMON:
        chosen = []
        # Bench Buneary first
        for i, opt in enumerate(options):
            if opt.cardId == BUNEARY and len(chosen) < select.maxCount:
                chosen.append(i)
        # Then Fan Rotom
        for i, opt in enumerate(options):
            if opt.cardId == FAN_ROTOM and i not in chosen and len(chosen) < select.maxCount:
                chosen.append(i)
        if chosen:
            return chosen[:select.maxCount]
        return list(range(min(select.minCount, len(options))))
    
    # --- SWITCH/TO_ACTIVE: Pick Mega Lopunny with energy ---
    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            if opt.cardId == MEGA_LOPUNNY_EX:
                score += 200
            if opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                bp = me.bench[opt.index]
                if pokemon_has_energy(bp):
                    score += 100
                score += count_energy(bp) * 10
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # --- TO_BENCH ---
    if context == SelectContext.TO_BENCH:
        chosen = []
        for i, opt in enumerate(options):
            if opt.cardId in (BUNEARY, MEGA_LOPUNNY_EX):
                chosen.append(i)
        if chosen:
            return chosen[:select.maxCount]
        return list(range(min(select.maxCount, len(options))))
    
    # --- TO_HAND: Search results — pick best cards ---
    if context == SelectContext.TO_HAND:
        scored = []
        for i, opt in enumerate(options):
            score = 0
            if opt.cardId == MEGA_LOPUNNY_EX:
                score = 100
            elif opt.cardId == BUNEARY:
                score = 80
            elif opt.cardId == FAN_ROTOM:
                score = 60
            else:
                cd = get_card_data(opt.cardId) if opt.cardId else None
                if cd:
                    if cd.cardType == CardType.BASIC_ENERGY:
                        score = 70
                    elif cd.cardType == CardType.SUPPORTER:
                        score = 50
                    elif cd.cardType == CardType.ITEM:
                        score = 40
                    else:
                        score = 30
                else:
                    score = 20
            scored.append((score, i))
        scored.sort(reverse=True)
        return [s[1] for s in scored[:select.maxCount]]
    
    # --- DISCARD: Discard least valuable ---
    if context == SelectContext.DISCARD:
        scored = []
        for i, opt in enumerate(options):
            score = 50
            cd = get_card_data(opt.cardId) if opt.cardId else None
            if cd:
                if is_mega_lopunny(cd.cardId): score = 5
                elif is_buneary(cd.cardId): score = 10
                elif cd.cardType == CardType.BASIC_ENERGY: score = 70  # Extra energy is fine to discard
                elif cd.cardType == CardType.SUPPORTER: score = 60
                elif cd.cardType == CardType.ITEM: score = 55
                else: score = 80
            scored.append((score, i))
        scored.sort(reverse=True)
        return [s[1] for s in scored[:select.maxCount]]
    
    # --- DAMAGE targeting ---
    if context in (SelectContext.DAMAGE, SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY):
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            if opt.playerIndex != state.yourIndex:
                score += 100
                if opt.area == AreaType.ACTIVE:
                    a = get_active(opp)
                    if a: score += (500 - a.hp)
                elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(opp.bench):
                    score += (500 - opp.bench[opt.index].hp)
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # --- HEAL ---
    if context in (SelectContext.HEAL, SelectContext.REMOVE_DAMAGE_COUNTER):
        best_i, best_dmg = 0, -1
        for i, opt in enumerate(options):
            if opt.playerIndex == state.yourIndex:
                if opt.area == AreaType.ACTIVE:
                    a = get_active(me)
                    if a and (a.maxHp - a.hp) > best_dmg:
                        best_dmg = a.maxHp - a.hp
                        best_i = i
                elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                    bp = me.bench[opt.index]
                    if (bp.maxHp - bp.hp) > best_dmg:
                        best_dmg = bp.maxHp - bp.hp
                        best_i = i
        return [best_i]
    
    # --- ATTACH_TO ---
    if context == SelectContext.ATTACH_TO:
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            if opt.area == AreaType.ACTIVE:
                a = get_active(me)
                if a and is_mega_lopunny(a.id) and count_energy(a) == 0:
                    score = 300
                elif a:
                    score = 50
            elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                bp = me.bench[opt.index]
                if is_mega_lopunny(bp.id) and count_energy(bp) == 0:
                    score = 250
                elif is_mega_lopunny(bp.id):
                    score = 40
                else:
                    score = 10
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # --- EVOLVES_FROM: Pick Buneary to evolve ---
    if context == SelectContext.EVOLVES_FROM:
        for i, opt in enumerate(options):
            if opt.cardId == BUNEARY:
                return [i]
        return [0]
    
    # --- EVOLVES_TO: Pick Mega Lopunny ---
    if context == SelectContext.EVOLVES_TO:
        for i, opt in enumerate(options):
            if opt.cardId == MEGA_LOPUNNY_EX:
                return [i]
        return [0]
    
    # --- LOOK ---
    if context == SelectContext.LOOK:
        scored = []
        for i, opt in enumerate(options):
            score = 0
            if opt.cardId == MEGA_LOPUNNY_EX: score = 100
            elif opt.cardId == BUNEARY: score = 80
            else:
                cd = get_card_data(opt.cardId) if opt.cardId else None
                if cd and cd.cardType == CardType.BASIC_ENERGY: score = 70
                elif cd and cd.cardType == CardType.SUPPORTER: score = 60
                else: score = 30
            scored.append((score, i))
        scored.sort(reverse=True)
        return [s[1] for s in scored[:select.maxCount]]
    
    # --- Default ---
    count = min(select.maxCount, len(options))
    count = max(count, select.minCount)
    return list(range(count)) if count > 0 else []


def handle_yes_no(obs: Observation) -> list[int]:
    select = obs.select
    context = select.context
    options = select.option
    
    # Go first
    if context == SelectContext.IS_FIRST:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES: return [i]
    # Mulligan: redraw
    if context == SelectContext.MULLIGAN:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES: return [i]
    # Activate effects: yes
    if context == SelectContext.ACTIVATE:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES: return [i]
    # Coin: heads
    if context == SelectContext.COIN_HEAD:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES: return [i]
    # Default: yes
    for i, opt in enumerate(options):
        if opt.type == OptionType.YES: return [i]
    return [0]


def handle_energy(obs: Observation) -> list[int]:
    select = obs.select
    count = min(select.maxCount, len(select.option))
    count = max(count, select.minCount)
    return list(range(count))


def handle_attack(obs: Observation) -> list[int]:
    select = obs.select
    state = obs.current
    best_i, best_score = 0, -1
    for i, opt in enumerate(select.option):
        score = score_attack(opt, state)
        if score > best_score:
            best_score = score
            best_i = i
    return [best_i]


def handle_count(obs: Observation) -> list[int]:
    select = obs.select
    # Pick maximum
    for i, opt in enumerate(select.option):
        if opt.type == OptionType.NUMBER and opt.number == select.maxCount:
            return [i]
    best_i, best_val = 0, -1
    for i, opt in enumerate(select.option):
        if opt.number is not None and opt.number > best_val:
            best_val = opt.number
            best_i = i
    return [best_i]


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def agent(obs_dict: dict) -> list[int]:
    _ensure_db()
    obs: Observation = to_observation_class(obs_dict)
    
    if obs.select is None:
        return read_deck_csv()
    
    select = obs.select
    
    try:
        if select.type == SelectType.MAIN:
            return handle_main(obs)
        elif select.type == SelectType.CARD:
            return handle_card(obs)
        elif select.type == SelectType.YES_NO:
            return handle_yes_no(obs)
        elif select.type == SelectType.ENERGY:
            return handle_energy(obs)
        elif select.type == SelectType.ATTACK:
            return handle_attack(obs)
        elif select.type == SelectType.COUNT:
            return handle_count(obs)
        elif select.type in (SelectType.ATTACHED_CARD, SelectType.CARD_OR_ATTACHED_CARD, SelectType.EVOLVE):
            return handle_card(obs)
        elif select.type == SelectType.SKILL:
            return list(range(min(select.maxCount, len(select.option))))
        elif select.type == SelectType.SPECIAL_CONDITION:
            return [0]
        else:
            count = min(select.maxCount, len(select.option))
            count = max(count, select.minCount)
            return random.sample(list(range(len(select.option))), count)
    except Exception:
        count = min(select.maxCount, len(select.option))
        count = max(count, select.minCount)
        if count <= 0: return []
        return random.sample(list(range(len(select.option))), count)
