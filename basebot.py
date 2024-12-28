from player import Player
import random

class BaseBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue):
        super().__init__(mycolor, terrList, myname, msgqueue)

    def pickATerritoryPlaceTroops(self):
        return self.myOwnedTerritories[
            random.randint(0, len(self.myOwnedTerritories)-1)]
    
    def pickATerritoryAttackTo(self):
        for t in range(self.maxTriesForActions):
            choice = self.terrList[
                random.randint(0, len(self.terrList)-1)]
            if not choice in self.myOwnedTerritories:
                return choice
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
