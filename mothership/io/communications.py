import json
import struct
import sys
import threading
import time
from collections import deque
from typing import Optional, Any

from mothership.gui.update_event import UpdateEvent, TankPlanetUpdate
from mothership.planet_state.planet_state_manager import PlanetStateManager
import socket

from planets.code.planet import Planet
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
    last_msg_to_tank: Optional[dict]

    logger: Logger

    unprocessed_tank_messages = deque[dict]
    lock: threading.Lock

    _COMS_CONFIG_PATH: str = "coms_config.json"

    tank_disconnect_async_due: bool

    def __init__(self, planet_manager: PlanetStateManager, logger: Logger):
        self.logger = logger
        self._load_coms_config()

        self.planet_manager = planet_manager
        self.tank_socket = None
        self.tank_address = None
        self.tank_disconnect_async_due = False
        self.last_msg_to_tank = None

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
            self.tank_socket.settimeout(0.4)
            time.sleep(1) # Give connection some time to be fully set up on both ends, weird errors otherwise
            self.logger.log(f"Accepted connection from {tank_address}")
            return True
        else:
            self.logger.log(f"Rejected connection from {tank_address}")
            tank_socket.close()
            return False

    def disconnect_tank(self):
        # Async so that we don't break the async socket update thread
        self.tank_disconnect_async_due = True

    def _async_tank_disconnect(self):
        if self.tank_socket is None:
            return

        self.tank_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        self.tank_socket.close()
        self.tank_socket = None
        self.tank_address = None

    def update(self) -> list[UpdateEvent]:
        # Receive messages asynchronously
        receive_thread = threading.Thread(target=self.update_tank_socket, daemon=True)
        receive_thread.start()

        # Process messages synchronously
        events: list[UpdateEvent] = list()
        while True:
            with self.lock:
                if self.unprocessed_tank_messages:
                    msg = self.unprocessed_tank_messages.pop()
                else:
                    return events
            events.extend(self.handle_tank_message(msg))

    def update_tank_socket(self):
        if self.tank_socket is None:
            return

        if self.tank_disconnect_async_due:
            self._async_tank_disconnect()
            self.tank_disconnect_async_due = False
            return

        try:
            message_buffer = []

            while True:
                # Receive data in chunks
                data = self.tank_socket.recv(1024)
                if not data:
                    break

                message_buffer.append(data.decode('utf-8'))
                message = ''.join(message_buffer)

                if message == "ping":
                    # Handle 'ping' message asynchronously
                    self.tank_socket.sendall(b"pong")
                    break

                try:
                    # Attempt to parse message as JSON
                    json_message = json.loads(message)
                    self.unprocessed_tank_messages.append(json_message)
                    break
                except json.JSONDecodeError:
                    # JSON not yet complete -> continue receiving data
                    continue

        except socket.timeout:
            pass

    def handle_tank_message(self, message: dict) -> list[UpdateEvent]:
        events: list[UpdateEvent] = list()

        if message['type'] == "internal_planet":
            self.logger.log(f"Processing tank internal planet message")
            events.extend(self.handle_internal_planet_msg(message))
        else:
            self.logger.log(f"Processing message from tank: {message}")

            if message['type'] == "node_arrival":
                self.handle_on_arrival(message)

            elif message['type'] == "path_chosen":
                self.handle_path_chosen(message)

        return events

    @staticmethod
    def handle_internal_planet_msg(message: dict) -> list[UpdateEvent]:
        return [
            TankPlanetUpdate(planet=Planet.from_dict(message['planet']), cur_node=message['cur_node'])
        ]

    def handle_on_arrival(self, _message: dict):
        last_message_was_approval = (self.last_msg_to_tank['type'] == "path_chosen_response"
                                     and self.last_msg_to_tank['request_response']['is_approved'])

        if last_message_was_approval or not self.planet_manager.tank.reached_first_node:
            self.planet_manager.on_tank_arrival()
            self.send_msg_to_tank(self.planet_manager.tank_arrival_response())
        else:
            self.send_msg_to_tank(
                message={"type": "error", "msg": "Last departure was not approved by the mothership"})

    def handle_path_chosen(self, message: dict):
        response = self.planet_manager.tank_path_chosen_response(Direction.from_str(message['direction']))
        self.send_msg_to_tank(response)

    def send_msg_to_tank(self, message: dict):
        self.tank_socket.sendall(json.dumps(message).encode('utf-8'))
        self.logger.log(f"Sent message to tank: {message}")
        self.last_msg_to_tank = message

    def send_tank_start_message(self):
        message = {
            "type": "start"
        }
        self.send_msg_to_tank(message)
