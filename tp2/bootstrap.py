import socket
import threading
import time
import json  # for JSON serialization
import queue
from Message import Message

class Bootstrap:
    def __init__(self, ):
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}
        self.lock = threading.Lock()
        self.connected_clients = set()
        self.bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        try:
            self.bootstrap_socket.bind(("", 3000))
        except socket.error as e:
            print(f"\nBootstrap : Socket Error: {e}")


    def read_neighbours_file(self, path):
        with open(path, "r") as f:
            data = json.load(f)
            for node in data["nodes"]:
                ip = node["ip"]
                neighbors = node["neighbors"]
                self.dic_with_neighbours[tuple(ip)] = neighbors

    #Função para receber mensagens de um dado socket.
    #Ao receber, coloca na queue de mensagens recebidas para serem futuramente processadas
    def receive_messages(self):
        while True:
            try:
                client_socket, client_address = self.bootstrap_socket.accept()
                self.connected_clients.add(client_socket)
                while True:
                    data = client_socket.recv(1024)
                    client_address = client_socket.getpeername()
                    print(f"\nBOOTSTRAP : Received this message from {client_address}: {data}")
                    if not data:
                        break
                    with self.lock:
                        self.receive_queue.put((data, client_socket))
            except Exception as e:
                print(f"\nBOOTSTRAP : An error occurred while receiving messages: {e}")

    #Função para processar as mensagens que estão na queue de mensagens recebidas
    #Apos o processamento, ela coloca as mensagens já processadas numa queue de mensagens processadas 
    #para depois poderem ser enviadas 
    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data, client_socket = self.receive_queue.get()
                    try:
                        # Deserialize the JSON data into a Python object
                        message_data = json.loads(data.decode())


                        if message_data["id"] == "1":
                            isNode = False
                            print(client_socket.getpeername())
                            for key, value in self.dic_with_neighbours.items():
                                for k in key:
                                    if message_data["data"] == k:
                                        if isinstance(value, list):
                                            isNode = True
                                            messagem = Message("2", client_socket.getsockname()[0], (client_socket.getpeername()[0],4000), json.dumps(value))
                            if not isNode:
                                messagem = Message("3", client_socket.getsockname()[0], client_socket.getpeername(), "NOT A NODE")
                        
                        if message_data["id"] == "4":
                            self.connected_clients.remove(client_socket)
                            client_socket.close()
                            return

                        # Handle other cases as needed...
                        self.process_queue.put((json.dumps(messagem.__dict__), client_socket))

                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty() :
                    data, client_socket = self.process_queue.get()
                    try:
                        message_data = json.loads(data)
                        destino = message_data["dest"]
                        client_socket.send(data.encode())
                        print(f"\nBOOTSTRAP : Send this message: {data} to: {destino}")
                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP : Error sending message in the send_messages function: {e}")

    def start(self):
        try:
            self.read_neighbours_file("bootstrapteste.json")
            self.bootstrap_socket.listen(5)

            while not self.wg.is_set():

                receive_thread = threading.Thread(target=self.receive_messages, args=())
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())

                receive_thread.start()
                process_thread.start()
                send_thread.start()


                receive_thread.join()
                process_thread.join()
                send_thread.join()

        except Exception as e:
            print(f"\nBOOTSTRAP : An error occurred in start function: {e}")
        finally:
            for client_socket in self.clients:
                client_socket.close()

            if self.bootstrap_socket:
                self.bootstrap_socket.close()