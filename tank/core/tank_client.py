import socket
import json


class TankClient:
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            print(f"Connected to server at {self.server_ip}:{self.server_port}")
        except socket.error as e:
            print(f"Failed to connect to server: {e}")

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


if __name__ == "__main__":
    tank_client = TankClient(server_ip='127.0.0.1', server_port=65432)

    tank_client.connect_to_server()

    message = {"command": "move", "direction": "forward", "distance": 10}
    tank_client.send_message(message)

    tank_client.receive_response()

    tank_client.close_connection()