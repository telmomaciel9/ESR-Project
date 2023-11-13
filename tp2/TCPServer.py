import socket
import threading
import time

class TCPServer:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.wg = threading.Event()
        self.clients = set()

    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.server_ip, self.server_port))
            return server_socket
        except socket.error as e:
            print(f"TCP : Socket Error: {e}")
    
    '''
    def tcp_aux(self, client_socket, client_address):
        print(f"TCP : Connected to: {client_address}")
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                if not data:
                    break

                for i in range(5):
                    time.sleep(2)
                    print(f"TCP : Received message from {client_address}: {data}")
                    response = b"TCP : Server received your message: " + data
                client_socket.send(response)
        except Exception as e:
            print(f"TCP : An error occurred: {e}")
        finally:
            print(f"TCP : Connection closed with {client_address}")
            client_socket.close()
            self.clients.remove(client_socket)
    '''

    def send_message(self, client_socket, message):
        try:
            client_socket.send(message)
        except Exception as e:
            print(f"TCP : An error occurred while sending message: {e}")

    def receive_messages(self, client_socket):
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                if not data:
                    break

                print(f"TCP : Received message from client: {data}")
                # Handle the received message as needed
        except Exception as e:
            print(f"TCP : An error occurred while receiving messages: {e}")

    def start(self):
        try:
            server_socket = self.create_and_bind_socket()
            server_socket.listen(5)
            print(f"TCP : Listening on {self.server_ip}:{self.server_port}")

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                self.clients.add(client_socket)

                receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
                send_thread = threading.Thread(target=self.send_message, args=(client_socket, b"Welcome to the server!\n"))

                receive_thread.start()
                send_thread.start()

        except Exception as e:
            print(f"TCP : An error occurred: {e}")
        finally:
            for client_socket in self.clients:
                client_socket.close()

            if server_socket:
                server_socket.close()