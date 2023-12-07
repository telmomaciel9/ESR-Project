import socket
import threading
import queue
import json
import time
from Message import Message
import bisect


class ONodeTCP:
    def __init__(self, bootstrap_ip,my_neighbours,have_stream):
        self.bootstrap_ip = bootstrap_ip
        self.wg = threading.Event()
        self.clients_sockets = []
        self.my_neighbours= my_neighbours
        self.lock = threading.Lock()
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.have_stream = have_stream
        self.avo = {}
        self.netos = {} 

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind(("0.0.0.0",4000))
        except socket.error as e:   
            print(f"\nTCP : Socket Error on Binding: {e}")


        self.ping_interval = 30
        self.timeout_threshold = 60
       
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
                client_socket, client_address = self.server_socket.accept()
                print(f"\nTCP [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nTCP [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
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
                print(f"\nTCP : An error occurred while receiving messages: {e}")

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
                #print(f"ELEMENTOS NA RECEIVE QUEUE : {self.receive_queue.qsize()}")
                if not self.receive_queue.empty():
                    data, host_addr,client_address,isMessage = self.receive_queue.get()
                    print(f"\nTCP [PROCESS THREAD] : GOING TO PROCESS A MESSAGE : {data}")
                    
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
                                self.my_neighbours[tuple(v)]= {"Vivo":False, "Ativo":False,"Visited" : False,"last_received_time":0,"Peso_Aresta": 0,"Streams":{}}

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
                            self.my_neighbours[src]["last_received_time"] = time_now

                            if "Streams" not in self.my_neighbours[src]:
                                self.my_neighbours[src]["Streams"] = {}

                            
                            if StreamId not in self.my_neighbours[src]["Streams"].keys():
                                self.my_neighbours[src]["Streams"][StreamId] = {src: {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}}
                            else:
                                if src not in self.my_neighbours[src]["Streams"][StreamId].keys():
                                    self.my_neighbours[src]["Streams"][StreamId][src] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada,"Ativo":False}
                                else:
                                    if soma_acumulada < self.my_neighbours[src]["Streams"][StreamId][src]["Soma_Acumulada"]:
                                        self.my_neighbours[src]["Streams"][StreamId][src] = {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada, "Ativo":False}


                            self.pprint_viz()

                            if not self.have_stream:
                                for key,value in self.my_neighbours.items():
                                    if value["Vivo"] == True and client_address not in key:
                                        lista = [StreamId, src, time_now, soma_acumulada]
                                        print(f"\nkey ; {key[0]}")
                                        mensagem = Message("9",host_addr,(key[0],4000),lista)
                                        self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here
                            #fazer aqui quando tem a stram - vai ser muito parecido com o tipo de processo 10
                            if self.have_stream:
                                lista = [StreamId, src, time_now, soma_acumulada]
                                mensagem = Message("10",host_addr,(src,4000),lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None,False))  # Fix the typo here





        

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

                            if self.have_stream:
                                lista = [StreamId, src, time_now, soma_acumulada]
                                message = Message("10",host_addr,(src,4000),lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None,False))


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


                        #fazer para o tipo de dados 11 - quando pede para cnacelar
                        elif message_data["id"] == "11":
                            self.have_stream = False

                            StreamId,filho = message_data["data"]

                            src= message_data["src"]

                            next_node = tuple()
                            for n in self.my_neighbours.keys():
                                if filho in n:
                                    next_node = n


                            #neto = self.escolher_melhor_neto(next_node,StreamId)
                            self.my_neighbours[next_node]["Ativo"] = False
                            neto=None
                            for k,v in self.my_neighbours[next_node]["Streams"][StreamId]:
                                if v["Ativo"] == True:
                                    v["Ativo"] = False
                                    neto = k
                            lista = [StreamId,host_addr,neto]
                            message = Message("11",host_addr,(next_node[0],4000),lista)

                        elif message_data["id"] == "12":
                            time_sent_message = message_data["data"]
                            src = message_data["src"]

                            curr_time = int(time.time()*1000)
                            time_diff = curr_time-time_sent_message

                            for k,v in self.my_neighbours.items():
                                if curr_time - v["last_received_time"] >fself.timeout_threshold:
                                    v["Vivo"] = False


                        elif message_data["id"] == "14":
                            for k, v in self.my_neighbours.items():
                                if v["Ativo"] == True and client_address not in k:
                                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    client_socket.connect((k[0], 4000))
                                    message = Message("14",host_addr,(k[0],4000),"Stream")
                                    #sent_message = json.dumps(message.__dict__)
                                    self.process_queue.put((json.dumps(message.__dict__),client_socket,True))

                        elif message_data["id"] == "15":
                            for k, v in self.my_neighbours.items():
                                if v["Ativo"] == True and client_address not in k:
                                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    client_socket.connect((k[0], 4000))
                                    message = Message("15",host_addr,(k[0],4000),"Stop")
                                    #sent_message = json.dumps(message.__dict__)
                                    self.process_queue.put((json.dumps(messagem.__dict__),client_socket,True))



                    except json.JSONDecodeError as e:
                        print(f"\nTCP [PROCESS THREAD]  : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nTCP [PROCESS THREAD] : Error in processing messages: {e}")


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
                        self.clients_sockets.append(client_socket)
                    try:
                        client_socket.send(data.encode())
                        print(f"\nTCP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data} ")

                    except json.JSONDecodeError as e:
                        print(f"\nTCP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nTCP [SEND THREAD] :  Error sending message in the send_messages function: {e}")
                    
                            
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

            #elif purpose == 3:
            #    time_now= int(time.time()*1000)

            #    messagem = Message("12",client_socket.getsockname()[0],(ip,pora),time_now)
            #    self.process_queue.put((json.dumps(messagem.__dict__),client_socket,True))

            self.clients_sockets.append(client_socket)
            #break  # Exit the loop if the connection is successful
        #break
        except Exception as e:
            print(f"\nTCP: An error occurred while sending a message in connect_to_other_node function in ip {ip}: {e}")
            attempt_count += 1
            print(f"\nTCP : Retrying connection to {ip}:{port}... (Attempt {attempt_count})")
            time.sleep(2)  # Adjust the delay between attempts as needed
        
        #if attempt_count >= 3:
        #    print(f"\nFailed to establish a connection to {ip}:{port} after multiple attempts.")
    '''
    def check_neighbours_status(self):
        curr_time = int(time.time()*1000)
            for k,v in self.my_neighbours.items():
                if curr_time - v["last_received_time"] >fself.timeout_threshold:
                    v["Vivo"] = False
    

    def ping_neighbours(self):
        while True:
            self.check_neighbours_status()
            time.sleep(self.ping_interval)
    '''

    def start(self):
            try:
                self.server_socket.listen(5)

                while not self.wg.is_set():

                    receive_thread = threading.Thread(target=self.receive_messages, args=())
                    process_thread = threading.Thread(target=self.process_messages, args=())
                    send_thread = threading.Thread(target=self.send_messages, args=())
                    #ping_thread = threading.Thread(target=self.ping_neighbours, args=())
                    receive_thread.start()
                    process_thread.start()
                    send_thread.start()

                
                    self.connect_to_other_node(self.bootstrap_ip,4000,1)

                    time.sleep(10)
                    for v in self.my_neighbours.keys() :
                        self.connect_to_other_node(v[0],4000,2)
                    
                    #time.sleep(20)
                    #flag = True
                    #while flag:
                    #    for v in self.my_neighbours.keys():
                    #        self.connect_to_other_node(v[0],4000,3)
                    #    sleep(30)
                    
                    print(f"\nTCP : OS MEUS VIZINHOS: {self.my_neighbours}")
                    receive_thread.join()
                    process_thread.join()
                    send_thread.join()
                    #print("ola")

            except Exception as e:
                print(f"\TCP : An error occurred in start function: {e}")
            finally:
                for client_socket in self.clients_sockets:
                    client_socket.close()

                if self.server_socket:
                    self.server_socket.close()