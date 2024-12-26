import os

class Territory:
    def __init__(self, name, pos):
        self.name = name
        self.adjecency_list = []
        self.pos = pos
        self.troops = 0
        self.color = 'white'
    
    def connectto(self, territory_o: 'Territory'):
        self.adjecency_list.append(territory_o)

    def isConnected(self, territory_o: 'Territory'):
        if territory_o in self.adjecency_list:
            return True
        return False

class Board:
    def __init__(self):
        self.mapfile = 'board.txt'
        self.maptxt = []
        self.board_dict = {}
        # NORTH AMERICA
        self.board_dict['alaska'] = Territory("Alaska", [1,2])
        self.board_dict['nwt'] = Territory("North West Territory", [1,14])
        self.board_dict['alberta'] = Territory("Alberta", [4,9])
        self.board_dict['ontario'] = Territory("Ontario", [4,17])
        self.board_dict['quebec'] = Territory("Quebec", [4,24])
        self.board_dict['wus'] = Territory("Western United States", [7,12])
        self.board_dict['eus'] = Territory("Eastern United States", [7,20])
        self.board_dict['greenland'] = Territory("Greenland", [1,31])
        self.board_dict['ca'] = Territory("Central America", [10,13])

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

    def addTroops(self, terrkey, num, playercolor):
        terr = self.getTerritory(terrkey)
        terr.troops += num


    def getTerritory(self, terrkey):
        if terrkey in self.board_dict:
            return self.board_dict[terrkey]
        else:
            print(f'ERROR: Wrong key -> {terrkey}')
            return Territory('???')

    def connections(self, terra, terrb):
        terrA = self.getTerritory(terra)
        terrB = self.getTerritory(terrb)

        if not terrA.isConnected(terrB):
            terrA.connectto(terrB)
        
        if not terrB.isConnected(terrA):
            terrB.connectto(terrA)

    def loadmap(self):
        if os.path.exists(self.mapfile):
            with open(self.mapfile) as mf:
                lines = mf.readlines()
                for line in lines:
                    self.maptxt.append(line)
        else:
            print(f'ERROR: No map file -> {self.mapfile}')