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

    def read_neighbours_file(self,path):
       with open(path, "r") as f:
            data = json.load(f)
            for node in data["nodes"]:
                ip = node["ip"]
                neighbors = node["neighbors"]
                self.dic_with_neighbours[ip] = neighbors


    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.bootstrap_ip, self.bootstrap_port))
            return server_socket
        except socket.error as e:
            print(f"Bootstrap : Socket Error: {e}")


    '''
    def send_data(self, client_socket, client_address):
        while not self.wg.is_set():
            # Implement your logic for sending data here
            time.sleep(2)
            data_to_send = "Not a Node"
            if(client_address[0] in self.dic_with_neighbours.keys()):
                data_to_send = json.dumps(self.dic_with_neighbours[client_address[0]])
            client_socket.send(data_to_send.encode())

    def receive_data(self, client_socket, client_address):
        while not self.wg.is_set():
            # Implement your logic for receiving data here
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Bootstrap: Received message from {client_address}: {data.decode()}")



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

    '''
    def bootstrap(self, client_socket, client_address):
        print(f"BOOTSTRAP: Connected to: {client_address}")
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                if not data:
                    break
                print(type(self.dic_with_neighbours.keys()))
                print(type(client_address[0])) 
                for i in range(5):
                    time.sleep(2)
                    print(f"BOOTSTRAP: Received message from {client_address}: {data}")
                    response = "NOT A NODE"

                    print(client_address[0])
                    print(self.dic_with_neighbours.keys())
                    print(self.dic_with_neighbours)
                    if(client_address[0] in self.dic_with_neighbours.keys()):
                        print("oalalalala")
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
            print(f"BOOTSTRAP: Listening on {self.bootstrap_ip}:{self.bootstrap_port}")

            self.read_neighbours_file("bootstrapteste.json")

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                '''
                self.threads.append(threading.Thread(target=self.bootstrap, args=(client_socket, client_address)))
                for thread in self.threads:
                    thread.start()
                '''
                thread = threading.Thread(target=self.bootstrap, args=(client_socket, client_address))
                thread.start()
                
        except Exception as e:
            print(f"BOOTSTRAP: An error occurred in the start function: {e}")
        finally:
            if server_socket:
                server_socket.close()