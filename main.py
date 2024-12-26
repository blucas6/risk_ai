import curses
from board import Board

class Colors:
    def __init__(self):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.red = curses.color_pair(1)
        self.yellow = curses.color_pair

class Game:
    def __init__(self):
        self.board = Board()

    def run(self, stdscr):
        curses.curs_set(0)
        curses.start_color()
        while True:
            stdscr.clear()

            self.printScreen(stdscr)

            stdscr.refresh()

            event = stdscr.getch()

            if event in (10,13):
                break

            if event == ord('a'):
                self.board

    def printScreen(self, stdscr):
        for r,line in enumerate(self.board.maptxt):
            stdscr.addstr(r,0, line)


if __name__ == "__main__":
    g = Game()
    curses.wrapper(g.run)