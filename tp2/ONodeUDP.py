import socket
import threading
import time
import queue

class ONodeUDP:
    def __init__(self,my_neighbours,have_stream):
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.my_neighbours = my_neighbours
        self.wg = threading.Event()
        self.threads = []
        self.have_stream = have_stream
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.server_socket.bind(("",3000))
        except socket.error as e:
            print(f"\nUDP: Socker Erro on Binding: {e}")


    def receive_messages(self):
        try:
            while not self.wg.is_set():
                data, remetente = self.server_socket.recvfrom(20480)
                print(f"UDP [Receive]: Received message from {remetente}: Pedido Recebido\n")
                self.receive_queue.put((data,remetente[0]))
        except Exception as e:
            print(f"\nUDP : An error occurred while receiving messages: {e}")

    def process_messages(self):
        try:
            while not self.wg.is_set():
                if not self.receive_queue.empty():
                    data, remetente = self.receive_queue.get()
                    print(f"\nUDP [Process] : Going to process this message: pedido de stream")

                    dest = None

                    for k,v in self.my_neighbours.items():
                        if v["Ativo"] and remetente not in k:
                            dest = k

                    self.process_queue.put((data,dest))
        except Exception as e:
            print(f"\nUDP [Process] : An error occured while processing messages: {e}")

    def send_messages(self):
        while True:
            send_soc = None
            try:
                if not self.process_queue.empty():
                    send_soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                    data,dest = self.process_queue.get()
                    if(isinstance(dest,tuple)):
                        send_soc.sendto(data, (dest[0],3000))
                    elif(isinstance(dest,str)):
                        send_soc.sendto(data,(dest,3000))
                    print(f"UDP : Sent message to {dest}: pedido stream\n")
            except Exception as e:
                print(f"\nUDP : An error occurred while sending messages: {e}")
            finally:
                if send_soc:
                    send_soc.close()

    def start(self):
        try:
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
            print(f"\nUDP : An error occurred: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

