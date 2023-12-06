import socket
import threading
import time
import queue

class ONodeUDP:
    def __init__(self,my_neighbours):
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.wg = threading.Event()
        self.threads = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.server_socket.bind(("",3000))
        except socket.error as e:
            print(f"\nUDP: Socker Erro on Binding: {e}")


    def receive_messages(self):
        try:
            while not self.wg.is_set():
                data, remetente = self.server_socket.recvfrom(1024)
                print(f"UDP [Receive]: Received message from {remetente}: {data}\n")
                self.receive_queue.put(data,remetente)
        except Exception as e:
            print(f"\nUDP : An error occurred while receiving messages: {e}")

    def process_messages(self):
        try:
            if not self.receive_queue.empty():
                data, remetente = self.receive_queue.get()
                print(f"\nUDP [Process] : Going to process this message: {data}")

                dest = None

                for k,v in self.my_neighbours.items():
                    if v["Ativo"]:
                        dest = k


                self.process_queue.put(data,dest)
        except Exception as e:
            print(f"\nUDP [Process] : An error occured while processing messages: {e}")

    def send_messages(self):
        try:
            if not self.process_queue.empty():
                data,dest = self.process_queue.get()
                socket.sendto(data.encode(), dest)
                print(f"UDP : Sent message to {dest}: {data}\n")
        except Exception as e:
            print(f"\nUDP : An error occurred while sending messages: {e}")

    def start(self):
        try:
            receive_thread = threading.Thread(target=self.receive_messages, args=())
            process_thread = threading.Thread(target=self.process_messages, args=())
            send_thread = threading.Thread(target=self.send_messages, args=())

            self.threads.extend([receive_thread, process_thread, send_thread])

            for thread in self.threads:
                thread.start()

            for thread in self.threads:
                thread.join()

        except Exception as e:
            print(f"\nUDP : An error occurred: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

