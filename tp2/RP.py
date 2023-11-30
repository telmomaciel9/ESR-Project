import socket
import threading
import time
import json  # for JSON serialization
import queue
import bisect
from Message import Message

class RP():
    def __init__(self, bootstrap_ip ):
        self.wg = threading.Event()
        self.threads = []
        self.dic_with_neighbours = {}
        self.lock = threading.Lock()
        self.connected_clients = set()
        self.rp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.lista_recebido = list()
        self.num_recebidos = 0
        self.arvore=dict()
        self.bootstrap_ip=bootstrap_ip
        self.my_neighbours= dict()

        try:
            self.rp_socket.bind(("0.0.0.0", 4000))
        except socket.error as e:
            print(f"\nRP : Socket Error: {e}")



    #Função para receber mensagens de um dado socket.
    #Ao receber, coloca na queue de mensagens recebidas para serem futuramente processadas
    def receive_messages(self):
        while True:
            try:
                client_socket, client_address = self.rp_socket.accept()
                print(f"\nRP [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nBOTTSTRAP [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    self.receive_queue.put((data, host_addr,client_address))

            except Exception as e:
                    print(f"\nRP : An error occurred while receiving messages: {e}")
   
    #Função para processar as mensagens que estão na queue de mensagens recebidas
    #Apos o processamento, ela coloca as mensagens já processadas numa queue de mensagens processadas 
    #para depois poderem ser enviadas 
    def process_messages(self):
        while True:
            with self.lock:
                #print(self.receive_queue.qsize())
                if not self.receive_queue.empty():
                    data, host_addr,client_address = self.receive_queue.get()
                    print(f"\nRP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    #print(f"\nRP [PROCESS TREAD] : I HAVE {self.receive_queue.qsize()} ELEMENTS IN THE RECEIVE QUEUE")
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
                                self.my_neighbours[v] = [False,False]

                            mensagem = Message("4", host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, vou terminar a conexao")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))
                        elif message_data["id"] == "3":
                            info = message_data["data"]
                            src = message_data["src"]
 
                            mensagem = Message("4",  host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, vou terminar a conexao")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))
                        elif message_data["id"] == "5":
                            info = message_data["data"]
                            src = message_data["src"]

                            mensagem = Message("6", host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, tambem consegues receber mensagens minhas?")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))
                        elif message_data["id"] == "6":
                            info = message_data["data"]
                            src = message_data["src"]

                            mensagem = Message("7",  host_addr, (client_address,4000),
                                               "SIM")

                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                        elif message_data["id"] == "7":
                            info = message_data["data"]
                            src = message_data["src"]

                            self.my_neighbours[src][0] = True
                            print(f"\n OS MEUS VIZINHOS!!!! {self.my_neighbours}")

                        elif message_data["id"] == "8":
                            print("\nasdlkjfdaslkjfasdkljfasdklj\n")
                            self.num_recebidos += 1
                            timeStart, pesoTotal = message_data["data"]
                            tuple_to_insert = (message_data["src"], pesoTotal)
                            #index_to_insert = bisect.bisect_left(self.lista_recebido, tuple_to_insert[1])
                            index_to_insert = bisect.bisect_left([x[1] for x in self.lista_recebido], tuple_to_insert[1])

                            self.lista_recebido.insert(index_to_insert, tuple_to_insert)
                            time_now = (time.time() * 1000)
                            aresta = time_now - timeStart
                            self.arvore[message_data["src"]] = aresta
                            print(f"\n\n{isinstance(self.num_recebidos, int)}")
                            print(f"\n\n{isinstance(sum(value == 1 for value in self.my_neighbours.values()),int)}")
                            #while True:
                                #print(f"\n{self.lista_recebido}")
                                #print(f"\n{sum(value == 1 for value in self.my_neighbours.values())}")
                                #print(f"\n{len(self.arvore)}")
                            if self.num_recebidos == sum(value == 1 for value in self.my_neighbours.values()):
                                mensagem=Message("9",host_addr,(self.lista_recebido[0][0],4000),pesoTotal)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                            else:
                                print("\nvou passar à frente porque ainda nao tenho todos os caminhos possiveis")
                                pass


                    except json.JSONDecodeError as e:
                        print(f"\nRP [PROCESS TREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP [PROCESS TREAD] : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    #client_socket = None
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    #print(f"\nRP [SEND THREAD] : GOING TO SEND A MESSAGE {data}")
                    #print(f"\nRP [SEND THREAD] : I HAVE {self.process_queue.qsize()} ELEMENTS IN THE PROCESS QUEUE")
                    message_data = json.loads(data)
                    ip_destino = message_data["dest"][0]
                    port_destino = message_data["dest"][1]
                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                    try:
                        
                        client_socket.send(data.encode())
                        print(f"\nRP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data}")
                    except json.JSONDecodeError as e:
                        print(f"\nRP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP [SEND THREAD] : Error sending message in the send_messages function: {e}")
    

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


            #self.client_sockets.append(client_socket)
            #break  # Exit the loop if the connection is successful
        #break
        except Exception as e:
            print(f"\nRP: An error occurred while sending a message in connect_to_other_node function in ip {ip}: {e}")
            attempt_count += 1
            print(f"\nRP : Retrying connection to {ip}:{port}... (Attempt {attempt_count})")
            time.sleep(2)  # Adjust the delay between attempts as needed
        
        #if attempt_count >= 3:
        #    print(f"\nFailed to establish a connection to {ip}:{port} after multiple attempts.")

                            
    def start(self):
            try:
                self.rp_socket.listen(5)

                while not self.wg.is_set():

                    receive_thread = threading.Thread(target=self.receive_messages, args=())
                    process_thread = threading.Thread(target=self.process_messages, args=())
                    send_thread = threading.Thread(target=self.send_messages, args=())
                    receive_thread.start()
                    process_thread.start()
                    send_thread.start()

                    
                    self.connect_to_other_node(self.bootstrap_ip,4000,1)
                    #print(f"\nTCP : ESTES SÃO OS MEUS VIZINHOS: {self.my_neighbours}")

                    time.sleep(10)
                    for v in self.my_neighbours.keys() :
                        self.connect_to_other_node(v,4000,2)
                    print(f"\nTCP : OS MEUS VIZINHOS: {self.my_neighbours}")

                    receive_thread.join()
                    process_thread.join()
                    send_thread.join()
                    #print("ola")

            except Exception as e:
                print(f"\RP : An error occurred in start function: {e}")
            finally:
                #for client_socket in self.clients:
                #    client_socket.close()

                if self.rp_socket:
                    self.rp_socket.close()