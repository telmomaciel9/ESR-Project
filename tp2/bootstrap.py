import socket
import threading
import time
import json  # for JSON serialization
import queue
from Message import Message

class Bootstrap():
    def __init__(self, my_neighbours,have_stream):
        self.wg = threading.Event()
        self.lock = threading.Lock()

        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()

        self.have_stream = have_stream
        self.clients = []
        self.my_neighbours= my_neighbours
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
            #print(f"  Netos : {v['Netos']}")
            print(f"  Visited : {v['Visited']}")
            for stream_id, values in v['Streams'].items():
                print(f"  Stream ID: {stream_id}")
                for ante,val in values.items():
                    print(f"    Antecessor: {ante}")
                    print(f"      Soma Acumulada: {val['Soma_Acumulada']}")
                    print(f"      Caminho Ativo: {val['Ativo']}")
            print("------------------------------")

    def receive_messages(self):
        while True:
            try:
                client_socket, client_address = self.bootstrap_socket.accept()
                print(f"\nBOOTSTRAP [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nBOOTSTRAP [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    try:
                        # Try to decode the data as JSON
                        json_data = json.loads(data.decode())
                        is_json = True
                    except json.JSONDecodeError:
                        # If decoding fails, assume it's not JSON
                        is_json = False

                    if is_json:
                        self.receive_queue.put((data, host_addr, client_address, True))
                    else:
                        self.receive_queue.put((data, host_addr, client_address, False))

            except Exception as e:
                print(f"\nBOOTSTRAP : An error occurred while receiving messages: {e}")


    def escolher_melhor_neto(self, filho, StreamId):
        melhor_soma_acumulada = float('inf')
        netinho = None

        for neto,val in self.my_neighbours[filho]["Streams"][StreamId].items():
            if val["Soma_Acumulada"]<melhor_soma_acumulada:
                melhor_soma_acumulada = val["Soma_Acumulada"]
                netinho = neto
        
        return netinho

    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data, host_addr,client_address, isMessage = self.receive_queue.get()
                    print(f"\nBOOTSTRAP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    try:
                        message_data = None
                        
                        if isMessage:
                        # Deserialize the JSON data into a Python object
                            message_data = json.loads(data.decode())
                        else:
                            message_data = data.decode()
                            

                        if message_data == "Stream" or message_data == "Stop":
                            for k, v in self.my_neighbours.items():
                                if v["Ativo"] == True and client_address not in k:
                                    print(f"\n\n{k}")
                                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    client_socket.connect((k[0], 4000))
                                    self.process_queue.put((message_data, client_socket, True))
                                    break

                        elif message_data["id"] == "1":
                            isNode = False
                            if len(self.my_neighbours) == 0:
                                for key, value in self.dic_with_neighbours.items():
                                    if host_addr in key:
                                        for v in value:
                                            self.my_neighbours[tuple(v)]= {"Vivo":False, "Ativo":False,"Peso_Aresta": 0,"Streams":{},"Visited" : False}                                              

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
                            mensagem = Message("7",  host_addr, (client_address,4000),
                                               "SIM")
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

                            time_now = int(time.time()*1000)
                            tempo_diff = time_now-time_sent_message
                            soma_acumulada = tempo_diff+soma_acumulada_recebida
                            
                            
                            if src not in self.my_neighbours.keys():
                                self.my_neighbours.setdefault(src, {})
                            
                            self.my_neighbours[src]["Vivo"] = True
                            self.my_neighbours[src]["Ativo"] = True
                            self.my_neighbours[src]["Peso_Aresta"] = tempo_diff
                            self.my_neighbours[src]["Visited"] = True

                            if "Streams" not in self.my_neighbours[src]:
                                self.my_neighbours[src]["Streams"] = {}

                            src_string = str(src)
                            if StreamId not in self.my_neighbours[src]["Streams"].keys():
                                self.my_neighbours[src]["Streams"][StreamId] = {src_string: {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}}
                            else:
                                if src_string not in self.my_neighbours[src]["Streams"][StreamId].keys():
                                    self.my_neighbours[src]["Streams"][StreamId][src_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}
                                else:
                                    if soma_acumulada < self.my_neighbours[src_string]["Streams"][StreamId][src_string]["Soma_Acumulada"]:
                                        self.my_neighbours[src]["Streams"][StreamId][src_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada, "Ativo":False}


                            self.pprint_viz()

                            if not self.have_stream:
                                for key,value in self.my_neighbours.items():
                                    if value["Vivo"] == 1 and client_address not in key:
                                        lista = [StreamId, src, time_now, soma_acumulada]
                                        
                                        mensagem = Message("9",host_addr,(key[0],4000),lista)
                                        self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here

                            if self.have_stream:
                                lista = [StreamId,host_addr]
                                mensagem = Message("10",host_addr,(src,4000),lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__),None,False))
                                   
                        elif message_data["id"] == "9": #entre nodos
                            #data - [timeStampAgora, somaAcumulada, Filho, id Flood]
                            StreamId,neto,time_sent_message,soma_acumulada_recebida = message_data["data"]
                            src = message_data["src"]

                            time_now = int(time.time()*1000)
                            tempo_diff = time_now-time_sent_message
                            soma_acumulada = tempo_diff+soma_acumulada_recebida

                            chave = tuple()
                            for k in self.my_neighbours.keys():
                                if src in k:
                                    chave = k
                                    break

                            
                            self.my_neighbours[chave]["Peso_Aresta"] = tempo_diff
                            self.my_neighbours[chave]["Visited"] = True
                            neto_string = str(neto)

                            if StreamId not in self.my_neighbours[chave]["Streams"].keys():
                                self.my_neighbours[chave]["Streams"][StreamId] = {neto_string: {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}}
                            else:
                                if neto_string not in self.my_neighbours[chave]["Streams"][StreamId].keys():
                                    self.my_neighbours[chave]["Streams"][StreamId][neto_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}
                                else:
                                    if soma_acumulada < self.my_neighbours[chave]["Streams"][StreamId][neto_string]["Soma_Acumulada"]:
                                        self.my_neighbours[chave]["Streams"][StreamId][neto_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}
                            self.pprint_viz()

                            if not self.have_stream:
                                for key,value in self.my_neighbours.items():
                                    if value["Vivo"] == True and client_address not in key and value["Visited"] == False:
                                        lista = [StreamId, src, time_now, soma_acumulada]
                                        print(f"\n\nasldkfjasdljf\n{key[0]}")
                                        mensagem = Message("9",host_addr,(key[0],4000),lista)
                                        self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                        
                        elif message_data["id"] == "10":
                            StreamId,avo,filho = message_data["data"]

                            src = message_data["src"]

                            chave = tuple()
                            for k in self.my_neighbours.keys():
                                if src in k:
                                    chave = k
                                    break


                            next_node = tuple()
                            for n in self.my_neighbours.keys():
                                if filho in n:
                                    next_node = n

                            neto = self.escolher_melhor_neto(next_node,StreamId)
                            self.my_neighbours[chave]["Ativo"] = True
                            self.my_neighbours[next_node]["Ativo"] = True
                            self.my_neighbours[next_node]["Streams"][StreamId][neto]["Ativo"]=True
                            lista = [StreamId,host_addr,neto]

                            if isinstance(next_node,tuple):
                                mensagem = Message("10",host_addr,(next_node[0],4000),lista)
                            elif isinstance(next_node,str):
                                mensagem = Message("10",host_addr,(next_node,4000),lista)
                            self.process_queue.put((json.dumps(mensagem.__dict__), None, False))
                            self.have_stream =True

                            self.pprint_viz()   
                            
                            




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
                    print(f"\n\Size da queue : {self.process_queue.qsize()}")
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    
                    ip_destino = ""
                    port_destino = 4000
                    try:
                        # Try to decode the data as JSON
                        message_data = json.loads(data)
                        ip_destino = message_data["dest"][0]

                        port_destino = message_data["dest"][1]
                    except json.JSONDecodeError:
                        # If decoding fails, assume it's not JSON
                        ip_destino = client_socket.getpeername()[0]


                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                        #self.clients_sockets.append(client_socket)
                    try:
                        client_socket.send(data.encode())
                        print(f"\nBOOTSTRAP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data} ")

                    except json.JSONDecodeError as e:
                        print(f"\nBOOTSTRAP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nBOOTSTRAP [SEND THREAD] :  Error sending message in the send_messages function: {e}")
                    
                            

    def start(self):
        try:
            self.read_neighbours_file("bootstraptestea.json")

            self.bootstrap_socket.listen(5)

            while not self.wg.is_set():

                receive_thread = threading.Thread(target=self.receive_messages, args=())
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())
                
                print(f"\nBOOTSTRAP : OS MEUS VIZINHOS: {self.my_neighbours}")

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