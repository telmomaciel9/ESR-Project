import socket
import threading
import time
import json  # for JSON serialization
#from Message import Message
import queue

class Bootstrap:
    def __init__(self, ):
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}
        self.receive_queue = queue.Queue()
        self.lock = threading.Lock()
        self.connected_clients = set()

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
            server_socket.bind(("", 3000))
            return server_socket
        except socket.error as e:
            print(f"Bootstrap : Socket Error: {e}")

    def send_messages(self,client_address):
        while not self.wg.is_set():
            with self.lock:
                response = ""
                if not self.receive_queue.empty():
                    data, client_socket = self.receive_queue.get()
                    decoded_data = data.decode()

                    if decoded_data == "1":
                        for key, value in self.dic_with_neighbours.items():
                            for k in key:
                                if client_address[0] == k:
                                    if isinstance(value, list):
                                        response = json.dumps(value)
                                    else:
                                        response = str(value)
                                    break
                    else:
                        response = "Not a node"

                    if decoded_data == "3":
                        print(f"\nBOOTSTRAP: Closing socket")
                        response = "4"
                        client_socket.send(response.encode())
                        client_socket.close()
                        self.connected_clients.remove(client_address)
                        return
                        
                    client_socket.send(response.encode())

    def receive_messages(self, client_socket,client_address):
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                print(f"\nBOOTSTRAP: Received message from {client_address}: {data.decode()}")
                
                if not data:
                    break

                with self.lock:
                    self.receive_queue.put((data, client_socket))

        except Exception as e:
            print(f"BOOTSTRAP: An error occurred while receiving messages: {e}")


    def bootstrap(self, client_socket, client_address):
        print(f"\nBOOTSTRAP: Connected to: {client_address}")
        self.connected_clients.add(client_address)
        try:
            while not self.wg.is_set():
                if client_address not in self.connected_clients:
                    print(f"\nBOOTSTRAP: Client {client_address} is no longer connected. Exiting.")
                    break

                receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket, client_address))
                send_thread = threading.Thread(target=self.send_messages, args=(client_address,))

                receive_thread.start()
                send_thread.start()

                receive_thread.join()
                send_thread.join()

        except Exception as e:
            print(f"\nBOOTSTRAP: An error occurred in the bootstrap function: {e}")
        finally:
            print(f"\nBOOTSTRAP: Connection closed with {client_address}")
            self.wg.set()
            client_socket.close()

    def start(self):
        try:
            self.read_neighbours_file("bootstrapteste.json")
            server_socket = self.create_and_bind_socket()
            server_socket.listen(10)

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                if client_address not in self.connected_clients:
                    print(f"\nBOOTSTRAP: New connection from {client_address}")
                    thread = threading.Thread(target=self.bootstrap, args=(client_socket, client_address))
                    thread.start()

            #thread.join()

        except Exception as e:
            print(f"BOOTSTRAP: An error occurred in the start function: {e}")
        finally:
            if server_socket:
                server_socket.close()



