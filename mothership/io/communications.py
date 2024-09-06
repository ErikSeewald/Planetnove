import json
import struct
import threading
import time
from collections import deque
from typing import Optional, Any

from mothership.update_event import UpdateEvent, TankPlanetUpdate, TankConnectionLost
from mothership.planet_state.planet_state_manager import PlanetStateManager
import socket

from planets.code.planet import Planet
from planets.code.route import Route
from util.direction import Direction
from util.logger import Logger


class Communications:
    """
    Class managing the mother ship's communications with entities like the tank robot.
    """

    _COMS_CONFIG_PATH: str = "coms_config.json"

    # Server
    server_socket: socket
    server_ip: str
    server_port: int

    # Tank
    tank_socket: Optional[socket]
    tank_address: Optional[Any]
    last_msg_to_tank: Optional[dict]

    # Threading
    unprocessed_tank_messages = deque[dict]
    lock: threading.Lock

    # Does the asynchronous tank disconnect function need to be run next iteration?
    tank_disconnect_async_due: bool

    # Does a tank lost event need to be returned during the next synchronous update iteration?
    tank_lost_event_due: bool

    # Other modules
    planet_manager: PlanetStateManager
    logger: Logger

    def __init__(self, planet_manager: PlanetStateManager, logger: Logger):
        self.logger = logger
        self._load_coms_config()

        self.planet_manager = planet_manager

        # Tank
        self.tank_socket = None
        self.tank_address = None
        self.tank_disconnect_async_due = False

        # Threading
        self.unprocessed_tank_messages = deque()
        self.lock = threading.Lock()
        self.tank_lost_event_due = False
        self.last_msg_to_tank = None

    def _load_coms_config(self):
        """
        Loads the communications configuration file from the default path.
        """

        self.logger.log(f"Loading {self._COMS_CONFIG_PATH}...")
        config = json.loads(open(self._COMS_CONFIG_PATH, "r").read())

        self.server_ip = config["mothership_ip"]
        self.server_port = config["mothership_port"]

        self.logger.log(f"Setting up server with ip: '{self.server_ip}' on port '{self.server_port}'...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(2)

    def update(self) -> list[UpdateEvent]:
        """
        Updates all communications and handles the received messages. Note that this function
        spawns an asynchronous thread for receiving communications with a timeout of 0.5 seconds.
        The update function should only be called ever 0.5. While the message receiving is
        asynchronous, each time this function is called the accumulated messages get handled synchronously.

        :returns: Update events that occurred during communications
        """

        events: list[UpdateEvent] = list()

        # If tank closed the connection, return and let the mothership know
        if self.tank_lost_event_due:
            events.append(TankConnectionLost(tank_ip=self.tank_address))
            self.handle_tank_lost_event()
            return events

        # Receive messages asynchronously
        receive_thread = threading.Thread(target=self.update_tank_socket, daemon=True)
        receive_thread.start()

        # Process messages synchronously
        while True:
            with self.lock:
                if self.unprocessed_tank_messages:
                    msg = self.unprocessed_tank_messages.pop()
                else:
                    return events
            events.extend(self.handle_tank_message(msg))

    # --- TANK SOCKET HANDLING ---
    def try_connect_tank(self, expected_ip: str) -> bool:
        """
        Tries to connect a tank client with the given ip to the tank socket.
        Returns whether or not a connection was made.
        """

        # Try to connect something
        try:
            tank_socket, tank_address = self.server_socket.accept()
        except TimeoutError:
            self.logger.log(f"Timed out while attempting to connect")
            return False

        self.logger.log(f"Connection attempt from {tank_address}")

        # See if the ip matches
        if tank_address[0] == expected_ip:
            self.tank_socket = tank_socket
            self.tank_address = tank_address
            self.tank_socket.settimeout(0.5)
            time.sleep(0.5)  # Give connection some time to be fully set up on both ends, weird errors otherwise
            self.logger.log(f"Accepted connection from {tank_address}")
            return True
        else:
            self.logger.log(f"Rejected connection from {tank_address}")
            tank_socket.close()
            return False

    def disconnect_tank(self):
        """
        Schedules a tank disconnect for the next asynchronous socket update.
        """

        # Async so that we don't break the async socket update thread
        self.tank_disconnect_async_due = True

    def _async_tank_disconnect(self):
        """
        Disconnects the tank socket. Only to be called by the asynchronous socket update function.
        """

        if self.tank_socket is None:
            return

        self.tank_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        self.tank_socket.close()
        self.tank_socket = None
        self.tank_address = None

    def handle_tank_lost_event(self):
        """
        Handles the event of losing connection to the tank socket.
        """

        self.tank_socket.close()
        self.tank_socket = None
        self.tank_address = None
        self.tank_lost_event_due = False

    def update_tank_socket(self):
        """
        Asynchronously called function that updates the tank socket and stores the received messages
        to be later handled in the synchronous update function.
        """

        if self.tank_socket is None:
            return

        if self.tank_disconnect_async_due:
            self._async_tank_disconnect()
            self.tank_disconnect_async_due = False
            return

        # Try to receive messages. Accept timeouts as the tank not sending any data but look out for
        # ConnectionResetErrors and possible schedule a tank lost event.
        try:
            message_buffer = []

            # Receive data in chunks until: a) no more data is being received or
            # b) a full JSON message can be constructed. In that case, store the message to be handled later.
            while True:
                try:
                    data = self.tank_socket.recv(1024)
                    if not data:
                        break

                    message_buffer.append(data.decode('utf-8'))
                    message = ''.join(message_buffer)

                    try:
                        json_message = json.loads(message)
                        self.unprocessed_tank_messages.append(json_message)
                        break
                    except json.JSONDecodeError:
                        continue  # JSON not yet complete -> continue receiving data
                except ConnectionAbortedError:
                    self.tank_lost_event_due = True
                    break
        except socket.timeout:
            pass
        except ConnectionResetError:
            self.tank_lost_event_due = True

    def send_msg_to_tank(self, message: dict):
        """
        Sends the given message to the tank client, logs it, and saves it to the last_msg_to_tank variable.
        """

        self.tank_socket.sendall(json.dumps(message).encode('utf-8'))
        self.logger.log(f"Sent message to tank: {message}")
        self.last_msg_to_tank = message

    # --- TANK MESSAGE HANDLING ---
    def handle_tank_message(self, message: dict) -> list[UpdateEvent]:
        """
        Handles a single message from the tank client.
        Returns any update events that occurred while handling the message.
        Assumes that the message has a 'type' key.
        """

        events: list[UpdateEvent] = list()

        # Do not log the entire internal planet message every time
        if message['type'] == "internal_planet":
            events.extend(self.handle_tank_internal_planet(message))

        else:
            # Log all other kinds of messages
            self.logger.log(f"Processing message from tank: {message}")

            if message['type'] == "connection_request":
                self.send_msg_to_tank({"type": "connection_approved"})

            elif message['type'] == "node_arrival":
                self.handle_tank_on_arrival(message)

            elif message['type'] == "path_chosen":
                self.handle_tank_path_chosen(message)

            elif message['type'] == "finished_exploring":
                self.handle_tank_finished_exploring(message)

            elif message['type'] == "stuck":
                self.handle_tank_stuck(message)

            elif message['type'] == "path_blocked":
                self.handle_tank_path_blocked(message)

        return events

    def handle_tank_internal_planet(self, message: dict) -> list[UpdateEvent]:
        self.logger.log(f"Processing tank internal planet message")
        return [
            TankPlanetUpdate(planet=Planet.from_dict(message['planet']), cur_node=message['cur_node'],
                             target_node=message['target_node'],
                             target_route=Route.from_dict(message['target_route']),
                             depart_dir=Direction.from_str(message['depart_dir']))
        ]

    def handle_tank_on_arrival(self, _message: dict):
        """
        Handles an arrival message from the tank client. Either sends a tank arrival response with the necessary
        node information or an error message if the tank was not previously approved for departure.
        """

        last_message_was_approval = (self.last_msg_to_tank['type'] == "path_chosen_response"
                                     and self.last_msg_to_tank['request_response']['is_approved'])

        if last_message_was_approval or not self.planet_manager.tank.reached_first_node:
            self.planet_manager.on_tank_arrival()
            self.send_msg_to_tank(self.planet_manager.tank_arrival_response())
        else:
            self.send_msg_to_tank(
                message={"type": "error", "msg": "Last departure was not approved by the mothership"})

    def handle_tank_path_chosen(self, message: dict):
        """
        Handles a path chosen message from the tank client.
        Sends a response either approving or denying the tank's choice based on the planet state manager.
        """

        response = self.planet_manager.tank_path_chosen_response(Direction.from_str(message['direction']))
        self.send_msg_to_tank(response)

    def handle_tank_finished_exploring(self, _message: dict):
        self.logger.log("Tank has finished exploring!")

    def handle_tank_stuck(self, _message: dict):
        self.logger.log("Tank is stuck!")

    def handle_tank_path_blocked(self, _message: dict):
        self.planet_manager.handle_tank_path_blocked()

    def send_tank_start_message(self):
        """
        Sends a start message to the tank client. Before the start message, the tank should be entirely
        idle and waiting for messages.
        """

        message = {
            "type": "start"
        }
        self.send_msg_to_tank(message)
