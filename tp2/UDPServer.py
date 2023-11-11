# udp_server.py
import socket
import threading
import time

class UDPServer:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.wg = threading.Event()
        self.threads = []

    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind((self.server_ip, self.server_port))
            return server_socket
        except socket.error as e:
            print(f"UDP : Socket Error: {e}")

    def udp_aux(self, socket, remetente, mensagem):
        for i in range(5):
            time.sleep(2)
            print(f"UDP : Recebi uma mensagem do {remetente}: {mensagem}\n")
        socket.sendto("UDP : Eu também :)\n".encode(), remetente)

    def start(self):
        try:
            server_socket = self.create_and_bind_socket()
            print(f"UDP : Estou a ouvir no ip: {self.server_ip} e na porta: {self.server_port} ")

            while not self.wg.is_set():
                data, remetente = server_socket.recvfrom(1024)
                thread = threading.Thread(target=self.udp_aux, args=(server_socket, remetente, data.decode()))
                self.threads.append(thread)
                thread.start()

        except Exception as e:
            print(f"UDP : An error occurred: {e}")
        finally:
            if server_socket:
                server_socket.close()
