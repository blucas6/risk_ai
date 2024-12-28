import numpy as np
class Layer:
    def __init__(self,activation_function,weight_initialization,debug_mode):
        self.activation_function,self.activation_derivative_function = self.get_activation_function(activation_function)
        self.weight_initializer = self.get_weight_initializer(weight_initialization)
        self.debug_mode = debug_mode
    def get_weight_initializer(self,weight_initialization):
        if weight_initialization == 'gaussian':
            return lambda size: np.random.randn(*size)
        elif weight_initialization == 'uniform':
            return lambda size: np.random.uniform(-1,1, size)
        elif weight_initialization == 'xavier':
            return lambda size: np.random.randn(*size) * np.sqrt(1/size[1])
        elif weight_initialization == 'kaiming':
            return lambda size: np.random.randn(*size) * np.sqrt(2/size[1])
        else:
            raise ValueError("Invalid weight initalizer.")
    def get_activation_function(self,activation_function):
        if activation_function == 'relu':
            function = lambda x: np.where(x>0,x,0)
            derivative = lambda x: np.where(x>0,1,0)
            return function,derivative
        elif activation_function == 'sigmoid':
            sigmoid = lambda x: 1/(1+np.exp(-x))
            function = sigmoid
            derivative = lambda x: sigmoid(x) * (1-sigmoid(x))
            return function,derivative
        elif activation_function == 'tanh':
            function = lambda x: np.tanh(x)
            derivative = lambda x: 1 - np.tanh(x)**2
            return function,derivative
        elif activation_function == 'linear':
            function = lambda x: x
            derivative = lambda x: np.ones_like(x)
            return function,derivative
        else:
            raise ValueError("Invalid Activation Function")
    def set_debug_model(self,mode):
        self.debug_mode = mode
    