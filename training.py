from TD_actor_critic import TDActorCritic
from tdacbot import TDACBot
#hyperparamters
num_players = 4
num_territories = 10
num_phases = 3
train_time_steps = 10000
update_time_step = 1000
observation_size = num_players * num_territories + num_phases + num_players
place_action_size = num_territories
attack_fortify_action_size = num_territories*num_territories + 1
#initalizing player agents
player_agents = []
path = "agents/"
for index in range(num_players):
    player = TDACBot(path+f"player_{index}")
    player_agents.append(player)
#initialization training
for agent in player_agents:
    agent.initialize_training()
#start train loop