import socket
import threading
import queue
import json
import time
from Message import Message
import re


class ONodeTCP:
    def __init__(self, bootstrap_ip, is_bootstrap):
        self.bootstrap_ip = bootstrap_ip
        self.wg = threading.Event()
        self.clients = set()
        self.is_bootstrap = is_bootstrap
        self.my_neighbours= dict()
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sockets = [] 
        try:
            self.server_socket.bind(("0.0.0.0",4000))
        except socket.error as e:   
            print(f"\nTCP : Socket Error on Binding: {e}")
        #self.ip = self.server_socket.getsockname()[0]
        #print(f"\nTCP : Server IP address: {self.ip}")
                
       
    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()
                print(f"\nTCP [RECEIVE THREAD] : RECEIVE THIS MESSAGE FROM {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    self.receive_queue.put((data, client_socket))
                    print(f"\nTCP [RECEIVE THREAD] : I'VE JUST PUT THE MESSAGE IN RECEIVE QUEUE: {data} ")
                    print(f"\nTCP [RECEIVE THREAD] : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
        except Exception as e:
            print(f"\nTCP : An error occurred while receiving messages from {client_address}: {e}")
        finally:
            with self.lock:
                self.clients.remove(client_socket)
                client_socket.close()

    def receive_messages(self):
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"\nBOOTSTRAP : CONNECTED WITH {client_address}")
                self.clients.add(client_socket)
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
        except Exception as e:
            print(f"\nTCP : An error occurred while accepting connections: {e}")

    def process_messages(self):
        while True:
            with self.lock:
                #print(f"ELEMENTOS NA RECEIVE QUEUE : {self.receive_queue.qsize()}")
                if not self.receive_queue.empty():
                    data, client_socket = self.receive_queue.get()
                    print(f"\nTCP [PROCESS THREAD] : GOING TO PROCESS A MESSAGE : {data}")
                    print(f"\nTCP [PROCESS THREAD] : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
                    try:
                        # Deserialize the JSON data into a Python object
                        message_data = json.loads(data.decode())

                        if message_data["id"] == "2":
                            info = message_data["data"]
                            src = message_data["src"]

                            # Remove brackets and split the string into a list
                            values = info[1:-1].split(', ')

                            # Remove double quotes from each element
                            cleaned_values = [value.strip('"') for value in values]
                        
                            for v in cleaned_values:
                                self.my_neighbours[v] = False

                            mensagem = Message("4", client_socket.getsockname()[0], (client_socket.getpeername()[0],3000),
                                               "Recebi a tua mensagem, vou terminar a conexao")

                        elif message_data["id"] == "3":
                            info = message_data["data"]
                            src = message_data["src"]
 
                            mensagem = Message("4", client_socket.getsockname()[0], (client_socket.getpeername()[0],3000),
                                               "Recebi a tua mensagem, vou terminar a conexao")

                        elif message_data["id"] == "5":
                            info = message_data["data"]
                            src = message_data["src"]

                            mensagem = Message("6", client_socket.getsockname()[0], (client_socket.getpeername()[0],4000),
                                               "Recebi a tua mensagem, tambem consegues receber mensagens minhas?")
                        
                        elif message_data["id"] == "6":
                            info = message_data["data"]
                            src = message_data["src"]

                            mensagem = Message("7", client_socket.getsockname()[0], (client_socket.getpeername()[0],4000),
                                               "SIM")

                        elif message_data["id"] == "7":
                            info = message_data["data"]
                            src = message_data["src"]

                            self.my_neighbours[src] = True


                        self.process_queue.put((json.dumps(mensagem.__dict__), client_socket,False))  # Fix the typo here



                        print(f"\nTCP [PROCESS THREAD] : I'VE JUST PUT THE MESSAGE IN PROCESS QUEUE: {data} ")
                        print(f"\nTCP [PROCESS THREAD] : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                            

                    except json.JSONDecodeError as e:
                        print(f"\nTCP [PROCESS THREAD]  : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nTCP [PROCESS THREAD] : Error in processing messages: {e}")


    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    client_socket = None
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    print(f"\nTCP [SEND THREAD] : GOING TO SEND THE MESSAGE: {data} ")
                    print(f"\nTCP [SEND THREAD] : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                    message_data = json.loads(data)
                    ip_destino = message_data["dest"][0]
                    port_destino = message_data["dest"][1]
                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                    try:
                        client_socket.send(data.encode())
                        print(f"\nTCP [SEND THREAD] : Sent this message: {data} to: ({ip_destino},{port_destino})")

                    except json.JSONDecodeError as e:
                        print(f"\nTCP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nTCP [SEND THREAD] :  Error sending message in the send_messages function: {e}")
                    finally:
                        if client_socket:
                            client_socket.close()
                            
    def connect_to_other_node(self, ip, port, purpose):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempt_count = 0

        #while attempt_count < 3:  # Adjust the maximum number of attempts as needed
        #time.sleep(5)
        try:
            client_socket.connect((ip, port))
            if purpose == 1:
                messagem = Message("1",client_socket.getsockname()[0],(ip,port),client_socket.getsockname()[0])
                self.process_queue.put((json.dumps(messagem.__dict__),client_socket,True))

            elif purpose == 2:
                messagem = Message("5",client_socket.getsockname()[0],(ip,port),client_socket.getsockname()[0])
                self.process_queue.put((json.dumps(messagem.__dict__),client_socket,True))


            self.client_sockets.append(client_socket)
            #break  # Exit the loop if the connection is successful
        #break
        except Exception as e:
            print(f"\nTCP: An error occurred while sending a message in connect_to_other_node function in ip {ip}: {e}")
            attempt_count += 1
            print(f"\nTCP : Retrying connection to {ip}:{port}... (Attempt {attempt_count})")
            time.sleep(2)  # Adjust the delay between attempts as needed
        
        #if attempt_count >= 3:
        #    print(f"\nFailed to establish a connection to {ip}:{port} after multiple attempts.")



    def start(self):
            try:
                self.server_socket.listen(5)

                #while not self.wg.is_set():

                receive_thread = threading.Thread(target=self.receive_messages, args=())
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())
                receive_thread.start()
                process_thread.start()
                send_thread.start()
                if not self.is_bootstrap:
                    self.connect_to_other_node(self.bootstrap_ip,3000,1)
                    print(f"\nTCP : ESTES SÃO OS MEUS VIZINHOS: {self.my_neighbours}")
                    time.sleep(10)
                    for v in self.my_neighbours.keys() :
                        self.connect_to_other_node(v,4000,2)
                
                receive_thread.join()
                process_thread.join()
                send_thread.join()
                #print("ola")

            except Exception as e:
                print(f"\TCP : An error occurred in start function: {e}")
            finally:
                for client_socket in self.clients:
                    client_socket.close()

                if self.server_socket:
                    self.server_socket.close()