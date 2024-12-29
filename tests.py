from main import Game

def validate(expA, expB, la, lb, g: Game):
    a, b = g.doRolls(la, lb)
    print(f'Test {la} vs. {lb}...', end='')
    if expA == a and expB == b:
        print('passed')
        return
    print('failed!')

if __name__ == '__main__':
    g = Game()

    # A 1 D 1
    validate(1, 0, [1], [1], g)
    validate(1, 0, [1], [6], g)
    # A 1 D 1 1
    validate(1, 0, [1], [1,1], g)
    validate(1, 0, [1], [6,1], g)

    # A 2 D 1
    validate(1, 0, [1,1], [1], g)
    validate(0, 1, [4,1], [1], g)
    validate(1, 0, [6,6], [6], g)

    # A 2 D 2
    validate(2, 0, [1,1], [1,1], g)
    validate(2, 0, [6,6], [6,6], g)
    validate(0, 2, [6,6], [1,1], g)
    validate(1, 1, [4,2], [4,1], g)
    validate(1, 1, [6,1], [4,1], g)

    # A 3 D 1
    validate(0, 1, [6,1,1], [4], g)
    validate(1, 0, [4,1,1], [4], g)

    # A 3 D 2
    validate(2, 0, [1,1,1], [1,1], g)
    validate(2, 0, [6,6,6], [6,6], g)
    validate(1, 1, [6,3,1], [6,1], g)
    validate(1, 1, [5,3,1], [6,1], g)
    validate(0, 2, [2,2,2], [1,1], g)
