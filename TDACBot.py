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
    def sample_attack_action(self,board,phase,player):

        pass
    def sample_fortify_action(self):
        pass
    def add_experience_to_place_troop_agent(self,state,next_state,action_index,reward):
        self.place_troops_agent.add_experience(state,next_state,action_index,reward)
    def add_experience_to_attack_fortify_agent(self,state,next_state,action_index,reward):
        self.attack_fortify_agent.add_experience(state,next_state,action_index,reward)
    #return the index to place troops in the territory array.
    def pickATerritoryPlaceTroops(self):
        pass
    
    def pickATerritoryAttackTo(self):
        for t in range(self.maxTriesForActions):
            pass
        self.msgqueue.addMessage('Warning: Failed to choose an attack target reached max tries!')
        return None
    def pickATerritoryAttackFrom(self):
        return self.myOwnedTerritories[
            random.randint(0, len(self.myOwnedTerritories)-1)]
    
    def pickATerritoryFortifyFrom(self):
        return self.myOwnedTerritories[
            random.randint(0, len(self.myOwnedTerritories)-1)]
    
    def pickATerritoryFortifyTo(self):
        return self.myOwnedTerritories[
            random.randint(0, len(self.myOwnedTerritories)-1)]

