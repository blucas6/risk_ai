
class MessageQueue:
    def __init__(self, printPos, termrows, termcols):
        self.msgs = []
        self.printPos = printPos
        self.maxMsgs = termrows - printPos[0]
        self.maxcols = termcols - printPos[1]

    def listToString(self, mylist):
        msg = ' ['
        for item in mylist:
            msg += str(item)+' '
        msg += ']'
        return msg

    def addMessage(self, msg, mylist=[], mylist2d=[]):
        if mylist:
            msg += self.listToString(mylist)
        if mylist2d:
            for i in range(mylist2d):
                msg += self.listToString()
        while len(msg) > self.maxcols:
            self.msgs.append(msg[:self.maxcols-1])
            msg = msg[self.maxcols-1:]
        self.msgs.append(msg)
        while len(self.msgs) > self.maxMsgs:
            del self.msgs[0]
