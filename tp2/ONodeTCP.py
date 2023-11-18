import socket
import threading
import queue
import json
import time

class ONodeTCP:
    def __init__(self, bootstrap_ip, is_bootstrap):
        self.bootstrap_ip = bootstrap_ip
        self.wg = threading.Event()
        self.clients = set()
        self.is_bootstrap = is_bootstrap
        self.my_neighbours= list()
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sockets = [] 


    def bind_socket(self):
        try:
            self.server_socket.bind(("0.0.0.0",4000))
        except socket.error as e:   
            print(f"TCP: Socket Error on Binding: {e}")

    def receive_messages(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                print(data)
                if not data:
                    break
                with self.lock:
                    self.receive_queue.put((data, client_socket))
        except Exception as e:
            print(f"TCP: An error occurred while receiving messages: {e}")

    def process_messages(self):
        while True:
            with self.lock:
                if not self.receive_queue.empty():
                    data, client_socket = self.receive_queue.get()
                    # Simulate processing the message
                    processed_message = f"Node {self.node_id}: Processed: {data.decode()}"
                    self.process_queue.put((processed_message, client_socket))

    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    processed_message, client_socket = self.process_queue.get()
                    # Simulate sending the message
                    sent_message = f"Node {self.node_id}: Sent: {processed_message}"
                    client_socket.send(sent_message.encode())

    def connect_to_other_node(self, ip, port, purpose):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempt_count = 0

        while attempt_count < 3:  # Adjust the maximum number of attempts as needed
            try:
                client_socket.connect((ip, port))

                if purpose == 1:
                    initial_message = "Hello Bootstrap"
                    self.send_queue.put((initial_message, len(self.client_sockets)))

                    data = client_socket.recv(1024)
                    decoded_data = data.decode()
                    print("decoded data")
                    print(decoded_data)
                    self.my_neighbours = json.loads(decoded_data)

                    print("neighbours")
                    print(self.my_neighbours)

                    self.send_queue.put(("3", len(self.client_sockets)))

                elif purpose == 2:
                    initial_message = "ola vizinho!!"
                    self.send_queue.put((initial_message, len(self.client_sockets)))
                    

                self.client_sockets.append(client_socket)
                break  # Exit the loop if the connection is successful

            except Exception as e:
                print(f"TCP: An error occurred while sending a message to another node: {e}")
                attempt_count += 1
                print(f"Retrying connection to {ip}:{port}... (Attempt {attempt_count})")
                time.sleep(2)  # Adjust the delay between attempts as needed

            finally:
                if not client_socket._closed:
                    client_socket.close()

        if attempt_count >= 3:
            print(f"Failed to establish a connection to {ip}:{port} after multiple attempts.")



    def start(self):
        try:
            #Dar bind ao self.server_socket de forma a que ele esteja disponível a ouvir
            self.bind_socket()
            self.server_socket.listen(5)
            #print(f"TCP: Listening on {self.server_ip}:{self.server_port}")



            if not self.is_bootstrap:
                self.connect_to_other_node(self.bootstrap_ip,3000,1)
                #self.process_queue.put(("Ola Bootrap",Bootstrap))

                for v in self.my_neighbours :
                    print(f"v - {v}")
                    self.connect_to_other_node(v,4000,2)
                    #self.process_queue.put(("ola viz",clientSocket))
                
            while not self.wg.is_set():
                client_socket, client_address = self.server_socket.accept()
                self.clients.add(client_socket)

                receive_thread = threading.Thread(target=self.receive_messages, args=(client_socket,))
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())

                receive_thread.start()
                process_thread.start()
                send_thread.start()

                receive_thread.join()
                process_thread.join()
                send_thread.join()

        except Exception as e:
            print(f"TCP: An error occurred: {e}")
        finally:
            for client_socket in self.clients:
                client_socket.close()

            if self.server_socket:
                self.server_socket.close()