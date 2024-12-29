from TD_actor_critic import TDActorCritic
from player import Player
from Models.config import *
import numpy as np
import math
class TDACBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue,index,path=None):
        super().__init__(mycolor, terrList, myname, msgqueue,index)
        if path is not None:
            self.place_troops_agent = TDActorCritic.load_model(path+"place_troops")
            self.attack_fortify_agent = TDActorCritic.load_model(path+"attack_fortify")
            self.attack_fortify_agent.critic = self.place_troops_agent.critic
    def initalize_agents(self,observation_size,place_action_size,attack_fortify_action_size,
                         place_troop_agent_exploration_rate,place_troop_agent_discount,
                         place_troop_agent_hidden_sizes,attack_fortify_agent_exploration_rate,attack_fortify_agent_discount,
                         attack_fortify_agent_hidden_sizes,shared_critic_hidden_sizes,num_phases,num_players):
        place_troop_agent = TDActorCritic(place_troop_agent_exploration_rate,place_troop_agent_discount)
        place_troop_agent.initalize_actor(observation_size,place_action_size,place_troop_agent_hidden_sizes)
        place_troop_agent.initialize_critic(observation_size,shared_critic_hidden_sizes)
        attack_fortify_agent = TDActorCritic(attack_fortify_agent_exploration_rate,attack_fortify_agent_discount)
        attack_fortify_agent.initalize_actor(observation_size,attack_fortify_action_size,attack_fortify_agent_hidden_sizes)
        attack_fortify_agent.set_critic(place_troop_agent.critic)
        self.place_troops_agent = place_troop_agent
        self.attack_fortify_agent = attack_fortify_agent
        self.num_phases = num_phases
        self.num_players = num_players
        self.initial_observation = None
        self.end_observation = None
        self.action_index = None
        self.msgqueue.addMessage(str(self.place_troops_agent))
        self.msgqueue.addMessage(str(self.attack_fortify_agent))
    def save_player_agent(self,path):
        TDActorCritic.save_model(self.place_troops_agent,path+"place_troops")
        TDActorCritic.save_model(self.attack_fortify_agent,path+"attack_fortify")
    def initialize_training(self):
        self.place_troops_agent.initalize_training()
        self.attack_fortify_agent.initalize_training()
    def set_debug_mode(self,mode):
        self.place_troops_agent.set_debug_mode(mode)
        self.attack_fortify_agent.set_debug_mode(mode)
    def update_agent(self,epochs,learning_rate,batch_size):
        self.place_troops_agent.update_actor_and_critic(epochs,learning_rate,batch_size)
        self.attack_fortify_agent.update_actor_and_critic(epochs,learning_rate,batch_size)
    def set_observation(self,board,phase,player):
        #returns reshaped observation space
        board_flat = np.array(board).reshape(-1)
        phase_one_hot = np.eye(self.num_phases)[phase]
        player_one_hot = np.eye(self.num_players)[player]
        observation = np.concatenate([board_flat,phase_one_hot,player_one_hot]).reshape(1,-1)
        return observation
    def sample_place_troop_action(self):
        self.place_troops_agent.get_observation(self.initial_observation)
        action = self.place_troops_agent.set_action()
        action_index = self.place_troops_agent.sample_action_from_distribution(action)
        self.action_index = action_index
        return action_index
    def sample_attack_fortify_action(self):
        #set the current state observation
        self.attack_fortify_agent.get_observation(self.initial_observation)
        #sample an attack from it
        action = self.attack_fortify_agent.set_action()
        action_index = self.attack_fortify_agent.sample_action_from_distribution(action)
        #store the action for later use
        self.action_index = action_index
        #return action_index as a tuple of (row,column)
        #if the bot chooses to do nothing, it will return (-1,-1)
        if action_index == len(action) - 1:
            return (-1,-1)
        num_of_territories = math.isqrt((len(action) - 1))
        #transform the action index back to a tuple (row, column) of the original NxN attack matrix
        terrIn_index = action_index // num_of_territories
        terrOut_index = action_index % num_of_territories
        print(f"Length of Action: {len(action)}, Action Index: {action_index}, Number of Territories: {num_of_territories}, TerrIn Index: {terrIn_index}, TerrOut Index: {terrOut_index}")
        return terrIn_index,terrOut_index 
    
    def add_experience(self,state,next_state,action_index,reward,phase):
        if phase == 0:
            self.place_troops_agent.add_experience(state,next_state,action_index,reward)
        else:
            self.attack_fortify_agent.add_experience(state,next_state,action_index,reward)
        
    ####OVERRIDE FUNCTIONS####
    def attack(self):
        terrIn,terrOut = self.sample_attack_fortify_action()
        return (self.terrList[terrIn],self.terrList[terrOut])
    def fortify(self, board_obj):
        terrIn,terrOut = self.sample_attack_fortify_action()
        terrIn = self.terrList[terrIn]
        terrOut = self.terrList[terrOut]
        self.msgqueue.addMessage(f'Fortify {terrIn} from {terrOut}')
        move = board_obj.fortificationIsValid(terrIn, terrOut, self.color)
        if move:
            troops = board_obj.getTerritory(terrOut).troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self.color)
                board_obj.removeTroops(terrOut, troops)
        return move
    def InitialObservation(self,territory_matrix,phase,player):
        phase -= 1
        self.initial_observation = self.set_observation(territory_matrix,phase,player)
    def UpdateObservation(self,territory_matrix,phase,player,move_legality,turn_count):
        phase -= 1
        self.end_observation = self.set_observation(territory_matrix,phase,player)
        if phase == 0:
            reward = np.sum(self.initial_observation - self.end_observation)
        else:
            reward = 0 if move_legality else -1
        self.add_experience(self.initial_observation,self.end_observation,self.action_index,reward,phase)
        if turn_count % 100:
            self.update_agent(10,0.0001,8)
    #return the index to place troops in the territory array.
    def pickATerritoryPlaceTroops(self):
        return self.terrList[self.sample_place_troop_action()]

