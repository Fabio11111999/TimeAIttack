import numpy as np
import random
from IPython.display import clear_output
from collections import deque
import progressbar
import gym
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, Embedding, Reshape
from tensorflow.keras.optimizers import Adam

enviroment = gym.make("Taxi-v3").env
enviroment.render()

print('Number of states: {}'.format(enviroment.observation_space.n))
print('Number of acrions: {}'.format(enviroment.action_space.n))

alpha = 0.1
gamma = 0.6
epsilon = 0.1
q_table = np.zeros([enviroment.observation_space.n, enviroment.action_space.n])

num_of_episodes = 10000

for episode in range(0, num_of_episodes):
    state = enviroment.reset()
    reward = 0
    terminated = False

    while not terminated:
        if random.uniform(0, 1) < epsilon:
            action = enviroment.action_space.sample()
        else:
            action = np.argmax(q_table[state])

        next_state, reward, terminated, info = enviroment.step(action)

        q_value = q_table[state, action]
        max_value = np.max(q_table[next_state])
        new_q_value = (1 - alpha) * q_value + alpha * (reward + gamma * max_value)

        q_table[state, action] = new_q_value

        state = next_state

    if (episode + 1) % 100 == 0:
        clear_output(wait=True)
        print('Episode: {}'.format(episode + 1))
        enviroment.render()

print('**************')
print('Training is done!\n')
print('**************')
