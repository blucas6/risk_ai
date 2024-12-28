from TD_actor_critic import TDActorCritic
from player import Player
import random
class TDACBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue,path=None):
        super().__init__(mycolor, terrList, myname, msgqueue)
        if path is not None:
            self.place_troops_agent = TDActorCritic.load_model(path+"place_troops")
            self.attack_fortify_agent = TDActorCritic.load_model(path+"attack_fortify")
            self.attack_fortify_agent.critic = self.place_troops_agent.critic
    def initalize_agents(self,observation_size,place_action_size,attack_fortify_action_size,
                         place_troop_agent_exploration_rate,place_troop_agent_discount,
                         place_troop_agent_hidden_sizes,attack_fortify_agent_exploration_rate,attack_fortify_agent_discount,
                         attack_fortify_agent_hidden_sizes,shared_critic_hidden_sizes):
        place_troop_agent = TDActorCritic(place_troop_agent_exploration_rate,place_troop_agent_discount)
        place_troop_agent.initalize_actor(observation_size,place_action_size,place_troop_agent_hidden_sizes)
        place_troop_agent.initialize_critic(observation_size,shared_critic_hidden_sizes)
        attack_fortify_agent = TDActorCritic(attack_fortify_agent_exploration_rate,attack_fortify_agent_discount)
        attack_fortify_agent.initalize_actor(observation_size,attack_fortify_action_size,attack_fortify_agent_hidden_sizes)
        attack_fortify_agent.set_critic(place_troop_agent.critic)
        self.place_troops_agent = place_troop_agent
        self.attack_fortify_agent = attack_fortify_agent
        print(self.place_troops_agent)
        print(self.attack_fortify_agent)
    def save_player_agent(self,path):
        TDActorCritic.save_model(self.place_troops_agent,path+"place_troops")
        TDActorCritic.save_model(self.attack_fortify_agent,path+"attack_fortify")
    def initialize_training(self):
        self.place_troops_agent.initalize_training()
        self.attack_fortify_agent.initalize_training()
    def update_agent(self,epochs,learning_rate,batch_size):
        self.place_troops_agent.update_actor_and_critic(epochs,learning_rate,batch_size)
        self.attack_fortify_agent.update_actor_and_critic(epochs,learning_rate,batch_size)
    def set_observation(self,board,phase,player):
        #returns reshaped observation space
        pass
    def sample_attack_fortify_action(self,board,phase,player):
        #put the observation in a format that can be used by the network
        observation = self.set_observation(board,phase,player)
        #set the current state observation
        self.attack_fortify_agent.get_observation(observation)
        #sample an attack from it
        action = self.attack_fortify_agent.set_action()
        action_index = self.attack_fortify_agent.sample_action_from_distribution(action)
        #return action_index as a tuple of (row,column)
        #if the bot chooses to do nothing, it will return (-1,-1)
        if action_index == len(action) - 1:
            return (-1,-1)
        num_of_territories = (len(action) - 1) // 2
        #transform the action index back to a tuple (row, column) of the original NxN attack matrix
        return (action_index // num_of_territories, action_index % num_of_territories)
    def add_experience_to_place_troop_agent(self,state,next_state,action_index,reward):
        self.place_troops_agent.add_experience(state,next_state,action_index,reward)
    def add_experience_to_attack_fortify_agent(self,state,next_state,action_index,reward):
        self.attack_fortify_agent.add_experience(state,next_state,action_index,reward)
    ####OVERRIDE FUNCTIONS####
    def attack(self):
        #missing the board,phase, and player info
        return self.sample_attack_fortify_action()
    def fortify(self, board_obj):
        terrIn,terrOut = self.sample_attack_fortify_action()
        self.msgqueue.addMessage(f'Fortify {terrIn} from {terrOut}')
        move = board_obj.fortificationIsValid(terrIn, terrOut, self.color)
        if move:
            troops = board_obj.getTerritory(terrOut).troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self.color)
                board_obj.removeTroops(terrOut, troops)
        return move
    #return the index to place troops in the territory array.
    def pickATerritoryPlaceTroops(self):
        pass

