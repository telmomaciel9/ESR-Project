import socket
import threading
import time

class ONodeUDP:
    def __init__(self):

        self.wg = threading.Event()
        self.threads = []

    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind(("0.0.0.0", 5000))
            return server_socket
        except socket.error as e:
            print(f"UDP : Socket Error: {e}")

    def udp_receive(self, socket):
        try:
            while not self.wg.is_set():
                data, remetente = socket.recvfrom(1024)
                print(f"UDP : Received message from {remetente}: {data.decode()}\n")
                # Process the received message as needed
        except Exception as e:
            print(f"UDP : An error occurred while receiving messages: {e}")

    def udp_send(self, socket, remetente, message):
        try:
            for i in range(5):
                time.sleep(2)
                print(f"UDP : Sending message to {remetente}: {message}\n")
                socket.sendto(message.encode(), remetente)
        except Exception as e:
            print(f"UDP : An error occurred while sending messages: {e}")

    def start(self):
        try:
            server_socket = self.create_and_bind_socket()
            #print(f"UDP : Listening on {self.server_ip}:{self.server_port} ")

            while not self.wg.is_set():
                data, remetente = server_socket.recvfrom(1024)

                receive_thread = threading.Thread(target=self.udp_receive, args=(server_socket,))
                send_thread = threading.Thread(target=self.udp_send, args=(server_socket, remetente, "UDP : Eu também :)"))

                receive_thread.start()
                send_thread.start()

        except Exception as e:
            print(f"UDP : An error occurred: {e}")
        finally:
            if server_socket:
                server_socket.close()
