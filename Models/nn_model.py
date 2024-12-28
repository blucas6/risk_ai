import numpy as np
from Models.fcnn import FCNNLayer
from Models.config import *
class NNModel:
    def __init__(self,loss_function_name,optimizer):
        self.loss_function,self.backward_loss_function,self.output_function = self.get_loss_function(loss_function_name)
        self.loss_function_name = loss_function_name
        self.optimizer = optimizer
        self.layers = []
        self.loss = []
    def addLayer(self,input_size,hidden_nodes,activation_function,weight_initialization,debug_mode=False):
        layer = FCNNLayer(input_size,hidden_nodes,activation_function,weight_initialization,self.optimizer,debug_mode)
        self.layers.append(layer)
    def setLossFunction(self,loss_function):
        self.loss_function = loss_function
    def setOptimizer(self,optimizer):
        self.optimizer = optimizer
    def start_train(self,X,y,epochs,batch_size,learning_rate):
        for epoch in range(epochs):
            num_batches = int(np.ceil(len(X)/batch_size))
            indicies = np.arange(0,len(X))
            np.random.shuffle(indicies)
            for i in range(num_batches):
                start = i * batch_size
                batchX = X[indicies[start: start + batch_size]]
                batchY = y[indicies[start: start + batch_size]]
                self.train_batch(batchX,batchY,learning_rate)
            loss = self.get_loss(X,y)
            self.loss.append(loss)
            debug_print(f"Epoch {epoch} Loss: {loss:.4f}")
        training_accuracy = self.evaluate(X,y)
        debug_print("Training Accuracy: " +  str(training_accuracy))
        return self.loss
    def train_batch(self,batchX,batchY,learning_rate):
        y_pred = self.predict(batchX)
        backward_loss = self.backward_loss_function(batchY,y_pred)
        for layer in reversed(self.layers):
            backward_loss = layer.backward(backward_loss,learning_rate)
    def get_loss_function(self,loss_function):
        if loss_function == 'CEL':
            loss = lambda y,y_pred: -np.mean(np.sum(y * np.log(y_pred + 1e-8),axis=1))
            backward_loss = lambda y,y_pred: (y_pred-y)/len(y)
            output_function = self.softmax
            return loss,backward_loss,output_function
        elif loss_function == 'MSE':
            loss = lambda y,y_pred: np.mean(0.5 * (y - y_pred)**2)
            backward_loss = lambda y,y_pred: (y_pred-y)/len(y)
            output_function = self.linear_output
            return loss,backward_loss,output_function
    def evaluate(self,X,y):
        if self.loss_function_name == 'CEL':
            y_pred = self.predict(X)
            y_pred = np.argmax(y_pred,axis=1)
            y = np.argmax(y,axis=1)
            return np.mean(y_pred == y)
        elif self.loss_function_name == 'MSE':
            y_pred = self.predict(X)
            mse = self.loss_function(y,y_pred)
            return mse      
    def get_loss(self,X,y):
        y_pred = self.predict(X)
        return self.loss_function(y,y_pred)
    def predict(self,X):
        output = X
        for layer in self.layers:
            output = layer.forward(output)
        return self.output_function(output)
    def softmax(self,z):
        z_exp = np.exp(z - np.max(z))
        return z_exp / (z_exp.sum(axis=1, keepdims=True) + 1e-8)
    def linear_output(self,x):
        return x
    def __repr__(self):
        rep = "Input Size: " + str(self.layers[0].input_size) + " Hidden Sizes: "
        hidden_sizes = [layer.hidden_nodes for layer in self.layers]
        for index,size in enumerate(hidden_sizes):
            rep += str(size) + ", " if index < len(hidden_sizes) - 1 else "Output Size: " + str(size)
        return rep