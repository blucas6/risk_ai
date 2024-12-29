from messagequeue import MessageQueue

class EndGameStats:
    def __init__(self, winner, totalturns, player_list, current_game):
        self.winner = winner
        self.totalTurns = totalturns
        self.totalTroops = sum(p.placedtroops for p in player_list)
        self.player_list = player_list
        self.current_game = current_game

    # Adds the stats to the message queue
    #  If lastgame is true, it will print the total session stats instead
    def printInfo(self, msgqueue: MessageQueue, lastgame=False):
        if lastgame:
            msgqueue.addMessage(f'** End of {self.current_game} Game Session **')
            for p in self.player_list:
                msgqueue.addMessage(f' Player {p.myname} Wins: {p.gameswon} ({round((p.gameswon/self.current_game)*100,2)}%)')
                if p.totalAttackRatio[1] == 0:
                    ratio = 0
                else:
                    ratio = round((p.totalAttackRatio[0]/p.totalAttackRatio[1])*100,2)
                msgqueue.addMessage(f'  Total Attack Winrate: {ratio}% [{p.totalAttackRatio[0]}/{p.totalAttackRatio[1]}]')
                if p.totalDefendRatio[1] == 0:
                    ratio = 0
                else:
                    ratio = round((p.totalDefendRatio[0]/p.totalDefendRatio[1])*100,2)
                msgqueue.addMessage(f'  Total Defend Winrate: {ratio}% [{p.totalDefendRatio[0]}/{p.totalDefendRatio[1]}]')
                msgqueue.addMessage(f'  Highest Territories: {p.totalmaxterritories}')
                msgqueue.addMessage(f'  Highest Troops: {p.totalplacedtroops}')
        else:
            msgqueue.addMessage(f'**Winner: Game {self.current_game} is Player {self.winner}!**')
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
