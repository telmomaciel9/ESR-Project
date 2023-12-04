import socket
import threading
import time
import json  # for JSON serialization
import queue
import bisect
from Message import Message

class RP():
    def __init__(self, bootstrap_ip ):
        self.bootstrap_ip=bootstrap_ip

        self.wg = threading.Event()
        self.lock = threading.Lock()
        
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()

        self.my_neighbours= dict()
        self.netos = []

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
            print(f"  Streams : {v['Streams']}")
            print(f"  Netos : {v['Netos']}")
            print(f"  Visited : {v['Visited']}")
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
                    self.receive_queue.put([data, host_addr, client_address])

            except Exception as e:
                    print(f"\nRP : An error occurred while receiving messages: {e}")
    
    def escolher_melhor_nodo(self,StreamId):
        nodos_ativos = [nodo for nodo, info in self.my_neighbours.items() if info["Ativo"]]
    
        if not nodos_ativos:
            return None  # Nenhum caminho ativo no momento

        melhor_nodo = min(nodos_ativos, key=lambda nodo: self.my_neighbours[nodo]["Streams"][StreamId]["Soma_Acumulada"])
    
        return melhor_nodo


    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data,host_addr,client_address = self.receive_queue.get()
                    print(f"\nRP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                    try:
                        # Deserialize the JSON data into a Python object
                        message_data = json.loads(data.decode())

                        if message_data["id"] == "2":
                            info = message_data["data"]
                            result_string = json.loads(info)

                            for v in result_string:
                                self.my_neighbours[tuple(v)]= {"Vivo":False, "Ativo":False,"Peso_Aresta": 0,"Streams":{},"Netos":[],"Visited" : False}

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

                            # Operações críticas começam aqui
                            
                            self.my_neighbours[chave]["Peso_Aresta"] = tempo_diff
                            self.my_neighbours[chave]["Streams"] = {StreamId: {"Time_Sent_flood": time_sent_message, "Soma_Acumulada": soma_acumulada}}
                            self.my_neighbours[chave]["Visited"] = True
                            if "Neto" not in self.my_neighbours[chave]:
                                self.my_neighbours[chave]["Neto"] = []
                            if neto not in self.my_neighbours[chave]["Neto"]:
                                self.my_neighbours[chave]["Neto"].append(neto)

                            self.pprint_viz()
                            
                            melhor_nodo = self.escolher_melhor_nodo(StreamId)
                            print(melhor_nodo)
                            if melhor_nodo:
                                print(f"\nMelhor nodo escolhido: {melhor_nodo}")
                                # Envie a mensagem para o melhor caminho
                                lista = [StreamId, host_addr, time_sent_message, soma_acumulada_recebida]
                                mensagem = Message("10", host_addr, (melhor_nodo[0], 4000), lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None, False))
                            else:
                                self.my_neighbours[chave]["Ativo"] = True
                                lista = [StreamId, host_addr, time_sent_message, soma_acumulada_recebida]
                                mensagem = Message("10", host_addr, (src, 4000), lista)
                                self.process_queue.put((json.dumps(mensagem.__dict__), None, False))
                                print("\nAtivando novo caminho")

                            
                        
                        

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