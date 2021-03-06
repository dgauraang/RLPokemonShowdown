import constants


def sandstream(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if state.weather not in constants.IRREVERSIBLE_WEATHER:
        return (
            constants.MUTATOR_WEATHER_START,
            constants.SAND,
            state.weather
        )
    return None


def snowwarning(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if state.weather not in constants.IRREVERSIBLE_WEATHER:
        return (
            constants.MUTATOR_WEATHER_START,
            constants.HAIL,
            state.weather
        )
    return None


def drought(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if state.weather not in constants.IRREVERSIBLE_WEATHER:
        return (
            constants.MUTATOR_WEATHER_START,
            constants.SUN,
            state.weather
        )
    return None


def drizzle(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if state.weather not in constants.IRREVERSIBLE_WEATHER:
        return (
            constants.MUTATOR_WEATHER_START,
            constants.RAIN,
            state.weather
        )
    return None


def desolateland(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_WEATHER_START,
        constants.DESOLATE_LAND,
        state.weather
    )


def primordialsea(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_WEATHER_START,
        constants.HEAVY_RAIN,
        state.weather
    )


def electricsurge(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_FIELD_START,
        constants.ELECTRIC_TERRAIN,
        state.field
    )


def psychicsurge(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_FIELD_START,
        constants.PSYCHIC_TERRAIN,
        state.field
    )


def grassysurge(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_FIELD_START,
        constants.GRASSY_TERRAIN,
        state.field
    )


def mistysurge(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    return (
        constants.MUTATOR_FIELD_START,
        constants.MISTY_TERRAIN,
        state.field
    )


def intimidate(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if defending_pokemon.ability not in ['fullmetalbody', 'clearbody', 'hypercutter', 'whitesmoke', 'defiant'] and defending_pokemon.attack_boost > -6:
        return (
            constants.MUTATOR_UNBOOST,
            defending_side,
            constants.ATTACK,
            1
        )
    # I shouldn't be doing this here but w/e sue me
    elif defending_pokemon.ability == 'defiant' and defending_pokemon.attack_boost < 6:
        return (
            constants.MUTATOR_BOOST,
            defending_side,
            constants.ATTACK,
            1
        )
    return None


ability_lookup = {
    "mistysurge": mistysurge,
    "grassysurge": grassysurge,
    "psychicsurge": psychicsurge,
    "electricsurge": electricsurge,
    "sandstream": sandstream,
    "snowwarning": snowwarning,
    "drought": drought,
    "drizzle": drizzle,
    "desolateland": desolateland,
    "primordialsea": primordialsea,
    'intimidate': intimidate
}


def ability_on_switch_in(ability_name, state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    ability_func = ability_lookup.get(ability_name)
    if ability_func is not None:
        return ability_func(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon)
    else:
        return None
