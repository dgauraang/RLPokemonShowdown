import constants
from showdown.helpers import normalize_name
from showdown.damage_calculator import is_super_effective


class Scoring:
    POKEMON_ALIVE_STATIC = 75
    POKEMON_HP = 100  # 100 points for 100% hp, 0 points for 0% hp. This is in addition to being alive
    POKEMON_HIDDEN = 10
    POKEMON_BOOSTS = {
        constants.ATTACK: 15,
        constants.DEFENSE: 15,
        constants.SPECIAL_ATTACK: 15,
        constants.SPECIAL_DEFENSE: 15,
        constants.SPEED: 25,
        constants.ACCURACY: 30,
        constants.EVASION: 30
    }

    POKEMON_BOOST_DIMINISHING_RETURNS = {
        -6: -3.3,
        -5: -3.15,
        -4: -3,
        -3: -2.5,
        -2: -2,
        -1: -1,
        0: 0,
        1: 1,
        2: 2,
        3: 2.5,
        4: 3,
        5: 3.15,
        6: 3.30,
    }

    POKEMON_STATUSES = {
        constants.BURN: -20,
        constants.FROZEN: -50,
        constants.SLEEP: -25,
        constants.PARALYZED: -25,
        constants.TOXIC: -30,
        constants.POISON: -10,
        None: 0
    }
    POKEMON_VOLATILE_STATUSES = {
        constants.LEECH_SEED: -30,
        constants.SUBSTITUTE: 40,
        constants.CONFUSION: -20
    }

    STATIC_SCORED_SIDE_CONDITIONS = {
        constants.REFLECT: 20,
        constants.STICKY_WEB: -25,
        constants.LIGHT_SCREEN: 20,
        constants.AURORA_VEIL: 40,
        constants.SAFEGUARD: 5,
        constants.TAILWIND: 7,
    }

    POKEMON_COUNT_SCORED_SIDE_CONDITIONS = {
        constants.STEALTH_ROCK: -15,
        constants.SPIKES: -7,
        constants.TOXIC_SPIKES: -7,
    }

    WEAK_TO_OPPONENT_TYPE = 5
    FASTER_POKEMON_IN_MATCHUP = 10
    SUPER_EFFECTIVE_DAMAGING_MOVE = 5
    FASTER_POKEMON_WITH_SUPER_EFFECTIVE_DAMAGING_MOVE = 3


def evaluate_pokemon(pkmn):
    score = 0
    if pkmn.hp <= 0:
        return score

    score += Scoring.POKEMON_ALIVE_STATIC
    score += Scoring.POKEMON_HP * (float(pkmn.hp) / pkmn.maxhp)

    # boosts have diminishing returns
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.attack_boost] * Scoring.POKEMON_BOOSTS[constants.ATTACK]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.defense_boost] * Scoring.POKEMON_BOOSTS[constants.DEFENSE]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.special_attack_boost] * Scoring.POKEMON_BOOSTS[constants.SPECIAL_ATTACK]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.special_defense_boost] * Scoring.POKEMON_BOOSTS[constants.SPECIAL_DEFENSE]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.speed_boost] * Scoring.POKEMON_BOOSTS[constants.SPEED]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.accuracy_boost] * Scoring.POKEMON_BOOSTS[constants.ACCURACY]
    score += Scoring.POKEMON_BOOST_DIMINISHING_RETURNS[pkmn.evasion_boost] * Scoring.POKEMON_BOOSTS[constants.EVASION]

    score += Scoring.POKEMON_STATUSES[pkmn.status]

    for vol_stat in pkmn.volatile_status:
        try:
            score += Scoring.POKEMON_VOLATILE_STATUSES[normalize_name(vol_stat)]
        except KeyError:
            pass

    score *= pkmn.scoring_multiplier

    return round(score)


def evaluate_matchup(user_pkmn, opponent_pkmn):
    score = 0

    if user_pkmn.hp <= 0 or opponent_pkmn.hp <= 0:
        return score

    if user_pkmn.speed > opponent_pkmn.speed:
        score += Scoring.FASTER_POKEMON_IN_MATCHUP
    elif user_pkmn.speed < opponent_pkmn.speed:
        score -= Scoring.FASTER_POKEMON_IN_MATCHUP

    # positive bonus for the bot's type being super effective against the opponent
    for user_type in user_pkmn.types:
        if is_super_effective(user_type, opponent_pkmn.types):
            score += Scoring.WEAK_TO_OPPONENT_TYPE

    # negative bonus for the opponent's type being super effective against the bot's
    for opponent_type in opponent_pkmn.types:
        if is_super_effective(opponent_type, user_pkmn.types):
            score -= Scoring.WEAK_TO_OPPONENT_TYPE

    return score


def evaluate(state):
    score = 0

    number_of_opponent_reserve_revealed = len(state.opponent.reserve) + 1
    bot_alive_reserve_count = len([p.hp for p in state.self.reserve.values() if p.hp > 0])
    opponent_alive_reserves_count = len([p for p in state.opponent.reserve.values() if p.hp > 0]) + (6-number_of_opponent_reserve_revealed)

    # evaluate the bot's pokemon
    score += evaluate_pokemon(state.self.active)
    for pkmn in state.self.reserve.values():
        this_pkmn_score = evaluate_pokemon(pkmn)
        score += this_pkmn_score

    # evaluate the opponent's visible pokemon
    score -= evaluate_pokemon(state.opponent.active)
    for pkmn in state.opponent.reserve.values():
        this_pkmn_score = evaluate_pokemon(pkmn)
        score -= this_pkmn_score

    # evaluate the side-conditions for the bot
    for condition, count in state.self.side_conditions.items():
        if condition in Scoring.STATIC_SCORED_SIDE_CONDITIONS:
            score += count * Scoring.STATIC_SCORED_SIDE_CONDITIONS[condition]
        elif condition in Scoring.POKEMON_COUNT_SCORED_SIDE_CONDITIONS:
            score += count * Scoring.POKEMON_COUNT_SCORED_SIDE_CONDITIONS[condition] * bot_alive_reserve_count

    # evaluate the side-conditions for the opponent
    for condition, count in state.opponent.side_conditions.items():
        if condition in Scoring.STATIC_SCORED_SIDE_CONDITIONS:
            score -= count * Scoring.STATIC_SCORED_SIDE_CONDITIONS[condition]
        elif condition in Scoring.POKEMON_COUNT_SCORED_SIDE_CONDITIONS:
            score -= count * Scoring.POKEMON_COUNT_SCORED_SIDE_CONDITIONS[condition] * opponent_alive_reserves_count

    score += evaluate_matchup(state.self.active, state.opponent.active)

    return int(score)
