import socket
import json
import time
from typing import Optional

from tank.core.logger import Logger
from util.direction import Direction


class TankClient:
    mothership_ip: str
    mothership_port: int
    logger: Logger

    connected_to_server: bool

    def __init__(self, mothership_ip: str, mothership_port: int, logger: Logger):
        self.logger = logger
        self.mothership_ip = mothership_ip
        self.mothership_port = mothership_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_to_server = False

    def wait_for_server_connection(self):
        self.connected_to_server = False
        timeout_seconds = 5
        wait_seconds = 10
        self.client_socket.settimeout(timeout_seconds)

        self.logger.log(f"Attempting to connect to mothership server at {self.mothership_ip}:{self.mothership_port}...")
        while True:
            try:
                self.client_socket.connect((self.mothership_ip, self.mothership_port))

                # Check if server closed the connection
                try:
                    # Ping server, expect pong response
                    self.client_socket.sendall(b'ping')
                    if not self.client_socket.recv(1024).decode('utf-8') == "pong":
                        self.logger.log("Server rejected the connection.")
                        self.client_socket.close()
                    else:
                        self.logger.log(f"Connected to server at {self.mothership_ip}:{self.mothership_port}")
                        self.connected_to_server = True
                        return
                except (socket.error, socket.timeout):
                    self.logger.log("Server rejected the connection.")
                    self.client_socket.close()

            except socket.error as e:
                self.logger.log(f"Failed to connect to server: {e}. \nTrying again in {wait_seconds} seconds")
                time.sleep(wait_seconds)

                # Reinitialize socket
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(timeout_seconds)

    def send_message(self, message: dict):
        try:
            message_str = json.dumps(message)
            self.client_socket.sendall(message_str.encode('utf-8'))
            print("Message sent to server.")
        except socket.error as e:
            print(f"Failed to send message: {e}")

    def receive_response(self) -> Optional[dict]:
        try:
            response = self.client_socket.recv(1024)
            if response:
                response_message = json.loads(response.decode('utf-8'))
                print("Response from server:", response_message)
                return response_message
            else:
                print("No response received.")
                return None
        except socket.error as e:
            print(f"Failed to receive response: {e}")
            return None

    def wait_for_response_of_type(self, response_type: str, attempts: int) -> Optional[dict]:
        for i in range(attempts):
            print(f"Attempt {i}")

            response = self.receive_response()
            if response:
                if response["type"] != response_type:
                    print(f"Received incorrect response type: {response['type']}")
                    continue
                return response
        return None

    def close_connection(self):
        self.client_socket.close()
        print("Connection closed.")

    def send_node_arrival(self):
        message = {
            "type": "node_arrival"
        }
        self.send_message(message)

    def get_node_arrival_response(self) -> Optional[dict]:
        return self.wait_for_response_of_type("arrival_response", attempts=5)

    def send_path_chosen(self, direction: Direction):
        message = {
            "type": "path_chosen",
            "direction": direction.name
        }
        self.send_message(message)

    def get_path_chosen_response(self) -> Optional[dict]:
        return self.wait_for_response_of_type("path_chosen_response", attempts=5)


