import socket
import threading
import sys
import time
import json
from Message import Message


class TCPSender:
    def __init__ (self,ip):
        self.ip_to_connect = ip
        try:
            self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except Exception as e:
            print(f"An error occurred while trying to create and connect to the server: {e}")
        self.my_neighbours = dict()
    
    def start(self):
        #self.client_socket.connect((self.ip_to_connect,3000))
        #message = Message("1",self.client_socket.getsockname()[0], self.ip_to_connect,self.client_socket.getsockname()[0])
        #serialized_message = json.dumps(message.__dict__)
        #self.client_socket.send(serialized_message.encode())
        #data = self.client_sockets.recv(1024)
        #message_data = json.loads(data.decode())
        #if message_data["id"] == "2":
        #    info = message_data["data"]
        #    src = message_data["src"]

        #    # Remove brackets and split the string into a list
        #    values = info[1:-1].split(', ')

        #    # Remove double quotes from each element
        #    cleaned_values = [value.strip('"') for value in values]
        #                
        #    for v in cleaned_values:
        #        self.my_neighbours[v] = False

        #mensagem = Message("4", host_addr, (client_address,3000),
        #                                       "Recebi a tua mensagem, vou terminar a conexao")
        #self.client_socket.send((json.dumps(messagem.__dict__)).encode())

        self.client_socket.connect((self.ip_to_connect,4000))
        time_now = int(time.time()*1000)
        ip = self.client_socket.getsockname()[0]
        
        lista = [1,time_now,0]
        message = Message("8",self.client_socket.getsockname()[0], self.ip_to_connect,lista)
        serialized_message = json.dumps(message.__dict__)
        self.client_socket.send(serialized_message.encode())
        print(message)

        
if __name__ == "__main__":
    
    connect_to_ip = sys.argv[1]

    cliente = TCPSender(connect_to_ip)
    cliente.start()
            