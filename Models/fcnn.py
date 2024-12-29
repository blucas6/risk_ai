import numpy as np
from Models.base_layer import Layer
from Models.config import *
class FCNNLayer(Layer):
    def __init__(self,input_size,hidden_nodes,activation_function,weight_initialization,optimizer,debug_mode):
        super().__init__(activation_function, weight_initialization,debug_mode)
        self.input_size = input_size
        self.hidden_nodes = hidden_nodes
        self.pre_activation_output = None
        self.input = None
        self.weights = self.weight_initializer((hidden_nodes,input_size))
        self.bias = np.zeros((1,hidden_nodes))
        self.optimizer = optimizer
        if self.optimizer == 'Adam':
            self.weight_moment1 = np.zeros_like(self.weights)
            self.weight_moment2 = np.zeros_like(self.weights)
            self.bias_moment1 = np.zeros_like(self.bias)
            self.bias_moment2 = np.zeros_like(self.bias)
            self.decay1 = 0.9
            self.decay2 = 0.99
            self.time_step = 1
    def forward(self,X):
        print(X.shape,self.weights.T.shape)
        X = X.reshape(X.shape[0],-1)
        self.input = X
        self.pre_activation_output = self.input @ self.weights.T + self.bias
        output = self.activation_function(self.pre_activation_output)
        if self.debug_mode:
            debug_print(f"Forward--> X Shape:{X.shape}, Pre-Activation Output Shape: {self.pre_activation_output.shape},Output Shape: {output.shape}")
        return output
    def backward(self,loss,learning_rate):
        activation_derivative = self.activation_derivative_function(self.pre_activation_output)
        weight_derivative = self.input
        new_loss = (loss * activation_derivative) @ self.weights
        dw = (loss * activation_derivative).T @ weight_derivative
        db = np.sum(loss * activation_derivative,axis=0,keepdims=True)
        if self.optimizer == 'Adam':
            self.weight_moment1 = self.decay1 * self.weight_moment1 + (1 - self.decay1) * dw
            self.weight_moment2 = self.decay2 * self.weight_moment2 + (1 - self.decay2) * (dw**2)

            corrected_weight_moment1 = self.weight_moment1 / (1 - self.decay1**(self.time_step))
            corrected_weight_moment2 = self.weight_moment2 / (1 - self.decay2**(self.time_step))

            self.bias_moment1 = self.decay1 * self.bias_moment1 + (1 - self.decay1) * db
            self.bias_moment2 = self.decay2 * self.bias_moment2 + (1 - self.decay2) * (db**2)

            corrected_bias_moment1  = self.bias_moment1 / (1 - self.decay1**(self.time_step))
            corrected_bias_moment2 = self.bias_moment2 / (1 - self.decay2**(self.time_step))

            self.weights -= (learning_rate / (np.sqrt(corrected_weight_moment2) + 1e-8)) * corrected_weight_moment1
            self.bias -= (learning_rate / (np.sqrt(corrected_bias_moment2) + 1e-8)) * corrected_bias_moment1
            self.time_step += 1
        else:
            self.weights -= learning_rate * dw
            self.bias -= learning_rate * db
        if self.debug_mode:
            debug_print(f"Backward--> Activation Derivative: {activation_derivative.shape}, Weight Derivative: {weight_derivative.shape}, New Loss: {new_loss.shape}, DW: {dw.shape}, DB: {db.shape}")
        return new_loss
   