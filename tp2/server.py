import socket
import threading
import sys
import time

class Server:

    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        # Create a UDP socket for the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.server_ip, self.server_port))

    def processMsg(self, client_address, data_received):
        
        # Printing received message from client
        print(f"Received from {client_address}: {data_received.decode()}")
        
        # Process the data and prepare a answer to client
        response = f"Server received: {data_received.decode()}"
        self.server_socket.sendto(response.encode(), client_address)

'''
    #def start(self):
    #    while 1:
    #        data,address = self.server_socket.recvfrom(1024)
    #        self.processMsg(address,data)                                                                                                         
    #    self.server_socket.close()
'''

if __name__ == "__main__":

    # In Case of giving the wrong command
    if len(sys.argv) != 2:
        println("Usage: python server.py <server_ip:server_port> ")
        sys.exit(1)

    # Splitting the first argument in order to have the server ip and server port
    aux = sys.argv[1].split(":")
    server_ip = aux[0]
    server_port = int(aux[1])

    #creating an object of type server
    server = Server(server_ip,server_port)
    
    while 1:
        data,address = server.server_socket.recvfrom(1024)
         # Process each client request in a new thread
        client_thread = threading.Thread(target=server.processMsg, args=(address, data))
        client_thread.start()                                                                                               
    server.server_socket.close()

