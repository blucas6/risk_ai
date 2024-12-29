import os
import copy
import math

from player import Player

# TERRITORY CLASS
#  Holds all info for board territories
class Territory:
    def __init__(self, name, pos):
        self.name = name            # Name of the territory, used for displaying ONLY (not dict key)
        self.adjecency_list = []    # List of all adjecent territories
        self.pos = pos              # Position on map, for displaying troops and attacks
        self.troops = 0             # Amount of troops on territory
        self.color = None           # Color of player that owns troops
    
    # Adds a connection to the adjecency list
    def connectto(self, territory_o: 'Territory'):
        self.adjecency_list.append(territory_o)

    # Checks if a territory is connected
    def isConnected(self, territory_o: 'Territory'):
        if territory_o in self.adjecency_list:
            return True
        return False

# BOARD CLASS
#  Contains all territories and manipulations of the territories
class Board:
    def __init__(self, colorwhite, msgqueue, printExtraDetails, continents):
        # References to game members
        self.msgqueue = msgqueue
        self.printExtraDetails = printExtraDetails

        # SETTINGS
        self.mapfileNA = 'northamerica.txt'
        self.mapfileSA = 'southamerica.txt'
        self.mapfileEuro = 'europe.txt'
        self.mapfileAfrica = 'africa.txt'
        self.mapfileRussia = 'russia.txt'
        self.mapfileAussie = 'australia.txt'
        # Where to load the entire ascii art
        self.maptxt = []                    # For displaying the map strings
        self.colorwhite = colorwhite        # Color for displaying
        self.maxrows = 0                # amount of rows in map file
        self.maxcols = 0                # amount of cols in map file
        self.continents = continents    # amount of continents on the board

        # TERRITORY INFO
        self.board_dict = {}        # Contains all territories
                                    # { <key>: <Territory()>, ...}
                                            
        self.territoryMatrix = []   # Observation space
                                    # Rows correspond to players
                                    # Rows contain all owned troops on territories
                                    #     t0 t1 t2 ...
                                    # p1 [ x, x, x, ...]
                                    # p2 [...]

        # NORTH AMERICA
        self.board_dict['alaska'] = Territory('Alaska', [1,3])
        self.board_dict['nwt'] = Territory('North West Territory', [1,14])
        self.board_dict['alberta'] = Territory('Alberta', [4,9])
        self.board_dict['ontario'] = Territory('Ontario', [4,17])
        self.board_dict['quebec'] = Territory('Quebec', [4,24])
        self.board_dict['wus'] = Territory('Western United States', [7,11])
        self.board_dict['eus'] = Territory('Eastern United States', [7,20])
        self.board_dict['greenland'] = Territory('Greenland', [1,32])
        self.board_dict['ca'] = Territory('Central America', [9,12])
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

        # SOUTH AMERICA
        if self.continents > 0:
            self.board_dict['venezuela'] = Territory('Venezuela', [13,18])
            self.board_dict['peru'] = Territory('Peru', [18,17])
            self.board_dict['brazil'] = Territory('Brazil', [16,23])
            self.board_dict['argentina'] = Territory('Argentina', [21,19])
            self.connections('venezuela', 'ca')
            self.connections('venezuela', 'peru')
            self.connections('venezuela', 'brazil')
            self.connections('peru', 'brazil')
            self.connections('peru', 'argentina')
            self.connections('brazil', 'argentina')
        
        # EUROPE
        if self.continents > 1:
            pass
            
        # AFRICA
        if self.continents > 2:
            pass

        # RUSSIA
        if self.continents > 3:
            pass

        # AUSTRALIA
        if self.continents > 4:
            pass

        # Load displaying map
        self.loadmap()

    # Any update to the territories must update the observation matrix
    def updateTerritoryMatrix(self, playerindex, territoryindex, troops):
        if (playerindex < len(self.territoryMatrix) and 
            territoryindex < len(self.territoryMatrix[0])):
            self.territoryMatrix[playerindex][territoryindex] = troops
        else:
            self.msgqueue.addMessage(
            f'ERROR: Illegal matrix update P:{playerindex} T:{territoryindex} ({len(self.territoryMatrix)-1},{len(self.territoryMatrix[0])-1})')

    # Set up the space for the observation matrix
    def createDefaultTerritoryMatrix(self, player_amount):
        for p in range(player_amount):
            row = len(list(self.board_dict.keys())) * [0]
            self.territoryMatrix.append(row)

    # Adding an amount of troops to a territory
    def addTroops(self, terrkey, num, player: Player):
        if num != 0:
            if self.printExtraDetails:
                self.msgqueue.addMessage(f'Adding {num} troops at {terrkey}')
            terr, tindex = self.getTerritory(terrkey)
            terr.troops += num
            terr.color = player.color
            self.updateTerritoryMatrix(player.index, tindex, terr.troops)
        
    # Setting the amount of troops on a territory to a fixed number
    def setTroops(self, terrkey, num, player: Player):
        if self.printExtraDetails:
            self.msgqueue.addMessage(f'Setting {num} troops at {terrkey}')
        terr, tindex = self.getTerritory(terrkey)
        terr.troops = num
        terr.color = player.color
        self.updateTerritoryMatrix(player.index, tindex, terr.troops)
    
    # Removing an amount of troops from a territory
    def removeTroops(self, terrkey, num, player: Player):
        if num != 0:
            if self.printExtraDetails:
                self.msgqueue.addMessage(f'Removing {num} troops from {terrkey}')
            terr, tindex = self.getTerritory(terrkey)
            terr.troops -= num
            self.updateTerritoryMatrix(player.index, tindex, terr.troops)

    # Check if fortification
    #  Includes real territories
    #  Is owned by the same player
    #  Are adjecent territories
    def fortificationIsValid(self, terrkeyIn, terrkeyOut, mycolor):
        terrIn, tindex = self.getTerritory(terrkeyIn)
        terrOut, tindex = self.getTerritory(terrkeyOut)

        if terrIn.name == '???' or terrOut.name == '???':
            self.msgqueue.addMessage('ERROR: Fortify failed, territories are not real')
            return False
        
        # make sure player owns both territories
        if terrIn.color != mycolor or terrOut.color != mycolor:
            if self.printExtraDetails:
                self.msgqueue.addMessage(' Invalid fortify: owner relationship invalid')
            return False

        return self.adjacencyIsValid(terrkeyIn, terrkeyOut)

    # Returns if 2 territories are adjecent
    def adjacencyIsValid(self, terrkeyA, terrkeyB):
        terrA, tindex = self.getTerritory(terrkeyA)
        terrB, tindex = self.getTerritory(terrkeyB)

        if terrA.name == '???' or terrB.name == '???':
            self.msgqueue.addMessage('ERROR: Attack failed, territories are not real')
            return False
        
        if terrB in terrA.adjecency_list:
            return True
        
        if self.printExtraDetails:
            self.msgqueue.addMessage(' Invalid move, territories are not adjecent')
        return False

    # Checks if attack
    #  Is between real territories
    #  Player does not own the attacked territory
    #  Player owns the territory they attack from
    #  Player has more than 1 troop to attack with
    def attackIsValid(self, terrkeyAttack, terrkeyFrom, mycolor):        
        terrAttack, tindex = self.getTerritory(terrkeyAttack)
        terrFrom, tindex = self.getTerritory(terrkeyFrom)

        if terrAttack.name == '???' or terrFrom.name == '???':
            self.msgqueue.addMessage('ERROR: Attack failed, territories are not real')
            return False
        
        # invalid if the player does not own the owned territory
        # or if the attacking territory is owned by that player
        if terrFrom.color != mycolor or terrAttack.color == mycolor:
            if self.printExtraDetails:
                self.msgqueue.addMessage(' Invalid attack, owner relationship invalid')
            return False
        
        # must have enough troops
        if terrFrom.troops <= 1:
            if self.printExtraDetails:
                self.msgqueue.addMessage(' Invalid attack, player does not have enough troops')
            return False

        return self.adjacencyIsValid(terrkeyAttack, terrkeyFrom)

    # Pass a key and get the corresponding territory and the index in the dictionary
    #  The index should correspond to the observation matrix index
    def getTerritory(self, terrkey):
        if terrkey in self.board_dict:
            keys = list(self.board_dict.keys())
            return self.board_dict[terrkey], keys.index(terrkey)
        else:
            self.msgqueue.addMessage(f'ERROR: Wrong key -> {terrkey}')
            return Territory('???', [0,0]), -1

    # Adds a connection the both territories
    def connections(self, terra, terrb):
        terrA, tindex = self.getTerritory(terra)
        terrB, tindex = self.getTerritory(terrb)

        if not terrA.isConnected(terrB):
            terrA.connectto(terrB)
        
        if not terrB.isConnected(terrA):
            terrB.connectto(terrA)

    # Loads the map into the board
    def loadmap(self):
        maps = [self.mapfileNA, self.mapfileSA, self.mapfileEuro,
                  self.mapfileAfrica, self.mapfileRussia, self.mapfileAussie]
        mapfile = maps[self.continents]
        if os.path.exists(mapfile):
            with open(mapfile, 'r') as mf:
                lines = mf.readlines()
                if len(lines) > self.maxrows:
                    self.maxrows = len(lines)
                for num,line in enumerate(lines):
                    if len(line) > self.maxcols:
                        self.maxcols = len(line)
                    self.maptxt.append(line.replace('x', ' '))
        else:
            self.msgqueue.addMessage(f'ERROR: No map file -> {mapfile}')

    # Print the number of troops in each territory 
    # with the color of the player that owns that territory
    def printTroops(self, stdscr):
        # prints troop number starting at first map 'x'
        # pos points to middle map 'x' for attack paths
        for name, terr in self.board_dict.items():
            if terr.color == None:
                stdscr.addstr(terr.pos[0], terr.pos[1]-1, '0', self.colorwhite)
            else:
                stdscr.addstr(terr.pos[0], terr.pos[1]-1, str(terr.troops), terr.color)

    # Returns a list of points from a to b
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
    
    # returns distance
    def distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
