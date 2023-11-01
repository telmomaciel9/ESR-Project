import socket
import threading
import time
import sys

class Database:
    def __init__(self):
        self.dados = {"coisas": 3, "jmf": -5, "redes": 1}
        self.lock = threading.Lock()

# Function to parse the arguments given in the command line and return the server IP and port
def rec_args(N_porta):
    if len(sys.argv) < 2:
        print("Usage: python3 server.py <server_ip:server_port>")
        sys.exit(1)

    if N_porta == 1:
        server_ip, server_port = sys.argv[1].split(":")
    elif N_porta == 2:
        server_ip, server_port = sys.argv[2].split(":")

    return server_ip, int(server_port)

# Function to create and bind the server socket
def bind_socket(server_ip, server_port):
    try:
        # Create the socket and bind it to listen
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((server_ip, server_port))
        return server_socket
    except socket.error as e:
        print(f"Socket error: {e}")

# Service 1 auxiliary function
def service1_aux(socket, remetente, mensagem):
    for i in range(5):
        time.sleep(2)
        print(f"Recebi uma mensagem do {remetente}: {mensagem}\n")

    socket.sendto("Eu também :)\n".encode(), remetente)

def service1(server_ip, server_port):
    try:
        # Bind the socket
        server_socket = bind_socket(server_ip, server_port)

        # While loop to be able to listen for more than one message
        # Threads to be able to process more packets at the same time
        while True:
            data, remetente = server_socket.recvfrom(1024)
            threading.Thread(target=service1_aux, args=(server_socket, remetente, data.decode())).start()

    # Handle with exceptions and close the socket at the end of the code block
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if server_socket:
            server_socket.close()

# Service 2 auxiliary function
def service2_aux(socket, remetente, mensagem, db):
    with db.lock:
        del db.dados["coisas"]
        del db.dados["redes"]

    for i in range(5):
        time.sleep(2)
        print("SUCESIUM\n")

    socket.sendto("SUCESIUM\n".encode(), remetente)

def service2(server_ip, server_port, db):
    try:
        # Bind the socket
        server_socket = bind_socket(server_ip, server_port)

        # While loop to be able to listen for more than one message
        # Threads to be able to process more packets at the same time
        while True:
            data, remetente = server_socket.recvfrom(1024)
            threading.Thread(target=service2_aux, args=(server_socket, remetente, data.decode(), db)).start()

    # Handle with exceptions and close the socket at the end of the code block
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if server_socket:
            server_socket.close()

# Service 3 function
def service3(db):
    while True:
        with db.lock:
            for key, value in db.dados.items():
                time.sleep(2)
                print(f"Chave: {key} || Valor inicial: {value} || Valor final: {db.dados[key]}\n")

if __name__ == "__main__":
    db = Database()

    threads = []
    wg = threading.Event()

    server_ip, server_port = rec_args(1)
    threads.append(threading.Thread(target=service1, args=(server_ip, server_port)))
    
    server_ip, server_port = rec_args(2)
    threads.append(threading.Thread(target=service2, args=(server_ip, server_port, db)))

    # Start the service3 function in a separate thread
    threads.append(threading.Thread(target=service3, args=(db,)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
