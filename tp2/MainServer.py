# main_server.py
import sys
import threading
from TCPServer import TCPServer
from UDPServer import UDPServer
from bootstrap import Bootstrap

def parserArgs(arg):
    ip, porta = sys.argv[arg].split(":")
    return ip, int(porta)

class MainServer(Server):
    def __init__(self,tcp_server_ip, tcp_server_port, udp_server_ip, udp_server_port,bootstrap_ip,bootstrap_port,bootstrap_mode):
        self.wg = threading.Event()
        self.threads = []
        self.mode=bootstrap_mode
        if self.mode:
            self.bootstrap= Bootstrap(bootstrap_ip,bootstrap_port)
        self.tcp_server = TCPServer(tcp_server_ip, tcp_server_port)
        self.udp_server = UDPServer(udp_server_ip, udp_server_port)
        

    def start(self):
        self.threads.append(threading.Thread(target=self.tcp_server.start))
        self.threads.append(threading.Thread(target=self.udp_server.start))
        if self.mode:
            self.threads.append(threading.Thread(target=self.bootstrap.start))

        for thread in self.threads:
            thread.start()

    def stop(self):
        self.wg.set()
        for thread in self.threads:
            thread.join()
        self.tcp_server.stop()
        self.udp_server.stop()

if __name__ == "__main__":
    # in case bootstrap mode is 1, otherwise, it is equal to 0
    bootstrap_mode = 0
    bootstrap_ip = bootstrap_port = None  # Initialize to None

    if sys.argv[1] == "--b":
        bootstrap_mode = 1
        bootstrap_ip, bootstrap_port = parserArgs(2)
        tcp_server_ip, tcp_server_port = parserArgs(3)
        udp_server_ip, udp_server_port = parserArgs(4)
    else:
        tcp_server_ip, tcp_server_port = parserArgs(1)
        udp_server_ip, udp_server_port = parserArgs(2)

    main_server = MainServer(tcp_server_ip, tcp_server_port, udp_server_ip, udp_server_port, bootstrap_ip, bootstrap_port, bootstrap_mode)
    main_server.start()