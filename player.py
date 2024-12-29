import random

class Player:
    def __init__(self, mycolor, terrList, myname, msgqueue, index):
        self.terrList = terrList        # List of all territories
        self.color = mycolor
        self.amountOfOwned = 0          # Amount of territories owned
        self.myOwnedTerritories = []    # Names of all owned territories
        self.myname = myname
        self.maxTriesForActions = 100
        self.msgqueue = msgqueue
        self.index = index
        # for stats
        self.attackRatio = [0,0]
        self.defendRatio = [0,0]
        self.maxterritories = 0
        self.placedtroops = 0

    def gainATerritory(self, terrkey):
        self.myOwnedTerritories.append(terrkey)
        self.amountOfOwned += 1
        if self.maxterritories < self.amountOfOwned:
            self.maxterritories = self.amountOfOwned

    def loseATerritory(self, terrkey):
        self.myOwnedTerritories.remove(terrkey)
        self.amountOfOwned -= 1

    def place_troops(self, board_obj):
        available = self.amountOfOwned
        for t in range(self.maxTriesForActions):
            terrkey = self.pickATerritoryPlaceTroops()
            if terrkey in self.myOwnedTerritories:
                board_obj.addTroops(terrkey, available, self)
                # stats
                self.placedtroops += available
                return True
        return False

    def attack(self):
        return self.pickATerritoryAttackTo(), self.pickATerritoryAttackFrom()

    def fortify(self, board_obj):
        terrIn = self.pickATerritoryFortifyTo()
        terrOut = self.pickATerritoryFortifyFrom()
        self.msgqueue.addMessage(f'Fortify {terrIn} from {terrOut}')
        if board_obj.fortificationIsValid(terrIn, terrOut, self.color):
            theTerr, tindex = board_obj.getTerritory(terrOut)
            troops = theTerr.troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self)
                board_obj.removeTroops(terrOut, troops, self)

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