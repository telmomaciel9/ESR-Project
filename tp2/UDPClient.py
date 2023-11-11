import socket
import threading
import sys

class Client:

    def __init__(self, connectTo_ip,connectTo_port):
        self.connectTo_ip = connectTo_ip
        self.connectTo_port = connectTo_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_data(self, data, server_addr):
        self.client_socket.sendto(data.encode(), server_addr)

    def receive_data(self, buffer_size=1024):
        return self.client_socket.recv(buffer_size).decode()

    def close(self):
        self.client_socket.close()

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python client.py <server_ip:server_port>")
        sys.exit(1)

    aux = sys.argv[1].split(":")
    server_ip = aux[0]
    server_port = int(aux[1])

    client   = Client(server_ip, server_port)

    message = "Hello, Server!"
 
    client.send_data(message, (server_ip, server_port))

    response = client.receive_data()
    print("Received from server:", response)

    client.close()
