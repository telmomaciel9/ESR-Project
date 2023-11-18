import socket
import threading
import time
import json  # for JSON serialization
#from Message import Message

class Bootstrap:
    def __init__(self, ):
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}

    def read_neighbours_file(self, path):
        with open(path, "r") as f:
            data = json.load(f)
            for node in data["nodes"]:
                ip = node["ip"]
                neighbors = node["neighbors"]
                #newKey = tuple(neighbors)
                self.dic_with_neighbours[tuple(ip)] = neighbors
                
    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(("0.0.0.0", 3000))
            return server_socket
        except socket.error as e:
            print(f"Bootstrap : Socket Error: {e}")

    def send_data(self, client_socket, client_address):
        while not self.wg.is_set():
            time.sleep(2)
            response = "NOT A NODE"
            #message = Message()

            print(client_address[0])
            for key,value in self.dic_with_neighbours.items():
                for k in key:
                    if client_address[0] == k:
                        if isinstance(value, list):
                            response = json.dumps(value)
                        else:
                            response = str(value)

            '''
                message.addType(2)
                message.addBody(json.dumps(self.dic_with_neighbours[client_address[0]]))

            else:
                message.addTypeAndBody(3,"YOU ARE NOT A NODE")
            '''
            print(response)
            try:
                client_socket.send(response.encode())
                #client_socket.send(message)
            except Exception as e:
                print(f"BOOTSTRAP: An error occurred while sending data to {client_address}: {e}")
                break


    #def process_data(self, data, client_socket,client_address):
    #    if data == 

    def receive_data(self, client_socket, client_address):
        while not self.wg.is_set():
            data = client_socket.recv(1024)
            if not data:
                break
            
            print(f"BOOTSTRAP: Received message from {client_address}: {data.decode()}")

            if data.decode() == "3":
                self.wg.set() 
     #       self.process_data(data, client_socket,client_address)

    def bootstrap(self, client_socket, client_address):
        print(f"BOOTSTRAP: Connected to: {client_address}")
        try:
            send_thread = threading.Thread(target=self.send_data, args=(client_socket, client_address))
            receive_thread = threading.Thread(target=self.receive_data, args=(client_socket, client_address))

            send_thread.start()
            receive_thread.start()

            send_thread.join()
            receive_thread.join()

        except Exception as e:
            print(f"BOOTSTRAP: An error occurred in the bootstrap function: {e}")
        finally:
            print(f"BOOTSTRAP: Connection closed with {client_address}")
            client_socket.close()

    def start(self):
        try:
            server_socket = self.create_and_bind_socket()
            server_socket.listen(10)
            #print(f"BOOTSTRAP: Listening on {self.bootstrap_ip}:{self.bootstrap_port}")

            self.read_neighbours_file("bootstrapteste.json")
            #print(self.dic_with_neighbours)

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                thread = threading.Thread(target=self.bootstrap, args=(client_socket, client_address))
                thread.start()

        except Exception as e:
            print(f"BOOTSTRAP: An error occurred in the start function: {e}")
        finally:
            if server_socket:
                server_socket.close()



