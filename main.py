import curses
import random
import time

from board import Board
from player import Player
from basebot import BaseBot

class MessageQueue:
    def __init__(self, printPos, termrows, termcols):
        self.msgs = []
        self.printPos = printPos
        self.maxMsgs = termrows - printPos[0]
        self.maxcols = termcols - printPos[1]

    def addMessage(self, msg, mylist=[]):
        if mylist:
            msg += ' ['
            for item in mylist:
                msg += str(item)+' '
            msg += ']'
        if len(msg) > self.maxcols:
            self.msgs.append(msg[:self.maxcols-1])
            self.msgs.append(msg[self.maxcols-1:])
        else:
            self.msgs.append(msg)
        while len(self.msgs) > self.maxMsgs:
            del self.msgs[0]

class EndGameStats:
    def __init__(self, winner, totalturns, player_list):
        self.winner = winner
        self.totalTurns = totalturns
        self.totalTroops = sum(p.placedtroops for p in player_list)
        self.player_list = player_list

    def printInfo(self, msgqueue: MessageQueue):
        msgqueue.addMessage(f'**Winner: Player {self.winner}!**')
        msgqueue.addMessage(f' Total Turn Count: {self.totalTurns}')
        msgqueue.addMessage(f' Total Troop Count: {self.totalTroops}')
        for p in self.player_list:
            msgqueue.addMessage(f' Player {p.myname}')
            if p.attackRatio[1] == 0:
                ratio = 0
            else:
                ratio = round((p.attackRatio[0]/p.attackRatio[1])*100,2)
            msgqueue.addMessage(f'  Attack Winrate: {ratio}% [{p.attackRatio[0]}/{p.attackRatio[1]}]')
            if p.defendRatio[1] == 0:
                ratio = 0
            else:
                ratio = round((p.defendRatio[0]/p.defendRatio[1])*100,2)
            msgqueue.addMessage(f'  Defend Winrate: {ratio}% [{p.defendRatio[0]}/{p.defendRatio[1]}]')
            msgqueue.addMessage(f'  Max Territories: {p.maxterritories}')
class Move():
    legal_move = 'Legal'
    illegal_move = 'Illegal'
class Game:
    def __init__(self):
        self.turnCount = 0
        self.running = True
        self.paused = False
        self.currentPlayer = 0
        self.currentPhase = 1

        self.currentAttackPath = []
        self.currentAttackColor = None
        self.stepMode = False

        self.winner = ''
        self.EndGameStats = None

        # MODIFIABLE
        self.printAttackDetails = False
        self.turnTime = 0
        self.attackPathToken = '#'
        self.TurnIndicatorLocation = [1, 40]
        self.endGameStatsLocation = [7,40]
        self.debugPanel = [0, 63]


    def start(self, stdscr):
        # can only start color after wrapper is called
        self.termrows, self.termcols = stdscr.getmaxyx()
        self.messageQueue = MessageQueue(self.debugPanel, self.termrows, self.termcols)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        red = curses.color_pair(1)
        yellow = curses.color_pair(2)
        blue = curses.color_pair(3)
        green = curses.color_pair(4)
        white = curses.color_pair(5)

        # pass color to objects
        self.board = Board(white, self.messageQueue, self.printAttackDetails)
        self.player1 = BaseBot(red, list(self.board.board_dict.keys()), '1', self.messageQueue)
        self.player2 = BaseBot(blue, list(self.board.board_dict.keys()), '2', self.messageQueue)
        self.player3 = BaseBot(yellow, list(self.board.board_dict.keys()), '3', self.messageQueue)
        self.player4 = BaseBot(green, list(self.board.board_dict.keys()), '4', self.messageQueue)
        self.player_list = [self.player1, self.player2, self.player3, self.player4]
        curses.curs_set(0)
        stdscr.nodelay(True)        # Enable non-blocking mode
        stdscr.timeout(100)         # Set a timeout for getch()

        # GAME SETUP
        self.setup()

        # GAME RUN
        self.mainloop(stdscr)

    def mainloop(self, stdscr):
        # amount of time between an action
        frames = self.turnTime

        while self.running:
            #time.sleep(0.1)  # Slight delay to reduce CPU usage

            # decrement frams
            frames -= 1

            # EVENTS
            event = stdscr.getch()
            self.events(event)

            # redraw screen
            stdscr.clear()
            self.printScreen(stdscr)
            stdscr.refresh()

            #self.currentAttackPath = [] # stop displaying attack paths

            # check for player turns
            self.checkForWinner()
            if not self.winner and frames <= 0 and (not self.paused or self.stepMode):
                frames = self.turnTime
                self.playersPlay()        

    def checkForWinner(self):
        active = [p for p in self.player_list if p.amountOfOwned > 0]
        if len(active) == 1:
            self.winner = active[0].myname
            self.EndGameStats = EndGameStats(
                self.winner, self.turnCount, self.player_list)
            self.EndGameStats.printInfo(self.messageQueue)

    def playersPlay(self):
        # get the current player
        currPlayer = self.player_list[self.currentPlayer]
        
        #self.messageQueue.addMessage(f'Curr Player {currPlayer.myname} Phase {self.currentPhase}')

        # check if player can play
        if currPlayer.amountOfOwned > 0:
            #store bool to see if it made a valid move
            valid_move = Move().illegal_move
            # Phase 1. Place troops on the board
            if self.currentPhase == 1:
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
            currPlayer.UpdateObservation(self.board,self.currentPhase,self.currentPlayer,valid_move)
        else:
            self.currentPlayer += 1
            self.currentPlayer = self.currentPlayer % len(self.player_list)

        if self.stepMode:
            self.stepMode = False

    def nextPlayer(self):
        self.turnCount += 1
        self.currentPlayer += 1
        self.currentPlayer = self.currentPlayer % len(self.player_list)
        self.messageQueue.addMessage(f'-Player {self.player_list[self.currentPlayer].myname} turn-')
        self.currentAttackPath = []

    def handleAttack(self, currPlayer):
        # find territory in and territory out
        terrkeyAttack, terrkeyFrom = currPlayer.attack()
        self.messageQueue.addMessage(f'Attack: player {currPlayer.myname} attacks {terrkeyAttack} from {terrkeyFrom}')
        
        # validate attack, quit if invalid
        if not self.board.attackIsValid(terrkeyAttack, terrkeyFrom, currPlayer.color):
            return True, Move().illegal_move
        
        # determine winners
        attackPath = self.doAttack(terrkeyAttack, terrkeyFrom)

        # quit on error
        if attackPath == None:
            if self.printAttackDetails:
                self.messageQueue.addMessage('ERROR: failed to make attack path!')
            return True, Move().illegal_move
        
        # set the display attack path
        self.currentAttackPath = attackPath
        self.currentAttackColor = currPlayer.color

        # check if done
        if random.randint(0,3) > 0:
            return True, Move().legal_move
        
        self.messageQueue.addMessage('Attacker attacks again!')
        return False, Move().legal_move

    def events(self, event):
        # end on enter
        if event in (10,13):
            self.running = False

        # pause on space
        if event == ord(' '):
            self.paused = not self.paused

        # step
        if event == ord('.'):
            self.stepMode = True

    def setup(self):
        # get all possible territory keys
        possible_terrs = list(self.board.board_dict.keys())
        player_ind = 0
        player_list = [self.player1, self.player2, self.player3, self.player4]
        # loop until all territories have troops
        while len(possible_terrs) > 0:
            # pick a random territory key
            terrind = random.randint(0, len(possible_terrs)-1)
            # add troops according to the current player index
            self.board.addTroops(possible_terrs[terrind], 1, player_list[player_ind].color)
            
            # give that player the territory
            player_list[player_ind].gainATerritory(possible_terrs[terrind])

            # remove territory from consideration
            del possible_terrs[terrind]

            player_ind += 1
            player_ind = player_ind % len(self.player_list)

    def doAttack(self, terrkeyAttack, terrkeyFrom):
        terrAttacker = self.board.getTerritory(terrkeyFrom)
        terrDefender = self.board.getTerritory(terrkeyAttack)

        playerA = self.getPlayerFromColor(terrAttacker.color)
        playerB = self.getPlayerFromColor(terrDefender.color)
        if playerA == None or playerB == None:
            self.messageQueue.addMessage('ERROR: Failed to find player!')

        if terrAttacker.name == '???' or terrDefender.name == '???':
            self.messageQueue.addMessage('ERROR: Attack failed, territories are not real')
            return None
        
        attackPath = self.board.drawPath(terrAttacker.pos, terrDefender.pos)
        if self.printAttackDetails:
            self.messageQueue.addMessage(' Attack path: ', attackPath)
        
        # do rolls
        while True:
            if self.printAttackDetails:
                self.messageQueue.addMessage(f' Combat throw: troops A {terrAttacker.troops} troops B {terrDefender.troops}')
            if terrAttacker.troops-1 >= 3:
                rollsA = 3
            elif terrAttacker.troops-1 == 2:
                rollsA = 2
            elif terrAttacker.troops-1 == 1:
                rollsA = 1
            else:
                # attacker lost, do nothing
                playerA.attackRatio[1] += 1
                playerB.defendRatio[0] += 1
                playerB.defendRatio[1] += 1
                self.messageQueue.addMessage('Result: Attacker loses')
                break
            
            if terrDefender.troops >= 2:
                rollsB = 2
            elif terrDefender.troops == 1:
                rollsB = 1
            else:
                # defender lost, move attacker troops into territory
                terrDefender.troops = terrAttacker.troops - 1
                terrDefender.color = terrAttacker.color
                terrAttacker.troops = 1
                playerA.gainATerritory(terrkeyAttack)
                playerA.attackRatio[0] += 1
                playerA.attackRatio[1] += 1
                playerB.defendRatio[1] += 1
                playerB.loseATerritory(terrkeyAttack)
                self.messageQueue.addMessage('Result: Attacker wins')
                break

            # roll for combat
            troopDiffA, troopDiffB = self.doRolls(rollsA, rollsB)
            terrAttacker.troops -= troopDiffA
            terrDefender.troops -= troopDiffB

        return attackPath

    def doRolls(self, rollsA, rollsB):
        troopDiffA = 0
        troopDiffB = 0
        pArolls = []
        pBrolls = []

        for r in range(rollsA):
            pArolls.append(random.randint(1,6))
        for r in range(rollsB):
            pBrolls.append(random.randint(1,6))
        
        pArolls = list(reversed(sorted(pArolls)))
        pBrolls = list(reversed(sorted(pBrolls)))

        if self.printAttackDetails:
            self.messageQueue.addMessage(f' Rolls A: {pArolls}, Rolls B: {pBrolls}')

        for i,dice in enumerate(pBrolls):
            if i <= len(pArolls)-1:
                if dice >= pArolls[i]:
                    troopDiffA += 1
                else:
                    troopDiffB += 1
        
        return troopDiffA, troopDiffB 

    def printScreen(self, stdscr):
        # print the map
        for r,line in enumerate(self.board.maptxt):
            stdscr.addstr(r,0, line)

        # print troops with color
        self.board.printTroops(stdscr)

        # print the turn indicator
        for i,p in enumerate(self.player_list):
            status = f'Player {p.myname}'
            if p.myname == str(self.currentPlayer+1):
                if self.currentPhase == 1:
                    status += ' place troops'
                elif self.currentPhase == 2:
                    status += ' attack'
                elif self.currentPhase == 3:
                    status += ' fortify'
            stdscr.addstr(self.TurnIndicatorLocation[0]+i, self.TurnIndicatorLocation[1],
                      status, p.color)

        # print attack path
        for pos in self.currentAttackPath:
            stdscr.addstr(pos[0], pos[1], self.attackPathToken, self.currentAttackColor)

        # print message queue
        for r,msg in enumerate(self.messageQueue.msgs):
            stdscr.addstr(self.debugPanel[0]+r, self.debugPanel[1], msg)

    def getPlayerFromColor(self, color):
        for p in self.player_list:
            if p.color == color:
                return p
        self.messageQueue.addMessage(f'ERROR: Color does not exist -> {color}')
        return None


if __name__ == "__main__":
    g = Game()
    curses.wrapper(g.start)