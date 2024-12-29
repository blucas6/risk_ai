from messagequeue import MessageQueue

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
