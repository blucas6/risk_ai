import random

# PLAYER CLASS
#  Default player class
#  Picks random territories for every action
class Player:
    def __init__(self, mycolor, terrList, myname, msgqueue, index):
        # Reference to game members
        self.msgqueue = msgqueue

        self.terrList = terrList        # List of all territory keys
        self.color = mycolor            # Color of the player
        self.amountOfOwned = 0          # Amount of territories owned
        self.myOwnedTerritories = []    # Keys of all owned territories
        self.myname = myname            # Player name (number as a string)
        self.maxTriesForActions = 100   # Default timeout for random actions
        self.index = index              # Index of the player (for board matrix)
        
        # for stats
        self.attackRatio = [0,0]
        self.defendRatio = [0,0]
        self.maxterritories = 0
        self.placedtroops = 0

    # Player gains a territory
    def gainATerritory(self, terrkey):
        self.myOwnedTerritories.append(terrkey)
        self.amountOfOwned += 1
        if self.maxterritories < self.amountOfOwned:
            self.maxterritories = self.amountOfOwned

    # Player loses a territory
    def loseATerritory(self, terrkey):
        self.myOwnedTerritories.remove(terrkey)
        self.amountOfOwned -= 1

    # GAME ACTION Phase 1
    #  Asks the player where to place troops
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
    
    # GAME ACTION Phase 2
    #  Asks the player where to attack from and to
    def attack(self):
        return self.pickATerritoryAttackTo(), self.pickATerritoryAttackFrom()

    # GAME ACTION Phase 3
    #  Asks the player where to fortify from and to
    def fortify(self, board_obj):
        terrIn = self.pickATerritoryFortifyTo()
        terrOut = self.pickATerritoryFortifyFrom()
        self.msgqueue.addMessage(f'Fortify {terrIn} from {terrOut}')
        move = board_obj.fortificationIsValid(terrIn, terrOut, self.color)
        if move:
            theTerr, tindex = board_obj.getTerritory(terrOut)
            troops = theTerr.troops - 1
            if troops > 0:
                board_obj.addTroops(terrIn, troops, self)
                board_obj.removeTroops(terrOut, troops, self)
        return move
    
    def UpdateObservation(self,board_obj,phase,player,move_legality):
        pass

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