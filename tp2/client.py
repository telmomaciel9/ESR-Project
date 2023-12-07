import socket
import threading
import sys
import time
import json
from Message import Message
from tkinter import Tk
from ClienteGUI import ClienteGUI
from RtpPacket import RtpPacket

class Client:
    def __init__ (self,ip):
        self.ip_to_connect = ip
        self.my_neighbours = dict()
        try:
            self.client_socket_sender = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.client_socket_receiver = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.client_socket_receiver.bind(("",4000))
        except Exception as e:
            print(f"An error occurred while trying to create and connect to the server: {e}")
    
    
    def receberMsg(self):
        while True:
            try:
                client_socket, client_address = self.client_socket_receiver.accept()
                print(f"\nCliente [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\ncliente [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
            except Exception as e:
                print(f"\nCliente: An error occcurred while receiving messges: {e}")

    def start(self):
        self.client_socket_receiver.listen(5)
        receive_thread = threading.Thread(target=self.receberMsg)
        receive_thread.start()

        self.client_socket_sender.connect((self.ip_to_connect,4000))
        time_now = int(time.time()*1000)
        ip = self.client_socket_sender.getsockname()[0]
        lista = [1,time_now,0]
        message = Message("8",self.client_socket_sender.getsockname()[0], self.ip_to_connect,lista)
        serialized_message = json.dumps(message.__dict__)
        self.client_socket_sender.send(serialized_message.encode())



if __name__ == "__main__":
    
    connect_to_ip = sys.argv[1]

    cliente = Client(connect_to_ip)
    cliente.start()

    self_addr = '127.0.0.1'

    root = Tk()
    
    # Create a new client
    app = ClienteGUI(root, self_addr, 3000, connect_to_ip, 4000)
    app.master.title("Cliente Exemplo")
    root.mainloop()
            