from Models.nn_model import NNModel
from Models.config import *
import numpy as np
import dill
import os
class TDActorCritic:
    def __init__(self,exploration_rate,discount,msgqueue,debug_mode=False,max_data=50000):
        self.actor = None
        self.critic = None
        self.current_observation = None
        self.data = None
        self.max_data = max_data
        self.exploration_rate = exploration_rate
        self.discount = discount
        self.msgqueue = msgqueue
        self.debug_mode = debug_mode
        self.actor_loss = []
        self.critic_loss = []
        self.reward = []
    def set_actor(self,actor):
        self.actor = actor
    def set_critic(self,critic):
        self.critic = critic
    def set_debug_mode(self,debug_mode):
        self.debug_mode = debug_mode
    def initialize_training(self):
        self.data = None
        self.actor_loss = []
        self.critic_loss = []
        self.reward = []
    def get_observation(self,observation):
        self.current_observation = observation
        #self.debug_mode and debug_print(f"Observation: {self.current_observation.shape}")
    """set_action: this method uses the actor to return an action based on the current observation."""
    def set_action(self):
        action = self.actor.predict(self.current_observation).reshape(-1)
        #self.debug_mode and debug_print(f"Action: {action.shape}")
        return action
    """sample_action_from_distribution: takes an action probability distribution and samples an action"""
    def sample_action_from_distribution(self,action):
        adjusted_with_exploration_action = (1 - self.exploration_rate) * action + (self.exploration_rate/len(action))
        adjusted_with_exploration_action /= sum(adjusted_with_exploration_action)
        selected_action = np.random.choice(len(adjusted_with_exploration_action),p=adjusted_with_exploration_action)
        #self.debug_mode and debug_print(f"Selected Action Index: {selected_action}")
        return selected_action
    """add_experience: This method takes as input experience that the agent has accumulated and adds its data."""
    def add_experience(self,state,next_state,action_index,reward):
        #self.debug_mode and print(f"New Experience Data--> State: {state.shape}, Next State: {next_state.shape}, Action Index: {action_index}, Reward: {reward}")
        self.reward.append(reward)
        new_data = np.concatenate([state.reshape(-1),next_state.reshape(-1),np.array([action_index]),np.array([reward])])
        if self.data is not None:
            if self.data.shape[0] < self.max_data:
                self.data = np.vstack((self.data,new_data))
            else:
                self.data = np.vstack((self.data[1:],new_data))
        else:
            self.data = new_data.reshape(1,-1)
        #self.debug_mode and debug_print (f"New Data: {new_data.shape}, All Data: {self.data.shape}")
    """update_actor_and_critic: This method uses the experience and transforms it into data that can be used to train the 
    actor and critic."""
    def update_actor_and_critic(self,epochs,learning_rate,batch_size):
        #for single data row
        #actor_data_x = the state --> used to predict current action distribution
        #actor_data_y = the improved action distribution --> created by the state,next state, and reward
        #critic_data_x = the state --> used to predic the value of that state
        #cirtic_data_y = reward + discount*value of next state --> create by the state, next state and reward
        #extracting the data
        observation_size = self.actor.layers[0].input_size
        state = self.data[:,:observation_size]
        next_state = self.data[:,observation_size:-2]
        action_index = self.data[:,-2].astype(int)
        reward = self.data[:,-1].reshape(-1,1)
        #self.debug_mode and print(f"Data Extraction--> State: {state.shape}, Next State: {next_state.shape}, Action Index {action_index}, Reward: {reward.shape}")
        #calculating data to train networks
        value_state = self.critic.predict(state)
        value_next_state = self.critic.predict(next_state)
        #self.debug_mode and print(f"Value State: {value_state}, Value Next State: {value_next_state}")
        td_error = (value_next_state * self.discount + reward - value_state).reshape(-1)
        improved_action_distribution = self.actor.predict(state)
        #self.msgqueue.addMessage(f"Action Distribution Before TD: {improved_action_distribution}")
        #self.debug_mode and print(f"Action Distribution Shape: {improved_action_distribution.shape} Action Index: {action_index}, TD Error: {td_error.shape}")
        improved_action_distribution[np.arange(improved_action_distribution.shape[0]),action_index] += td_error
        #self.msgqueue.addMessage(f"Action Distribution After TD: {improved_action_distribution}")
        improved_action_distribution = self.softmax(improved_action_distribution)
        #self.msgqueue.addMessage(f"Action Distribution After Softmax: {improved_action_distribution}")
        critic_data_x = state
        critic_data_y = value_next_state * self.discount + reward
        actor_data_x = state
        actor_data_y = improved_action_distribution
        #self.msgqueue.addMessage(f"Critic Data X: {critic_data_x}")
        #self.msgqueue.addMessage(f"Critic Data Y: {critic_data_y}")
        #self.msgqueue.addMessage(f"Actor Data X: {actor_data_x}")
        #self.msgqueue.addMessage(f"Actor Data Y: {actor_data_y}")
        #train networks
        actor_loss = self.actor.start_train(actor_data_x,actor_data_y,epochs,batch_size,learning_rate)
        critic_loss = self.critic.start_train(critic_data_x,critic_data_y,epochs,batch_size,learning_rate)
        avg_actor_loss = np.mean(actor_loss)
        avg_critic_loss = np.mean(critic_loss)
        self.actor_loss.append(avg_actor_loss)
        self.critic_loss.append(avg_critic_loss)
    """initalize_critic: This method intializes the critic neural network architecture. The critic has an output length
     of 1 as it outputs the value for a given state"""
    def initialize_critic(self,observation_size,hidden_sizes):
        model = NNModel('MSE',None)
        last_hidden_size = observation_size
        for hidden_size in hidden_sizes:
            model.addLayer(observation_size,hidden_size,'relu','kaiming')
            last_hidden_size = hidden_size
        model.addLayer(last_hidden_size,1,'linear','kaiming')
        self.critic = model
        self.debug_mode and debug_print(self.critic)
        return model
    """initalize_actor: This method initalizes the actor neural network architecture. The actor input the observation 
    and will output an action."""
    def initalize_actor(self,observation_size,action_size,hidden_sizes):
        model = NNModel('CEL',None)
        last_hidden_size = observation_size
        for hidden_size in hidden_sizes:
            model.addLayer(observation_size,hidden_size,'relu','kaiming')
            last_hidden_size = hidden_size
        model.addLayer(last_hidden_size,action_size,'linear','kaiming')
        self.actor = model
        self.debug_mode and debug_print(self.actor)
        return model
    def save_model(self, path):
        agents_folder = "Agents"
        os.makedirs(agents_folder, exist_ok=True)
        save_path = os.path.join(agents_folder, f"{path}.pkl")
        with open(save_path, "wb") as f:
            dill.dump(self, f)
        print(f"Model saved to {save_path}")
    @staticmethod
    def load_model(path):
        load_path = f"{path}.pkl"
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"File '{load_path}' does not exist.")
        with open(load_path, "rb") as f:
            agent = dill.load(f)
        debug_print(f"Model loaded from {load_path}")
        return agent
    def __repr__(self):
        rep = "Actor: " + str(self.actor) + "\nCritic: " + str(self.critic)
        return rep
    
    def softmax(self,z):
        z_exp = np.exp(z - np.max(z))
        return z_exp / (z_exp.sum(axis=1, keepdims=True) + 1e-8)

