import socket
import threading

class TCPServer:
    def __init__(self, bootstrap_ip, bootstrap_port, is_bootstrap):
        self.bootstrap_ip = bootstrap_ip
        self.bootstrap_port = int(bootstrap_port)
        self.wg = threading.Event()
        self.clients = set()
        self.is_bootstrap = is_bootstrap
        self.my_neighbours=set()

    def create_and_bind_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #host_name = server_socket   
            #print(f"ahhahahahahahahahah{socket.gethostbyname(socket.gethostname())}")
            server_socket.bind(("0.0.0.0",4000))
            return server_socket
        except socket.error as e:   
            print(f"TCP: Socket Error: {e}")

    def send_message(self, client_socket, message):
        try:
            client_socket.send(message.encode())
        except Exception as e:
            print(f"TCP: An error occurred while sending message: {e}")

    def receive_messages(self, client_socket):
        try:
            while not self.wg.is_set():
                data = client_socket.recv(1024)
                if not data:
                    break

                print(f"TCP: Received message from client: {data}")
                # Handle the received message as needed
        except Exception as e:
            print(f"TCP: An error occurred while receiving messages: {e}")

    def connect_to_bootstrap(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            client_socket.connect((self.bootstrap_ip, self.bootstrap_port))
            
            initial_message = "Hello Bootstrap"
            self.send_message(client_socket, initial_message)

            data = client_socket.recv(1024)
            
            decoded_data = data.decode()

            self.my_neighbours=decoded_data
            print(self.my_neighbours)

            self.send_message(client_socket,"3")

            
        except Exception as e:
            print(f"TCP: An error occurred while connecting to bootstrap: {e}")
        finally:
            if client_socket:
                client_socket.close()
    def start(self):
        try:

            server_socket = self.create_and_bind_socket()
            #print(127.0.0.1 )
            server_socket.listen(5)
            #print(f"TCP: Listening on {self.server_ip}:{self.server_port}")

            if not self.is_bootstrap:
                self.connect_to_bootstrap()

            while not self.wg.is_set():
                client_socket, client_address = server_socket.accept()
                self.clients.add(client_socket)

                receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
                send_thread = threading.Thread(target=self.send_message, args=(client_socket, b"Welcome to the server!\n"))

                receive_thread.start()
                send_thread.start()

        except Exception as e:
            print(f"TCP: An error occurred: {e}")
        finally:
            for client_socket in self.clients:
                client_socket.close()

            if server_socket:
                server_socket.close()