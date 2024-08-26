import json

from util.logger import Logger
from tank.core.tank_client import TankClient
from tank.core.tank_robot import TankRobot

_COMS_CONFIG_PATH = "coms_config.json"


def init():
    logger = Logger()

    # TANK CLIENT
    logger.log(f"Loading {_COMS_CONFIG_PATH}...")
    config = json.loads(open(_COMS_CONFIG_PATH, "r").read())

    mothership_ip = config["mothership_ip"]
    mothership_port = config["mothership_port"]

    tank_client = TankClient(mothership_ip, mothership_port, logger)
    tank_client.wait_for_server_connection()

    logger.log("Waiting for the mothership to send a start signal...")
    while True:
        msg = tank_client.receive_message()
        if msg:
            if msg['type'] == "start":
                logger.log("Received start signal")
                break
            else: logger.log(f"Received a message that was not a start signal: {msg}")

    # TANK ROBOT
    tank = TankRobot(tank_client, logger)
    tank.core_loop()


if __name__ == "__main__":
    init()
