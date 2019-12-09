import os

import gym
import numpy as np
import matplotlib.pyplot as plt
import time

from stable_baselines.bench import Monitor
from stable_baselines.results_plotter import load_results, ts2xy
from stable_baselines import results_plotter
from stable_baselines.common.policies import MlpPolicy, MlpLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2
from stable_baselines import ACER

import pokemon


best_mean_reward, n_steps, last_saved_game = -np.inf, 0, 0

def callback(_locals, _globals):

    """
    Callback called at each step (for DQN an others) or after n steps (see ACER or PPO2)
    :param _locals: (dict)
    :param _globals: (dict)
    """
    global best_mean_reward, base_env, last_saved_game

    cur_game = base_env.game_counter

    if cur_game - last_saved_game > 100:

        last_saved_game = cur_game

        # Evaluate policy training performance 
        x, y = ts2xy(load_results(log_dir), 'timesteps') 
        if len(x) > 0:
            mean_reward = np.mean(y[-100:])
            print('\n\nMean reward: {}\n\n'.format(mean_reward))
            print(x[-1], 'timesteps')
            print("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(best_mean_reward, mean_reward))
            print('Writing replay log...')
            base_env.write_replay_log()

            # Save model
            if (n_steps % 10000 == 0):
                print('Saving model ' + str(cur_game))
                #time_str = time.strftime('%Y%m%d-%H%M%S')
                # Model name is how many games the agent has trained on
                _locals['self'].save(log_dir + '/game' + str(cur_game) + '.pkl')

            # New best model, you could save the agent here
            if mean_reward > best_mean_reward:
                best_mean_reward = mean_reward
                # Example for saving best model
                print("Saving new best model")
                _locals['self'].save(log_dir + '/best_model.pkl')


    return True

epochs = 1
log_time_str = None

for i in range(epochs):
    # Create log dir with timestamp
    log_dir = "./log_showdown/1v1_self_play/"
    time_str = time.strftime('%Y%m%d-%H%M%S')
    log_dir += time_str
    os.makedirs(log_dir, exist_ok=True)

    # Create and wrap the environment
    base_env = gym.make('Pokemon-v0', log_dir=log_dir, HER=False, num_pokemon=1, update_model=True, new_opp_model_every_x_episodes=10000, opponent_random_policy=False)
    env = Monitor(base_env, log_dir, allow_early_resets=True)
    env = DummyVecEnv([lambda: env])
    model = PPO2(MlpPolicy, env, verbose=0)
    base_env.set_model(model)
    training_steps = 1000000
    model.learn(training_steps, callback=callback)
    #results_plotter.plot_results([log_dir], 15000, results_plotter.X_TIMESTEPS, "Showdown")
    #plt.show()
