import json
from typing import Optional, Any
from mothership.planet_state.planet_state_manager import PlanetStateManager
import socket


class Communications:
    """
    Class managing the mother ship's communications with entities like the tank robot.
    """

    planet_manager: PlanetStateManager
    server_socket: socket
    tank_socket: Optional[socket]
    tank_address: Optional[Any]

    def __init__(self, planet_manager: PlanetStateManager):
        self.planet_manager = planet_manager

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', 65432))
        self.server_socket.listen(1)

        self.tank_socket = None
        self.tank_address = None

        #self.connect_tank()

        # conn.close()
        # server_socket.close()

    def connect_tank(self):
        self.tank_socket, self.tank_address = self.server_socket.accept()
        print(f"Connected by {self.tank_address}")

        self.tank_socket.settimeout(1.0)

    def update(self):
        self.update_tank_socket()

    def update_tank_socket(self):
        if self.tank_socket is None:
            return

        try:
            data = self.tank_socket.recv(1024)
            if data:
                message = json.loads(data.decode('utf-8'))
                print("Received message:", message)

                # Optionally send a response
                response = json.dumps({"status": "Message received"})
                self.tank_socket.sendall(response.encode('utf-8'))
            else:
                print("No new messages.")
        except socket.timeout:
            print("No new messages within the last second.")

