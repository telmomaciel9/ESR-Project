# bootstrap.py
import socket
import threading
import time
import json  # for JSON serialization


class Bootstrap:
    def __init__(self,bootstrap_ip,bootstrap_port):
        self.bootstrap_ip=bootstrap_ip
        self.bootstrap_port=bootstrap_port
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}
    '''
    def read_neighbours_file(self,path):
        #bootstrap_teste2"
        with open(path, "r") as f:    #config   
            for line in f: 
                nodo,viz = line.split(":")
                for v in viz:
                    self.dic_with_neighbours[nodo]=viz.strip().split(";")
    '''

    def read_neighbours_file(self,path):
        with open(path,"r") as f:
            self.dic_with_neighbours = json.load(f)


    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.bootstrap_ip, self.bootstrap_port))
            return server_socket
        except socket.error as e:
            print(f"Bootstrap : Socket Error: {e}")

    '''
    def bootstrap_aux(self,client_socket,client_address):
        if(client_address[0] in self.dic_with_neighbours.keys()):
            data_json = json.dumps(self.dic_with_neighbours[client_address[0]])
            client_socket.send(data_json.encode())
            #client_socket.close()
    
    def bootstrap(self,client_socket,client_address):
        try:
            while not self.wg.is_set():
                
                self.bootstrap_aux(client_socket, client_address)
        except Exception as e:
            print(f"An error occurred while handling client: {e}")
        finally:
            client_socket.close()
    '''

    def bootstrap(self, client_socket, client_address):
        print(f"BOOTSTRAP: Connected to: {client_address}")
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                if not data:
                    break

                for i in range(5):
                    time.sleep(2)
                    print(f"BOOTSTRAP: Received message from {client_address}: {data}")
                    response = "NOT A NODE"

                    if(client_address[0] in self.dic_with_neighbours.keys()):
                        response = json.dumps(self.dic_with_neighbours[client_address[0]])

                client_socket.send(response.encode())
        except Exception as e:
            print(f"BOOTSTRAP : An error occurred in the bootstrap function: {e}")
        finally:
            print(f"BOOTSTRAP : Connection closed with {client_address}")
            client_socket.close()
            #self.clients.remove(client_socket)

    def start(self):
        try:
            server_socket = self.create_and_bind_socket()
            server_socket.listen(5)
            print(f"BOOTSTRAP : Estou a ouvir no ip: {self.bootstrap_ip} e na porta: {self.bootstrap_port} ")
            
            self.read_neighbours_file("bootstrapteste.json")

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                self.threads.append(threading.Thread(target=self.bootstrap, args=(client_socket, client_address)))

                for thread in self.threads:
                    thread.start()
                for thread in self.threads:
                    thread.join()
        except Exception as e:
            print(f"BOOTSTRAP : An error occurred in the start function: {e}")
        finally:
            if server_socket:
                server_socket.close()
