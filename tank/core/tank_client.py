import socket
import json
import sys
from typing import Optional

from planets.code.planet import Planet
from util.logger import Logger
from util.direction import Direction


class TankClient:
    """
    Communications client of the tank robot.
    Handles sending and receiving messages to and from the mothership.
    """

    mothership_ip: str
    mothership_port: int
    logger: Logger

    def __init__(self, mothership_ip: str, mothership_port: int, logger: Logger):
        self.logger = logger
        self.mothership_ip = mothership_ip
        self.mothership_port = mothership_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def wait_for_server_connection(self):
        """
        Loops until a connection with the mothership has been established.
        """

        self.logger.log(f"Attempting to connect to mothership server at {self.mothership_ip}:{self.mothership_port}...")
        while True:
            try:
                self.client_socket.connect((self.mothership_ip, self.mothership_port))

                try:
                    self.send_message({"type": "connection_request"})
                    response = json.loads(self.client_socket.recv(1024).decode('utf-8'))
                    if not response['type'] == "connection_approval":
                        self._handle_mothership_rejection()
                    else:
                        self.logger.log(f"Connected to mothership at {self.mothership_ip}:{self.mothership_port}")
                        return
                except (socket.error, socket.timeout):
                    self._handle_mothership_rejection()

            except socket.error as e:
                self.logger.log(f"Failed to connect to server: {e}. Trying again.")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _handle_mothership_rejection(self):
        """
        Handles the event of the mothership rejecting a connection attempt during wait_for_server_connection()
        """

        self.logger.log("Mothership rejected the connection. Trying again.")
        self.client_socket.close()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_message(self, message: dict):
        """
        Tries to send the given message to the mothership. Calls sys.exit(1) if the message fails to send.
        """

        try:
            message_str = json.dumps(message)
            self.client_socket.sendall(message_str.encode('utf-8'))

            if message['type'] == "internal_planet":
                self.logger.log(f"Sent internal planet to mothership")
            else:
                self.logger.log(f"Sent message to mothership: {message}")
        except socket.error as e:
            self.logger.log(f"Failed to send message: {e}")
            sys.exit(1)

    def receive_message(self) -> Optional[dict]:
        """
        Tries to receive a message from the mothership.
        Returns None if no message was received.
        Calls sys.exit(1) if a socket error occurs.
        """

        try:
            response = self.client_socket.recv(1024)
            if response:
                response_message = json.loads(response.decode('utf-8'))
                self.logger.log(f"Received message from mothership: {response_message}")
                return response_message
        except socket.error as e:
            self.logger.log(f"Failed to receive message: {e}")
            sys.exit(1)

        return None

    def get_response_of_type(self, response_type: str) -> Optional[dict]:
        """
        Tries to receive a message from the mothership of the given response type.
        Returns None if no message or a message of an incorrect type was received.
        """

        response = self.receive_message()
        if response:
            if response["type"] != response_type:
                self.logger.log(f"Received unexpected response type: {response['type']}")
            else:
                return response
        return None

    # NODE ARRIVAL
    def send_node_arrival(self):
        message = {
            "type": "node_arrival"
        }
        self.send_message(message)

    def get_node_arrival_response(self) -> Optional[dict]:
        return self.get_response_of_type("arrival_response")

    # PATH CHOSEN
    def send_path_chosen(self, direction: Direction):
        message = {
            "type": "path_chosen",
            "direction": direction.name
        }
        self.send_message(message)

    def get_path_chosen_response(self) -> Optional[dict]:
        return self.get_response_of_type("path_chosen_response")

    # INTERNAL PLANET
    def send_internal_planet_update(self, planet: Planet, cur_node: str):
        message = {
            "type": "internal_planet",
            "planet": planet.to_dict(),
            "cur_node": cur_node
        }
        self.send_message(message)
