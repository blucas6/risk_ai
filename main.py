import curses
import random
import time
import argparse
from datetime import datetime
import threading

from board import Board
from player import Player
from basebot import BaseBot
from TDACBot import TDACBot
from messagequeue import MessageQueue
from endgamestats import EndGameStats

class Move:
    legal_move = 'Legal'
    illegal_move = 'Illegal'

# GAME CLASS
#   Controls the entire game
class Game:
    def __init__(self, args: argparse.Namespace):
        # APP CONTROL
        self.running = True         # app is running
        self.paused = False         # pauses the game
        self.stepMode = False       # activates the step mode of the app
        
        # GAME INFO
        self.currentPlayer = 0      # current player index
        self.currentPhase = 1       # current phase of a players turn
        self.currentGame = 1        # If playing multiple games
        self.maxGames = args.games  # set by command line
        self.mapSize = args.mapsize # amount of continents

        # DISPLAYING INFO
        self.currentAttackPath = []     # stores the attack path for displaying
        self.currentAttackColor = None  # stores the color of the player that attacks

        # STATS
        self.turnCount = 0              # keeps track of the turn count
        self.winner = ''                # fill with a player to end the game
        self.EndGameStats = None        # gets filled at the end of the game

        # GRAPHS
        self.showGraphs = args.charts   # Display model learning

        # MODIFIABLE
        self.printExtraDetails = args.debug     # Extra debug statements
        self.turnTime = 0                       # Frame delay between player turns
        self.inputTimeout = args.turndelay      # Frame delay between input
        self.attackPathToken = '#'              # Attack path character
        self.TurnIndicatorLocation = [1, 40]    # Where to print the turn indicator
        self.debugPanel = [0, 63]               # Where to print the debug panel

    # Entrance to the program
    def start(self, stdscr: curses.window):
        # get max size info
        self.termrows, self.termcols = stdscr.getmaxyx()
        
        # COLORS
        # can only start color after wrapper is called
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.red = curses.color_pair(1)
        self.yellow = curses.color_pair(2)
        self.blue = curses.color_pair(3)
        self.green = curses.color_pair(4)
        self.white = curses.color_pair(5)

        # MESSAGE QUEUE
        self.messageQueue = MessageQueue(
            self.debugPanel, self.termrows, self.termcols,
            f"log-{str(datetime.now()).replace(':','')}.txt")

        # BOARD
        self.board = Board(self.white, self.messageQueue, self.printExtraDetails, self.mapSize)

        # PLAYERS
        self.player1 = TDACBot(self.red, list(self.board.board_dict.keys()), '1', self.messageQueue, 0,2,self.board.total_territories,3,1000,self.showGraphs,5,"Agents/agent1_89998","agent2",mode="Training")
        #self.player1 = BaseBot(self.red, list(self.board.board_dict.keys()), '1', self.messageQueue, 0)
        self.player2 = Player(self.blue, list(self.board.board_dict.keys()), '2', self.messageQueue, 1)
        #self.player3 = Player(self.yellow, list(self.board.board_dict.keys()), '3', self.messageQueue, 2)
        #self.player4 = Player(self.green, list(self.board.board_dict.keys()), '4', self.messageQueue, 3)

        # PLAYER LIST (Modify to adjust the amount of players)
        self.player_list = [self.player1, self.player2]#self.player3, self.player4]

        #curses info
        curses.curs_set(0)
        stdscr.nodelay(True)                # Enable non-blocking mode
        stdscr.timeout(self.inputTimeout)   # Set a timeout for getch()
        # GAME SETUP
        self.newGame()

        # GAME RUN
        self.mainloop(stdscr)

        # END APP
        self.messageQueue.endQueue()

    # Sets up a new game
    def newGame(self):
        # Clear winner
        self.winner = ''

        # Reset board
        self.board.reset()

        # Reset turns
        self.turnCount = 0
        
        # PLAYERS
        #  Clear previous data but not stats
        for p in self.player_list:
            p.archiveStats()
            p.clearPlayer()

        # OBSERVATION MATRIX
        #  Need player list to be initialized, which needs territories first
        self.board.createDefaultTerritoryMatrix(len(self.player_list))
        # PLACE TROOPS
        self.distributeLand()

    # MAIN
    def mainloop(self, stdscr):
        # amount of time between an action
        frames = self.turnTime

        while self.running:
            #time.sleep(0.1)  # Slight delay to reduce CPU usage
            # decrement frames
            frames -= 1

            # EVENTS
            event = stdscr.getch()
            self.events(event)

            # redraw screen
            stdscr.clear()
            self.printScreen(stdscr)
            stdscr.refresh()

            # check for player turns
            self.checkForWinner()
            # do a player turn IF
            #  there is no winner
            #  we have waited through the turn delay
            #  we are not paused (step mode bypasses 1 turn of pausing)
            if not self.winner and frames <= 0 and (not self.paused or self.stepMode):
                frames = self.turnTime
                self.playersPlay()        

    # Checks for win condition
    # triggers the end game
    def checkForWinner(self):
        if not self.winner:
            active = [p for p in self.player_list if p.amountOfOwned > 0]
            if len(active) == 1:
                # archive all the player stats
                for p in self.player_list:
                    p.archiveStats()
                # load the winner
                self.winner = active[0].myname
                active[0].gameswon += 1
                # load the stats
                self.EndGameStats = EndGameStats(
                    self.winner, self.turnCount, self.player_list, self.currentGame)
                # if done playing print all game stats
                if self.currentGame >= self.maxGames:
                    if self.maxGames > 1:
                        self.EndGameStats.printInfo(self.messageQueue,
                            self.board.maxTroopsOnTerr, 
                            self.getPlayerFromColor(self.board.maxTroopsOnTerrColor), 
                            lastgame=True)
                    else:
                        self.EndGameStats.printInfo(self.messageQueue)
                else:
                    self.EndGameStats.printInfo(self.messageQueue)
                    # Not finished with all games, launch next one
                    self.currentGame += 1
                    self.newGame()

    # Get a turn from a player
    def playersPlay(self):
        # get the current player
        currPlayer = self.player_list[self.currentPlayer]
        
        #self.messageQueue.addMessage(f'Curr Player {currPlayer.myname} Phase {self.currentPhase}')

        # check if player can play
        if currPlayer.amountOfOwned > 0:
            #store initial observation
            currPlayer.InitialObservation(self.board.territoryMatrix,self.currentPhase,self.currentPlayer)
            #store bool to see if it made a valid move
            valid_move = Move().illegal_move
            phase = self.currentPhase
            player = self.currentPlayer
            # Phase 1. Place troops on the board
            if self.currentPhase == 1:
                self.messageQueue.addMessage(f'-Player {self.player_list[self.currentPlayer].myname} turn-')
                move = currPlayer.place_troops(self.board)
                valid_move = Move().legal_move if move else Move().illegal_move
                if not move:
                    self.messageQueue.addMessage('Warning: Failed to deploy troops reached max tries!')
                self.currentPhase = 2
            # Phase 2. Attack
            elif self.currentPhase == 2:
                move,valid_move = self.handleAttack(currPlayer)
                if move:
                    self.currentPhase = 3
            # Phase 3. Fortify
            elif self.currentPhase == 3:
                move = currPlayer.fortify(self.board)
                valid_move = Move().legal_move if move else Move().illegal_move
                self.currentPhase = 1
                self.nextPlayer()
            # Update Player Observation After Action
            legality = True if valid_move == Move().legal_move else False
            currPlayer.UpdateObservation(self.board.territoryMatrix,phase,player,legality)
        else:
            self.currentPlayer += 1
            self.currentPlayer = self.currentPlayer % len(self.player_list)

        if self.stepMode:
            self.stepMode = False

    # Increment whose turn it is
    def nextPlayer(self):
        if self.currentPlayer == 1:
            self.turnCount += 1
        self.currentPlayer += 1
        self.currentPlayer = self.currentPlayer % len(self.player_list)
        self.currentAttackPath = []

    # Carry out the attack of a player
    def handleAttack(self, currPlayer: Player):
        # find territory in and territory out
        terrkeyAttack, terrkeyFrom = currPlayer.attack()
        
        # validate attack, quit if invalid
        if not self.board.attackIsValid(terrkeyAttack, terrkeyFrom, currPlayer.color):
            return True, Move().illegal_move
        
        # determine winners
        attackPath = self.doAttack(terrkeyAttack, terrkeyFrom)

        # quit on error
        if attackPath == None:
            if self.printExtraDetails:
                self.messageQueue.addMessage('ERROR: failed to make attack path!')
            return True, Move().illegal_move
        
        # set the display attack path
        self.currentAttackPath = attackPath
        self.currentAttackColor = currPlayer.color

        # check if done
        if random.randint(0,3) > 0:
            return True, Move().legal_move
        
        self.messageQueue.addMessage('  Attacker attacks again!')
        return False, Move().legal_move

    # Deal with events
    def events(self, event):
        # end on enter
        if event in (10,13):
            for p in self.player_list:
                if p is TDACBot:
                    p.graphthreadinstance.stop()
                    p.graphthreadinstance.join()
            self.running = False

        # pause on space
        if event == ord(' '):
            self.paused = not self.paused

        # step mode
        #  bypasses 1 pause state, sets itself back to off after 1 turn
        if event == ord('.'):
            self.stepMode = True

    # Game set up
    #  Set up the board matrix
    #  Players get initial random territories
    def distributeLand(self):
        # get all possible territory keys
        possible_terrs = list(self.board.board_dict.keys())
        player_ind = 0
        # loop until all territories have troops
        while len(possible_terrs) > 0:
            # pick a random territory key
            terrind = random.randint(0, len(possible_terrs)-1)
            # add troops according to the current player index
            self.board.addTroops(possible_terrs[terrind], 1, self.player_list[player_ind])
            
            # give that player the territory
            self.player_list[player_ind].gainATerritory(possible_terrs[terrind])

            # remove territory from consideration
            del possible_terrs[terrind]

            player_ind += 1
            player_ind = player_ind % len(self.player_list)

    # Perform a players attack
    def doAttack(self, terrkeyAttack, terrkeyFrom):
        terrAttacker, tindex = self.board.getTerritory(terrkeyFrom)
        terrDefender, tindex = self.board.getTerritory(terrkeyAttack)

        playerA = self.getPlayerFromColor(terrAttacker.color)
        playerB = self.getPlayerFromColor(terrDefender.color)
        if playerA == None or playerB == None:
            self.messageQueue.addMessage('ERROR: Failed to find player!')

        if terrAttacker.name == '???' or terrDefender.name == '???':
            self.messageQueue.addMessage('ERROR: Attack failed, territories are not real')
            return None
        
        attackPath = self.board.drawPath(terrAttacker.pos, terrDefender.pos)
        if self.printExtraDetails:
            self.messageQueue.addMessage(' Attack path: ', attackPath)
        
        # do rolls
        while True:
            if self.printExtraDetails:
                self.messageQueue.addMessage(f' Combat throw: troops A {terrAttacker.troops} troops B {terrDefender.troops}')
            if terrAttacker.troops-1 >= 3:
                diceA = 3
            elif terrAttacker.troops-1 == 2:
                diceA = 2
            elif terrAttacker.troops-1 == 1:
                diceA = 1
            else:
                # attacker lost, do nothing
                playerA.attackRatio[1] += 1
                playerB.defendRatio[0] += 1
                playerB.defendRatio[1] += 1
                self.messageQueue.addMessage('   Result: Attacker loses')
                break
            
            if terrDefender.troops >= 2:
                diceB = 2
            elif terrDefender.troops == 1:
                diceB = 1
            else:
                # defender lost, move attacker troops into territory
                self.board.setTroops(terrkeyAttack, terrAttacker.troops - 1, playerA)
                self.board.setTroops(terrkeyFrom, 1, playerA)
                playerA.gainATerritory(terrkeyAttack)
                playerA.attackRatio[0] += 1
                playerA.attackRatio[1] += 1
                playerB.defendRatio[1] += 1
                playerB.loseATerritory(terrkeyAttack)
                self.messageQueue.addMessage('   Result: Attacker wins')
                break

            # roll for combat
            troopDiffA, troopDiffB = self.computeAttack(diceA, diceB)
            self.board.removeTroops(terrkeyFrom, troopDiffA, playerA)
            self.board.removeTroops(terrkeyAttack, troopDiffB, playerB)

        return attackPath
    
    # Roll dice and figure out troop losses
    def computeAttack(self, diceA, diceB):
        rollsA, rollsB = self.getRolls(diceA, diceB)
        return self.doRolls(rollsA, rollsB)
    
    # Returns rolled dice in a sorted array
    def getRolls(self, diceA, diceB):
        pArolls = []
        pBrolls = []

        for r in range(diceA):
            pArolls.append(random.randint(1,6))
        for r in range(diceB):
            pBrolls.append(random.randint(1,6))
        
        pArolls = list(reversed(sorted(pArolls)))
        pBrolls = list(reversed(sorted(pBrolls)))

        if self.printExtraDetails:
            self.messageQueue.addMessage(f' Rolls A: {pArolls}, Rolls B: {pBrolls}')
        return pArolls, pBrolls

    # Computes troop losses
    def doRolls(self, rollsA, rollsB):
        troopDiffA = 0
        troopDiffB = 0

        for i,dice in enumerate(rollsB):
            if i <= len(rollsA)-1:
                if dice >= rollsA[i]:
                    troopDiffA += 1
                else:
                    troopDiffB += 1
        
        return troopDiffA, troopDiffB 

    # Prints the screen
    def printScreen(self, stdscr):
        # print the map
        for r,line in enumerate(self.board.maptxt):
            stdscr.addstr(r,0, line)

        # print troops with color
        self.board.printTroops(stdscr)

        # print the turn indicator
        stdscr.addstr(self.TurnIndicatorLocation[0], self.TurnIndicatorLocation[1],
                      f'=Game {self.currentGame} Turn {self.turnCount}=')
        for i,p in enumerate(self.player_list):
            status = f'Player {p.myname}'
            if p.myname == str(self.currentPlayer+1):
                if self.currentPhase == 1:
                    status += ' place troops'
                elif self.currentPhase == 2:
                    status += ' attack'
                elif self.currentPhase == 3:
                    status += ' fortify'
            stdscr.addstr(self.TurnIndicatorLocation[0]+i+1, self.TurnIndicatorLocation[1],
                      status, p.color)

        # print attack path
        for pos in self.currentAttackPath:
            stdscr.addstr(pos[0], pos[1], self.attackPathToken, self.currentAttackColor)

        # print message queue
        for r,msg in enumerate(self.messageQueue.msgs):
            stdscr.addstr(self.debugPanel[0]+r, self.debugPanel[1], msg)

    # Utility function to figure out the player from a color
    def getPlayerFromColor(self, color):
        for p in self.player_list:
            if p.color == color:
                return p
        self.messageQueue.addMessage(f'ERROR: Color does not exist -> {color}')
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Risk AI command line args')
    parser.add_argument('-g', '--games', type=int, default=1,
                        help='Amount of games in a row (default 1)')
    parser.add_argument('-m', '--mapsize', type=int, choices=[0,1,2,3,4], default=0,
                        help='0=NA 1=SA 2=Europe 3=Africa 4=Russia 5=Australia')
    parser.add_argument('-t', '--turndelay', type=int, default=10,
                        help='Delay time between getch()')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Prints additional debug statements')
    parser.add_argument('-c', '--charts', action='store_true',
                        help='Shows model charts during gameplay')
    args = parser.parse_args()
    g = Game(args)
    curses.wrapper(g.start)