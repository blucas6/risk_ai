import os
import copy
import math

from player import Player

class Territory:
    def __init__(self, name, pos):
        self.name = name
        self.adjecency_list = []
        self.pos = pos
        self.troops = 0
        self.color = None
    
    def connectto(self, territory_o: 'Territory'):
        self.adjecency_list.append(territory_o)

    def isConnected(self, territory_o: 'Territory'):
        if territory_o in self.adjecency_list:
            return True
        return False

class Board:
    def __init__(self, colorwhite, msgqueue, printAttackDetails):
        # References to game members
        self.msgqueue = msgqueue

        self.mapfile = 'board.txt'
        self.maptxt = []
        self.board_dict = {}
        self.territoryMatrix = []
        self.colorwhite = colorwhite
        self.maxrows = 0
        self.maxcols = 0
        self.printAttackDetails = printAttackDetails
        # NORTH AMERICA
        self.board_dict['alaska'] = Territory("Alaska", [1,2])
        self.board_dict['nwt'] = Territory("North West Territory", [1,14])
        self.board_dict['alberta'] = Territory("Alberta", [4,9])
        self.board_dict['ontario'] = Territory("Ontario", [4,17])
        self.board_dict['quebec'] = Territory("Quebec", [4,24])
        self.board_dict['wus'] = Territory("Western United States", [7,11])
        self.board_dict['eus'] = Territory("Eastern United States", [7,20])
        self.board_dict['greenland'] = Territory("Greenland", [1,32])
        self.board_dict['ca'] = Territory("Central America", [9,12])

        self.connections('alaska', 'greenland')
        self.connections('alaska', 'nwt')
        self.connections('alaska', 'alberta')
        self.connections('nwt', 'greenland')
        self.connections('nwt', 'alberta')
        self.connections('nwt', 'ontario')
        self.connections('alberta', 'ontario')
        self.connections('alberta', 'wus')
        self.connections('ontario', 'quebec')
        self.connections('ontario', 'greenland')
        self.connections('quebec', 'greenland')
        self.connections('quebec', 'eus')
        self.connections('wus', 'eus')
        self.connections('wus', 'ca')
        self.connections('eus', 'ca')

        self.loadmap()

    def updateTerritoryMatrix(self, playerindex, territoryindex, troops):
        if (playerindex < len(self.territoryMatrix) and 
            territoryindex < len(self.territoryMatrix[0])):
            self.territoryMatrix[playerindex][territoryindex] = troops
        else:
            self.msgqueue.addMessage(
            f'ERROR: Illegal matrix update P:{playerindex} T:{territoryindex} ({len(self.territoryMatrix)-1},{len(self.territoryMatrix[0])-1})')

    def createDefaultTerritoryMatrix(self, player_amount):
        for p in range(player_amount):
            row = len(list(self.board_dict.keys())) * [0]
            self.territoryMatrix.append(row)

    def addTroops(self, terrkey, num, player: Player):
        if num != 0:
            self.msgqueue.addMessage(f'Adding {num} troops at {terrkey}')
            terr, tindex = self.getTerritory(terrkey)
            terr.troops += num
            terr.color = player.color
            self.updateTerritoryMatrix(player.index, tindex, terr.troops)
        
    def setTroops(self, terrkey, num, player: Player):
        self.msgqueue.addMessage(f'Setting {num} troops at {terrkey}')
        terr, tindex = self.getTerritory(terrkey)
        terr.troops = num
        terr.color = player.color
        self.updateTerritoryMatrix(player.index, tindex, terr.troops)
    
    def removeTroops(self, terrkey, num, player: Player):
        if num != 0:
            self.msgqueue.addMessage(f'Removing {num} troops from {terrkey}')
            terr, tindex = self.getTerritory(terrkey)
            terr.troops -= num
            self.updateTerritoryMatrix(player.index, tindex, terr.troops)

    def fortificationIsValid(self, terrkeyIn, terrkeyOut, mycolor):
        terrIn, tindex = self.getTerritory(terrkeyIn)
        terrOut, tindex = self.getTerritory(terrkeyOut)

        if terrIn.name == '???' or terrOut.name == '???':
            self.msgqueue.addMessage('ERROR: Fortify failed, territories are not real')
            return False
        
        # make sure player owns both territories
        if terrIn.color != mycolor or terrOut.color != mycolor:
            if self.printAttackDetails:
                self.msgqueue.addMessage(' Invalid fortify: owner relationship invalid')
            return False

        return self.adjacencyIsValid(terrkeyIn, terrkeyOut)

    def adjacencyIsValid(self, terrkeyA, terrkeyB):
        terrA, tindex = self.getTerritory(terrkeyA)
        terrB, tindex = self.getTerritory(terrkeyB)

        if terrA.name == '???' or terrB.name == '???':
            self.msgqueue.addMessage('ERROR: Attack failed, territories are not real')
            return False
        
        if terrB in terrA.adjecency_list:
            return True
        
        if self.printAttackDetails:
            self.msgqueue.addMessage(' Invalid move, territories are not adjecent')
        return False

    def attackIsValid(self, terrkeyAttack, terrkeyFrom, mycolor):        
        terrAttack, tindex = self.getTerritory(terrkeyAttack)
        terrFrom, tindex = self.getTerritory(terrkeyFrom)

        if terrAttack.name == '???' or terrFrom.name == '???':
            self.msgqueue.addMessage('ERROR: Attack failed, territories are not real')
            return False
        
        # invalid if the player does not own the owned territory
        # or if the attacking territory is owned by that player
        if terrFrom.color != mycolor or terrAttack.color == mycolor:
            if self.printAttackDetails:
                self.msgqueue.addMessage(' Invalid attack, owner relationship invalid')
            return False
        
        # must have enough troops
        if terrFrom.troops <= 1:
            if self.printAttackDetails:
                self.msgqueue.addMessage(' Invalid attack, player does not have enough troops')
            return False

        return self.adjacencyIsValid(terrkeyAttack, terrkeyFrom)

    def getTerritory(self, terrkey):
        if terrkey in self.board_dict:
            keys = list(self.board_dict.keys())
            return self.board_dict[terrkey], keys.index(terrkey)
        else:
            self.msgqueue.addMessage(f'ERROR: Wrong key -> {terrkey}')
            return Territory('???', [0,0]), -1

    def connections(self, terra, terrb):
        terrA, tindex = self.getTerritory(terra)
        terrB, tindex = self.getTerritory(terrb)

        if not terrA.isConnected(terrB):
            terrA.connectto(terrB)
        
        if not terrB.isConnected(terrA):
            terrB.connectto(terrA)

    def loadmap(self):
        maxcols = 0
        if os.path.exists(self.mapfile):
            with open(self.mapfile) as mf:
                lines = mf.readlines()
                self.maxrows = len(lines)
                for line in lines:
                    if len(lines) > maxcols:
                        maxcols = len(lines)
                    self.maptxt.append(line.replace('x', ' '))
            self.maxcols = maxcols
        else:
            self.msgqueue.addMessage(f'ERROR: No map file -> {self.mapfile}')

    def printTroops(self, stdscr):
        for name, terr in self.board_dict.items():
            if terr.color == None:
                stdscr.addstr(terr.pos[0], terr.pos[1], '0', self.colorwhite)
            else:
                stdscr.addstr(terr.pos[0], terr.pos[1], str(terr.troops), terr.color)

    def drawPath(self, pos1, pos2):
        normal = self.distance(pos1, pos2)
        # xplus = self.distance(pos1, [pos2[0], pos2[1]+self.maxcols])
        # xminus = self.distance(pos1, [pos2[0], ])
        points = []
        currp = copy.deepcopy(pos1)
        while currp != pos2:
            if currp[0] < pos2[0]:
                currp[0] += 1
            elif currp[0] > pos2[0]:
                currp[0] -= 1

            if currp[1] < pos2[1]:
                currp[1] += 1
            elif currp[1] > pos2[1]:
                currp[1] -= 1
            points.append(copy.deepcopy(currp))
        return points[:-1]
    
    def distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
