from player import Player
import random

class MediumBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue, index, board_obj):
        super().__init__(mycolor, terrList, myname, msgqueue, index, board_obj)

    # find which territory has the most opps
    def pickATerritoryPlaceTroops(self):
        placeAt = None
        maxOpps = 0
        for tkey in self.myOwnedTerritories:
            terr, tindex = self.board.getTerritory(tkey)
            numOpps = sum(1 for nTerr in terr.adjecency_list if not nTerr.dkey in self.myOwnedTerritories)
            # save terr with most opponents
            if maxOpps < numOpps:
                maxOpps = numOpps
                placeAt = tkey
        return placeAt
    
    # basically find weakest neighbour
    def attack(self):
        maxChance = None
        attackFrom = ''
        attackTo = ''
        # go through owned
        for tkey in self.myOwnedTerritories:
            terr, tindex = self.board.getTerritory(tkey)
            # find a possible opponent
            for nTerr in terr.adjecency_list:
                if not nTerr.dkey in self.myOwnedTerritories:
                    # save highest potential victory
                    mc = self.outcomePotential(tkey, nTerr.dkey)
                    if maxChance == None or mc > maxChance:
                        maxChance = mc
                        attackFrom = tkey
                        attackTo = nTerr.dkey
        return attackTo, attackFrom
    
    # find most threatened territory
    def fortify(self):
        threat = None
        fortifyFrom = ''
        fortifyTo = ''
        # find weakest territory
        for tkey in self.myOwnedTerritories:
            terr, tindex = self.board.getTerritory(tkey)
            for oTerr in terr.adjecency_list:
                if not oTerr.dkey in self.myOwnedTerritories:
                    # threat
                    if (threat == None or
                        oTerr.troops - terr.troops > threat):
                        helpkey = self.whoCanGiveMost(terr)
                        if helpkey != '':
                            fortifyFrom = helpkey
                            fortifyTo = tkey
        return fortifyTo, fortifyFrom                        
    
    # finds which territory can donate the most troops into a territory
    def whoCanGiveMost(self, terrObj):
        give = 1    # must be able to donate
        terrGiveKey = ''
        for nTerr in terrObj.adjecency_list:
            if nTerr.dkey in self.myOwnedTerritories:
                if nTerr.troops > give:
                    terrGiveKey = nTerr.dkey
        return terrGiveKey

    # determines how risky an attack would be (troop difference)
    def outcomePotential(self, tkeyFrom, tkeyAttack):
        terrAttack, tindexa = self.board.getTerritory(tkeyAttack)
        terrFrom, tindexf = self.board.getTerritory(tkeyFrom)
        diff = terrFrom.troops - terrAttack.troops
        return diff

class BaseBot(Player):
    def __init__(self, mycolor, terrList, myname, msgqueue, index, board_obj):
        super().__init__(mycolor, terrList, myname, msgqueue, index, board_obj)

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
