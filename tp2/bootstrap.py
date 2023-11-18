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
        #self.process_queue = queue.Queue()
        #self.send_queue = queue.Queue()
        self.lock = threading.Lock()

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

    '''
    def send_data(self, client_socket, client_address):
        try:
            while not self.wg.is_set():
                time.sleep(2)
                response = "NOT A NODE"

                for key, value in self.dic_with_neighbours.items():
                    for k in key:
                        if client_address[0] == k:
                            if isinstance(value, list):
                                response = json.dumps(value)
                            else:
                                response = str(value)
                            break
                print(f"\nBOOTSTRAP: Sending a message to {client_address}: {response}")            
                self.wg.set()    

                client_socket.send(response.encode())

        except BrokenPipeError:
            print(f"\nBOOTSTRAP: Broken Pipe. Client {client_address} has disconnected.")
        except Exception as e:
            print(f"\nBOOTSTRAP: An error occurred while sending data to {client_address}: {e}")
        finally:
            print(f"\nBOOTSTRAP: Closing socket with {client_address}")
            client_socket.close()

    def receive_data(self, client_socket, client_address):
        while not self.wg.is_set():
            data = client_socket.recv(1024)
            if not data:
                break
            
            print(f"\nBOOTSTRAP: Received message from {client_address}: {data.decode()}")

            if data.decode() == "3":
                self.wg.set() 
     #       self.process_data(data, client_socket,client_address)

    '''

    #def process_data(self, data, client_socket,client_address):
    #    if data == 

    def send_messages(self):
        while True:
            with self.lock:
                response = ""
                if not self.receive_queue.empty():
                    data, client_socket = self.receive_queue.get()
                    # Simulate processing the message
                    if data == "Hello Bootstrap":
                        #print(f"\nBOOTSTRAP: Received message from {client_address}: {data.decode()}")
                    #processed_message = f"Node {self.node_id}: Processed: {data.decode()}"
                        
                        for key, value in self.dic_with_neighbours.items():
                            for k in key:
                                if client_address[0] == k:
                                    if isinstance(value, list):
                                        response = json.dumps(value)
                                    else:
                                        response = str(value)
                                    break
                    if data == "3":
                        print(f"\nBOOTSTRAP: Closing socket")
                        client_socket.close()
                    # Simulate sending the message
                    #sent_message = f"Node {self.node_id}: Sent: {response}"
                    client_socket.send(response.encode())

    def receive_messages(self, client_socket,client_address):
        try:
            while True:
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
        try:
            receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket, client_address))
            send_thread = threading.Thread(target=self.send_messages, args=())

            send_thread.start()
            receive_thread.start()

            send_thread.join()
            receive_thread.join()

        except Exception as e:
            print(f"\nBOOTSTRAP: An error occurred in the bootstrap function: {e}")
        finally:
            print(f"\nBOOTSTRAP: Connection closed with {client_address}")
            client_socket.close()
            self.wg.set()

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



