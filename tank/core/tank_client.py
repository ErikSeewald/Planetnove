import socket
import json
import time

from tank.core.logger import Logger


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

    def receive_response(self):
        try:
            response = self.client_socket.recv(1024)
            if response:
                response_message = json.loads(response.decode('utf-8'))
                print("Response from server:", response_message)
            else:
                print("No response received.")
        except socket.error as e:
            print(f"Failed to receive response: {e}")

    def close_connection(self):
        self.client_socket.close()
        print("Connection closed.")