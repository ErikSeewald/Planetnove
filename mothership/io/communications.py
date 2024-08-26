import json
from typing import Optional, Any
from mothership.planet_state.planet_state_manager import PlanetStateManager
import socket

from util.direction import Direction


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

    _COMS_CONFIG_PATH: str = "coms_config.json"

    def __init__(self, planet_manager: PlanetStateManager):
        self._load_coms_config()

        self.planet_manager = planet_manager
        self.tank_socket = None
        self.tank_address = None

        # conn.close()
        # server_socket.close()

    def _load_coms_config(self):
        print(f"Loading {self._COMS_CONFIG_PATH}...")
        config = json.loads(open(self._COMS_CONFIG_PATH, "r").read())

        self.server_ip = config["mothership_ip"]
        self.server_port = config["mothership_port"]

        print(f"Setting up server with ip: '{self.server_ip}' on port '{self.server_port}'...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(1)

    def try_connect_tank(self, expected_ip: str) -> bool:
        try:
            tank_socket, tank_address = self.server_socket.accept()
        except TimeoutError:
            print(f"Timed out while attempting to connect")
            return False

        print(f"Connection attempt from {tank_address}")

        if tank_address[0] == expected_ip:
            print(f"Accepted connection from {tank_address}")
            self.tank_socket = tank_socket
            self.tank_address = tank_address
            self.tank_socket.settimeout(1.0)
            return True
        else:
            print(f"Rejected connection from {tank_address}")
            tank_socket.close()
            return False

    def update(self):
        self.update_tank_socket()

    def update_tank_socket(self):
        if self.tank_socket is None:
            return

        try:
            data = self.tank_socket.recv(1024)
            if data:
                message = data.decode('utf-8')

                if message == "ping":
                    print("Received ping from client.")
                    self.tank_socket.sendall(b"pong")
                else:
                    json_message = json.loads(message)
                    print("Received message:", json_message)
                    self.handle_message(json_message)
            else:
                print("No new messages.")
        except socket.timeout:
            print("No new messages within the last second.")

    def handle_message(self, message: dict):
        response = None

        if message['type'] == "node_arrival":
            self.planet_manager.on_tank_arrival()
            response = json.dumps(self.planet_manager.tank_arrival_response())

        if message['type'] == "path_chosen":
            self.planet_manager.on_tank_path_chosen(Direction.from_str(message['direction']))
            response = json.dumps(self.planet_manager.tank_path_chosen_response())

        if response:
            self.tank_socket.sendall(response.encode('utf-8'))
