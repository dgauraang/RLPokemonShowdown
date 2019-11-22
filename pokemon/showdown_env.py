import gym
from gym import spaces
import numpy as np
import json
from .client import send_action
from .client import reset_server
from .client import reset_game
from .load_embeddings import load_embeddings

class ShowdownEnv(gym.Env):
    
    # As a parameter, we also want to pass in the opponent's policy
    def __init__(self, model=None):
        """{"player1":{"buffs":{"atk":0,"def":0,"spe":0,"spa":0,"spd":0,"evasion":0,"accuracy":0},"effects":[0,0,0,0],
        "pokemons":[{"name":"Mewtwo","hp":1,"active":true,"status":[0,0,0,0,0,0]},{"name":"Snorlax","hp":1,"active":false,"status":[0,0,0,0,0,0]}],"activemoves":[{"name":"splash","enabled":true},{"name":"leechseed","enabled":true},{"name":"haze","enabled":true}]},"player2":{"buffs":{"atk":0,"def":0,"spe":0,"spa":0,"spd":0,"evasion":0,"accuracy":0},"effects":[0,0,0,0],"pokemons":[{"name":"Mew","hp":1,"active":true,"status":[0,0,0,0,0,0]},{"name":"Snorlax","hp":1,"active":false,"status":[0,0,0,0,0,0]}],"activemoves":[{"name":"splash","enabled":true},{"name":"leechseed","enabled":true},
        {"name":"haze","enabled":true}]},"winner":"empty"}"""
        # Input dimensions and their high and low values 
        obs_low, obs_high = self.high_low()
        self.observation_space = spaces.Box(obs_low, obs_high)
        # State dimensions
        self.action_space = spaces.Discrete(9)
        # Load the move embeddings and the pokemon embeddings
        self.move_dict, self.poke_dict = load_embeddings()
        self.model = model

    # Convert the observation we receive from the environment into a vector interpretable by our RL algo
    def vectorize_obs(self, obs):
        players = ['player1', 'player2']
        players_obs = np.array([]) 
        for player in players:
            # Add player buffs to np array 
            buff_obs = np.zeros((6))
            buff_dict = obs[player]['buffs']
            stat_num = 0
            for stat in list(buff_dict.keys()):
                # Sp. Attack and Sp. Defense are the same, so don't count the value twice
                if stat != 'spd':
                    buff_obs[stat_num] = buff_dict[stat]
                    stat_num += 1
            # Set effect obs(ie. leech seed, confusion, reflect, light screen)
            effect_obs = np.zeros((4))
            effects = obs[player]['effects']
            effect_num = 0
            for effect in effects:
                effect_obs[effect_num] = effect
                effect_num += 1

            pokemons = obs[player]['pokemons'] 
            pokes_obs = np.array([]) 
            # Add pokemon obs
            for pokemon in pokemons:
                # Get the pokemon obs 
                poke_obs = self.poke_dict[pokemon['name']]
                # Set if the pokemon is active
                active_obs = np.array([1]) if pokemon['active'] else np.array([0])
                poke_obs = np.concatenate((poke_obs, active_obs))
                # Get the status of a pokemon
                status_obs = np.array(pokemon['status'])
                # Get the hp of the pokemon
                hp_obs = np.array(pokemon['hp'])
                # Get each pokemon move obs (if its active)
                moves_obs = np.array([])
                if pokemon['active']:
                    num_moves = 0
                    active_moves = obs[player]['activemoves']
                    for move in active_moves:
                        # Get the move embedding based on the name
                        move_embedding = self.move_dict[move['name']]
                        # Set whether the move is enabled or disabled
                        enabled_obs = np.array([1]) if move['enabled'] else np.array([0])
                        move_obs = np.concatenate((move_embedding, enabled_obs), axis=0)
                        # Add the observation to the array of moves
                        moves_obs = np.concatenate((moves_obs, move_obs), axis=0)
                        num_moves += 1
                    # Add zeroed-out vectors for move embeddings to keep size of input to neural net consistent while accounting for pokes with < 4 moves
                    while num_moves < 4:
                        # This is 1 x 11 because a move embedding is length 10 and the enabled/disabled boolean is length 1
                        moves_obs = np.concatenate((moves_obs, np.zeros(11)), axis=0)
                        num_moves += 1
                # Stores each move observation
                moves_obs = np.array(moves_obs)
                # Stores the entire pokemon observation
                full_poke_obs = np.concatenate((poke_obs, status_obs, hp_obs.flatten(), moves_obs.flatten()))
                pokes_obs = np.concatenate((pokes_obs, full_poke_obs), axis=0)
            # Stores each pokemon observation
            pokes_obs = np.array(pokes_obs)
            # Stores the full player observation
            player_obs = np.concatenate((buff_obs, effect_obs, pokes_obs))   
            players_obs = np.concatenate((players_obs, player_obs), axis=0)
        # Combine each observation into a vector
        players_obs = np.array(players_obs).astype(np.double)
        return players_obs


    def step(self, action):
        info = {} 
        obs = 0
        reward = 0
        done = False
        # Send the action to the simulator
        res = send_action(action)
        # The result includes the variables observation, and done
        print('Raw result:', res)
        res_dict = json.loads(res)
        obs = np.array(res_dict['obs'])
        self.state = np.array(obs, copy=True)
        reward = self._reward()
        done = True if reward != 0 else False
        return obs, reward, done, info     


    def _reward(self):
        if self.state[4] <= 0:
            return -1
        elif self.state[5] <= 0:
            return 1
        else:
            return 0


    # Set the initial state and begin a new game
    def reset(self):
        self.state = json.loads(reset_game())
        self.state = self.vectorize_obs(self.state)
        return self.state

    # Define the upper (high) and lower (low) bounds for the input of the for the RL algo
    # input vector:
    # Low: [p1 active pokembedding: [-2] * 10 + active[0], p1 hp:[0],p1 moves: [-2] * 10 + disabled after each, p1 buffs [-6] * 6 
    # p1 status [0] * 6, p1 effects [0], p2 active pokembedding: [-2] * 10 + active[0]
    # , p2 active hp: [0], p2 status[0] * 6, p2 confusion [0, 0, 0 ,0], 
    def high_low(self):
        pokembedding_low = np.array([-2] * 10) 
        active_low = np.array([0])
        active_pokembedding_low = np.concatenate((pokembedding_low, active_low), axis=0)
        hp_low = np.array([0])

        movembedding_low = np.array([-2] * 10)
        enabled_move_low = np.array([0])
        move_low = np.concatenate((movembedding_low, enabled_move_low), axis=0)


        buffs_low = np.array([-6] * 6)
        status_low = np.array([0] * 6)
        effects_low = np.array([0, 0, 0, 0])

        p1_low = np.concatenate((buffs_low, effects_low, active_pokembedding_low, status_low, hp_low, move_low, move_low, move_low, move_low), axis=0)
        p2_low = np.concatenate((buffs_low, effects_low, active_pokembedding_low, status_low, hp_low, move_low, move_low, move_low, move_low), axis=0)
        
        obs_low = np.concatenate((p1_low, p2_low), axis=0)
        
        pokembedding_high = np.array([2] * 10) 
        active_high = np.array([1])
        active_pokembedding_high = np.concatenate((pokembedding_high, active_high), axis=0)

        hp_high = np.array([1])

        movembedding_high = np.array([2] * 10)
        enabled_move_high = np.array([1])
        move_high = np.concatenate((movembedding_high, enabled_move_high), axis=0)


        buffs_high = np.array([6] * 6)
        status_high = np.array([1] * 6)
        effects_high = np.array([1, 1, 1, 1])

        p1_high = np.concatenate((buffs_high, effects_high, active_pokembedding_high, status_high, hp_high, move_high, move_high, move_high, move_high), axis=0)
        p2_high = np.concatenate((buffs_high, effects_high, active_pokembedding_high, status_high, hp_high, move_high, move_high, move_high, move_high), axis=0)
        
        obs_high = np.concatenate((p1_high, p2_high), axis=0)
        return obs_low, obs_high
        