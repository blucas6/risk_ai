import random

class Player:
    def __init__(self, mycolor, terrList, myname, msgqueue):
        self.terrList = terrList        # List of all territories
        self.color = mycolor
        self.amountOfOwned = 0          # Amount of territories owned
        self.myOwnedTerritories = []    # Names of all owned territories
        self.myname = myname
        self.maxTriesForActions = 100
        self.msgqueue = msgqueue

    def place_troops(self, board_obj):
        available = self.amountOfOwned
        for t in range(self.maxTriesForActions):
            terrkey = self.pickATerritoryPlaceTroops()
            if terrkey in self.myOwnedTerritories:
                board_obj.addTroops(terrkey, available, self.color)
                return True
        return False

    def attack(self):
        return self.pickATerritoryAttackTo(), self.pickATerritoryAttackFrom()

    def fortify(self, board_obj):
        terrIn = self.pickATerritoryFortifyTo()
        terrOut = self.pickATerritoryFortifyFrom()
        self.msgqueue.addMessage(f'Fortify {terrIn} from {terrOut}')
        if board_obj.fortificationIsValid(terrIn, terrOut, self.color):
            troops = board_obj.getTerritory(terrOut).troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self.color)
                board_obj.removeTroops(terrOut, troops)

    def pickATerritory(self):
        return self.terrList[random.randint(0,len(self.terrList)-1)]
    
    def pickATerritoryPlaceTroops(self):
        return self.pickATerritory()
    
    def pickATerritoryAttackTo(self):
        return self.pickATerritory()
    
    def pickATerritoryAttackFrom(self):
        return self.pickATerritory()
    
    def pickATerritoryFortifyTo(self):
        return self.pickATerritory()
    
    def pickATerritoryFortifyFrom(self):
        return self.pickATerritory()