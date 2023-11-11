import socket
import threading
import sys


def parserArgs(arg):
    ip,porta = arg.split(":")
    return ip,int(porta)
'''
def create_and_connect_socket(server_ip,server_port):
    try:
        server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_socket.connect((server_ip,server_port))
        return server_socket
    except socket.error as e:
        print("---------------------------------->  Socket Error: {e}")
'''     

if __name__ == "__main__":

    try:
        server_ip,server_port = parserArgs(sys.argv[1])
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client_socket.connect((server_ip,server_port))
            # Send data to the server
        message = "Hello, server!"
        client_socket.send(message.encode())

        # Receive and process the server's response
        response = client_socket.recv(1024)
        print("Server response:", response.decode())
    except socket.error as e:
        print(f"---------------------------------->  Socket Error: {e}")
    finally:
        client_socket.close()    

'''
    server_ip,server_port = parserArgs(sys.argv[1])

    client_socket = create_and_connect_socket(server_ip,server_port)
    
    # Send data to the server
    message = "Hello, server!"
    client_socket.send(message.encode())

    # Receive and process the server's response
    response = client_socket.recv(1024)
    print("Server response:", response.decode())

    # Close the client socket
    client_socket.close()


'''