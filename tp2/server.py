import socket
import threading
import sys

class Server:

    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        # Create a UDP socket for the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.server_ip, self.server_port))

    def receiveData(self):
        data,address = self.server_socket.recvfrom(1024)
        print(f"Received from {address}: {data.decode()}")


    def start(self):
        self.receiveData()                                                                                                         
        self.server_socket.close()
         
if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python server.py <server_ip> <server_port>")
        sys.exit(1)

    node = Server(sys.argv[1],int(sys.argv[2]))

    node.start()

