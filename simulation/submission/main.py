"""
Pokémon TCG AI Battle Challenge — Heuristic Agent v1.0
Strategy: Gouging Fire ex Turbo
- Prioritize getting Gouging Fire ex into active and powered up
- Use Firebreather to grab Fire energy in bulk
- Alternate Blaze Blitz (260) with Heat Blast (60) or rotate via Switch
- Use Boss's Orders to target weak bench Pokemon for easy KOs
"""

import os
import random
from cg.api import (
    Observation, SelectData, Option, State, PlayerState, Pokemon, Card, CardData, Attack,
    OptionType, SelectType, SelectContext, AreaType, EnergyType, CardType,
    to_observation_class, all_card_data, all_attack
)

# ============================================================================
# CARD DATABASE (loaded once)
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
    deck = []
    for line in csv[:60]:
        deck.append(int(line.strip()))
    return deck

# ============================================================================
# KEY CARD IDS
# ============================================================================
GOUGING_FIRE_EX = 46
FIRE_ENERGY = 2
PRECIOUS_TROLLEY = 1126
ULTRA_BALL = 1121
MASTER_BALL = 1125
SWITCH = 1123
PRIME_CATCHER = 1088
BOSSS_ORDERS = 1182
FIREBREATHER = 1232
LILLIES_DETERMINATION = 1227
NIGHT_STRETCHER = 1097
MAXIMUM_BELT = 1158
SURVIVAL_BRACE = 1155

# ============================================================================
# HELPER FUNCTIONS
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

def get_active_pokemon(player: PlayerState) -> Pokemon | None:
    if player.active and len(player.active) > 0 and player.active[0] is not None:
        return player.active[0]
    return None

def count_energy(pokemon: Pokemon, energy_type: EnergyType | None = None) -> int:
    """Count energies on a pokemon, optionally filtering by type."""
    if energy_type is None:
        return len(pokemon.energies)
    return sum(1 for e in pokemon.energies if e == energy_type)

def is_gouging_fire(card_id: int) -> bool:
    return card_id == GOUGING_FIRE_EX

def pokemon_can_attack(pokemon: Pokemon) -> bool:
    """Check if pokemon has enough energy for any attack."""
    cd = get_card_data(pokemon.id)
    if cd is None:
        return False
    for aid in cd.attacks:
        atk = get_attack_data(aid)
        if atk is None:
            continue
        if can_pay_attack_cost(pokemon, atk):
            return True
    return False

def can_pay_attack_cost(pokemon: Pokemon, attack: Attack) -> bool:
    """Check if a pokemon has enough energy to use an attack."""
    available = list(pokemon.energies)
    needed = list(attack.energies)
    
    for e in needed:
        if e in available:
            available.remove(e)
        elif EnergyType.COLORLESS in [e] or e == EnergyType.COLORLESS:
            # Colorless can be paid by any energy
            if available:
                available.pop(0)
            else:
                return False
        else:
            # Try to pay with any available energy for colorless cost
            return False
    return True

def score_attack_option(option: Option, state: State) -> float:
    """Score an attack option based on damage and strategic value."""
    atk = get_attack_data(option.attackId)
    if atk is None:
        return 0.0
    
    score = float(atk.damage)
    
    # Bonus for attacks that can KO the opponent's active
    opp = get_opp_state(state)
    opp_active = get_active_pokemon(opp)
    if opp_active and opp_active.hp <= atk.damage:
        score += 500  # Huge bonus for KO
    
    # Penalty for self-damage or can't-use-again restrictions (but still worth doing)
    text = atk.text.lower()
    if "damage to itself" in text:
        score -= 20
    
    return score

# ============================================================================
# MAIN SELECTION LOGIC
# ============================================================================
def handle_main_selection(obs: Observation) -> list[int]:
    """Handle the MAIN selection (what to do on your turn)."""
    state = obs.current
    select = obs.select
    options = select.option
    me = get_my_state(state)
    opp = get_opp_state(state)
    my_active = get_active_pokemon(me)
    
    # Categorize available options
    play_options = []      # Play cards from hand
    attach_options = []    # Attach energy
    evolve_options = []    # Evolve pokemon
    ability_options = []   # Use abilities
    attack_options = []    # Attack
    retreat_options = []   # Retreat
    end_options = []       # End turn
    
    for i, opt in enumerate(options):
        if opt.type == OptionType.PLAY:
            play_options.append(i)
        elif opt.type == OptionType.ATTACH:
            attach_options.append(i)
        elif opt.type == OptionType.EVOLVE:
            evolve_options.append(i)
        elif opt.type == OptionType.ABILITY:
            ability_options.append(i)
        elif opt.type == OptionType.ATTACK:
            attack_options.append(i)
        elif opt.type == OptionType.RETREAT:
            retreat_options.append(i)
        elif opt.type == OptionType.END:
            end_options.append(i)
    
    # === PRIORITY 1: Play Supporter cards (draw/search) ===
    if not state.supporterPlayed:
        for i in play_options:
            opt = options[i]
            if me.hand is None:
                continue
            hand_card = me.hand[opt.index] if opt.index < len(me.hand) else None
            if hand_card is None:
                continue
            cd = get_card_data(hand_card.id)
            if cd and cd.cardType == CardType.SUPPORTER:
                # Prioritize Firebreather (energy search) and Lillie's (draw)
                if hand_card.id == FIREBREATHER:
                    return [i]
                if hand_card.id == LILLIES_DETERMINATION:
                    return [i]
                if hand_card.id == BOSSS_ORDERS:
                    # Use Boss's Orders if opponent has a weak benched pokemon
                    opp_bench = opp.bench
                    opp_active = get_active_pokemon(opp)
                    if opp_bench:
                        # Check if there's a weaker target on bench
                        weakest_bench_hp = min(p.hp for p in opp_bench)
                        active_hp = opp_active.hp if opp_active else 999
                        if weakest_bench_hp < active_hp:
                            return [i]
    
    # === PRIORITY 2: Play Item cards ===
    for i in play_options:
        opt = options[i]
        if me.hand is None:
            continue
        hand_card = me.hand[opt.index] if opt.index < len(me.hand) else None
        if hand_card is None:
            continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.ITEM:
            # Play search items first (Ultra Ball, Master Ball, Precious Trolley)
            if hand_card.id in (ULTRA_BALL, MASTER_BALL, PRECIOUS_TROLLEY):
                return [i]
            # Play Night Stretcher to recover resources
            if hand_card.id == NIGHT_STRETCHER:
                return [i]
            # Play Switch if active can't attack but benched Gouging Fire can
            if hand_card.id == SWITCH and my_active:
                if not pokemon_can_attack(my_active):
                    for bp in me.bench:
                        if is_gouging_fire(bp.id) and pokemon_can_attack(bp):
                            return [i]
                # Also switch if Gouging Fire used Blaze Blitz (to reset it)
                # We detect this indirectly: if active is Gouging Fire with 3+ energy but 
                # we have another powered Gouging Fire on bench
                if is_gouging_fire(my_active.id) and count_energy(my_active) >= 3:
                    for bp in me.bench:
                        if is_gouging_fire(bp.id) and count_energy(bp) >= 3:
                            return [i]
            if hand_card.id == PRIME_CATCHER:
                return [i]
    
    # === PRIORITY 3: Play Tool cards ===
    for i in play_options:
        opt = options[i]
        if me.hand is None:
            continue
        hand_card = me.hand[opt.index] if opt.index < len(me.hand) else None
        if hand_card is None:
            continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.TOOL:
            return [i]
    
    # === PRIORITY 4: Attach energy to active Gouging Fire first, then bench ===
    if attach_options and not state.energyAttached:
        best_attach = None
        best_score = -1
        for i in attach_options:
            opt = options[i]
            score = 0
            # Prefer attaching to active pokemon
            if opt.inPlayArea == AreaType.ACTIVE:
                score += 100
                # Extra bonus if it's Gouging Fire and needs energy
                if my_active and is_gouging_fire(my_active.id):
                    energy_count = count_energy(my_active)
                    if energy_count < 3:
                        score += 200 - energy_count * 50  # Higher priority when fewer energy
            elif opt.inPlayArea == AreaType.BENCH:
                # Prefer attaching to benched Gouging Fire
                if opt.inPlayIndex < len(me.bench):
                    bp = me.bench[opt.inPlayIndex]
                    if is_gouging_fire(bp.id):
                        energy_count = count_energy(bp)
                        if energy_count < 3:
                            score += 50
            if score > best_score:
                best_score = score
                best_attach = i
        if best_attach is not None:
            return [best_attach]
    
    # === PRIORITY 5: Play basic pokemon from hand to bench ===
    for i in play_options:
        opt = options[i]
        if me.hand is None:
            continue
        hand_card = me.hand[opt.index] if opt.index < len(me.hand) else None
        if hand_card is None:
            continue
        cd = get_card_data(hand_card.id)
        if cd and cd.cardType == CardType.POKEMON and cd.basic:
            if len(me.bench) < me.benchMax:
                return [i]
    
    # === PRIORITY 6: Use abilities ===
    for i in ability_options:
        return [i]
    
    # === PRIORITY 7: Retreat if active can't attack but benched pokemon can ===
    if retreat_options and my_active:
        if not pokemon_can_attack(my_active):
            for bp in me.bench:
                if pokemon_can_attack(bp):
                    return [retreat_options[0]]
    
    # === PRIORITY 8: Attack! ===
    if attack_options:
        best_attack = None
        best_score = -1
        for i in attack_options:
            opt = options[i]
            score = score_attack_option(opt, state)
            if score > best_score:
                best_score = score
                best_attack = i
        if best_attack is not None:
            return [best_attack]
    
    # === PRIORITY 9: End turn ===
    if end_options:
        return [end_options[0]]
    
    # Fallback: random
    return random.sample(list(range(len(options))), select.maxCount)


def handle_card_selection(obs: Observation) -> list[int]:
    """Handle card selection prompts (search, discard, switch, etc.)."""
    select = obs.select
    state = obs.current
    options = select.option
    context = select.context
    me = get_my_state(state)
    opp = get_opp_state(state)
    
    # --- SETUP: Choose active pokemon ---
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        # Pick Gouging Fire ex if available
        for i, opt in enumerate(options):
            if opt.type == OptionType.CARD and opt.cardId == GOUGING_FIRE_EX:
                return [i]
        # Otherwise pick highest HP
        best_i, best_hp = 0, 0
        for i, opt in enumerate(options):
            cd = get_card_data(opt.cardId) if opt.cardId else None
            if cd and cd.hp > best_hp:
                best_hp = cd.hp
                best_i = i
        return [best_i]
    
    # --- SETUP: Choose bench pokemon ---
    if context == SelectContext.SETUP_BENCH_POKEMON:
        # Put all available Gouging Fire on bench
        chosen = []
        for i, opt in enumerate(options):
            if opt.type == OptionType.CARD and opt.cardId == GOUGING_FIRE_EX:
                chosen.append(i)
        if chosen:
            return chosen[:select.maxCount]
        # Put any pokemon on bench
        chosen = [i for i, opt in enumerate(options) if opt.type == OptionType.CARD]
        if chosen:
            return chosen[:select.maxCount]
        return list(range(min(select.minCount, len(options))))
    
    # --- SWITCH: Pick best pokemon to switch to ---
    if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
        # Prefer a powered-up Gouging Fire
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            cd = get_card_data(opt.cardId) if opt.cardId else None
            if cd and is_gouging_fire(cd.cardId):
                score += 200
            # Check if this bench pokemon can attack
            if opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                bp = me.bench[opt.index]
                if pokemon_can_attack(bp):
                    score += 100
                score += count_energy(bp) * 20
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # --- TO_BENCH: Bench pokemon selection ---
    if context == SelectContext.TO_BENCH:
        # Prefer Gouging Fire
        chosen = []
        for i, opt in enumerate(options):
            if opt.cardId == GOUGING_FIRE_EX:
                chosen.append(i)
        if chosen:
            return chosen[:select.maxCount]
        # Otherwise any pokemon
        return list(range(min(select.maxCount, len(options))))
    
    # --- TO_HAND: Pick best card to add to hand ---
    if context == SelectContext.TO_HAND:
        # Prefer Gouging Fire, then energy, then supporters
        best = []
        for i, opt in enumerate(options):
            cd = get_card_data(opt.cardId) if opt.cardId else None
            if cd:
                if is_gouging_fire(cd.cardId):
                    best.insert(0, i)  # Top priority
                elif cd.cardId == FIRE_ENERGY:
                    best.append(i)
                elif cd.cardType == CardType.SUPPORTER:
                    best.append(i)
                elif cd.cardType == CardType.ITEM:
                    best.append(i)
                else:
                    best.append(i)
            else:
                best.append(i)
        if best:
            return best[:select.maxCount]
        return list(range(min(select.maxCount, len(options))))
    
    # --- DISCARD: Choose least valuable cards ---
    if context == SelectContext.DISCARD:
        # Discard order: duplicate supporters > items > energy > pokemon
        scored = []
        for i, opt in enumerate(options):
            score = 50  # Default
            cd = get_card_data(opt.cardId) if opt.cardId else None
            if cd:
                if cd.cardType == CardType.BASIC_ENERGY:
                    score = 20  # Low priority to discard energy
                elif cd.cardType == CardType.SUPPORTER:
                    score = 70
                elif cd.cardType == CardType.ITEM:
                    score = 60
                elif cd.cardType == CardType.POKEMON:
                    if is_gouging_fire(cd.cardId):
                        score = 5  # Don't discard our main attacker
                    else:
                        score = 80
            scored.append((score, i))
        scored.sort(reverse=True)
        return [s[1] for s in scored[:select.maxCount]]
    
    # --- DAMAGE/DAMAGE_COUNTER: Target opponent's weakest pokemon ---
    if context in (SelectContext.DAMAGE, SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY):
        # Target weakest opponent pokemon for KO
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            if opt.playerIndex != state.yourIndex:  # Opponent's pokemon
                score += 100
                # Prefer lower HP targets (closer to KO)
                if opt.area == AreaType.ACTIVE:
                    opp_active = get_active_pokemon(opp)
                    if opp_active:
                        score += (500 - opp_active.hp)
                elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(opp.bench):
                    score += (500 - opp.bench[opt.index].hp)
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]
    
    # --- HEAL: Heal our most damaged pokemon ---
    if context in (SelectContext.HEAL, SelectContext.REMOVE_DAMAGE_COUNTER):
        best_i, best_damage = 0, -1
        for i, opt in enumerate(options):
            if opt.playerIndex == state.yourIndex:
                if opt.area == AreaType.ACTIVE:
                    active = get_active_pokemon(me)
                    if active:
                        damage = active.maxHp - active.hp
                        if damage > best_damage:
                            best_damage = damage
                            best_i = i
                elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                    bp = me.bench[opt.index]
                    damage = bp.maxHp - bp.hp
                    if damage > best_damage:
                        best_damage = damage
                        best_i = i
        return [best_i]
    
    # --- ATTACH_TO: Attach to pokemon that needs energy most ---
    if context == SelectContext.ATTACH_TO:
        best_i, best_score = 0, -1
        for i, opt in enumerate(options):
            score = 0
            if opt.area == AreaType.ACTIVE:
                active = get_active_pokemon(me)
                if active and is_gouging_fire(active.id):
                    score = 300 - count_energy(active) * 50
                elif active:
                    score = 100 - count_energy(active) * 20
            elif opt.area == AreaType.BENCH and opt.index is not None and opt.index < len(me.bench):
                bp = me.bench[opt.index]
                if is_gouging_fire(bp.id):
                    score = 200 - count_energy(bp) * 50
                else:
                    score = 50
            if score > best_score:
                best_score = score
                best_i = i
        return [best_i]

    # --- EVOLVES_FROM/EVOLVES_TO: Evolution selection ---
    if context in (SelectContext.EVOLVES_FROM, SelectContext.EVOLVES_TO):
        return [0]  # Just pick first option

    # --- ATTACH_FROM: Pick best card to detach ---
    if context == SelectContext.ATTACH_FROM:
        return [0]
    
    # --- LOOK: Looking at cards ---
    if context == SelectContext.LOOK:
        # Pick the most valuable cards
        best = []
        for i, opt in enumerate(options):
            cd = get_card_data(opt.cardId) if opt.cardId else None
            score = 0
            if cd:
                if is_gouging_fire(cd.cardId):
                    score = 100
                elif cd.cardId == FIRE_ENERGY:
                    score = 80
                elif cd.cardType == CardType.SUPPORTER:
                    score = 70
                elif cd.cardType == CardType.ITEM:
                    score = 60
            best.append((score, i))
        best.sort(reverse=True)
        return [b[1] for b in best[:select.maxCount]]
    
    # --- Default: return a valid selection ---
    count = min(select.maxCount, len(options))
    count = max(count, select.minCount)
    if count <= 0:
        return []
    return list(range(count))


def handle_yes_no(obs: Observation) -> list[int]:
    """Handle Yes/No prompts."""
    select = obs.select
    context = select.context
    options = select.option
    
    # Go first if given the choice
    if context == SelectContext.IS_FIRST:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES:
                return [i]
    
    # Mulligan: redraw if no basic pokemon
    if context == SelectContext.MULLIGAN:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES:
                return [i]
    
    # Activate effects: generally yes
    if context == SelectContext.ACTIVATE:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES:
                return [i]
    
    # Coin flip: heads
    if context == SelectContext.COIN_HEAD:
        for i, opt in enumerate(options):
            if opt.type == OptionType.YES:
                return [i]
    
    # Default: yes
    for i, opt in enumerate(options):
        if opt.type == OptionType.YES:
            return [i]
    return [0]


def handle_energy_selection(obs: Observation) -> list[int]:
    """Handle energy selection (for discard costs, etc.)."""
    select = obs.select
    options = select.option
    # Just pick the first available energies up to maxCount
    count = min(select.maxCount, len(options))
    count = max(count, select.minCount)
    return list(range(count))


def handle_attack_selection(obs: Observation) -> list[int]:
    """Handle attack selection."""
    select = obs.select
    state = obs.current
    options = select.option
    
    best_i, best_score = 0, -1
    for i, opt in enumerate(options):
        score = score_attack_option(opt, state)
        if score > best_score:
            best_score = score
            best_i = i
    return [best_i]


def handle_count_selection(obs: Observation) -> list[int]:
    """Handle count selection (how many cards to draw, etc.)."""
    select = obs.select
    # Generally pick the maximum
    for i, opt in enumerate(select.option):
        if opt.type == OptionType.NUMBER and opt.number == select.maxCount:
            return [i]
    # If max not available, pick highest
    best_i, best_val = 0, -1
    for i, opt in enumerate(select.option):
        if opt.number is not None and opt.number > best_val:
            best_val = opt.number
            best_i = i
    return [best_i]


def handle_special_condition(obs: Observation) -> list[int]:
    """Handle special condition selection."""
    return [0]


def handle_skill_selection(obs: Observation) -> list[int]:
    """Handle skill ordering."""
    select = obs.select
    return list(range(min(select.maxCount, len(select.option))))


# ============================================================================
# MAIN AGENT ENTRY POINT
# ============================================================================
def agent(obs_dict: dict) -> list[int]:
    """Main agent function called by the Kaggle environment."""
    _ensure_db()
    obs: Observation = to_observation_class(obs_dict)
    
    # Initial deck selection
    if obs.select is None:
        return read_deck_csv()
    
    select = obs.select
    
    try:
        # Route to the appropriate handler based on selection type
        if select.type == SelectType.MAIN:
            return handle_main_selection(obs)
        elif select.type == SelectType.CARD:
            return handle_card_selection(obs)
        elif select.type == SelectType.YES_NO:
            return handle_yes_no(obs)
        elif select.type == SelectType.ENERGY:
            return handle_energy_selection(obs)
        elif select.type == SelectType.ATTACK:
            return handle_attack_selection(obs)
        elif select.type == SelectType.COUNT:
            return handle_count_selection(obs)
        elif select.type == SelectType.SPECIAL_CONDITION:
            return handle_special_condition(obs)
        elif select.type == SelectType.SKILL:
            return handle_skill_selection(obs)
        elif select.type == SelectType.ATTACHED_CARD:
            return handle_card_selection(obs)
        elif select.type == SelectType.CARD_OR_ATTACHED_CARD:
            return handle_card_selection(obs)
        elif select.type == SelectType.EVOLVE:
            return handle_card_selection(obs)
        else:
            # Fallback for unknown selection types
            count = min(select.maxCount, len(select.option))
            count = max(count, select.minCount)
            return random.sample(list(range(len(select.option))), count)
    except Exception:
        # Ultimate fallback: random valid selection
        count = min(select.maxCount, len(select.option))
        count = max(count, select.minCount)
        if count <= 0:
            return []
        return random.sample(list(range(len(select.option))), count)
