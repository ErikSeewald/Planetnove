import json
import threading
import time
from collections import deque
from typing import Optional, Any
from mothership.planet_state.planet_state_manager import PlanetStateManager
import socket

from util.direction import Direction
from util.logger import Logger


class Communications:
    """
    Class managing the mother ship's communications with entities like the tank robot.
    """

    planet_manager: PlanetStateManager
    server_socket: socket
    server_ip: str
    server_port: int
    tank_socket: Optional[socket]
    tank_address: Optional[Any]

    logger: Logger

    unprocessed_tank_messages = deque[dict]
    lock: threading.Lock

    _COMS_CONFIG_PATH: str = "coms_config.json"

    def __init__(self, planet_manager: PlanetStateManager, logger: Logger):
        self.logger = logger
        self._load_coms_config()

        self.planet_manager = planet_manager
        self.tank_socket = None
        self.tank_address = None

        self.unprocessed_tank_messages = deque()
        self.lock = threading.Lock()

        # conn.close()
        # server_socket.close()

    def _load_coms_config(self):
        self.logger.log(f"Loading {self._COMS_CONFIG_PATH}...")
        config = json.loads(open(self._COMS_CONFIG_PATH, "r").read())

        self.server_ip = config["mothership_ip"]
        self.server_port = config["mothership_port"]

        self.logger.log(f"Setting up server with ip: '{self.server_ip}' on port '{self.server_port}'...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(2)

    def try_connect_tank(self, expected_ip: str) -> bool:
        try:
            tank_socket, tank_address = self.server_socket.accept()
        except TimeoutError:
            self.logger.log(f"Timed out while attempting to connect")
            return False

        self.logger.log(f"Connection attempt from {tank_address}")

        if tank_address[0] == expected_ip:
            self.tank_socket = tank_socket
            self.tank_address = tank_address
            self.tank_socket.settimeout(0.5)
            time.sleep(1) # Give connection some time to be fully set up on both ends, weird errors otherwise
            self.logger.log(f"Accepted connection from {tank_address}")
            return True
        else:
            self.logger.log(f"Rejected connection from {tank_address}")
            tank_socket.close()
            return False

    def update(self):
        # Receive messages asynchronously
        receive_thread = threading.Thread(target=self.update_tank_socket, daemon=True)
        receive_thread.start()

        # Process messages synchronously
        while True:
            with self.lock:
                if self.unprocessed_tank_messages:
                    msg = self.unprocessed_tank_messages.pop()
                else:
                    return
            self.handle_tank_message(msg)

    def update_tank_socket(self):
        if self.tank_socket is None:
            return

        try:
            data = self.tank_socket.recv(1024)
            if data:
                message = data.decode('utf-8')

                if message == "ping":
                    # Ping is allowed to be handled asynchronously
                    self.tank_socket.sendall(b"pong")
                else:
                    json_message = json.loads(message)
                    self.unprocessed_tank_messages.append(json_message)
        except socket.timeout:
            pass # Socket timeout of 1 second

    def handle_tank_message(self, message: dict):
        self.logger.log(f"Processing message from tank: {message}")

        if message['type'] == "node_arrival":
            self.planet_manager.on_tank_arrival()
            self.send_msg_to_tank(self.planet_manager.tank_arrival_response())

        if message['type'] == "path_chosen":
            response = self.planet_manager.tank_path_chosen_response(Direction.from_str(message['direction']))
            self.send_msg_to_tank(response)

    def send_msg_to_tank(self, message: dict):
        self.tank_socket.sendall(json.dumps(message).encode('utf-8'))
        self.logger.log(f"Sent message to tank: {message}")

    def send_tank_start_message(self):
        message = {
            "type": "start"
        }
        self.send_msg_to_tank(message)
