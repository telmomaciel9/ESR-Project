import socket
import threading
import time
import json  # for JSON serialization
import queue
from Message import Message

class RP:
    def __init__(self, ):
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}
        self.lock = threading.Lock()
        self.connected_clients = set()
        self.rp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        try:
            self.rp_socket.bind(("0.0.0.0", 3000))
        except socket.error as e:
            print(f"\nRP : Socket Error: {e}")



    #Função para receber mensagens de um dado socket.
    #Ao receber, coloca na queue de mensagens recebidas para serem futuramente processadas
    def receive_messages(self):
        try:
            while True:
                client_socket, client_address = self.rp_socket.accept()
                print(f"\nRP : CONNECTED WITH {client_address}")
                self.connected_clients.add(client_socket)
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()
                print(f"\nRP : Received this message from {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    self.receive_queue.put((data, client_socket))
                    print(f"\nRP : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
                    
        except Exception as e:
            print(f"\nRP : An error occurred while receiving messages: {e}")

    #Função para processar as mensagens que estão na queue de mensagens recebidas
    #Apos o processamento, ela coloca as mensagens já processadas numa queue de mensagens processadas 
    #para depois poderem ser enviadas 

    #FIXMe MUDAR O PORCESSAMENTO DAS MENSAGENS 
    def process_messages(self):
        while True:
            with self.lock:
                #print(self.receive_queue.qsize())
                if not self.receive_queue.empty():
                    print("\nRP : GOING TO PROCESS A MESSAGE")
                    data, client_socket = self.receive_queue.get()
                    print(f"\nRP : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
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
                                            messagem = Message("2", client_socket.getsockname()[0], (client_socket.getpeername()[0],4000), json.dumps(value))
                            if not isNode:
                                messagem = Message("3", client_socket.getsockname()[0], client_socket.getpeername(), "NOT A NODE")
                        
                        if message_data["id"] == "4":
                            self.connected_clients.remove(client_socket)
                            #client_socket.close()
                            print(f"\nRP : CLOSED A CONNECTION WITH {client_socket.getsockname()[0]}")
                            

                        # Handle other cases as needed...
                        self.process_queue.put((json.dumps(messagem.__dict__), client_socket,False))
                        print(f"\nRP : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                    except json.JSONDecodeError as e:
                        print(f"\nRP : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    print("\nRP : GOING TO SEND A MESSAGE")
                    #client_socket = None
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    print(f"\nRP : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                    message_data = json.loads(data)
                    ip_destino = message_data["dest"][0]
                    port_destino = message_data["dest"][1]
                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                    try:
                        
                        client_socket.send(data.encode())
                        print(f"\nTCP : Sent this message: {data} to: ({ip_destino},{port_destino})")
                    except json.JSONDecodeError as e:
                        print(f"\nRP : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP : Error sending message in the send_messages function: {e}")
                    finally:
                        if client_socket:
                            print(f"\nRP : CLOSED CONNECTOIN WITH {client_socket.getpeername()}")
                            client_socket.close()
                            

    def start(self):
        try:
            #self.read_neighbours_file("RPteste.json")
            self.read_neighbours_file("teste3.json")
            self.rp_socket.listen(5)

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
            print(f"\nRP : An error occurred in start function: {e}")
        finally:
            for client_socket in self.clients:
                client_socket.close()

            if self.rp_socket:
                self.rp_socket.close()