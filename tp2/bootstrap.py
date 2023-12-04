import socket
import threading
import time
import json  # for JSON serialization
import queue
from Message import Message

class Bootstrap():
    def __init__(self, ):
        self.wg = threading.Event()
        self.lock = threading.Lock()

        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()

        self.have_stream = False
        self.clients = []
        self.my_neighbours= dict()
        self.dic_with_neighbours = {}

        self.bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.bootstrap_socket.bind(("0.0.0.0", 4000))
        except socket.error as e:
            print(f"\nBootstrap : Socket Error: {e}")


    def read_neighbours_file(self, path):
        with open(path, "r") as f:
            data = json.load(f)
            for node_name, node_info in data["nodes"].items():
                ips = tuple(node_info["ips"])
                neighbors = node_info["neighbors"]

                # Substitui os nomes dos vizinhos pelos IPs correspondentes
                neighbor_ips = [data["nodes"][neighbor]["ips"] for neighbor in neighbors]

                self.dic_with_neighbours[tuple(ips)] = neighbor_ips

    def pprint_viz(self):
        print("\n")
        print("---------------- Meus Vizinhos ---------------")
        for k,v in self.my_neighbours.items():
            print(f"Nodo com Ips: {k}")
            print(f"  Vivo : {v['Vivo']}")
            print(f"  Ativo : {v['Ativo']}")
            print(f"  Peso Aresta : {v['Peso_Aresta']}")
            print(f"  Streams : {v['Streams']}")
            print(f"  Netos : {v['Netos']}")
            print(f"  Visited : {v['Visited']}")
            print("------------------------------")

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
   
    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data, host_addr,client_address = self.receive_queue.get()
                    print(f"\nBOOTSTRAP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    try:
                        # Deserialize the JSON data into a Python object
                        message_data = json.loads(data.decode())

                        if message_data["id"] == "1":
                            isNode = False
                            if len(self.my_neighbours) == 0:
                                for key, value in self.dic_with_neighbours.items():
                                    if host_addr in key:
                                        for v in value:
                                            self.my_neighbours[tuple(v)] = {"Vivo":False, "Ativo":False,"Peso_Aresta": 0,"Streams":{},"Netos":[],"Visited" : False}                                              

                            for key, value in self.dic_with_neighbours.items():
                                for k in key:
                                    if message_data["data"] == k:
                                        if isinstance(value, list):
                                            isNode = True
                                            messagem = Message("2", host_addr, (client_address,4000), json.dumps(value))
                                            break

                            if not isNode:
                                messagem = Message("3", host_addr, (client_address,4000), "NOT A NODE")
                            
                            self.process_queue.put((json.dumps(messagem.__dict__), None,False))
                        
                        if message_data["id"] == "4":
                            print(f"\nBOOTSTRAP [PROCESS TREAD] : CLOSED A CONNECTION WITH {client_address}")
                            
                        elif message_data["id"] == "5":
                            mensagem = Message("6", host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, tambem consegues receber mensagens minhas?")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))

                            mensagem = Message("5", host_addr, (client_address,4000),
                                               host_addr)
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))

                        elif message_data["id"] == "6":
                            mensagem = Message("7",  host_addr, (client_address,4000),"SIM")

                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here

                        elif message_data["id"] == "7":
                            src = message_data["src"]
                            
                            for k,v in self.my_neighbours.items():
                                if src in k:
                                    v["Vivo"] = True
                                    break
                            
                            self.pprint_viz()

                        elif message_data["id"] == "8":#quando é um cliente a enviar
                            #data - [timeStampAgora, somaAcumulada, Filho, id Flood]
                            StreamId, time_sent_message, soma_acumulada_recebida = message_data["data"]
                            src = message_data["src"]
                            dest = message_data["dest"]

                            time_now = int(time.time()*1000)
                            tempo_diff = time_now-time_sent_message
                            soma_acumulada = tempo_diff+soma_acumulada_recebida
                            
                            if src not in self.my_neighbours.keys():
                                self.my_neighbours.setdefault(src, {})
                            self.my_neighbours[src]["Vivo"] = 1
                            self.my_neighbours[src]["Ativo"] = 1
                            self.my_neighbours[src]["Peso_Aresta"] = tempo_diff
                            self.my_neighbours[src]["Streams"] = {StreamId:{"Time_Sent_flood":time_sent_message,"Soma_Acumulada":soma_acumulada}}
                            self.my_neighbours[src]["Visited"] = True
                            if "Netos" not in self.my_neighbours[k]:
                                self.my_neighbours[k]["Neto"] = []

                            self.pprint_viz()

                            if not self.have_stream:
                                for key,value in self.my_neighbours.items():
                                    if value["Vivo"] == 1 and client_address not in key:
                                        lista = [StreamId, src, time_now, soma_acumulada]
                                        
                                        mensagem = Message("9",host_addr,(key[0],4000),lista)
                                        self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                                    
                        elif message_data["id"] == "9": #entre nodos
                            #data - [timeStampAgora, somaAcumulada, Filho, id Flood]
                            StreamId,neto,time_sent_message,soma_acumulada_recebida = message_data["data"]
                            src = message_data["src"]

                            time_now = int(time.time()*1000)
                            tempo_diff = time_now-time_sent_message
                            soma_acumulada = tempo_diff+soma_acumulada_recebida

                            for k,v in self.my_neighbours.items():
                                if src in k:
                                    self.my_neighbours[k]["Peso_Aresta"] = tempo_diff
                                    self.my_neighbours[k]["Streams"] = {StreamId:{"Time_Sent_flood":time_sent_message,"Soma_Acumulada":soma_acumulada}}
                                    self.my_neighbours[k]["Visited"] = True
                                    if "Netos" not in self.my_neighbours[k]:
                                        self.my_neighbours[k]["Netos"] = []
                                    if neto not in self.my_neighbours[k]["Netos"]:    
                                        self.my_neighbours[k]["Netos"].append(neto)
                                    break
                            
                            self.pprint_viz()
                            if not self.have_stream:
                                for key,value in self.my_neighbours.items():
                                    if value["Vivo"] == 1 and client_address not in key and value["Visited"] == False:
                                        lista = [StreamId, src, time_now, soma_acumulada]

                                        mensagem = Message("9",host_addr,(key[0],4000),lista)
                                        self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                        elif message_data["id"] == "10":
                            StreamId,avo,time_I_sent_message,soma_acumulada_enviada = message_data["data"]

                            self.my_neighbours[src]


                            self.pai = message_data["data"][0]
                            timeStamp_mensagem_enviada = message_data["data"][1]
                            soma_acumulada_mensagem_enviada = message_data["data"][2]

                            #for k,v in self.my_neighbours.items():
                            #    if v[""]



                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP [PROCESS TREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP [PROCESS TREAD] : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    client_socket = None
                    data, client_socket, Socket_is_Created = self.process_queue.get()

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
            self.read_neighbours_file("bootstraptestea.json")

            self.bootstrap_socket.listen(5)

            while not self.wg.is_set():

                receive_thread = threading.Thread(target=self.receive_messages, args=())
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())
                
                print(f"\nTCP : OS MEUS VIZINHOS: {self.my_neighbours}")

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