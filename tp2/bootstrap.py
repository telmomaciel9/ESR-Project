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
            self.bootstrap_socket.bind(("0.0.0.0", 3000))
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
                print(f"\nBOOTSTRAP [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nBOTTSTRAP [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    self.receive_queue.put((data, host_addr,client_address))

            except Exception as e:
                print(f"\nBOOTSTRAP : An error occurred while receiving messages: {e}")
   
    #Função para processar as mensagens que estão na queue de mensagens recebidas
    #Apos o processamento, ela coloca as mensagens já processadas numa queue de mensagens processadas 
    #para depois poderem ser enviadas 
    def process_messages(self):
        while True:
            with self.lock:
                #print(self.receive_queue.qsize())
                if not self.receive_queue.empty():
                    data, host_addr,client_address = self.receive_queue.get()
                    print(f"\nBOOTSTRAP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    #print(f"\nBOOTSTRAP [PROCESS TREAD] : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
                    try:
                        # Deserialize the JSON data into a Python object
                        message_data = json.loads(data.decode())

                        if message_data["id"] == "1":
                            isNode = False

                            for key, value in self.dic_with_neighbours.items():
                                for k in key:
                                    if message_data["data"] == k:
                                        if isinstance(value, list):
                                            isNode = True
                                            messagem = Message("2", host_addr, (client_address,4000), json.dumps(value))
                            if not isNode:
                                messagem = Message("3", host_addr, (client_address,4000), "NOT A NODE")
                            
                            self.process_queue.put((json.dumps(messagem.__dict__), None,False))
                        
                        if message_data["id"] == "4":
                            #self.connected_clients.remove(client_socket)
                            #client_socket.close()
                            print(f"\nBOOTSTRAP [PROCESS TREAD] : CLOSED A CONNECTION WITH {client_address}")
                            

                        # Handle other cases as needed...

                        #print(f"\nBOOTSTRAP [PROCESS THREAD] : I'VE JUST PUT THE MESSAGE IN PROCESS QUEUE: {data} ")
                        #print(f"\nBOOTSTRAP [PROCESS THREAD] : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                            
                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP [PROCESS TREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP [PROCESS TREAD] : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    #client_socket = None
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    #print(f"\nBOOTSTRAP [SEND THREAD] : GOING TO SEND A MESSAGE {data}")
                    #print(f"\nBOOTSTRAP [SEND THREAD] : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                    message_data = json.loads(data)
                    ip_destino = message_data["dest"][0]
                    port_destino = message_data["dest"][1]
                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                    try:
                        
                        client_socket.send(data.encode())
                        print(f"\nBOOTSTRAP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data}")
                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP [SEND THREAD] : Error sending message in the send_messages function: {e}")
                    
                            

    def start(self):
        try:
            #self.read_neighbours_file("bootstrapteste.json")
            self.read_neighbours_file("teste3.json")
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