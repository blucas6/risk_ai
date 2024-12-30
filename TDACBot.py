from TD_actor_critic import TDActorCritic
from player import Player
from Models.config import *
import numpy as np
import math
import threading
import matplotlib.pyplot as plt
import queue
from matplotlib.animation import FuncAnimation
class TDACBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue,index,num_players,num_territories,num_phases,max_troops,showGraphs,updateGraphs=5,load_name=None,save_name=None,mode='Train'):
        super().__init__(mycolor, terrList, myname, msgqueue,index)
        self.graphThreadDataQueue = queue.Queue()
        self.graphthreadinstance = threading.Thread(target=self.updateGraphThread, daemon=True)
        self.currentGraphData = [[],[],[],[],[],[]]
        self.updateGraphsEvery = updateGraphs
        if showGraphs:
            self.graphthreadinstance.start()

        self.num_phases = num_phases
        self.num_players = num_players
        self.max_troops = max_troops
        self.initial_observation = None
        self.end_observation = None
        self.action_index = None
        self.time_step = 0
        self.mode = mode
        self.save_name = save_name

        if load_name is not None:
            self.place_troops_agent = TDActorCritic.load_model(load_name+"_pta")
            self.attack_fortify_agent = TDActorCritic.load_model(load_name+"_afa")
            self.attack_fortify_agent.critic = self.place_troops_agent.critic
            self.place_troops_agent.initialize_training()
            self.attack_fortify_agent.initialize_training()
        else:
            observation_size = num_players * num_territories + num_phases + num_players
            place_action_size = num_territories
            attack_fortify_action_size = num_territories*num_territories + 1
            self.initalize_agents(observation_size,place_action_size,
                                      attack_fortify_action_size,0.2,0.9,
                                      [128],0.2,0.9,[128],[128],num_phases,
                                      num_players,max_troops,msgqueue)
        self.set_debug_mode(False)
        if self.mode == 'Evaluation':
            self.place_troops_agent.exploration_rate = 0
            self.attack_fortify_agent.exploration_rate = 0
        self.msgqueue.addMessage(str(self.place_troops_agent))
        self.msgqueue.addMessage(str(self.attack_fortify_agent))
    
    def initalize_agents(self,observation_size,place_action_size,attack_fortify_action_size,
                         place_troop_agent_exploration_rate,place_troop_agent_discount,
                         place_troop_agent_hidden_sizes,attack_fortify_agent_exploration_rate,attack_fortify_agent_discount,
                         attack_fortify_agent_hidden_sizes,shared_critic_hidden_sizes,num_phases,num_players,max_troops,msgqueue):
        
        place_troop_agent = TDActorCritic(place_troop_agent_exploration_rate,place_troop_agent_discount,msgqueue)
        place_troop_agent.initalize_actor(observation_size,place_action_size,place_troop_agent_hidden_sizes)
        place_troop_agent.initialize_critic(observation_size,shared_critic_hidden_sizes)
        attack_fortify_agent = TDActorCritic(attack_fortify_agent_exploration_rate,attack_fortify_agent_discount,msgqueue)
        attack_fortify_agent.initalize_actor(observation_size,attack_fortify_action_size,attack_fortify_agent_hidden_sizes)
        attack_fortify_agent.set_critic(place_troop_agent.critic)
        self.place_troops_agent = place_troop_agent
        self.attack_fortify_agent = attack_fortify_agent
        self.num_phases = num_phases
        self.num_players = num_players
        self.max_troops = max_troops
        self.initial_observation = None
        self.end_observation = None
        self.action_index = None
        self.time_step = 0
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
    
    def set_observation(self,board,phase,player,max_troops):
        #returns reshaped observation space
        board_flat = np.array(board).reshape(-1) / max_troops
        phase_one_hot = np.eye(self.num_phases)[phase]
        player_one_hot = np.eye(self.num_players)[player]
        observation = np.concatenate([board_flat,phase_one_hot,player_one_hot]).reshape(1,-1)
        #print(f"Observation: {board_flat.shape}, {phase_one_hot.shape}, {player_one_hot.shape}, {observation.shape}")
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
        #print(f"Length of Action: {len(action)}, Action Index: {action_index}, Number of Territories: {num_of_territories}, TerrIn Index: {terrIn_index}, TerrOut Index: {terrOut_index}")
        return terrIn_index,terrOut_index 
    
    def add_experience(self,state,next_state,action_index,reward,phase):
        if phase == 0:
            self.place_troops_agent.add_experience(state,next_state,action_index,reward)
        else:
            self.attack_fortify_agent.add_experience(state,next_state,action_index,reward)
    
    def return_metrics(self):
        pta_actor_loss = self.place_troops_agent.actor_loss
        pta_critic_loss = self.place_troops_agent.critic_loss
        pta_reward = self.place_troops_agent.reward
        afa_actor_loss = self.attack_fortify_agent.actor_loss
        afa_critic_loss = self.attack_fortify_agent.critic_loss
        afa_reward = self.attack_fortify_agent.reward
        # return pta_actor_loss,pta_critic_loss,pta_reward,afa_actor_loss,afa_critic_loss,afa_reward
        self.graphThreadDataQueue.put([pta_actor_loss,pta_critic_loss,pta_reward,afa_actor_loss,afa_critic_loss,afa_reward])
    def graph_metrics(self):
        pta_al,pta_cl,pta_r,afa_al,afa_cl,afa_r = self.return_metrics()
        data = [pta_al,pta_cl,pta_r,afa_al,afa_cl,afa_r]
        titles = ['Place Troops Actor Loss','Place Troops Critic Loss',
                   'Place Troops Reward', 'Attack Fortify Actor Loss',
                   'Attack Fortify Critic Loss', 'Attack Fortify Reward']
        fig,axes = plt.subplots(2,3,figsize=(8,4))
        axes = axes.flatten()
        for i, ax in enumerate(axes):
            ax.plot(data[i],color='blue')
            ax.set_title(titles[i])
        plt.tight_layout()
        plt.show()

    def updateGraphThread(self):
        fig,axes = plt.subplots(2,3,figsize=(8,3))
        # plt.subplots_adjust(left=1, right=1, top=1, bottom=1, wspace=1, hspace=1)
        ani = FuncAnimation(fig, self.checkDataQueueThread, fargs=(axes,), interval=1000)
        plt.tight_layout()
        plt.show()

    def checkDataQueueThread(self, frame, axes):
        while not self.graphThreadDataQueue.empty():
            self.currentGraphData = self.graphThreadDataQueue.get()
        titles = ['Place Troops Actor Loss','Place Troops Critic Loss',
                   'Place Troops Reward', 'Attack Fortify Actor Loss',
                   'Attack Fortify Critic Loss', 'Attack Fortify Reward']
        axes = axes.flatten()
        for i, ax in enumerate(axes):
            ax.clear()
            ax.plot(self.currentGraphData[i],color='blue')
            ax.set_title(titles[i])
        
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
            theTerr, tindex = board_obj.getTerritory(terrOut)
            troops = theTerr.troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self)
                board_obj.removeTroops(terrOut, troops, self)
        return move
    
    def InitialObservation(self,territory_matrix,phase,player):
        phase -= 1
        self.initial_observation = self.set_observation(territory_matrix,phase,player,self.max_troops)
        #state value debug
        value = self.place_troops_agent.critic.predict(self.initial_observation).reshape(-1)
        self.msgqueue.addMessage(msg=f"Value of State: {value}")
    
    def UpdateObservation(self,territory_matrix,phase,player,move_legality):
        self.time_step += 1
        phase -= 1
        self.end_observation = self.set_observation(territory_matrix,phase,player,self.max_troops)
        if phase == 0:
            reward = np.sum(self.end_observation - self.initial_observation) * self.max_troops
            if reward == 0:
                reward = -10
        else:
            reward = 10 if move_legality else -10
        self.msgqueue.addMessage(f"Phase: {phase}, Received Reward: {reward}")
        self.add_experience(self.initial_observation,self.end_observation,self.action_index,reward,phase)
        if self.mode == "Training":
            if (self.time_step // 3 + 1) % 1000 == 0:
                self.update_agent(10,0.0001,32)
            if (self.time_step // 3  + 1) % 10000 == 0:
                turns = self.time_step
                TDActorCritic.save_model(self.place_troops_agent,f"{self.save_name}_{turns}_pta")
                TDActorCritic.save_model(self.place_troops_agent,f"{self.save_name}_{turns}_afa")
            if (self.time_step // 3 + 1) % self.updateGraphsEvery == 0:
                self.return_metrics()
        elif self.mode == "Evaluation":
             if (self.time_step // 3 + 1) % 1000 == 0:
                self.return_metrics()
    
    #return the index to place troops in the territory array.
    def pickATerritoryPlaceTroops(self):
        return self.terrList[self.sample_place_troop_action()]

