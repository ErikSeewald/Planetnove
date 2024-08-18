from tank.core.tank_robot import TankRobot


def init():
    tank = TankRobot()
    tank.core_loop()


if __name__ == "__main__":
    init()
