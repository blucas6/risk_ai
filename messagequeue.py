import os

class MessageQueue:
    def __init__(self, printPos, termrows, termcols, logfile):
        self.msgs = []
        self.printPos = printPos
        self.maxMsgs = termrows - printPos[0]
        self.maxcols = termcols - printPos[1]
        self.logfile = logfile
        self.logarea = 'logs'
        if not os.path.exists(self.logarea):
            os.makedirs(self.logarea)
        self.fo = open(os.path.join(self.logarea,self.logfile), 'w+')

    def endQueue(self):
        if not self.fo.closed:
            self.fo.close()

    def listToString(self, mylist):
        msg = ' ['
        for item in mylist:
            msg += str(item)+' '
        msg += ']'
        return msg
    
    def pushMsgToQueue(self, msg):
        self.msgs.append(msg)
        if not self.fo.closed:
            self.fo.write(msg+'\n')

    def addMessage(self, msg, mylist=[], mylist2d=[]):
        if mylist:
            msg += self.listToString(mylist)
        if mylist2d:
            for i in range(mylist2d):
                msg += self.listToString()
        while len(msg) > self.maxcols:
            self.pushMsgToQueue(msg[:self.maxcols-1])
            msg = msg[self.maxcols-1:]
        self.pushMsgToQueue(msg)
        while len(self.msgs) > self.maxMsgs:
            del self.msgs[0]
