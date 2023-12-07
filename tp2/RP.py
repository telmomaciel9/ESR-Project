import socket
import threading
import time
import json  # for JSON serialization
import queue
import bisect
from Message import Message

class RP():
    def __init__(self, bootstrap_ip,my_neighbours,have_stream):
        self.bootstrap_ip=bootstrap_ip

        self.wg = threading.Event()
        self.lock = threading.Lock()
        
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()

        self.my_neighbours= my_neighbours
        self.netos = []
        self.have_stream= have_stream

        self.servidores = dict()

        self.rp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rp_socket.bind(("0.0.0.0", 4000))
        except socket.error as e:
            print(f"\nRP : Socket Error: {e}")

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
                client_socket, client_address = self.rp_socket.accept()
                print(f"\nRP [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nRP [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
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
                print(f"\nRP : An error occurred while receiving messages: {e}")
    
    def escolher_melhor_nodo(self, StreamId):
        nodos_ativos = []
        melhor_nodo = None
        melhor_ant = None
        melhor_soma_acumulada = float('inf')

        for node, info in self.my_neighbours.items():
            if info["Ativo"]:
                nodos_ativos.append(node)

        if not nodos_ativos:
            return None,None
        else:
            for n in nodos_ativos:
                for ante, info in self.my_neighbours[n]["Streams"][StreamId].items():
                    if info["Soma_Acumulada"] < melhor_soma_acumulada:
                        melhor_soma_acumulada = info["Soma_Acumulada"]
                        melhor_nodo = n
                        melhor_ant = ante

        return melhor_nodo,melhor_ant

    def antigo_melhor_nodo(self, StreamId):
        nodo_anterior = None
        anterior_anterior = None

        for node,value in self.my_neighbours.items():
            if value["Ativo"] and StreamId in value["Streams"].keys():
                nodo_anterior = node
                for ante,val in self.my_neighbours[node]["Streams"][StreamId].items():
                    if val["Ativo"]:
                        anterior_anterior = ante
                        break

        return nodo_anterior,anterior_anterior

    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data,host_addr,client_address,isMessage = self.receive_queue.get()
                    print(f"\nRP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    try:
                        message_data = None
                        
                        if isMessage:
                        # Deserialize the JSON data into a Python object
                            message_data = json.loads(data.decode())
                        else:
                            message_data = data.decode()
                            
                        if message_data["id"] == "2":
                            info = message_data["data"]
                            result_string = json.loads(info)

                            for v in result_string:
                                self.my_neighbours[tuple(v)]= {"Vivo":False, "Ativo":False,"Peso_Aresta": 0,"Streams":{},"Visited" : False}

                            self.pprint_viz()

                            mensagem = Message("4", host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, vou terminar a conexao")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))

                        elif message_data["id"] == "3":
                            mensagem = Message("4",  host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, vou terminar a conexao")
                            self.process_queue.put((json.dumps(mensagem.__dict__), None,False))
                        
                        elif message_data["id"] == "5":
                            mensagem = Message("6", host_addr, (client_address,4000),
                                               "Recebi a tua mensagem, tambem consegues receber mensagens minhas?")
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

                        elif message_data["id"] == "9":
                            StreamId, neto, time_sent_message, soma_acumulada_recebida = message_data["data"]
                            src = message_data["src"]

                            time_now = int(time.time() * 1000)
                            tempo_diff = time_now - time_sent_message
                            soma_acumulada = tempo_diff + soma_acumulada_recebida

                            chave = tuple()
                            for k in self.my_neighbours.keys():
                                if src in k:
                                    chave = k
                                    break
                            
                            self.my_neighbours[chave]["Peso_Aresta"] = tempo_diff
                            self.my_neighbours[chave]["Visited"] = True

                            neto_string = str(neto)
                            
                            if StreamId not in self.my_neighbours[chave]["Streams"].keys():
                                self.my_neighbours[chave]["Streams"][StreamId] = {neto_string: {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada, "Ativo": False}}
                            else:
                                if neto_string not in self.my_neighbours[chave]["Streams"][StreamId].keys():
                                    self.my_neighbours[chave]["Streams"][StreamId][neto_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada, "Ativo": False}
                                else:
                                    if soma_acumulada < self.my_neighbours[chave]["Streams"][StreamId][neto_string]["Soma_Acumulada"]:
                                        self.my_neighbours[chave]["Streams"][StreamId][neto_string] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada, "Ativo" : False}

                            
                            nodo_anterior,ant_anterior = self.antigo_melhor_nodo(StreamId)
                            melhor_nodo,melhor_ant = self.escolher_melhor_nodo(StreamId)
                            
                            print(f"\nNodo anterior: {nodo_anterior}")
                            print(f"\nMelhor nodo: {melhor_nodo}")

                            #for k,v in self.my_neighbours[chave][]
                            if (melhor_nodo != nodo_anterior) and melhor_nodo!=None and nodo_anterior!=None:
                                self.my_neighbours[melhor_nodo]["Ativo"] = True
                                self.my_neighbours[melhor_nodo]["Streams"][StreamId][melhor_ant]["Ativo"] = True
                                lista = [StreamId, host_addr, melhor_ant]
                                mensagem = Message("10", host_addr, (melhor_nodo[0], 4000), lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None, False))


                                self.my_neighbours[nodo_anterior]["Ativo"] = False
                                self.my_neighbours[nodo_anterior]["Streams"][StreamId][ant_anterior]["Ativo"] = False
                                lista= [StreamId,host_addr,ant_anterior]
                                mensagem = Message("11",host_addr,(nodo_anterior[0],4000),lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None, False))

                            if melhor_nodo == None and nodo_anterior == None:
                                print("\nAinda não tenho nodo para mandar essa stream")
                                self.my_neighbours[chave]["Ativo"] = True
                                self.my_neighbours[chave]["Streams"][StreamId][neto]["Ativo"] = True
                                lista = [StreamId, host_addr, neto]
                                
                                mensagem = Message("10", host_addr, (src, 4000), lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None, False))

                            self.pprint_viz()

                        elif message_data["id"] =="13":
                            ip,time_sent = message_data["data"]

                            time_now = int(time.time()*1000)
                            time_diff = time_now - time_sent
                            self.servidores[client_address]["Vivo"] = True
                            self.servidores[client_address]["Latencia"] = time_diff 
                            self.servidores[client_address]["Ativo"] = False   
                            print(f"\nservidores ativos {self.servidores.keys()}") 


                        elif message_data["id"] == "14":
                            if not self.have_stream:
                                #calcular o ip do melhor servidor
                                #mandar esta mensagem para pedir para straemmar

                                melhor_latencia = float('inf')
                                melhor_servidor = None


                                for k,v in self.servidores.items():
                                    if v["Latencia"]<melhor_latencia:
                                        melhor_latencia = v["Latencia"]
                                        melhor_nodo = k

                                self.servidores[melhor_nodo]["Ativo"] = True
                                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                                client_socket.connect((melhor_nodo, 4000))
                                message = Message("14",host_addr,(melhor_nodo,4000),"Stream")
                                self.process_queue.put((json.dumps(message.__dict__), client_socket, True))

                        elif message_data["id"] == "15":
                            if not self.have_stream:
                                #calcular o ip do melhor servidor
                                #mandar esta mensagem para pedir para straemmar
                                for k,v in self.servidores.items():
                                    if v["Ativo"]:
                                        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                                        client_socket.connect((k, 4000))
                                        message = Message("15",host_addr,(k,4000),"Stop")
                                        self.process_queue.put((json.dumps(message.__dict__), client_socket, True))


                    except json.JSONDecodeError as e:
                        print(f"\nRP [PROCESS TREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP [PROCESS TREAD] : Error in processing messages: {e}")

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

                        print(ip_destino)


                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                        #self.clients_sockets.append(client_socket)
                    try:
                        client_socket.send(data.encode())
                        print(f"\nRP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data} ")

                    except json.JSONDecodeError as e:
                        print(f"\nRP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP [SEND THREAD] :  Error sending message in the send_messages function: {e}")

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

                    time.sleep(10)
                    for v in self.my_neighbours.keys() :
                        self.connect_to_other_node(v[0],4000,2)
                    
                    print(f"\nRP : OS MEUS VIZINHOS: {self.my_neighbours}")

                    receive_thread.join()
                    process_thread.join()
                    send_thread.join()

            except Exception as e:
                print(f"\RP : An error occurred in start function: {e}")
            finally:
                #for client_socket in self.clients:
                #    client_socket.close()

                if self.rp_socket:
                    self.rp_socket.close()