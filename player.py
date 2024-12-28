import random

class Player:
    def __init__(self, mycolor, terrList, myname):
        self.terrList = terrList        # List of all territories
        self.color = mycolor
        self.amountOfOwned = 0          # Amount of territories owned
        self.myOwnedTerritories = []    # Names of all owned territories
        self.myname = myname
        self.maxTriesForActions = 100

    def place_troops(self, board_obj):
        available = self.amountOfOwned
        for t in range(self.maxTriesForActions):
            terrkey = self.pickATerritory()
            if terrkey in self.myOwnedTerritories:
                board_obj.addTroops(terrkey, available, self.color)
                return True
        return False

    def attack(self):
        return self.pickATerritory(), self.pickATerritory()

    def fortify(self, board_obj):
        terrIn = self.myOwnedTerritories[random.randint(0, len(self.myOwnedTerritories)-1)]
        terrOut = self.myOwnedTerritories[random.randint(0, len(self.myOwnedTerritories)-1)]
        if board_obj.fortificationIsValid(terrIn, terrOut, self.color):
            troops = board_obj.getTerritory(terrOut).troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self.color)
                board_obj.removeTroops(terrOut, troops)

    def pickATerritory(self):
        return self.terrList[random.randint(0,len(self.terrList)-1)]