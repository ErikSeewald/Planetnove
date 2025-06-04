from mothership.mothership import Mothership


def init():
    mothership = Mothership()
    mothership.loop()


if __name__ == "__main__":
    init()
